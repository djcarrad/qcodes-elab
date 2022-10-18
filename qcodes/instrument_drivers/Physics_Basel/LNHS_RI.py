from functools import partial
import time
import numpy as np


from qcodes.instrument.visa import VisaInstrument
from qcodes.utils.validators import Enum, Anything


class LNHS_RI(VisaInstrument):

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\r', **kwargs)


        self.add_parameter(
                   name='gain',
                   unit='V/A',
                   set_cmd=self._setgain,
                   get_cmd=self._getgain,
                   vals=Enum(1E5,1E6,1E7,1E8,1E9))

        self.add_parameter(
                   name='overload',
                   get_cmd=self._getoverload)

        self.add_parameter(
                   name='filter',
                   unit='Hz',
                   set_cmd=self._setfilter,
                   get_cmd=self._getfilter,
                   vals=Enum(30,100,300,1000,3000,10000,30000,100000,'full'))




    def _setfilter(self,val):
        self.device_clear()
        self.ask('SET F {}'.format(val))

    def _getfilter(self):
        while True:
            self.device_clear()
            response = self.ask('GET F')
            if 'O' in response: # The fucking thing is too talkative, there is no way to stop it from automatically spamming overload messages. This is not elegant but should work.
                continue
            else:
                if 'kHz' in response:
                    fltr = float(response[response.find(' '):response.find('kHz')])*1000
                    break
                elif 'FULL' in response:
                    fltr = 'FULL'
                    break
                else:
                    fltr = float(response[response.find(' '):response.find('Hz')])
                    break
        return fltr



    def _setgain(self,val):
        self.device_clear()
        self.ask('SET G {:.0E}'.format(val).replace('E+0','E'))

    def _getgain(self):
        while True:
            self.device_clear()
            response = self.ask('GET G')
            if 'O' in response: # The fucking thing is too talkative, there is no way to stop it from automatically spamming overload messages. This is not elegant but should work.
                continue
            else:
                gain = float(response[response.find(' '):])
                break
        return gain



    def _getoverload(self):
        self.device_clear()
        response = self.ask("GET O")
        if 'ON' in response:
            return True
        if 'OFF' in response:
            return False

