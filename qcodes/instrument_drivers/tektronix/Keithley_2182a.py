from qcodes import VisaInstrument
from qcodes.utils.validators import Numbers, Ints, Enum, MultiType, Bool

from functools import partial


def parse_output_string(s):
    """ Parses and cleans string outputs of the Keithley """
    # Remove surrounding whitespace and newline characters
    s = s.strip()

    # Remove surrounding quotes
    if (s[0] == s[-1]) and s.startswith(("'", '"')):
        s = s[1:-1]

    s = s.lower()

    # Convert some results to a better readable version
    conversions = {
        'mov': 'moving',
        'rep': 'repeat',
    }

    if s in conversions.keys():
        s = conversions[s]

    return s


def parse_output_bool(value):
    return True if int(value) == 1 else False


class Keithley_2182a(VisaInstrument):
    """
    Driver for the Keithley 2182a nanovoltmeter.
    Currently written to support VOLTAGE MEASUREMENTS ONLY
    Temperature may be supported at a later date.
    """
    def __init__(self, name, address, reset=False, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)

        self._trigger_sent = False

        self._mode_map = {
            'dc_voltage': '"VOLT:DC"',
            'temperature': '"TEMP"',
        }


        self.add_parameter('channel',
                           get_cmd='SENS:CHAN?',
                           set_cmd="SENS:CHAN {}")       

        self.add_parameter('mode',
                           get_cmd='SENS:FUNC?',
                           set_cmd="SENS:FUNC {}",
                           val_mapping=self._mode_map)

        # Mode specific parameters
        self.add_parameter('volt',
                           get_cmd='FETC?',
                           get_parser=self._volt_parser,
                           label='Voltage',
                           unit='V',
                           docstring=#"Sets voltage in 'VOLT' mode. "
                                     "Get returns measured voltage if "
                                     "sensing 'VOLT'")

        self.add_parameter('nplc',
                           get_cmd='VOLT:NPLC?',
                           set_cmd='VOLT:NPLC {}',
                           vals=Numbers(min_value=0.01, max_value=10))

        # TODO: validator, this one is more difficult since different modes
        # require different validation ranges
        self.add_parameter('range',
                           get_cmd='VOLT:RANG?',
                           set_cmd='VOLT:RANG {}',
                           vals=Numbers())

        self.add_parameter('voltage_offset',
                           get_cmd='VOLT:REF:STAT?',
                           set_cmd='VOLT:REF:STAT {}',
                           vals=Numbers())

        self.add_parameter('auto_range_enabled',
                           get_cmd='VOLT:RANG:AUTO?',
                           set_cmd='VOLT:RANG:AUTO {}',
                           vals=Bool())

        self.add_parameter('digits',
                           get_cmd='VOLT:DIG?',
                           set_cmd='VOLT:DIG {}',
                           vals=Ints(min_value=4, max_value=7))

        self.add_parameter('autozero_enabled',
                           get_cmd='SYST:AZER:STAT?',
                           set_cmd='SYST:AZER:STAT {}',
                           vals=Bool())
        self.add_parameter('linesync_enabled',
                           get_cmd='SYST:LSYN:STAT?',
                           set_cmd='SYST:LSYN:STAT {}',
                           vals=Bool())


        # Global parameters
        self.add_parameter('display_enabled',
                           get_cmd='DISP:ENAB?',
                           get_parser=parse_output_bool,
                           set_cmd='DISP:ENAB {}',
                           set_parser=int,
                           vals=Bool())

        self.add_parameter('trigger_continuous',
                           get_cmd='INIT:CONT?',
                           get_parser=parse_output_bool,
                           set_cmd='INIT:CONT {}',
                           set_parser=int,
                           vals=Bool())

        self.add_parameter('trigger_count',
                           get_cmd='TRIG:COUN?',
                           get_parser=int,
                           set_cmd='TRIG:COUN {}',
                           vals=MultiType(Ints(min_value=1, max_value=9999),
                                          Enum('inf',
                                               'default',
                                               'minimum',
                                               'maximum')))

        self.add_parameter('trigger_delay',
                           get_cmd='TRIG:DEL?',
                           get_parser=float,
                           set_cmd='TRIG:DEL {}',
                           unit='s',
                           vals=Numbers(min_value=0, max_value=999999.999))

        self.add_parameter('trigger_source',
                           get_cmd='TRIG:SOUR?',
                           set_cmd='TRIG:SOUR {}',
                           val_mapping={
                               'immediate': 'IMM',
                               'timer': 'TIM',
                               'manual': 'MAN',
                               'bus': 'BUS',
                               'external': 'EXT',
                           })

        self.add_parameter('trigger_timer',
                           get_cmd='TRIG:TIM?',
                           get_parser=float,
                           set_cmd='TRIG:TIM {}',
                           unit='s',
                           vals=Numbers(min_value=0.001, max_value=999999.999))

        self.add_parameter('amplitude',
                           unit='arb.unit',
                           get_cmd=self._read_next_value)

        self.add_function('reset', call_cmd='*RST')

        if reset:
            self.reset()

        # Set the data format to have only ascii data without units and channels
        self.write('FORM:DATA ASCII')
        self.write('FORM:ELEM READ')

        self.connect_message()

    def trigger(self):
        if not self.trigger_continuous():
            self.write('INIT')
            self._trigger_sent = True

    def _read_next_value(self):
        # Prevent a timeout when no trigger has been sent
        if not self.trigger_continuous() and not self._trigger_sent:
            return 0.0

        self._trigger_sent = False

        return float(self.ask('SENSE:DATA:FRESH?'))

    def _volt_parser(self, val):
        if self.mode.get_latest()!='dc_voltage':
            raise AttributeError('Instrument not set to voltage mode')
        else:
            return val