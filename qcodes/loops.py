"""
Data acquisition loops.

The general scheme is:

1. create a (potentially nested) Loop, which defines the sweep setpoints and
delays

2. activate the loop (which changes it to an ActiveLoop object),
or omit this step to use the default measurement as given by the
Loop.set_measurement class method.

3. run it with the .run method, which creates a DataSet to hold the data,
and defines how and where to save the data.

Some examples:

- set default measurements for later Loop's to use

>>> Loop.set_measurement(param1, param2, param3)

- 1D sweep, using the default measurement set

>>> Loop(sweep_values, delay).run()

- 2D sweep, using the default measurement set sv1 is the outer loop, sv2 is the
  inner.

>>> Loop(sv1, delay1).loop(sv2, delay2).run()

- 1D sweep with specific measurements to take at each point

>>> Loop(sv, delay).each(param4, param5).run()

- Multidimensional sweep: 1D measurement of param6 on the outer loop, and the
  default measurements in a 2D loop

>>> Loop(sv1, delay).each(param6, Loop(sv2, delay)).run()

Supported commands to .set_measurement or .each are:

    - Parameter: anything with a .get method and .name or .names see
      parameter.py for options
    - ActiveLoop (or Loop, will be activated with default measurement)
    - Task: any callable that does not generate data
    - Wait: a delay
"""

from datetime import datetime
import logging
import time
import numpy as np
from tqdm.auto import tqdm

from qcodes.station import Station
from qcodes.data.data_set import new_data, load_data
from qcodes.data.data_array import DataArray
from qcodes.utils.helpers import wait_secs, full_class, tprint
from qcodes.utils.metadata import Metadatable
from qcodes.instrument.parameter import MultiParameter

from .actions import (_actions_snapshot, Task, Wait, _Measure, _Nest,
                      BreakIf, _QcodesBreak)


log = logging.getLogger(__name__)


def param_move(param_name,end_value,steps=101,step_time=0.03):
    start_value = param_name()
    for i in range(0,steps):
        param_name(start_value + (end_value - start_value)/(steps-1) * i)
        time.sleep(step_time)
    param_name(end_value)

def active_loop():
    return ActiveLoop.active_loop


def active_data_set():
    loop = active_loop()
    if loop is not None and loop.data_set is not None:
        return loop.data_set
    else:
        return None


