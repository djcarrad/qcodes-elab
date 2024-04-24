from qcodes import VisaInstrument
from qcodes.utils.validators import Strings, Enum,Bool


class Keithley_2450(VisaInstrument):
    """
    QCoDeS driver for the Keithley 2450 voltage source.
    """

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)

        self.add_parameter('rangev_source',
                           get_cmd='SOUR:VOLT:RANG?',
                           get_parser=float,
                           set_cmd='SOUR:VOLT:RANG {:f}',
                           label='Voltage range')

        self.add_parameter('rangev_sense',
                           get_cmd='SENS:VOLT:RANG?',
                           get_parser=float,
                           set_cmd='SENS:VOLT:RANG {:f}',
                           label='Voltage range')

        self.add_parameter('rangei_source',
                           get_cmd='SOUR:CURR:RANG?',
                           get_parser=float,
                           set_cmd='SOUR:CURR:RANG {:f}',
                           label='Current range')

        self.add_parameter('rangei_sense',
                           get_cmd='SENS:CURR:RANG?',
                           get_parser=float,
                           set_cmd='SENS:CURR:RANG {:f}',
                           label='Current range')

        self.add_parameter('compliancev',
                           get_cmd='SOUR:CURR:VLIM:LEV?',
                           get_parser=float,
                           set_cmd='SOUR:CURR:VLIM:LEV {:.16f}',
                           label='Voltage Compliance')

        self.add_parameter('compliancei',
                           get_cmd='SOUR:VOLT:ILIM:LEV?',
                           get_parser=float,
                           set_cmd='SOUR:VOLT:ILIM:LEV {:.16f}',
                           label='Current Compliance')

        self.add_parameter('volt',
                           get_cmd=self._get_volt,
                           get_parser=float,
                           set_cmd=self._set_volt,
                           label='Voltage',
                           unit='V',
                           docstring="Sets voltage in 'VOLT' mode. "
                                     "Get returns measured voltage if "
                                     "sensing 'VOLT' otherwise it returns "
                                     "setpoint value. "
                                     "Note that it is an error to read voltage with "
                                     "output off")

        self.add_parameter('curr',
                           get_cmd=self._get_current,
                           get_parser=float,
                           set_cmd=self._set_current,
                           label='Current',
                           unit='A',
                           docstring = "Sets current in 'CURR' mode. "
                                        "Get returns measured current if "
                                        "sensing 'CURR' otherwise it returns "
                                        "setpoint value. "
                                        "Note that it is an error to read current with "
                                        "output off")


        self.add_parameter('source',
                           vals=Enum('VOLT', 'CURR'),
                           get_cmd=':SOUR:FUNC?',
                           set_cmd=self._set_mode_and_sense,
                           label='Source mode')

        self.add_parameter('sense',
                           vals=Strings(),
                           get_cmd=':SENS:FUNC?',
                           set_cmd=':SENS:FUNC "{:s}"',
                           label='Sense mode')

        self.add_parameter('fourwiresense',
                           get_parser=int,
                           get_cmd=self._get_rsense,
                           set_cmd=self._set_rsense)

        self.add_parameter('output',
                           get_parser=int,
                           set_cmd=':OUTP:STAT {:d}',
                           get_cmd=':OUTP:STAT?')

        self.add_parameter('nplcv',
                           get_cmd='SENS:VOLT:NPLC?',
                           get_parser=float,
                           set_cmd='SENS:VOLT:NPLC {:f}',
                           label='Voltage integration time')

        self.add_parameter('nplci',
                           get_cmd='SENS:CURR:NPLC?',
                           get_parser=float,
                           set_cmd='SENS:CURR:NPLC {:f}',
                           label='Current integration time')

        self.add_parameter('resistance',
                           get_cmd=self._get_resistance,
                           get_parser=float,
                           label='Resistance',
                           unit='Ohm',
                           docstring="Measure resistance from current and voltage "
                                     "Note that it is an error to read current "
                                     "and voltage with output off")


        self.connect_message()


### FUNCTIONS

    def _get_volt(self):
        if self.output()==0:
            raise RuntimeError(self.name+' output not turned on')
        else:
            if self.sense().startswith('"VOLT'):
                return self.ask('READ?')
            elif self.source()=='VOLT':
                return self.ask('SOUR:VOLT?')
            else:
                raise RuntimeError(self.name+' not set to either source or sense voltage')

    def _set_volt(self,value):
        if self.output()==0:
            raise RuntimeError(self.name+' output not turned on')
        else:
            if self.source()=='VOLT':
                self.write(':SOUR:VOLT:LEV {:.8f}'.format(value))
            else:
                raise RuntimeError(self.name+' not set to source voltage')

    def _get_rsense(self):
        sensestatus=self.sense().split('"')[1]
        return self.ask(f'SENS:{sensestatus}:RSEN?')

    def _set_rsense(self,value):
        sensestatus=self.sense().split('"')[1]
        return self.write(f'SENS:{sensestatus}:RSEN {value}')

    def _get_current(self):
        if self.output()==0:
            raise RuntimeError(self.name+' output not turned on')
        else:
            if self.sense().startswith('"CURR'):
                return self.ask('READ?')
            elif self.source()=='CURR':
                return self.ask('SOUR:CURR?')
            else:
                raise RuntimeError(self.name+' not set to either source or sense current')

    def _set_current(self,value):
        if self.output()==0:
            raise RuntimeError(self.name+' output not turned on')
        else:
            if self.source()=='CURR':
                self.write(':SOUR:CURR:LEV {:.16f}'.format(value))
            else:
                raise RuntimeError(self.name+' not set to source current')


    def _get_resistance(self):
        if self.output()==0:
            raise RuntimeError(self.name+' output not turned on')
        else:
            if self.sense().startswith('"CURR') and self.source()=='VOLT':
                return self.ask('READ?')
            elif self.source()=='CURR' and self.sense().startswith('"VOLT'):
                return self.ask('READ?')
            else:
                raise RuntimeError(self.name+' not set to measure resistance')

### OLD FUNCTIONS INHERITED FROM 2400. MAY BE USEFUL,MAY NOT

    def _get_read_output_protected(self) -> str:
        """
        This wrapper function around ":READ?" exists because calling
        ":READ?" on an instrument with output disabled is an error.
        So first we check that output is on and if not we return
        nan for volt, curr etc.
        """
        output = self.output.get_latest()
        if output is None:
            # if get_latest returns None we have
            # to ask the instrument for the status of output
            output = self.output.get()

        if output == 1:
            msg = self.ask(':READ?')
        else:
            raise RuntimeError("Cannot perform read with output off")
        return msg

        self.connect_message()

    def _set_mode_and_sense(self, msg):
        # This helps set the correct read out curr/volt
        if msg == 'VOLT':
            self.sense('CURR')
        elif msg == 'CURR':
            self.sense('VOLT')
        else:
            raise AttributeError('Mode does not exist')
        self.write(':SOUR:FUNC {:s}'.format(msg))

    def reset(self):
        """
        Reset the instrument. When the instrument is reset, it performs the
        following actions.

            Returns the SourceMeter to the GPIB default conditions.

            Cancels all pending commands.

            Cancels all previously send `*OPC` and `*OPC?`
        """
        self.write(':*RST')

    def _volt_parser(self, msg):
        fields = [float(x) for x in msg.split(',')]
        return fields[0]

    def _curr_parser(self, msg):
        fields = [float(x) for x in msg.split(',')]
        return fields[1]

    def _resistance_parser(self, msg):
        fields = [float(x) for x in msg.split(',')]
        res = fields[0] / fields[1]
        return res
