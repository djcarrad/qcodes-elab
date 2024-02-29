from qcodes.instrument.parameter import MultiParameter, Parameter
from qcodes import Station,Plot,DataSet,param_move,set_data_format,Loop
import numpy as np
from datetime import date

class QDac_current(Parameter):
    def __init__(self, qdac, channel):

        self._channel = str(channel).zfill(2)
        self.name = (qdac.name+'_ch'+self._channel+'_curr')

        super().__init__(name=self.name)

        self._qdac=qdac

        self.label = ('Current')
        self.unit = ('A')

        self.serial=qdac.IDN()['serial']
        self.fit_params_low=np.loadtxt('C:/git/qcodes-elab/qcodes/wrappers/damon/'+self.serial+'fit_params_low_latest.dat')[channel-1]
        self.fit_params_high=np.loadtxt('C:/git/qcodes-elab/qcodes/wrappers/damon/'+self.serial+'fit_params_high_latest.dat')[channel-1]

    def get_raw(self):

        volt = self._qdac.channel(self._channel).volt()
        curr_raw = self._qdac.channel(self._channel).curr()

        if self._qdac.channel(self._channel).curr_range()=='LOW':
        	fitindex=np.shape(self.fit_params_low)[0]
        	value=curr_raw-sum(self.fit_params_low[i]*volt**(fitindex-1-i) for i in range(fitindex))
        if self._qdac.channel(self._channel).curr_range()=='HIGH':
        	fitindex=np.shape(self.fit_params_high)[0]
        	value=curr_raw-sum(self.fit_params_high[i]*volt**(fitindex-1-i) for i in range(fitindex))

        return value

