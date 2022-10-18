from qcodes import VisaInstrument
from qcodes.utils.validators import Numbers, Ints, Enum, MultiType
import time

class SR5210(VisaInstrument):
    """
    This is the qcodes driver for the Princeton Signal Recovery 5210
    Lock-in Amplifier
    """

    _VOLT_TO_N = {1e-07: 0,
                  3e-07: 1,
                  1e-06: 2,
                  3e-06: 3,
                  1e-05: 4,
                  3e-05: 5,
                  0.0001: 6,
                  0.0003: 7,
                  0.001: 8,
                  0.003: 9,
                  0.01: 10,
                  0.03: 11,
                  0.1: 12,
                  0.3: 13,
                  1: 14,
                  3: 15}
    _TIME_TO_N = {1e-3:   0,
                  3e-3:   1,
                  10e-3:  2,
                  30e-3:  3,
                  100e-3: 4,
                  300e-3: 5,
                  1:     6,
                  3:     7,
                  10:    8,
                  30:    9,
                  100:   10,
                  300:   11,
                  1e3:   12,
                  3e3:   13}

#     _N_TO_VOLT = {v: k for k, v in _VOLT_TO_N.items()}


    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, **kwargs)

        self.add_parameter('X',
                           get_cmd='X?',
                           get_parser=self._get_converted,
                           unit='V')

        self.add_parameter('Y',
                           get_cmd='Y?',
                           get_parser=self._get_converted,
                           unit='V')

        self.add_parameter('R',
                           get_cmd='MAG?',
                           get_parser=self._get_converted,
                           unit='V')

        self.add_parameter('P',
                           get_cmd='PHA?',
                           get_parser=self._get_converted,
                           unit='deg')

        self.add_parameter(name='sensitivity',
                           label='Sensitivity',
                           get_cmd='SEN?',
                           set_cmd='SEN {:d}',
                           val_mapping=self._VOLT_TO_N
                           )

        self.add_parameter('time_constant',
                           label='Time constant',
                           get_cmd='TC?',
                           set_cmd='TC {}',
                           unit='s',
                           val_mapping=self._TIME_TO_N)

        self.add_parameter('frequency',
                           label='Frequency',
                           get_cmd='FRQ?',
                           get_parser=self._get_freq,
                           unit='Hz')

        # time.sleep(5)
        # a = 0
        # b = 0
        # for i in range(10):
        #     try:
        #         self.connect_message()
        #         a = 1
        #         break
        #     except:
        #         pass

        # for i in range(10):
        #     try:
        #         self.sensitivity.get()
        #         b = 1
        #         break
        #     except:
        #         pass
        # print(a,b)

    def get_idn(self):
        vendor = 'Stanford Research Systems'
        model = self.visa_handle.ask('ID?').strip()
        serial = None
        firmware = self.visa_handle.ask('VER?').strip()
        return {'vendor': vendor, 'model': model,
                'serial': serial, 'firmware': firmware}

    def _get_converted(self, s):
        sens = self.sensitivity.get_latest()
        return float(s)*1e-4*sens

    def _get_freq(self, s):
        return float(s)*1e-3