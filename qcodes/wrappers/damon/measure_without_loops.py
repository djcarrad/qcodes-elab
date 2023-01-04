from qcodes import DataArray, new_data, Plot
import numpy as np

def arrays_to_data(arrays,labels,units,names,datasetname=None,plotting=False):
    xarray=DataArray(label=labels[0],unit=units[0],array_id=names[0],name=names[0],preset_data=arrays[0],is_setpoint=True)
    data=new_data(name=datasetname)
    data.add_array(xarray)
    yarrays=[]
    for i in range(int(np.shape(arrays)[0]-1)):
        yarrays.append(DataArray(label=labels[i+1],unit=units[i+1],array_id=names[i+1],name=names[i+1],preset_data=arrays[i+1],set_arrays=(xarray,)))
        data.add_array(yarrays[-1])
    data.finalize()
    if plotting==True:
        pp=Plot()
        for i in range(int(np.shape(arrays)[0]-1)):
            pp.add(data.arrays[names[i+1]],subplot=i)
    return data

def qcarrays_to_data(arrays,datasetname=None,plotting=False):
    data=new_data(name=datasetname)
    for i in range(int(np.shape(arrays)[0])):
        data.add_array(arrays[i])
    data.finalize()
    if plotting==True:
        pp=Plot()
        j=0
        for key in data.arrays.keys():
            if data.snapshot()['arrays'][key]['is_setpoint']==False:
                pp.add(data.arrays[key],subplot=j)
                j=j+1
    return data