def calibrate_qdac_currents(qdac,lowcurrent=True,highcurrent=True,nplc=2,numdatapoints=201,fitindex=10,plot_results=False,channel_list=0,overwrite_latest=True):
    
    #This procedure calibrates the open circuit current of a QDevil QDac-II. 
    #Due to common mode error, each channel measures a unique, voltage dependent current in open circuit which must be corrected for.
    #To run the calibration, remove all loads from the outputs.
    #
    
    serial=qdac.IDN()['serial']
    name=qdac.name
    
    internal_station=Station(qdac)
    
    originaldatafmt=DataSet.location_provider.fmt
    
    #Do not let the user overwrite the calibration used by QDac_current driver unless they are going to do every channel
    if channel_list!=0:
        overwrite_latest=False

    if channel_list==0:
        channel_list=[i+1 for i in range(24)]
    print('Calibrating '+str(qdac.name)+' channels '+str(channel_list))
    
    print('Saving initial configuration')
    initialconfig=qdac.snapshot()
    
    for i,channel in enumerate(channel_list):
        channel_list[i]=str(channel_list[i]).zfill(2)
    
    print('Setting all outputs to zero, with high output range and filter')
    for i,channel in enumerate(channel_list):
        qdac.channel(channel).dc_mode('FIX')
        qdac.channel(channel).volt(0)
        qdac.channel(channel).output_range('HIGH')
        qdac.channel(channel).output_filter('HIGH')
        qdac.channel(channel).measurement_count(1)
        qdac.channel(channel).measurement_nplc(nplc)

    if lowcurrent==True:
        set_data_format(fmt='C:/Users/Triton12/Measurements/qdaccalibrations/serial'+serial+'/{date}/low/#{counter}_{name}_{date}_{time}')
        fit_parameters_low=[]
        if plot_results==True:
            pp_low=Plot()
        print('Running calibration for low current range on channel:')
        for i,channel in enumerate(channel_list):
            internal_station.set_measurement(qdac.channel(channel).curr)
            print(channel)
            qdac.channel(channel).curr_range('LOW')
            param_move(qdac.channel(channel).volt,-10,5)
            loop=Loop(qdac.channel(channel).volt.sweep(-10,10,num=numdatapoints,print_warning=False),delay=qdac.channel(channel).measurement_aperture_s()*2).each(*internal_station.measure())
            data=loop.get_data_set(name='QDac#{} ch{} low'.format(serial,channel))
            if plot_results==True:
                data.publisher=pp_low
                pp_low.add(data.arrays[name+'_ch'+channel+'_curr'],name='low_curr',title='ch'+channel,subplot=i)
            loop.run(station=internal_station,quiet=True)
            param_move(qdac.channel(channel).volt,0,5)
            fit=np.polyfit(data.arrays[name+'_ch'+channel+'_volt_set'],data.arrays[name+'_ch'+channel+'_curr'], fitindex)
            fit_parameters_low.append(fit)
        np.savetxt('C:\\Users\\Triton12\\Measurements\\qdaccalibrations\\serial'+serial+'\\'+str(date.today())+'\\low\\'+serial+'fit_params_low_'+str(date.today())+'.dat',fit_parameters_low)
        print('Low current calibration values saved to')
        print('C:\\Users\\Triton12\\Measurements\\qdaccalibrations\\serial'+serial+'\\'+str(date.today())+'\\low\\'+serial+'fit_params_low_'+str(date.today())+'.dat')
        if overwrite_latest==True:
            np.savetxt('C:\\git\\qcodes-elab\\qcodes\\wrappers\\damon\\'+serial+'fit_params_low_latest.dat',fit_parameters_low)
            print('and C:\\git\\qcodes-elab\\qcodes\\wrappers\\damon\\'+serial+'fit_params_low_latest.dat')
            
    if highcurrent==True:
        set_data_format(fmt='C:/Users/Triton12/Measurements/qdaccalibrations/serial'+serial+'/{date}/high/#{counter}_{name}_{date}_{time}')
        fit_parameters_high=[]
        if plot_results==True:
            pp_high=Plot()
        print('Running calibration for high current range on channel:')
        for i,channel in enumerate(channel_list):
            internal_station.set_measurement(qdac.channel(channel).curr)
            print(channel)
            qdac.channel(channel).curr_range('HIGH')
            param_move(qdac.channel(channel).volt,-10,5)
            loop=Loop(qdac.channel(channel).volt.sweep(-10,10,num=numdatapoints,print_warning=False),delay=qdac.channel(channel).measurement_aperture_s()*2).each(*internal_station.measure())
            data=loop.get_data_set(name='QDac#{} ch{} high'.format(serial,channel))
            if plot_results==True:
                data.publisher=pp_high
                pp_high.add(data.arrays[name+'_ch'+channel+'_curr'],name='high_curr',title='ch'+channel,subplot=i)
            loop.run(station=internal_station,quiet=True)
            param_move(qdac.channel(channel).volt,0,5)
            fit=np.polyfit(data.arrays[name+'_ch'+channel+'_volt_set'],data.arrays[name+'_ch'+channel+'_curr'], fitindex)
            fit_parameters_high.append(fit)
        np.savetxt('C:\\Users\\Triton12\\Measurements\\qdaccalibrations\\serial'+serial+'\\'+str(date.today())+'\\high\\'+serial+'fit_params_high_'+str(date.today())+'.dat',fit_parameters_low)
        print('High current calibration values saved to')
        print('C:\\Users\\Triton12\\Measurements\\qdaccalibrations\\serial'+serial+'\\'+str(date.today())+'\\high\\'+serial+'fit_params_high_'+str(date.today())+'.dat')
        if overwrite_latest==True:
            np.savetxt('C:\\git\\qcodes-elab\\qcodes\\wrappers\\damon\\'+serial+'fit_params_high_latest.dat',fit_parameters_low)
            print('and C:\\git\\qcodes-elab\\qcodes\\wrappers\\damon\\'+serial+'fit_params_low_latest.dat')
        
    print('Returning qdac to initial configuration')
    for i,channel in enumerate(channel_list):
        qdac.channel(channel).curr_range(initialconfig['submodules']['ch'+channel]['parameters']['curr_range']['raw_value'])
        qdac.channel(channel).dc_mode(initialconfig['submodules']['ch'+channel]['parameters']['dc_mode']['raw_value'])
        qdac.channel(channel).output_range(initialconfig['submodules']['ch'+channel]['parameters']['output_range']['raw_value'])
        qdac.channel(channel).output_filter(initialconfig['submodules']['ch'+channel]['parameters']['output_filter']['raw_value'])
        qdac.channel(channel).measurement_count(initialconfig['submodules']['ch'+channel]['parameters']['measurement_count']['raw_value'])
        qdac.channel(channel).measurement_nplc(initialconfig['submodules']['ch'+channel]['parameters']['measurement_nplc']['raw_value'])

    set_data_format(fmt=originaldatafmt)
    print('Calibration complete.')