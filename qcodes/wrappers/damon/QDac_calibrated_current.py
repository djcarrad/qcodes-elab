from qcodes.instrument.parameter import MultiParameter, Parameter
from qcodes import Station,Plot,DataSet,param_move,set_data_format,Loop
import numpy as np
from datetime import date
import inspect
import time
import json

class QDac_current(Parameter):

    def __init__(self, qdac, channel, name=0):
        qclocation=inspect.getfile(Station).split('station')[0]
        self._channel = str(channel).zfill(2)
        if name==0:
            self.name = (qdac.name+'_ch'+self._channel+'_curr')
        else:
            self.name = name

        super().__init__(name=self.name)

        self._qdac=qdac

        self.label = ('Current')
        self.unit = ('A')

        self.serial=qdac.IDN()['serial']
        with open(qclocation+'wrappers/damon/'+self.serial+'fit_params_low_latest.json','r') as f:
            self.loaded_data_low=json.load(f)[self._channel]
            self.calibration_date_low=self.loaded_data_low['calibration_date']
            self.fit_params_low=self.loaded_data_low['fit_params']
        f.close()
        with open(qclocation+'wrappers/damon/'+self.serial+'fit_params_high_latest.json','r') as f:
            self.loaded_data_high=json.load(f)[self._channel]
            self.calibration_date_high=self.loaded_data_low['calibration_date']
            self.fit_params_high=self.loaded_data_low['fit_params']
        f.close()

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

