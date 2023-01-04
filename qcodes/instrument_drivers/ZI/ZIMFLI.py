from zhinst.ziPython import ziDAQServer
from zhinst.utils import utils
from qcodes.instrument.base import Instrument
from qcodes.utils.validators import Numbers, Enum, Ints
from qcodes import DataArray
from functools import partial
import numpy as np
import time

class ZIMFLI(Instrument):
    """
    This is the driver for the Zurich Instruments MFLI compatible with the older qcodes v0.1.11.
    It has the most important functions for configuring outputs and reading off inputs to qcodes.

    Serial - the device serial number printed on the chassis used for connecting to the device

    TODO: everything

    """
    LI = {
            "numSigouts": 1,   # number of signal outputs
            "numOscs": 1,      # number of oscillators
            "numDemods": 1,    # number of demodulators
            "numVins": 1,      # number of voltage inputs
            "numIins": 1,      # number of current inputs
            "numAUXouts": 4,   # number of AUX outputs
            "numAUXins": 2,     # number of AUX inputs
            "numscopes": 1
        }

    scoperates = {
            '0': 60e6,
            '1': 30e6,
            '2': 15e6,
            '3': 7.5e6,
            '4': 3.75e6,
            '5': 1.88e6,
            '6': 936e3,
            '7': 469e3,
            '8': 234e3,
            '9': 117e3,
            '10': 58.6e3,
            '11': 29.3e3,
            '12': 14.6e3,
            '13': 7.32e3,
            '14': 3.66e3,
            '15': 1.83e3}
    scopechaninputs = { #Note there are technically more options: Only including keys for those we have installed
            '0': 'Signal input 1',
            '1': 'Current input 1',
            '2': 'Trigger input 1',
            '3': 'Trigger input 2',
            '4': 'Aux output 1',
            '5': 'Aux output 2',
            '6': 'Aux output 3',
            '7': 'Aux output 4',
            '8': 'Aux input 1',
            '9': 'Aux input 2',
            '10': 'Osc phase demod 2',
            '11': 'Osc phase demod 4',
            '14': 'Trigger output 1',
            '15': 'Trigger output 2',
            '16': 'Demod 1 X',
            '17': 'Demod 2 X',
            '32': 'Demod 1 Y',
            '33': 'Demod 2 Y',
            '48': 'Demod 1 R',
            '49': 'Demod 2 R',
            '64': 'Demod 1 theta',
            '65': 'Demod 2 theta'}

    def print_scope_rates(self):
        print(self.scoperates)
    def print_scope_chaninputs(self):
        print(self.scopechaninputs)

    def __init__(self, name, serial, server="local", **kwargs):
        global daq
        if server == "internal":
            self.daq = ziDAQServer('mf-{}'.format(serial), 8004, 6)  # Unlike the HF2 where the server runs on the computer, on MF instruments the server runs on the instrument, so the host is the instrument not "localhost"
        elif server == "local":
            self.daq = ziDAQServer('localhost', 8004, 6)
        else:
            raise ValueError('Server should be either internal or local')
        super().__init__(name, **kwargs)

        self.name = name
        self.serial = serial


        # Register clock source
        self.add_parameter(name='clock_src',
                           label='Clock_source',
                           set_cmd=partial(self.daq.setInt,'/{}/system/extclk'.format(self.serial)),
                           get_cmd=partial(self.daq.getInt,'/{}/system/extclk'.format(self.serial)),
                           get_parser = int,
                           val_mapping={
                                       "10MHz" : 1,
                                       "Internal" : 0,
                                       },
                           vals=Ints(min_value=0, max_value=1))



        # Register oscillators
        for n in range(self.LI["numOscs"]):
            self.add_parameter(name='osc{}_freq'.format(n),
                               label='osc{}_freq'.format(n),
                               unit='Hz',
                               set_cmd= partial(self.daq.setDouble,'/{}/oscs/{}/freq'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/oscs/{}/freq'.format(self.serial, n)),
                               get_parser = float,
                               vals = Numbers(min_value=0, max_value=5E6)) # IMPORTANT! VALIDATOR FOR FREQUENCY RANGE



        # Register Demodulators
        for n in range(self.LI["numDemods"]):
            # Demod Input
            self.add_parameter(name='demod{}_input'.format(n),
                               label='demod{}_input'.format(n),
                               set_cmd=partial(self.daq.setInt,'/{}/demods/{}/adcselect'.format(self.serial, n)),
                               get_cmd=partial(self.daq.getInt,'/{}/demods/{}/adcselect'.format(self.serial, n)),
                               get_parser = int,
                               val_mapping={
                                           "Vin" : 0,
                                           "Iin" : 1,
                                           "Trig1": 2,
                                           "Trig2" : 3,
                                           "AUXout1" :4,
                                           "AUXout2" :5,
                                           "AUXout3" :6,
                                           "AUXout4" :7,
                                           "AUXin1" :8,
                                           "AUXin2" :9,
                                           },
                               vals=Ints(min_value=0, max_value=9))

            #Demod X
            self.add_parameter(name='demod{}_X'.format(n),
                               label='X',
                               unit='V',
                               get_cmd= partial(self.getX,'/{}/demods/{}/sample'.format(self.serial,n)),
                               get_parser = float)

            #Demod Y
            self.add_parameter(name='demod{}_Y'.format(n),
                               label='Y',
                               unit='V',
                               get_cmd= partial(self.getY,'/{}/demods/{}/sample'.format(self.serial,n)),
                               get_parser = float)

            #Demod R
            self.add_parameter(name='demod{}_R'.format(n),
                               label='R',
                               unit='V',
                               get_cmd= partial(self.getR,'/{}/demods/{}/sample'.format(self.serial,n)),
                               get_parser = float)

            # Demod phase
            self.add_parameter(name='demod{}_phase'.format(n),
                               label='Phase',
                               unit='deg',
                               get_cmd= partial(self.getP,'/{}/demods/{}/sample'.format(self.serial,n)),
                               get_parser = float)

            # Demod on or off
            self.add_parameter(name='demod{}_enabled'.format(n),
                               label='demod{}'.format(n),
                               set_cmd=partial(self.daq.setInt,'/{}/demods/{}/enable'.format(self.serial, n)),
                               get_cmd=partial(self.daq.getInt,'/{}/demods/{}/enable'.format(self.serial, n)),
                               get_parser = int,
                               val_mapping={
                                           True : 1,
                                           False : 0,
                                           },
                               vals=Ints(min_value=0, max_value=1))

            # Timeconstant
            self.add_parameter(name='demod{}_tc'.format(n),
                               label='demod{}_tc'.format(n),
                               set_cmd= partial(self.daq.setDouble,'/{}/demods/{}/timeconstant'.format(self.serial,n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/demods/{}/timeconstant'.format(self.serial,n)),
                               get_parser=float,)


            # Low pass filter order
            self.add_parameter(name='demod{}_LPorder'.format(n),
                               label='demod{}_LPorder'.format(n),
                               set_cmd=partial(self.daq.setInt,'/{}/demods/{}/order'.format(self.serial, n)),
                               get_cmd=partial(self.daq.getInt,'/{}/demods/{}/order'.format(self.serial, n)),
                               get_parser = int,
                               vals=Ints(min_value=1, max_value=8))

            # External reference on or off
            if (n == 1):
                self.add_parameter(name='demod{}_mode'.format(n),
                               label='demod{}_mode'.format(n),
                               set_cmd=partial(self.daq.setInt,'/{}/extrefs/{}/enable'.format(self.serial, n-1)),
                               get_cmd=partial(self.daq.getInt,'/{}/extrefs/{}/enable'.format(self.serial, n-1)),
                               get_parser = int,
                               val_mapping={
                                           True : 1,
                                           False : 0,
                                           },
                               vals=Ints(min_value=0, max_value=1))




        # Register sigouts

        """
        TODO: switching on the 50 Ohm output impedance changes the available ranges on the sigout, so that will fuck up the user input value validator.
        Need to figure out how to switch the validator when imp50 is toggled
        """
        for n in range(self.LI["numSigouts"]):

            # output on or off
            self.add_parameter(name='out{}_enabled'.format(n),
                               label='out{}_output'.format(n),
                               set_cmd= partial(self.daq.setInt, '/{}/sigouts/{}/on'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getInt, '/{}/sigouts/{}/on'.format(self.serial, n)),
                               val_mapping={
                                           True : 1,
                                           False : 0,
                                           },
                               vals=Ints(min_value=0, max_value=1))

            # output range
            self.add_parameter(name='out{}_range'.format(n),
                               label='out{}_range'.format(n),
                               unit='V',
                               set_cmd= partial(self.daq.setDouble,'/{}/sigouts/{}/range'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/sigouts/{}/range'.format(self.serial, n)),
                               get_parser= float,
                               vals = Enum(0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10))

            # sine wave offset to the output
            self.add_parameter(name='out{}_offset'.format(n),
                               label='out{}_offset'.format(n),
                               unit='V',
                               set_cmd= partial(self.daq.setDouble,'/{}/sigouts/{}/offset'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/sigouts/{}/offset'.format(self.serial, n)),
                               get_parser= float,
                               vals = Numbers(min_value=0, max_value=1))

            # output amplitude
            self.add_parameter(name='out{}_amp'.format(n),
                               label='out{}_amplitude'.format(n),
                               unit='V',
                               set_cmd=partial(self.setAmplitude,'/{}/sigouts/{}/amplitudes/1'.format(self.serial, n)),
                               get_cmd=partial(self.getAmplitude,'/{}/sigouts/{}/amplitudes/1'.format(self.serial, n)),
                               get_parser = float,
                               vals = Numbers(min_value=0, max_value=10))


            # output impedance set to 50 Ohm true or false
            self.add_parameter(name='out{}_imp50'.format(n),
                               label='out{}_imp50'.format(n),
                               set_cmd= partial(self.daq.setInt, '/{}/sigouts/{}/imp50'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getInt, '/{}/sigouts/{}/imp50'.format(self.serial, n)),
                               val_mapping={
                                           True : 1,
                                           False : 0,
                                           },
                               vals=Ints(min_value=0, max_value=1))



        # Register voltage inputs
        for n in range(self.LI["numVins"]):
            # input range
            self.add_parameter(name='Vin{}_range'.format(n),
                               label='Vin{}_range'.format(n),
                               unit='V',
                               set_cmd= partial(self.daq.setDouble,'/{}/sigins/{}/range'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/sigins/{}/range'.format(self.serial, n)),
                               get_parser = float,
                               vals = Numbers(min_value=0.001, max_value=3))

            # arbitrary scaling factor
            self.add_parameter(name='Vin{}_scaling'.format(n),
                               label='Vin{}_scaling'.format(n),
                               unit='V/V',
                               set_cmd= partial(self.daq.setDouble,'/{}/sigins/{}/scaling'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/sigins/{}/scaling'.format(self.serial, n)),
                               get_parser = float)


            # AC coupling on or off
            self.add_parameter(name='Vin{}_AC'.format(n),
                               label='Vin{}_AC'.format(n),
                               set_cmd= partial(self.daq.setInt, '/{}/sigins/{}/ac'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getInt, '/{}/sigins/{}/ac'.format(self.serial, n)),
                               val_mapping={
                                           True : 1,
                                           False : 0,
                                           },
                               vals=Ints(min_value=0, max_value=1))


            # 50 Ohm impedance on or off
            self.add_parameter(name='Vin{}_imp50'.format(n),
                               label='Vin{}_imp50'.format(n),
                               set_cmd= partial(self.daq.setInt, '/{}/sigins/{}/imp50'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getInt, '/{}/sigins/{}/imp50'.format(self.serial, n)),
                               val_mapping={
                                           True : 1,
                                           False : 0,
                                           },
                               vals=Ints(min_value=0, max_value=1))


            # differential measurement on or off
            self.add_parameter(name='Vin{}_diff'.format(n),
                               label='Vin{}_diff'.format(n),
                               set_cmd= partial(self.daq.setInt, '/{}/sigins/{}/diff'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getInt, '/{}/sigins/{}/diff'.format(self.serial, n)),
                               val_mapping={
                                           True : 1,
                                           False : 0,
                                           },
                               vals=Ints(min_value=0, max_value=1))


            # Float input
            self.add_parameter(name='Vin{}_float'.format(n),
                               label='Vin{}_float'.format(n),
                               set_cmd= partial(self.daq.setInt, '/{}/sigins/{}/float'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getInt, '/{}/sigins/{}/float'.format(self.serial, n)),
                               val_mapping={
                                           True : 1,
                                           False : 0,
                                           },
                               vals=Ints(min_value=0, max_value=1))


        # Register current inputs
        for n in range(self.LI["numIins"]):
            # input range
            self.add_parameter(name='Iin{}_range'.format(n),
                               label='Iin{}_range'.format(n),
                               unit='A',
                               set_cmd= partial(self.daq.setDouble,'/{}/currins/{}/range'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/currins/{}/range'.format(self.serial, n)),
                               get_parser = float,
                               vals = Numbers(min_value=1E-9, max_value=0.01))

            # arbitrary scaling factor
            self.add_parameter(name='Iin{}_scaling'.format(n),
                               label='Iin{}_scaling'.format(n),
                               unit='A/A',
                               set_cmd= partial(self.daq.setDouble,'/{}/currins/{}/scaling'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/currins/{}/scaling'.format(self.serial, n)),
                               get_parser = float)


            # Float input
            self.add_parameter(name='Iin{}_float'.format(n),
                               label='Iin{}_float'.format(n),
                               set_cmd= partial(self.daq.setInt, '/{}/currins/{}/float'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getInt, '/{}/currins/{}/float'.format(self.serial, n)),
                               val_mapping={
                                           True : 1,
                                           False : 0,
                                           },
                               vals=Ints(min_value=0, max_value=1))



        # Register AUX Outputs
        for n in range(self.LI["numAUXouts"]):
            # Signal to output select
            self.add_parameter(name='AUXout{}_signal'.format(n),
                               label='AUXout{}_signal'.format(n),
                               set_cmd= partial(self.daq.setInt,'/{}/auxouts/{}/outputselect'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getInt,'/{}/auxouts/{}/outputselect'.format(self.serial, n)),
                               val_mapping={
                                           "Manual" : -1,
                                           "DemodX" : 0,
                                           "DemodY" : 1,
                                           "DemodR" : 2,
                                           "DemodTheta" : 3,
                                           "TU_filtered" : 11,
                                           "TU_output" : 13,
                                           },
                               vals= Enum(-1, 0, 1, 2, 3, 11, 13))


            # Channel
            self.add_parameter(name='AUXout{}_channel'.format(n),
                               label='AUXout{}_channel'.format(n),
                               set_cmd= partial(self.daq.setInt,'/{}/auxouts/{}/demodselect'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getInt,'/{}/auxouts/{}/demodselect'.format(self.serial, n)),
                               vals= Ints(min_value=1, max_value=4))


            # Preoffset
            self.add_parameter(name='AUXout{}_preoffset'.format(n),
                               label='AUXout{}_preoffset'.format(n),
                               unit = "V",
                               set_cmd= partial(self.daq.setDouble,'/{}/auxouts/{}/preoffset'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/auxouts/{}/preoffset'.format(self.serial, n)),
                               get_parser = float,
                               vals= Ints(min_value=1, max_value=4))


            # arbitrary scaling factor
            self.add_parameter(name='AUXout{}_scale'.format(n),
                               label='AUXout{}_scale'.format(n),
                               set_cmd= partial(self.daq.setDouble,'/{}/auxouts/{}/scale'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/auxouts/{}/scale'.format(self.serial, n)),
                               get_parser = float)


            # offset
            self.add_parameter(name='AUXout{}_offset'.format(n),
                               label='AUXout{}_offset'.format(n),
                               unit = "V",
                               set_cmd= partial(self.daq.setDouble,'/{}/auxouts/{}/offset'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/auxouts/{}/offset'.format(self.serial, n)),
                               get_parser = float,
                               vals= Numbers(min_value=-10, max_value=10))


            # lower limits
            self.add_parameter(name='AUXout{}_lowerlim'.format(n),
                               label='AUXout{}_lowerlim'.format(n),
                               unit = "V",
                               set_cmd= partial(self.daq.setDouble,'/{}/auxouts/{}/limitlower'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/auxouts/{}/limitlower'.format(self.serial, n)),
                               get_parser = float,
                               vals= Numbers(min_value=-10, max_value=10))


            # upper limits
            self.add_parameter(name='AUXout{}_upperlim'.format(n),
                               label='AUXout{}_upperlim'.format(n),
                               unit = "V",
                               set_cmd= partial(self.daq.setDouble,'/{}/auxouts/{}/limitupper'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/auxouts/{}/limitupper'.format(self.serial, n)),
                               get_parser = float,
                               vals= Numbers(min_value=-10, max_value=10))


            # AUX output value
            self.add_parameter(name='AUXout{}_value'.format(n),
                               label='AUXout{}_value'.format(n),
                               unit = "V",
                               get_cmd= partial(self.daq.getDouble,'/{}/auxouts/{}/value'.format(self.serial, n)),
                               get_parser = float)



        # REgister AUX inputs
        for n in range(self.LI["numAUXins"]):
            # AUX input value
            self.add_parameter(name='AUXin{}_value'.format(n),
                               label='AUXin{}_value'.format(n),
                               unit = "V",
                               get_cmd= partial(self.daq.getDouble,'/{}/auxins/0/values/{}'.format(self.serial, n)),
                               get_parser = float)


        ################## MDS stuff ##############

        # # Register self to MDS

        # self.add_parameter(name='MDS_add',
        #                    label='MDS_add',
        #                    set_cmd=partial(self.daq.setByte,'/zi/mds/groups/0/devices'.format(self.serial, n)),
        #                    get_cmd=partial(self.daq.getInt,'/{}/system/extclk'.format(self.serial, n)),
        #                    get_parser = int,
        #                    val_mapping={
        #                                "10MHz" : 1,
        #                                "Internal" : 0,
        #                                },
        #                    vals=Ints(min_value=0, max_value=1))

        # Scope parameters
        for n in range(self.LI["numscopes"]):
            self.add_parameter(name='scope{}_length'.format(n),
                                label='scope{}_length'.format(n),
                                unit='samples',
                                get_cmd=partial(self.daq.getInt,'/{}/scopes/{}/length'.format(self.serial,n)),
                                set_cmd=partial(self.daq.setInt,'/{}/scopes/{}/length'.format(self.serial,n)))
            self.add_parameter(name='scope{}_triglevel'.format(n),
                                label='scope{}_triglevel'.format(n),
                                unit='V',
                                get_cmd=partial(self.daq.getDouble,'/{}/scopes/{}/triglevel'.format(self.serial,n)),
                                set_cmd=partial(self.daq.setDouble,'/{}/scopes/{}/triglevel'.format(self.serial,n)))
            self.add_parameter(name='scope{}_channel'.format(n),
                                label='scope{}_channel'.format(n),
                                get_cmd=partial(self.daq.getInt,'/{}/scopes/{}/channel'.format(self.serial,n)),
                                get_parser=self.scope_chan_parser,
                                set_cmd=partial(self.daq.setInt,'/{}/scopes/{}/channel'.format(self.serial,n)),
                                vals= Ints(min_value=1, max_value=3))
            self.add_parameter(name='scope{}_rate'.format(n),
                                label='scope{}_rate'.format(n),
                                get_cmd=partial(self.daq.getInt,'/{}/scopes/{}/time'.format(self.serial,n)),
                                get_parser=self.scope_rate_parser,
                                set_cmd=partial(self.daq.setInt,'/{}/scopes/{}/time'.format(self.serial,n)),
                                vals= Ints(min_value=1, max_value=15))
            self.add_parameter(name='scope{}_data'.format(n),
                                get_cmd=self.getScope)
            self.add_parameter(name='scope{}_trigsource'.format(n),
                                label='scope{}_trigsource'.format(n),
                                get_cmd=partial(self.daq.getInt,'/{}/scopes/{}/trigchannel'.format(self.serial,n)),
                                get_parser=self.scope_chaninput_parser,
                                set_cmd=partial(self.daq.setInt,'/{}/scopes/{}/trigchannel'.format(self.serial,n)),
                                vals= Enum(0,1,2,3,4,5,6,7,8,9,10,11,14,15,16,17,32,33,48,49,64,65))
            for chan in range(2):
                self.add_parameter(name='scope{}_ch{}_input'.format(n,chan+1),
                                label='scope{}_ch{}_input'.format(n,chan+1),
                                get_cmd=partial(self.daq.getInt,'/{}/scopes/{}/channels/{}/inputselect'.format(self.serial,n,chan)),
                                get_parser=self.scope_chaninput_parser,
                                set_cmd=partial(self.daq.setInt,'/{}/scopes/{}/channels/{}/inputselect'.format(self.serial,n,chan)),
                                vals= Enum(0,1,2,3,4,5,6,7,8,9,10,11,14,15,16,17,32,33,48,49,64,65))

    ## commands

    def setAmplitude(self,path,val):
        """
        The lock-in sets amplitude as fraction of output range, the command here converts it such that you can input actual voltage as a normal person.
        DC 2022-08-17. Not true, at least for MFLI. Removed output range, changed it to be rms
        """


        idx = path.find('dev')
        serial = path[idx:idx+7]
        sig = path[path.find('outs')+5]

        outRange = self.daq.getDouble('/{}/sigouts/{}/range'.format(serial,sig))
        out = val*np.sqrt(2)

        if out <= 1:
            self.daq.setDouble(path, out)
        else:
            raise ValueError("Value {} is outside the output range".format(val))

    def getAmplitude(self,path):
        idx = path.find('dev')
        serial = path[idx:idx+7]
        sig = path[path.find('outs')+5]

        outRange = self.daq.getDouble('/{}/sigouts/{}/range'.format(serial,sig))
        val = self.daq.getDouble(path)
        out = val/np.sqrt(2)

        return out


    def getX(self,path):
        data = self.daq.getSample(path)
        x = float(data['x'])
        return x

    def getY(self,path):
        data = self.daq.getSample(path)
        y = float(data['y'])
        return y

    def getR(self,path):
        data = self.daq.getSample(path)
        x = float(data['x'])
        y = float(data['y'])
        R = np.sqrt(x**2+y**2)
        return R
        
    def getP(self,path):
        data = self.daq.getSample(path)
        P = float(data['phase'])
        return P

    def scope_chan_parser(self,val):
        if val==3:
            return 'Both Channel 1 and 2'
        if val==2:
            return 'Channel 2'
        if val==1:
            return 'Channel 1'

    def scope_rate_parser(self,val):
        return self.scoperates[str(val)]

    def scope_chaninput_parser(self,val):
        return self.scopechaninputs[str(val)]

    def getScope(self):
        scope=self.daq.scopeModule()

        #At the moment assuming only one scope to simplify code. Not sure if possible to have more scopes with add-ons
        scope.subscribe('/{}/scopes/0/wave'.format(self.serial))
        scope.execute()
        #Need to wait until data is returned after execute. But not obvious exactly how long this should be
        #It's not just totalsamples/samplerate, seems to depend on communication time, which is always somewhat random
        #Therefore just read the data until it includes the device serial; then the aquisition is definitely complete
        read=scope.read()
        while self.serial not in read:
            read=scope.read()
        data=read[self.serial]['scopes']['0']['wave'][0][0]

        #At the moment assuming xaxis is time, need to change this if it's the FFT...
        dt=data['dt']
        totalsamples=data['totalsamples']
        xdata=[-totalsamples*dt/2+dt*i for i in range(totalsamples)]
        xarray=DataArray(label='Time',unit='s',array_id='time',name='time',preset_data=xdata,is_setpoint=True)

        #The data retured depends on how many scope channels are running. Find this out and return accordingly.
        #Also need to find out if the current input is being used, to assign units correctly
        numchans=partial(self.daq.getInt,'/{}/scopes/0/channel'.format(self.serial))()

        #Returns qcodes arrays. 
        if numchans==3:
            chan1input=partial(self.daq.getInt,'/{}/scopes/0/channels/0/inputselect'.format(self.serial))()
            chan2input=partial(self.daq.getInt,'/{}/scopes/0/channels/1/inputselect'.format(self.serial))()
            print(chan1input,chan2input)
            if chan1input==1:
                units=['A','V']
            elif chan2input==1:
                units=['V','A']
            else:
                units=['V','V']
            ydata_ch1=data['wave'][0]
            yarray1=DataArray(label='Scope Ch 1',unit=units[0],array_id='channel1',name='channel1',preset_data=ydata_ch1,set_arrays=(xarray,))
            ydata_ch2=data['wave'][1]
            yarray2=DataArray(label='Scope Ch 2',unit=units[1],array_id='channel2',name='channel2',preset_data=ydata_ch2,set_arrays=(xarray,))
            return(xarray,yarray1,yarray2)

        elif numchans==2:
            if partial(self.daq.getInt,'/{}/scopes/0/channels/1/inputselect'.format(self.serial))() ==1:
                units='A'
            else:
                units='V'
            ydata_ch2=data['wave'][0]
            yarray=DataArray(label='Scope Ch 2',unit=units,array_id='channel2',name='channel2',preset_data=ydata_ch2,set_arrays=(xarray,))
            return(xarray,yarray)

        elif numchans==1:
            if partial(self.daq.getInt,'/{}/scopes/0/channels/0/inputselect'.format(self.serial))() ==1:
                units='A'
            else:
                units='V'
            ydata_ch1=data['wave'][0]
            yarray=DataArray(label='Scope Ch 1',unit=units,array_id='channel1',name='channel1',preset_data=ydata_ch1,set_arrays=(xarray,))
            return(xarray,yarray)

        else:
            return('No scope channels active')