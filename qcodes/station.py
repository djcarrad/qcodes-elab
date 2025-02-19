"""Station objects - collect all the equipment you use to do an experiment."""
from typing import Dict, List, Optional, Sequence, Any

import time

from qcodes.utils.metadata import Metadatable
from qcodes.utils.helpers import make_unique, DelegateAttributes

from qcodes.instrument.base import Instrument
from qcodes.instrument.parameter import Parameter, MultiParameter, _BaseParameter
from qcodes.instrument.parameter import ElapsedTimeParameter

from qcodes.actions import _actions_snapshot


class Station(Metadatable, DelegateAttributes):

    """
    A representation of the entire physical setup.

    Lists all the connected Components and the current default
    measurement (a list of actions). Contains a convenience method
    `.measure()` to measure these defaults right now, but this is separate
    from the code used by `Loop`.

    Args:
        *components (list[Any]): components to add immediately to the
             Station. Can be added later via self.add_component

        monitor (None): Not implemented, the object that monitors the system
            continuously

        default (bool): is this station the default, which gets
            used in Loops and elsewhere that a Station can be specified,
            default true

        update_snapshot (bool): immediately update the snapshot
            of each component as it is added to the Station, default true

    Attributes:
        default (Station): class attribute to store the default station
        delegate_attr_dicts (list): a list of names (strings) of dictionaries
            which are (or will be) attributes of self, whose keys should be
            treated as attributes of self
    """

    default = None # type: 'Station'

    def __init__(self, *components: Metadatable, add_variables: Any=None,
                 monitor: Any=None, default: bool=True,
                 update_snapshot: bool=True, inc_timer=True,**kwargs) -> None:
        super().__init__(**kwargs)

        # when a new station is defined, store it in a class variable
        # so it becomes the globally accessible default station.
        # You can still have multiple stations defined, but to use
        # other than the default one you must specify it explicitly.
        # If for some reason you want this new Station NOT to be the
        # default, just specify default=False
        if default:
            Station.default = self

        self.components = {} # type: Dict[str, Metadatable]
        for item in components:
            self.add_component(item, update_snapshot=update_snapshot)

        if inc_timer==True:
            timer=ElapsedTimeParameter(name='timer')
            self.add_component(timer, update_snapshot=update_snapshot)

        self.monitor = monitor

        self.default_measurement = [] # type: List

        if add_variables is not None:
            self.auto_add(add_variables)

    def snapshot_base(self, update: bool=False,
                      params_to_skip_update: Sequence[str]=None) -> Dict:
        """
        State of the station as a JSON-compatible dict.

        Note: in the station contains an instrument that has already been
        closed, not only will it not be snapshotted, it will also be removed
        from the station during the execution of this function.

        Args:
            update (bool): If True, update the state by querying the
             all the children: f.ex. instruments, parameters, components, etc.
             If False, just use the latest values in memory.

        Returns:
            dict: base snapshot
        """
        snap = {
            'instruments': {},
            'parameters': {},
            'components': {},
            'default_measurement': _actions_snapshot(
                self.default_measurement, update)
        }

        components_to_remove = []

        for name, itm in self.components.items():
            if isinstance(itm, Instrument):
                # instruments can be closed during the lifetime of the
                # station object, hence this 'if' allows to avoid
                # snapshotting instruments that are already closed
                if Instrument.is_valid(itm):
                    snap['instruments'][name] = itm.snapshot(update=update)
                else:
                    components_to_remove.append(name)
            elif isinstance(itm, (_BaseParameter
                                  )):
                snap['parameters'][name] = itm.snapshot(update=update)
            else:
                snap['components'][name] = itm.snapshot(update=update)

        for c in components_to_remove:
            self.remove_component(c)

        return snap

    def auto_add(self,variables,add_instruments: bool=True,add_parameters: bool=True,update_snapshot: bool=True):
        """
        Automatically add instruments to the station.
        Usually, variables=globals()
        """
        if add_instruments==True:
            if 'instruments' in self.snapshot_base():
                for variable in variables:
                    if isinstance(variables[variable],Instrument):
                        if variables[variable].name not in self.snapshot_base()['instruments']:
                            self.add_component(variables[variable],update_snapshot=update_snapshot)
            else:
                for variable in variables:
                    if isinstance(variables[variable],Instrument):
                        self.add_component(variables[variable],update_snapshot=update_snapshot)

            if 'instruments' not in self.snapshot_base():
                raise KeyError('No instruments found in variable list!')
            else:
                names=[]
                for variable in self.snapshot_base()['instruments']:
                    names.append(variable)
                print('Instruments in station: '+str(names))
        if add_parameters==True:
            if 'parameters' in self.snapshot_base():
                for variable in variables:
                    if isinstance(variables[variable],_BaseParameter):
                        if variables[variable].name not in self.snapshot_base()['parameters']:
                            self.add_component(variables[variable],update_snapshot=update_snapshot)
            else:
                for variable in variables:
                    if isinstance(variables[variable],_BaseParameter):
                        self.add_component(variables[variable],update_snapshot=update_snapshot)

            if 'parameters' not in self.snapshot_base():
                raise KeyError('No parameters found in variable list!')
            else:
                names=[]
                for variable in self.snapshot_base()['parameters']:
                    names.append(variable)
                print('Parameters in station: '+str(names))

    def add_component(self, component: Metadatable, name: str=None,
                      update_snapshot: bool=True) -> str:
        """
        Record one component as part of this Station.

        Args:
            component (Any): components to add to the Station.
            name (str): name of the component
            update_snapshot (bool): immediately update the snapshot
                of each component as it is added to the Station, default true

        Returns:
            str: The name assigned this component, which may have been changed to
            make it unique among previously added components.

        """
        try:
            component.snapshot(update=update_snapshot)
        except:
            pass
        if name is None:
            name = getattr(component, 'name',
                           'component{}'.format(len(self.components)))
        namestr = make_unique(str(name), self.components)
        self.components[namestr] = component
        return namestr

    def remove_component(self, name: str) -> Optional[Metadatable]:
        """
        Remove a component with a given name from this Station.

        Args:
            name: name of the component

        Returns:
            the component that has been removed (this behavior is the same as
            for python dictionaries)

        Raises:
            KeyError if a component with the given name is not part of this
            station
        """
        try:
            return self.components.pop(name)
        except KeyError as e:
            if name in str(e):
                raise KeyError(f'Component {name} is not part of the station')
            else:
                raise e

    def set_measurement(self, *actions):
        """
        Save a set ``*actions``` as the default measurement for this Station.

        These actions will be executed by default by a Loop if this is the
        default Station, and any measurements among them can be done once
        by .measure
        Args:
            *actions: parameters to set as default  measurement
        """
        # Validate now so the user gets an error message ASAP
        # and so we don't accept `Loop` as an action here, where
        # it would cause infinite recursion.
        # We need to import Loop inside here to avoid circular import
        from .loops import Loop
        Loop.validate_actions(*actions)

        self.default_measurement = actions

        if 'timer' in self.components:
            self.default_measurement = self.default_measurement + (self.components['timer'],)

    def communication_time(self,measurement_num=1):
        commtimes=[]
        for i in range(measurement_num):
            starttime=time.time()
            self.measurement()
            endtime=time.time()
            commtimes.append(endtime-starttime)
        return commtimes

    def measurement(self, *actions):
        """
        Measure the default measurement, or parameters in actions.

        Args:
            *actions: parameters to mesure
        """
        if not actions:
            actions = self.default_measurement

        out = []

        # this is a stripped down, uncompiled version of how
        # ActiveLoop handles a set of actions
        # callables (including Wait) return nothing, but can
        # change system state.
        for action in actions:
            if hasattr(action, 'get'):
                out.append(action.get())
            elif callable(action):
                action()

        return out

    def measure(self,*actions):
        """
        Pass the default measurement or parameters in actions to a loop.
        """

        if not actions:
            actions = self.default_measurement

        return actions

    # station['someitem'] and station.someitem are both
    # shortcuts to station.components['someitem']
    # (assuming 'someitem' doesn't have another meaning in Station)
    def __getitem__(self, key):
        """Shortcut to components dict."""
        return self.components[key]

    delegate_attr_dicts = ['components']