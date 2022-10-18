
from zhinst.ziPython import ziDAQServer
from zhinst.utils import utils
from qcodes.instrument.base import Instrument
from qcodes.utils.validators import Numbers, Enum, Ints
from functools import partial
import numpy as np



class ZIHF2LI(Instrument):
    """
    This is the driver for the Zurich Instruments HF2LI compatible with the older qcodes v0.1.11.
    It has the most important functions for configuring outputs and reading off inputs to qcodes.

    Serial - the device serial number printed on the chassis used for connecting to the device

    TODO add remaining parameters, perhaps change the output amplitudes to Vrms for easier setup.
    Add validators to parameters that don't have them yet.
    """

    LI = {
            "numSigouts": 2,   # number of signal outputs
            "numModes": 8,     # number of output modes
            "numOscs": 6,      # number of oscillators
            "numDemods": 6,    # number of demodulators
            "numDemodsExt": 2, # number of external reference demodulators
            "numVins": 2,      # number of voltage inputs
            "numAUXouts": 4,   # number of AUX outputs
            "numAUXins": 2     # number of AUX inputs
        }


    daq = ziDAQServer('localhost', 8005,1)

                
    def __init__(self, name, serial, **kwargs):
        super().__init__(name, **kwargs)
        self.name = name
        self.serial = serial




        # Register oscillators
        for n in range(self.LI["numOscs"]):
            self.add_parameter(name='osc{}_freq'.format(n),
                               label='osc{}_freq'.format(n),
                               unit='Hz',
                               set_cmd= partial(self.daq.setDouble,'/{}/oscs/{}/freq'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/oscs/{}/freq'.format(self.serial, n)),
                               get_parser = float,
                               vals = Numbers(min_value=0, max_value=50E6))
            
        

        # Register outputs
        for n in range(self.LI["numSigouts"]):
            # Output on or off
            self.add_parameter(name='out{}_enabled'.format(n),
                           label='out{}_output'.format(n),
                           set_cmd= partial(self.daq.setInt, '/{}/sigouts/{}/on'.format(self.serial, n)),
                           get_cmd= partial(self.daq.getInt, '/{}/sigouts/{}/on'.format(self.serial, n)),
                           val_mapping={
                                       True : 1,
                                       False : 0,
                                       },
                          vals=Ints(min_value=0, max_value=1))

            # Output range
            self.add_parameter(name='out{}_range'.format(n),
                               label='out{}_range'.format(n),
                               unit='V',
                               set_cmd= partial(self.daq.setDouble,'/{}/sigouts/{}/range'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/sigouts/{}/range'.format(self.serial, n)),
                               get_parser= float,
                               vals = Enum(0.01, 0.1, 1, 10))

            # Output offset
            self.add_parameter(name='out{}_offset'.format(n),
                               label='out{}_offset'.format(n),
                               unit='V',
                               set_cmd= partial(self.daq.setDouble,'/{}/sigouts/{}/offset'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/sigouts/{}/offset'.format(self.serial, n)),
                               get_parser= float,
                               vals = Numbers(min_value=-1, max_value=1))




            # Register modes
            for i in range(self.LI["numModes"]):
                #mode amplitudes
                self.add_parameter(name='out{}_amp{}'.format(n, i),
                                   label='out{}_amplitude{}'.format(n, i),
                                   unit='V',
                                   set_cmd=partial(self.setAmplitude,'/{}/sigouts/{}/amplitudes/{}'.format(self.serial, n, i)),
                                   get_cmd=partial(self.getAmplitude,'/{}/sigouts/{}/amplitudes/{}'.format(self.serial, n, i)),
                                   get_parser = float)
            

                # modes on or off
                self.add_parameter(name='out{}_mode{}_enabled'.format(n, i),
                                   label='out{}_mode{}'.format(n, i),
                                   set_cmd=partial(self.daq.setInt,'/{}/sigouts/{}/enables/{}'.format(self.serial, n, i)),
                                   get_cmd=partial(self.daq.getInt,'/{}/sigouts/{}/enables/{}'.format(self.serial, n, i)),
                                   get_parser = int,
                                   val_mapping={
                                               True : 1,
                                               False : 0,
                                               },
                                   vals=Ints(min_value=0, max_value=1))

        





        for n in range(self.LI["numDemods"]):
            self.add_parameter(name='demod{}_X'.format(n),
                               label='X',
                               unit='V',
                               get_cmd= partial(self.getX,'/{}/demods/{}/sample'.format(self.serial,n)),
                               get_parser = float)
            


            self.add_parameter(name='demod{}_Y'.format(n),
                               label='Y',
                               unit='V',
                               get_cmd= partial(self.getY,'/{}/demods/{}/sample'.format(self.serial,n)),
                               get_parser = float)
            


            self.add_parameter(name='demod{}_phase'.format(n),
                               label='Phase',
                               unit='deg',
                               get_cmd= partial(self.getP,'/{}/demods/{}/sample'.format(self.serial,n)),
                               get_parser = float)
            


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



            self.add_parameter(name='demod{}_tc'.format(n),
                               label='demod{}_tc'.format(n),
                               set_cmd= partial(self.daq.setDouble,'/{}/demods/{}/timeconstant'.format(self.serial,n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/demods/{}/timeconstant'.format(self.serial,n)),
                               get_parser=float,)



            self.add_parameter(name='demod{}_osc'.format(n),
                               label='demod{}_oscillator'.format(n),
                               set_cmd=partial(self.daq.setInt,'/{}/demods/{}/oscselect'.format(self.serial, n)),
                               get_cmd=partial(self.daq.getInt,'/{}/demods/{}/oscselect'.format(self.serial, n)),
                               get_parser = int,
                               vals=Ints(min_value=0, max_value=5))



            self.add_parameter(name='demod{}_input'.format(n),
                               label='demod{}_input'.format(n),
                               set_cmd=partial(self.daq.setInt,'/{}/demods/{}/adcselect'.format(self.serial, n)),
                               get_cmd=partial(self.daq.getInt,'/{}/demods/{}/adcselect'.format(self.serial, n)),
                               get_parser = int,
                               val_mapping={
                                           "Vin0" : 0,
                                           "Vin1" : 1,
                                           },
                               vals=Ints(min_value=0, max_value=1))


            # Low pass filter order
            self.add_parameter(name='demod{}_LPorder'.format(n),
                               label='demod{}_LPorder'.format(n),
                               set_cmd=partial(self.daq.setInt,'/{}/demods/{}/order'.format(self.serial, n)),
                               get_cmd=partial(self.daq.getInt,'/{}/demods/{}/order'.format(self.serial, n)),
                               get_parser = int,
                               vals=Ints(min_value=1, max_value=8))


        for n in range(self.LI["numDemodsExt"]):
            # External reference on or off
            self.add_parameter(name='demod{}_mode'.format(n+6),
                           label='demod{}_mode'.format(n+6),
                           set_cmd=partial(self.daq.setInt,'/{}/plls/{}/enable'.format(self.serial, n)),
                           get_cmd=partial(self.daq.getInt,'/{}/plls/{}/enable'.format(self.serial, n)),
                           get_parser = int,
                           val_mapping={
                                       True : 1,
                                       False : 0,
                                       },
                           vals=Ints(min_value=0, max_value=1))



            self.add_parameter(name='demod{}_input'.format(n+6),
                               label='demod{}_input'.format(n+6),
                               set_cmd=partial(self.daq.setInt,'/{}/plls/{}/adcselect'.format(self.serial, n)),
                               get_cmd=partial(self.daq.getInt,'/{}/plls/{}/adcselect'.format(self.serial, n)),
                               get_parser = int,
                               val_mapping={
                                           "Vin0" : 0,
                                           "Vin1" : 1,
                                           "AUXin1": 2,
                                           "AUXin2": 3,
                                           },
                               vals=Ints(min_value=0, max_value=3))




            





        # REgister inputs
        for n in range(self.LI["numVins"]):
            self.add_parameter(name='Vin{}_range'.format(n),
                               label='Vin{}_range'.format(n),
                               set_cmd= partial(self.daq.setDouble,'/{}/sigins/{}/range'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getDouble,'/{}/sigins/{}/range'.format(self.serial, n)),
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
                                           },
                               vals= Enum(-1, 0, 1, 2, 3, 11, 13))


            # Channel
            self.add_parameter(name='AUXout{}_channel'.format(n),
                               label='AUXout{}_channel'.format(n),
                               set_cmd= partial(self.daq.setInt,'/{}/auxouts/{}/demodselect'.format(self.serial, n)),
                               get_cmd= partial(self.daq.getInt,'/{}/auxouts/{}/demodselect'.format(self.serial, n)),
                               vals= Ints(min_value=1, max_value=6))




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
                               get_cmd= partial(self.daq.getDouble,'/{}/auxins/{}/value'.format(self.serial, n)),
                               get_parser = float)




                              
                           
        


    
    
    def setAmplitude(self,path,val):
        """
        The lock-in sets amplitude as fraction of output range, the command here converts it such that you can input actual voltage as a normal person.
        It also converts from the rms value that should be given to qcodes into the pk-pk value accepted at the LI
        """


        idx = path.find('dev')
        serial = path[idx:idx+7]
        sig = path[path.find('outs')+5]
        
        outRange = self.daq.getDouble('/{}/sigouts/{}/range'.format(serial,sig))
        out = val*np.sqrt(2)/outRange
        
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
        out = val*outRange/np.sqrt(2)
        
        return out
    
    
    def getX(self,path):
        data = self.daq.getSample(path)
        x = float(data['x'])
        return x
    
    def getY(self,path):
        data = self.daq.getSample(path)
        y = float(data['y'])
        return y
    
    def getP(self,path):
        data = self.daq.getSample(path)
        P = float(data['phase'])
        return P
            