def calibrate_qdac_currents(qdac,lowcurrent=True,highcurrent=True,nplc=2,numdatapoints=201,fitindex=10,plot_results=False,channel_list=0,overwrite_latest=True,base_folder='C:/Users/Triton12/Measurements/qdaccalibrations/'):
    
    #This procedure calibrates the open circuit current of a QDevil QDac-II. 
    #Due to common mode error, each channel measures a unique, voltage dependent current in open circuit which must be corrected for.
    #To run the calibration, remove all loads from the outputs.
    #
    loc_folder=inspect.getfile(QDac_current).split('QDac')[0]

    serial=qdac.IDN()['serial']
    name=qdac.name
    
    internal_station=Station(qdac)
    
    originaldatafmt=DataSet.location_provider.fmt
    
    #Do not let the user overwrite the calibration used by QDac_current driver unless they are going to do every channel
    # if channel_list!=0:
    #     overwrite_latest=False

    if channel_list==0:
        channel_list=[i+1 for i in range(24)]
    print('Calibrating '+str(qdac.name)+', with serial number '+serial+'. Channels '+str(channel_list))
    
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

    def set_qdac_multiple(val):
        for channel in channel_list:
            qdac.channel(channel).volt(val)
    def get_qdac_multiple():
        return qdac.channel(channel_list[0]).volt()
    qdac_multiple=Parameter(name='qdac_multiple',label='Voltage',unit='V',set_cmd=set_qdac_multiple,get_cmd=get_qdac_multiple)

    print('Started calibration: '+time.asctime())

    internal_station.set_measurement(*[qdac.channel(channel).curr for channel in channel_list])

    if lowcurrent==True:
        set_data_format(fmt=base_folder+'serial'+serial+'/{date}/low/#{counter}_{name}_{date}_{time}')
        fit_parameters_low={}
        if plot_results==True:
            pp_low=Plot()
        print('Running calibration for low current range')
        
        param_move(qdac_multiple,-10,10)
        time.sleep(10)
        loop=Loop(qdac_multiple.sweep(-10,10,num=numdatapoints,print_warning=False),delay=qdac.channel(channel_list[0]).measurement_aperture_s()*2).each(*internal_station.measure())
        data=loop.get_data_set(name='QDac#{} calibration low current'.format(serial,channel))

        for i,channel in enumerate(channel_list):
            qdac.channel(channel).curr_range('LOW')
            if plot_results==True:
                data.publisher=pp_low
                pp_low.add(data.arrays[name+'_ch'+channel+'_curr'],name='low_curr',title='ch'+channel,subplot=i)

        loop.run(station=internal_station,quiet=True,progress_interval=300)
        for channel in enumerate(channel_list):
            param_move(qdac.channel(channel).volt,0,5)

        for channel in channel_list:
            fit=np.polyfit(data.arrays['qdac_multiple_set'],data.arrays[name+'_ch'+channel+'_curr'], fitindex)
            fit=fit.tolist()
            fit_parameters_low[channel]={}
            fit_parameters_low[channel]['fit_params']=fit
            fit_parameters_low[channel]['calibration_date']=str(date.today())
        
        filename=base_folder+'serial'+serial+'/'+str(date.today())+'/low/'+serial+'fit_params_low_'+str(date.today())
        with open(filename+'.json','w') as f:
            json.dump(fit_parameters_low, f, indent=4)
        print('\nLow current calibration values saved to')
        print(filename+'.json')
        if overwrite_latest==True:
            filename_latest=loc_folder+serial+'fit_params_low_latest'
            try: #makes a file if this is the first time calibration.
                with open(filename_latest+'.json', 'r') as f:
                    loaded_data_low=json.load(f)
            except:
                f=open(filename_latest+'.json', 'x')
                f.close()
                loaded_data_low={}
            for channel in channel_list:
                loaded_data_low[channel]={}
                loaded_data_low[channel]['calibration_date']=fit_parameters_low[channel]['calibration_date']
                loaded_data_low[channel]['fit_params']=fit_parameters_low[channel]['fit_params']
            with open(filename_latest+'.json','w') as f:
                json.dump(loaded_data_low, f, indent=4)
            print('and '+filename_latest+' updated')
            
    if highcurrent==True:
        set_data_format(fmt=base_folder+'serial'+serial+'/{date}/high/#{counter}_{name}_{date}_{time}')
        fit_parameters_high={}
        if plot_results==True:
            pp_high=Plot()
        print('Running calibration for high current range:')

        param_move(qdac_multiple,-10,10)
        time.sleep(10)
        loop=Loop(qdac_multiple.sweep(-10,10,num=numdatapoints,print_warning=False),delay=qdac.channel(channel_list[0]).measurement_aperture_s()*2).each(*internal_station.measure())
        data=loop.get_data_set(name='QDac#{} calibration high current'.format(serial,channel))

        for i,channel in enumerate(channel_list):
            qdac.channel(channel).curr_range('HIGH')
            if plot_results==True:
                data.publisher=pp_high
                pp_high.add(data.arrays[name+'_ch'+channel+'_curr'],name='high_curr',title='ch'+channel,subplot=i)
        loop.run(station=internal_station,quiet=True)
        for channel in enumerate(channel_list):
            param_move(qdac.channel(channel).volt,0,5)

        for channel in channel_list:
            fit=np.polyfit(data.arrays['qdac_multiple_set'],data.arrays[name+'_ch'+channel+'_curr'], fitindex)
            fit=fit.tolist()
            fit_parameters_high[channel]={}
            fit_parameters_high[channel]['fit_params']=fit
            fit_parameters_high[channel]['calibration_date']=str(date.today())

        filename=base_folder+'serial'+serial+'/'+str(date.today())+'/high/'+serial+'fit_params_high_'+str(date.today())
        with open(filename+'.json','w') as f:
            json.dump(fit_parameters_high, f, indent=4)
        print('\nHigh current calibration values saved to')
        print(filename+'.json')
        if overwrite_latest==True:
            filename_latest=loc_folder+serial+'fit_params_high_latest'
            try: #makes a file if this is the first time calibration.
                with open(filename_latest+'.json', 'r') as f:
                    loaded_data_high=json.load(f)
            except:
                f=open(filename_latest+'.json', 'x')
                f.close()
                loaded_data_high={}
            for channel in channel_list:
                loaded_data_high[channel]={}
                loaded_data_high[channel]['calibration_date']=fit_parameters_high[channel]['calibration_date']
                loaded_data_high[channel]['fit_params']=fit_parameters_high[channel]['fit_params']
            with open(filename_latest+'.json','w') as f:
                json.dump(loaded_data_high, f, indent=4)
            print('and '+filename_latest+' updated')
        
    print('Returning qdac to initial configuration')
    for i,channel in enumerate(channel_list):
        qdac.channel(channel).curr_range(initialconfig['submodules']['ch'+channel]['parameters']['curr_range']['raw_value'])
        qdac.channel(channel).dc_mode(initialconfig['submodules']['ch'+channel]['parameters']['dc_mode']['raw_value'])
        qdac.channel(channel).output_range(initialconfig['submodules']['ch'+channel]['parameters']['output_range']['raw_value'])
        qdac.channel(channel).output_filter(initialconfig['submodules']['ch'+channel]['parameters']['output_filter']['raw_value'])
        qdac.channel(channel).measurement_count(initialconfig['submodules']['ch'+channel]['parameters']['measurement_count']['raw_value'])
        qdac.channel(channel).measurement_nplc(initialconfig['submodules']['ch'+channel]['parameters']['measurement_nplc']['raw_value'])

    set_data_format(fmt=originaldatafmt)
    print('Calibration complete at: '+time.asctime())


