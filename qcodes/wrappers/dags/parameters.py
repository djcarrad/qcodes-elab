from qcodes.instrument.parameter import MultiParameter
import numpy as np

class ResistanceParameterVB(MultiParameter):
    def __init__(self, volt_param, curr_param, v_amp_ins, c_amp_ins, name='Resistance'):
        p_name = 'resistance'

        super().__init__(name=name, names=(name, volt_param.name), shapes=((), ()))

        self._volt_param = volt_param
        self._curr_param = curr_param
        self._instrument = v_amp_ins
        self._instrumentcurr = c_amp_ins

        v_label = getattr(volt_param, 'label', None)
        v_unit = getattr(volt_param, 'unit', None)

        self.labels = ('Resistance', v_label)
        self.units = ('Ohm', v_unit)

    def get(self):
        volt = (0.1 * self._volt_param.get() * self._instrument.lockinsens.get())/self._instrument.gain.get()
        curr = (0.1 * self._curr_param.get() * self._instrumentcurr.lockinsens.get() * self._instrumentcurr.gain.get())

        resist = volt/curr

        value = (resist, volt)
        self._save_val(value)
        return value