class Loop(Metadatable):
    """
    The entry point for creating measurement loops

    Args:
        sweep_values: a SweepValues or compatible object describing what
            parameter to set in the loop and over what values
        delay: a number of seconds to wait after setting a value before
            continuing. 0 (default) means no waiting and no warnings. > 0
            means to wait, potentially filling the delay time with monitoring,
            and give an error if you wait longer than expected.
        progress_interval: should progress of the loop every x seconds. Default
            is None (no output)

    After creating a Loop, you attach one or more ``actions`` to it, making an
    ``ActiveLoop``

    TODO:
        how? Maybe obvious but not specified! that you can ``.run()``,
        or you can ``.run()`` a ``Loop`` directly, in which
        case it takes the default ``actions`` from the default ``Station``

    ``actions`` is a sequence of things to do at each ``Loop`` step: that can be
    a ``Parameter`` to measure, a ``Task`` to do (any callable that does not
    yield data), ``Wait`` times, or another ``ActiveLoop`` or ``Loop`` to nest
    inside this one.
    """
    def __init__(self, sweep_values, delay=0, station=None,
                 progress_interval=None,progress_bar=True):
        super().__init__()
        if delay < 0:
            raise ValueError('delay must be > 0, not {}'.format(repr(delay)))

        self.sweep_values = sweep_values
        self.delay = delay
        self.station = station
        self.nested_loop = None
        self.actions = None
        self.then_actions = ()
        self.bg_task = None
        self.bg_final_task = None
        self.bg_min_delay = None
        self.progress_interval = progress_interval
        self.progress_bar=progress_bar

    def __getitem__(self, item):
        """
        Retrieves action with index `item`
        Args:
            item: actions index

        Returns:
            loop.actions[item]
        """
        return self.actions[item]

    def loop(self, sweep_values, delay=0):
        """
        Nest another loop inside this one.

        Args:
            sweep_values ():
            delay (int):

        Examples:
            >>> Loop(sv1, d1).loop(sv2, d2).each(*a)

            is equivalent to:

            >>> Loop(sv1, d1).each(Loop(sv2, d2).each(*a))

        Returns: a new Loop object - the original is untouched
        """
        out = self._copy()

        if out.nested_loop:
            # nest this new loop inside the deepest level
            out.nested_loop = out.nested_loop.loop(sweep_values, delay)
        else:
            out.nested_loop = Loop(sweep_values, delay)

        return out

    def _copy(self):
        out = Loop(self.sweep_values, self.delay,
                   progress_interval=self.progress_interval)
        out.nested_loop = self.nested_loop
        out.then_actions = self.then_actions
        out.station = self.station
        return out

    def each(self, *actions):
        """
        Perform a set of actions at each setting of this loop.
        TODO(setting vs setpoints) ? better be verbose.

        Args:
            *actions (Any): actions to perform at each setting of the loop

        Each action can be:

        - a Parameter to measure
        - a Task to execute
        - a Wait
        - another Loop or ActiveLoop

        """

        actions = list(actions)
        # check for nested Loops, and activate them with default measurement
        for i, action in enumerate(actions):
            if isinstance(action, Loop):
                default = Station.default.default_measurement
                actions[i] = action.each(*default)

        if isinstance(self.sweep_values.parameter,MultiParameter):
            # If this loop is an outer loop, the MultiParameter components need to get sent to
            # the inner loop. This isn't recursive, so it will only work for up to 2D loops.
            # The day where we actually run 3D loops.... we will think about it.
            if any(isinstance(action, ActiveLoop) for action in actions):
                for i, action in enumerate(actions):
                    if isinstance(action, ActiveLoop):
                        action.actions = [self.sweep_values.parameter,*action.actions]
            else:
                actions=[self.sweep_values.parameter,*actions]

        self.validate_actions(*actions)

        if self.nested_loop:
            # recurse into the innermost loop and apply these actions there
            actions = [self.nested_loop.each(*actions)]

        return ActiveLoop(self.sweep_values, self.delay, *actions,
                          then_actions=self.then_actions, station=self.station,
                          progress_interval=self.progress_interval,
                          bg_task=self.bg_task, bg_final_task=self.bg_final_task, bg_min_delay=self.bg_min_delay)

    def with_bg_task(self, task, bg_final_task=None, min_delay=0.01):
        """
        Attaches a background task to this loop.

        Args:
            task: A callable object with no parameters. This object will be
                invoked periodically during the measurement loop.

            bg_final_task: A callable object with no parameters. This object will be
                invoked to clean up after or otherwise finish the background
                task work.

            min_delay (default 0.01): The minimum number of seconds to wait
                between task invocations.
                Note that if a task is doing a lot of processing it is recommended
                to increase min_delay.
                Note that the actual time between task invocations may be much
                longer than this, as the task is only run between passes
                through the loop.
        """
        return _attach_bg_task(self, task, bg_final_task, min_delay)

    @staticmethod
    def validate_actions(*actions):
        """
        Whitelist acceptable actions, so we can give nice error messages
        if an action is not recognized
        """
        for action in actions:
            if isinstance(action, (Task, Wait, BreakIf, ActiveLoop)):
                continue
            if hasattr(action, 'get') and (hasattr(action, 'name') or
                                           hasattr(action, 'names')):
                continue
            raise TypeError('Unrecognized action:', action,
                            'Allowed actions are: objects (parameters) with '
                            'a `get` method and `name` or `names` attribute, '
                            'and `Task`, `Wait`, `BreakIf`, and `ActiveLoop` '
                            'objects. `Loop` objects are OK too, except in '
                            'Station default measurements.')

    def run(self, *args, **kwargs):
        """
        shortcut to run a loop with the default measurement set
        stored by Station.set_measurement
        """
        default = Station.default.default_measurement
        return self.each(*default).run(*args, **kwargs)

    def run_temp(self, *args, **kwargs):
        """
        shortcut to run a loop in the foreground as a temporary dataset
        using the default measurement set
        """
        return self.run(*args, quiet=True, location=False, **kwargs)

    def then(self, *actions, overwrite=False):
        """
        Attach actions to be performed after the loop completes.

        These can only be ``Task`` and ``Wait`` actions, as they may not generate
        any data.

        returns a new Loop object - the original is untouched

        This is more naturally done to an ActiveLoop (ie after .each())
        and can also be done there, but it's allowed at this stage too so that
        you can define final actions and share them among several ``Loops`` that
        have different loop actions, or attach final actions to a Loop run

        TODO:
            examples of this ? with default actions.

        Args:
            *actions: ``Task`` and ``Wait`` objects to execute in order

            overwrite: (default False) whether subsequent .then() calls (including
                calls in an ActiveLoop after .then() has already been called on
                the Loop) will add to each other or overwrite the earlier ones.
        Returns:
            a new Loop object - the original is untouched
        """
        return _attach_then_actions(self._copy(), actions, overwrite)

    def snapshot_base(self, update=False):
        """
        State of the loop as a JSON-compatible dict.

        Args:
            update (bool): If True, update the state by querying the underlying
             sweep_values and actions. If False, just use the latest values in
             memory.

        Returns:
            dict: base snapshot
        """
        return {
            '__class__': full_class(self),
            'sweep_values': self.sweep_values.snapshot(update=update),
            'delay': self.delay,
            'then_actions': _actions_snapshot(self.then_actions, update)
        }