def linearity_test(qdac,channel_list=0,plotting=True,plot_raw=True,plot_calibrated=True,curr_range='LOW',output_range='HIGH',numdatapoints=201,nplc=2,base_folder='C:/Users/Triton12/Measurements/qdaccalibrations/'):
    
    serial=qdac.IDN()['serial']
    name=qdac.name
    
    internal_station=Station(qdac)
    
    initialconfig=qdac.snapshot()
    originaldatafmt=DataSet.location_provider.fmt
    set_data_format(fmt=originaldatafmt)
    
    if channel_list==0:
        channel_list=[i+1 for i in range(24)]
    
    for i,channel in enumerate(channel_list):
        channel_list[i]=str(channel_list[i]).zfill(2)
        
    qdaccurrents=[QDac_current(qdac,channel,name='qdac_ch'+channel+'_currcal') for channel in channel_list]

    def set_qdac_multiple(val):
        for channel in channel_list:
            qdac.channel(channel).volt(val)
    def get_qdac_multiple():
        return qdac.channel(channel_list[0]).volt()
    qdac_multiple=Parameter(name='qdac_multiple',label='Voltage',unit='V',set_cmd=set_qdac_multiple,get_cmd=get_qdac_multiple)
    
    if plotting==True:
        pp=Plot()
    
    set_data_format(fmt=base_folder+'serial'+serial+'/lin_tests/{date}/#{counter}_{name}_{date}_{time}')
    
    for i,channel in enumerate(channel_list):
        qdac.channel(channel).curr_range(curr_range)
        qdac.channel(channel).dc_mode('FIX')
        qdac.channel(channel).volt(0)
        qdac.channel(channel).measurement_nplc(nplc)
        qdac.channel(channel).measurement_count(1)
        qdac.channel(channel).output_range(output_range)
        qdac.channel(channel).output_filter('HIGH')
        
    internal_station.set_measurement(*[qdac.channel(channel).curr for channel in channel_list],*qdaccurrents)

    if output_range=='LOW':
        start=-2
        stop=2
        param_move(qdac_multiple,-2,10)
        time.sleep(10)
    elif output_range=='HIGH':
        start=-10
        stop=10
        param_move(qdac_multiple,-10,10)
        time.sleep(10)
    else:
        print('Imporperly defined output range. Use output_range=\'LOW\' or \'HIGH\'' )

    loop=Loop(qdac_multiple.sweep(start=start,stop=stop,num=numdatapoints,print_warning=False),delay=qdac.channel(channel_list[0]).measurement_aperture_s()*2).each(*internal_station.measure())
    data=loop.get_data_set(name='QDac#{} ch{} lin_test output_range {}'.format(serial,channel,output_range))

    if plotting==True:
        data.publisher=pp
        if plot_raw==True:
            for i,channel in enumerate(channel_list):
                pp.add(data.arrays['qdac_ch'+channel+'_curr'],name='uncalibrated',title='ch'+channel,subplot=i)
        if plot_calibrated==True:
            for i,channel in enumerate(channel_list):
                pp.add(data.arrays['qdac_ch'+channel+'_currcal'],name='calibrated',title='ch'+channel,subplot=i)

    loop.run(station=internal_station,quiet=True,progress_interval=300)
     
    for channel in channel_list:   
        qdac.channel(channel).curr_range(initialconfig['submodules']['ch'+channel]['parameters']['curr_range']['raw_value'])
        qdac.channel(channel).dc_mode(initialconfig['submodules']['ch'+channel]['parameters']['dc_mode']['raw_value'])
        qdac.channel(channel).output_range(initialconfig['submodules']['ch'+channel]['parameters']['output_range']['raw_value'])
        qdac.channel(channel).output_filter(initialconfig['submodules']['ch'+channel]['parameters']['output_filter']['raw_value'])
        qdac.channel(channel).measurement_count(initialconfig['submodules']['ch'+channel]['parameters']['measurement_count']['raw_value'])
        qdac.channel(channel).measurement_nplc(initialconfig['submodules']['ch'+channel]['parameters']['measurement_nplc']['raw_value'])
        qdac.channel(channel).volt(initialconfig['submodules']['ch'+channel]['parameters']['volt']['raw_value'])
    
    set_data_format(fmt=originaldatafmt)