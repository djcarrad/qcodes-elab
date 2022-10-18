#Useful functions developed over the years to speed up various analysis tasks

import numpy as np
import glob
from qcodes.data import data_set        
                    
def IGconvert(listofnumbers,z_param='camp1_conductance',x_param='default',y_param='default',datafolder='data',exportfolder="inspectragadget"):
    #convert many xyz qcodes datasets to three column data files for loading in InSpectra Gadget
    #x and y default to the the 'set' parameters in qcodes data. z defaults to conductance. change as required.
    #listofnumbers is a list of strings, in the format used in the file name, e.g. "#004"
    #Since qcodes defaults to 3 digit numbers, problems will arise with more than 999 data sets. Including the character after the number should help
    print(listofnumbers)
    for i in range (np.shape(listofnumbers)[0]):
        datapaths = [glob.glob('{}/#{}*/'.format(datafolder,listofnumbers[i]))]
        if np.shape(datapaths[0])[0]>1:
            raise ValueError('Multiple data sets with number {} found! check numbering. '
                             'If you have more than 999 data sets try including '
                             'the character/delimiter after the number'.format(listofnumbers[i]))
        elif np.shape(datapaths[0])[0]==0:
            raise ValueError('No dataset with number {} found! check numbering. '.format(listofnumbers[i]))
        else:
            data=data_set.load_data(datapaths[0][0])
            
            if x_param=='default':
                x_param=list(data.arrays.keys())[0]
            if y_param=='default':
                y_param=list(data.arrays.keys())[1]
            x_data=data.arrays[x_param]
            y_data=data.arrays[y_param]
            z_data=data.arrays[z_param]
            
            filename = (datapaths[0][0].split("\\"))[1]
            print(filename)
            with open(exportfolder+"/"+filename+".dat", "w") as txt_file:
                for j in range(np.shape(z_data)[0]):
                    for k in range(np.shape(z_data)[1]):
                        txt_file.write('{} {} {}\n'.format(x_data[j],y_data[j,k],z_data[j,k]))