def _attach_then_actions(loop, actions, overwrite):
    """Inner code for both Loop.then and ActiveLoop.then."""
    for action in actions:
        if not isinstance(action, (Task, Wait)):
            raise TypeError('Unrecognized action:', action,
                            '.then() allows only `Task` and `Wait` '
                            'actions.')

    if overwrite:
        loop.then_actions = actions
    else:
        loop.then_actions = loop.then_actions + actions

    return loop


def _attach_bg_task(loop, task, bg_final_task, min_delay):
    """Inner code for both Loop and ActiveLoop.bg_task"""
    if loop.bg_task is None:
        loop.bg_task = task
        loop.bg_min_delay = min_delay
    else:
        raise RuntimeError('Only one background task is allowed per loop')

    if bg_final_task:
        loop.bg_final_task = bg_final_task

    return loop


class ActiveLoop(Metadatable):
    """
    Created by attaching ``actions`` to a ``Loop``, this is the object that
    actually runs a measurement loop. An ``ActiveLoop`` can no longer be nested,
    only run, or used as an action inside another ``Loop`` which will run the
    whole thing.

    The ``ActiveLoop`` determines what ``DataArrays`` it will need to hold the
    data it collects, and it creates a ``DataSet`` holding these ``DataArrays``
    """

    # Currently active loop, is set when calling loop.run(set_active=True)
    # is reset to None when active measurement is finished
    active_loop = None

    def __init__(self, sweep_values, delay, *actions, then_actions=(),
                 station=None, progress_interval=None, bg_task=None,
                 bg_final_task=None, bg_min_delay=None,progress_bar=True):
        super().__init__()
        self.sweep_values = sweep_values
        self.delay = delay
        self.actions = list(actions)
        self.progress_interval = progress_interval
        self.then_actions = then_actions
        self.station = station
        self.bg_task = bg_task
        self.bg_final_task = bg_final_task
        self.bg_min_delay = bg_min_delay
        self.data_set = None
        self.progress_bar=progress_bar
        self.was_broken=False

        # if the first action is another loop, it changes how delays
        # happen - the outer delay happens *after* the inner var gets
        # set to its initial value
        self._nest_first = hasattr(actions[0], 'containers')

    def __getitem__(self, item):
        """
        Retrieves action with index `item`
        Args:
            item: actions index

        Returns:
            loop.actions[item]
        """
        return self.actions[item]

    def then(self, *actions, overwrite=False):
        """
        Attach actions to be performed after the loop completes.

        These can only be ``Task`` and ``Wait`` actions, as they may not
        generate any data.

        returns a new ActiveLoop object - the original is untouched



        Args:
            *actions: ``Task`` and ``Wait`` objects to execute in order

            overwrite: (default False) whether subsequent .then() calls (including
                calls in an ActiveLoop after .then() has already been called on
                the Loop) will add to each other or overwrite the earlier ones.
        """
        loop = ActiveLoop(self.sweep_values, self.delay, *self.actions,
                          then_actions=self.then_actions, station=self.station)
        return _attach_then_actions(loop, actions, overwrite)

    def with_bg_task(self, task, bg_final_task=None, min_delay=0.01):
        """
        Attaches a background task to this loop.

        Args:
            task: A callable object with no parameters. This object will be
                invoked periodically during the measurement loop.

            bg_final_task: A callable object with no parameters. This object will be
                invoked to clean up after or otherwise finish the background
                task work.

            min_delay (default 1): The minimum number of seconds to wait
                between task invocations. Note that the actual time between
                task invocations may be much longer than this, as the task is
                only run between passes through the loop.
        """
        return _attach_bg_task(self, task, bg_final_task, min_delay)

    def snapshot_base(self, update=False):
        """Snapshot of this ActiveLoop's definition."""
        return {
            '__class__': full_class(self),
            'sweep_values': self.sweep_values.snapshot(update=update),
            'delay': self.delay,
            'actions': _actions_snapshot(self.actions, update),
            'then_actions': _actions_snapshot(self.then_actions, update)
        }

    def containers(self):
        """
        Finds the data arrays that will be created by the actions in this
        loop, and nests them inside this level of the loop.

        Recursively calls `.containers` on any enclosed actions.
        """
        loop_size = len(self.sweep_values)
        data_arrays = []
        # For MultiParameter sweeps, make sure the setpoint array gets the correct labelling and units
        if isinstance(self.sweep_values.parameter,MultiParameter):
            if np.shape(np.shape(self.sweep_values))[0]==1:
                loop_array = DataArray(parameter=self.sweep_values.parameter,
                               is_setpoint=True,name=self.sweep_values.parameter.name,unit=self.sweep_values.parameter.parameters[0].unit)
            else:
                loop_array = DataArray(parameter=self.sweep_values.parameter,
                               is_setpoint=True,name=self.sweep_values.parameter.name+'_index',unit='')
        
        else:    
            loop_array = DataArray(parameter=self.sweep_values.parameter,
                               is_setpoint=True,data_type=self.sweep_values.parameter.data_type)
        loop_array.nest(size=loop_size)

        data_arrays = [loop_array]
        # hack set_data into actions
        new_actions = self.actions[:]
        if hasattr(self.sweep_values, "parameters"): # combined or multi parameter
            for parameter in self.sweep_values.parameters:
                new_actions.append(parameter)

        for i, action in enumerate(new_actions):
            if hasattr(action, 'containers'):
                action_arrays = action.containers()

            elif hasattr(action, 'get'):
                # this action is a parameter to measure
                # note that this supports lists (separate output arrays)
                # and arrays (nested in one/each output array) of return values
                action_arrays = self._parameter_arrays(action)
            else:
                # this *is* covered but the report misses it because Python
                # optimizes it away. See:
                # https://bitbucket.org/ned/coveragepy/issues/198
                continue  # pragma: no cover

            for array in action_arrays:
                array.nest(size=loop_size, action_index=i,
                           set_array=loop_array)
            data_arrays.extend(action_arrays)
        return data_arrays

    def _parameter_arrays(self, action):
        out = []

        # first massage all the input parameters to the general multi-name form
        if hasattr(action, 'names'):
            names = action.names
            full_names = action.full_names
            labels = getattr(action, 'labels', names)
            if len(labels) != len(names):
                raise ValueError('must have equal number of names and labels')
            action_indices = tuple((i,) for i in range(len(names)))
        elif hasattr(action, 'name'):
            names = (action.name,)
            full_names = (action.full_name,)
            labels = (getattr(action, 'label', action.name),)
            action_indices = ((),)
        else:
            raise ValueError('a gettable parameter must have .name or .names')
        if hasattr(action, 'names') and hasattr(action, 'units'):
            units = action.units
        elif hasattr(action, 'unit'):
            units = (action.unit,)
        else:
            units = tuple(['']*len(names))
        num_arrays = len(names)
        shapes = getattr(action, 'shapes', None)
        sp_vals = getattr(action, 'setpoints', None)
        sp_names = getattr(action, 'setpoint_names', None)
        sp_labels = getattr(action, 'setpoint_labels', None)
        sp_units = getattr(action, 'setpoint_units', None)

        if shapes is None:
            shapes = (getattr(action, 'shape', ()),) * num_arrays
            sp_vals = (sp_vals,) * num_arrays
            sp_names = (sp_names,) * num_arrays
            sp_labels = (sp_labels,) * num_arrays
            sp_units = (sp_units,) * num_arrays
        else:
            sp_blank = (None,) * num_arrays
            # _fill_blank both supplies defaults and tests length
            # if values are supplied (for shapes it ONLY tests length)
            shapes = self._fill_blank(shapes, sp_blank)
            sp_vals = self._fill_blank(sp_vals, sp_blank)
            sp_names = self._fill_blank(sp_names, sp_blank)
            sp_labels = self._fill_blank(sp_labels, sp_blank)
            sp_units = self._fill_blank(sp_units, sp_blank)

        # now loop through these all, to make the DataArrays
        # record which setpoint arrays we've made, so we don't duplicate
        all_setpoints = {}
        for name, full_name, label, unit, shape, i, sp_vi, sp_ni, sp_li, sp_ui in zip(
                names, full_names, labels, units, shapes, action_indices,
                sp_vals, sp_names, sp_labels, sp_units):

            if shape is None or shape == ():
                shape, sp_vi, sp_ni, sp_li, sp_ui= (), (), (), (), ()
            else:
                sp_blank = (None,) * len(shape)
                sp_vi = self._fill_blank(sp_vi, sp_blank)
                sp_ni = self._fill_blank(sp_ni, sp_blank)
                sp_li = self._fill_blank(sp_li, sp_blank)
                sp_ui = self._fill_blank(sp_ui, sp_blank)

            setpoints = ()
            # loop through dimensions of shape to make the setpoint arrays
            for j, (vij, nij, lij, uij) in enumerate(zip(sp_vi, sp_ni, sp_li, sp_ui)):
                sp_def = (shape[: 1 + j], j, setpoints, vij, nij, lij, uij)
                if sp_def not in all_setpoints:
                    all_setpoints[sp_def] = self._make_setpoint_array(*sp_def)
                    out.append(all_setpoints[sp_def])
                setpoints = setpoints + (all_setpoints[sp_def],)

            # finally, make the output data array with these setpoints

            out.append(DataArray(name=name, full_name=full_name, label=label,
                                 shape=shape, action_indices=i, unit=unit,
                                 set_arrays=setpoints, parameter=action, data_type=action.data_type))
        return out

    def _fill_blank(self, inputs, blanks):
        if inputs is None:
            return blanks
        elif len(inputs) == len(blanks):
            return inputs
        else:
            raise ValueError('Wrong number of inputs supplied')

    def _make_setpoint_array(self, shape, i, prev_setpoints, vals, name,
                             label, unit):
        if vals is None:
            vals = self._default_setpoints(shape)
        elif isinstance(vals, DataArray):
            # can't simply use the DataArray, even though that's
            # what we're going to return here, because it will
            # get nested (don't want to alter the original)
            # DataArrays do have the advantage though of already including
            # name and label, so take these if they exist
            if vals.name is not None:
                name = vals.name
            if vals.label is not None:
                label = vals.label

            # extract a copy of the numpy array
            vals = np.array(vals.ndarray)
        else:
            # turn any sequence into a (new) numpy array
            vals = np.array(vals)

        if vals.shape != shape:
            raise ValueError('nth setpoint array should have shape matching '
                             'the first n dimensions of shape.')

        if name is None:
            name = 'index{}'.format(i)

        return DataArray(name=name, label=label, set_arrays=prev_setpoints,
                         shape=shape, preset_data=vals, unit=unit, is_setpoint=True)

    def _default_setpoints(self, shape):
        if len(shape) == 1:
            return np.arange(0, shape[0], 1)

        sp = np.ndarray(shape)
        sp_inner = self._default_setpoints(shape[1:])
        for i in range(len(sp)):
            sp[i] = sp_inner

        return sp

    def set_common_attrs(self, data_set, use_threads):
        """
        set a couple of common attributes that the main and nested loops
        all need to have:
        - the DataSet collecting all our measurements
        - a queue for communicating with the main process
        """
        self.data_set = data_set
        self.use_threads = use_threads
        for action in self.actions:
            if hasattr(action, 'set_common_attrs'):
                action.set_common_attrs(data_set, use_threads)

    def get_data_set(self, *args, **kwargs):
        """
        Return the data set for this loop.

        If no data set has been created yet, a new one will be created and
        returned. Note that all arguments can only be provided when the
        `DataSet` is first created; giving these during `run` when
        `get_data_set` has already been called on its own is an error.

        Args:
            data_manager: a DataManager instance (omit to use default,
                False to store locally)

        kwargs are passed along to data_set.new_data. The key ones are:

        Args:
            location: the location of the DataSet, a string whose meaning
                depends on formatter and io, or False to only keep in memory.
                May be a callable to provide automatic locations. If omitted, will
                use the default DataSet.location_provider
            name: if location is default or another provider function, name is
                a string to add to location to make it more readable/meaningful
                to users
            formatter: knows how to read and write the file format
                default can be set in DataSet.default_formatter
            io: knows how to connect to the storage (disk vs cloud etc)
            write_period: how often to save to storage during the loop.
                default 5 sec, use None to write only at the end

        returns:
            a DataSet object that we can use to plot
        """
        if self.data_set is None:
            data_set = new_data(arrays=self.containers(), *args, **kwargs)
            self.data_set = data_set

        else:
            has_args = len(kwargs) or len(args)
            if has_args:
                raise RuntimeError(
                    'The DataSet for this loop already exists. '
                    'You can only provide DataSet attributes, such as '
                    'data_manager, location, name, formatter, io, '
                    'write_period, when the DataSet is first created.')

        return self.data_set

    def time_estimate(self,station=None,extra_delay=[0,0]):
        """
        Give the user an estimate of how long their measurement will take
        extra_delay must be an array with the same shape as the loop. Outerloop as 0, inner loop(s) as 1
        Currently only works for 1D or 2D loops, including 2D loops with multiple subloops.
        """
        if self.data_set is None:
            raise RuntimeError('No DataSet yet defined for this loop')
        station = station or self.station or Station.default
        if station is None:
            print('Note: Station not declared. Estimate does not include'
                    'an estimate of communication time.')
        else:
            commtime=np.average(station.communication_time(measurement_num=10))

        estimate=self.sweep_values.snapshot()['values'][0]['num']*(commtime+self.delay+extra_delay[0])
        for action in self.actions:
            if isinstance(action, ActiveLoop):
                estimate=estimate+self.sweep_values.snapshot()['values'][0]['num']*action.sweep_values.snapshot()['values'][0]['num']*(commtime+action.delay+extra_delay[1])
        
        print(f'Estimated time: {estimate} s, {estimate/60} mins, {estimate/3600} hours')
        print(f'Done at: {time.asctime(time.localtime(time.time()+estimate))}')


        #return estimate

    def run_temp(self, **kwargs):
        """
        wrapper to run this loop in the foreground as a temporary data set,
        especially for use in composite parameters that need to run a Loop
        as part of their get method
        """
        return self.run(quiet=True, location=False, **kwargs)

    def run(self, use_threads=False, quiet=False, station=None,
            progress_interval=False, set_active=True, publisher=None,
            progress_bar=True, check_written_data=True,
            *args, **kwargs):
        """
        Execute this loop.

        Args:
            use_threads: (default False): whenever there are multiple `get` calls
                back-to-back, execute them in separate threads so they run in
                parallel (as long as they don't block each other)
            quiet: (default False): set True to not print anything except errors
            station: a Station instance for snapshots (omit to use a previously
                provided Station, or the default Station)
            progress_interval (default None): show progress of the loop every x
                seconds. If provided here, will override any interval provided
                with the Loop definition

        kwargs are passed along to data_set.new_data. These can only be
        provided when the `DataSet` is first created; giving these during `run`
        when `get_data_set` has already been called on its own is an error.
        The key ones are:

        Args:
            location: the location of the DataSet, a string whose meaning
                depends on formatter and io, or False to only keep in memory.
                May be a callable to provide automatic locations. If omitted, will
                use the default DataSet.location_provider
            name: if location is default or another provider function, name is
                a string to add to location to make it more readable/meaningful
                to users
            formatter: knows how to read and write the file format
                default can be set in DataSet.default_formatter
            io: knows how to connect to the storage (disk vs cloud etc)
                write_period: how often to save to storage during the loop.
                default 5 sec, use None to write only at the end


        returns:
            a DataSet object that we can use to plot
        """
        self.progress_bar=progress_bar
        if progress_interval is not False:
            self.progress_interval = progress_interval

        data_set = self.get_data_set(*args, **kwargs)
        if publisher is not None:
            data_set.publisher = publisher

        self.set_common_attrs(data_set=data_set, use_threads=use_threads)

        station = station or self.station or Station.default
        if station:
            data_set.add_metadata({'station': station.snapshot()})

        # information about the loop definition is in its snapshot
        data_set.add_metadata({'loop': self.snapshot()})
        # then add information about how and when it was run
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_set.add_metadata({'loop': {
            'ts_start': ts,
            'use_threads': use_threads,
        }})

        data_set.save_metadata()

        if set_active:
            ActiveLoop.active_loop = self

        try:
            if not quiet:
                print(datetime.now().strftime('Started at %Y-%m-%d %H:%M:%S'))
            self._run_wrapper()
            ds = self.data_set

        finally:
            if not quiet:
                print(repr(self.data_set))
                print(datetime.now().strftime('Finished at %Y-%m-%d %H:%M:%S'))
            
            # Check if the data written to file matches that in memory.
            # If not, save a copy and warn the user.
            if check_written_data==True:
                try:
                    writtendata=load_data(self.data_set.location)
                    for array in self.data_set.arrays:
                        if self.data_set.arrays[array].data_type==float:
                            if not np.array_equal(writtendata.arrays[array],self.data_set.arrays[array],equal_nan=True):
                                self.data_set.write_copy(self.data_set.location+'/copy')
                                #print(self.data_set.arrays[array],writtendata.arrays[array])
                                log.warning('Data in memory found to be different from data written to file. '
                                        'A copy of the data in memory has been saved at '
                                        f'{self.data_set.location}/copy. Please check the data for consistency.')
                                break
                # If anything fails for any reason, write a copy anyway, since everything above should always work and
                # there are almost certainly problems if something doesn't.
                except Exception as e:
                    self.data_set.write_copy(self.data_set.location+'/copy')
                    log.warning('Data in memory found to be different from data written to file. '
                                'A copy of the data in memory has been saved at '
                                f'{self.data_set.location}/copy. Please check the data for consistency.\n'
                                f'Exception: {e}')

            # After normal loop execution we clear the data_set so we can run
            # again. But also if something went wrong during the loop execution
            # we want to clear the data_set attribute so we don't try to reuse
            # this one later.
            self.data_set = None
            if set_active:
                ActiveLoop.active_loop = None

        return ds

    def _compile_actions(self, actions, action_indices=()):
        callables = []
        measurement_group = []
        for i, action in enumerate(actions):
            new_action_indices = action_indices + (i,)
            if hasattr(action, 'get'):
                measurement_group.append((action, new_action_indices))
                continue
            elif measurement_group:
                callables.append(_Measure(measurement_group, self.data_set,
                                          self.use_threads))
                measurement_group[:] = []

            callables.append(self._compile_one(action, new_action_indices))

        if measurement_group:
            callables.append(_Measure(measurement_group, self.data_set,
                                      self.use_threads))
            measurement_group[:] = []

        return callables

    def _compile_one(self, action, new_action_indices):
        if isinstance(action, Wait):
            return Task(self._wait, action.delay)
        elif isinstance(action, ActiveLoop):
            return _Nest(action, new_action_indices)
        else:
            return action

    def _run_wrapper(self, *args, **kwargs):
        try:
            self._run_loop(*args, **kwargs)
        finally:
            if hasattr(self, 'data_set'):
                # TODO (giulioungaretti) WTF?
                # somehow this does not show up in the data_set returned by
                # run(), but it is saved to the metadata
                ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.data_set.add_metadata({'loop': {'ts_end': ts}})
                self.data_set.finalize()

    def _run_loop(self, first_delay=0, action_indices=(),
                  loop_indices=(), current_values=(),
                  **ignore_kwargs):
        """
        the routine that actually executes the loop, and can be called
        from one loop to execute a nested loop

        first_delay: any delay carried over from an outer loop
        action_indices: where we are in any outer loop action arrays
        loop_indices: setpoint indices in any outer loops
        current_values: setpoint values in any outer loops
        signal_queue: queue to communicate with main process directly
        ignore_kwargs: for compatibility with other loop tasks
        """

        # at the beginning of the loop, the time to wait after setting
        # the loop parameter may be increased if an outer loop requested longer
        delay = max(self.delay, first_delay)

        callables = self._compile_actions(self.actions, action_indices)
        n_callables = 0
        for item in callables:
            if hasattr(item, 'param_ids'):
                n_callables += len(item.param_ids)
            else:
                n_callables += 1
        t0 = time.time()
        last_task = t0
        imax = len(self.sweep_values)

        self.last_task_failed = False

        station = self.station or Station.default
        if 'timer' in self.data_set.arrays:
            station.timer.reset_clock()

        # If the parameter to be swept is the outermost loop it is the zeroth array element.
        # Run tqdm in this instance to only give a progress bar for the outermost loop.
        if self.progress_bar==True and list(self.data_set.arrays)[0]==self.sweep_values.parameter.full_name+'_set':
            iterator=tqdm(self.sweep_values, bar_format='{l_bar}{bar}{r_bar}. Estimated finish time: {eta}')
        else:
            iterator=self.sweep_values

        i=0
        for value in iterator:
            if self.progress_interval is not None:
                tprint('loop %s: %d/%d (%.1f [s])' % (
                    self.sweep_values.name, i, imax, time.time() - t0),
                    dt=self.progress_interval, tag='outerloop')
                if i:
                    tprint("Estimated finish time: %s" % (
                        time.asctime(time.localtime(t0 + ((time.time() - t0) * imax / i)))),
                           dt=self.progress_interval, tag="finish")

            set_val = self.sweep_values.set(value)

            new_indices = loop_indices + (i,)
            new_values = current_values + (value,)
            data_to_store = {}

            if hasattr(self.sweep_values, "parameters"):  # combined parameter
                set_name = self.data_set.action_id_map[action_indices]
                if hasattr(self.sweep_values, 'aggregate'):
                    value = self.sweep_values.aggregate(*set_val)
                self.data_set.store(new_indices, {set_name: value})
                # set_val list of values to set [param1_setpoint, param2_setpoint ..]
                for j, val in enumerate(set_val):
                    set_index = action_indices + (j+n_callables, )
                    set_name = (self.data_set.action_id_map[set_index])
                    data_to_store[set_name] = val
            if isinstance(self.sweep_values.parameter,MultiParameter):
                set_name = self.data_set.action_id_map[action_indices]
                if type(value) is int or type(value) is float: #then the sweep is common values
                    data_to_store[set_name] = value
                else:
                    data_to_store[set_name] = i

            else:
                set_name = self.data_set.action_id_map[action_indices]
                data_to_store[set_name] = value

            self.data_set.store(new_indices, data_to_store)

            if not self._nest_first:
                # only wait the delay time if an inner loop will not inherit it
                self._wait(delay)

            try:
                for f in callables:
                    # below is useful but too verbose even at debug
                    # log.debug('Going through callables at this sweep step.'
                    #           ' Calling {}'.format(f))
                    f(first_delay=delay,
                      loop_indices=new_indices,
                      current_values=new_values)

                    # after the first action, no delay is inherited
                    delay = 0
            except _QcodesBreak:
                self.was_broken=True
                break

            # after the first setpoint, delay reverts to the loop delay
            delay = self.delay

            # now check for a background task and execute it if it's
            # been long enough since the last time
            # don't let exceptions in the background task interrupt
            # the loop
            # if the background task fails twice consecutively, stop
            # executing it
            if self.bg_task is not None:
                t = time.time()
                if t - last_task >= self.bg_min_delay:
                    try:
                        self.bg_task()
                    except Exception:
                        if self.last_task_failed:
                            self.bg_task = None
                        self.last_task_failed = True
                        log.exception("Failed to execute bg task")

                    last_task = t
            i=i+1
        # run the background task one last time to catch the last setpoint(s)
        if self.bg_task is not None:
            log.debug('Running the background task one last time.')
            self.bg_task()

        # the loop is finished - run the .then actions
        #log.debug('Finishing loop, running the .then actions...')
        for f in self._compile_actions(self.then_actions, ()):
            #log.debug('...running .then action {}'.format(f))
            f()

        # run the bg_final_task from the bg_task:
        if self.bg_final_task is not None:
            log.debug('Running the bg_final_task')
            self.bg_final_task()

    def _wait(self, delay):
        if delay:
            finish_clock = time.perf_counter() + delay
            t = wait_secs(finish_clock)
            time.sleep(t)