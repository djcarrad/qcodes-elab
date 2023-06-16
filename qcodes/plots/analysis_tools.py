#Useful functions developed over the years to speed up various analysis tasks

import numpy as np
import glob
import os
from qcodes.data import data_set
import matplotlib.pyplot as plt
from matplotlib import cm    
from matplotlib.ticker import MultipleLocator
                    
def IGconvert(listofnumbers,z_param='conductance',x_param='default',y_param='default',datafolder='data',exportfolder="inspectragadget"):
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
            if not os.path.exists(exportfolder):
                os.makedirs(exportfolder)
            with open(exportfolder+"/"+filename+".dat", "w") as txt_file:
                for j in range(np.shape(z_data)[0]):
                    for k in range(np.shape(z_data)[1]):
                        txt_file.write('{} {} {}\n'.format(x_data[j],y_data[j,k],z_data[j,k]))
            print('Exported to {}/{}.dat'.format(exportfolder,filename))

def IGexport(data,z_param='conductance',x_param='default',y_param='default',exportfolder="inspectragadget"):
    #export a previously loaded qcodes dataset to three column data files for loading in InSpectra Gadget
    #x and y default to the the 'set' parameters in qcodes data. z defaults to conductance. change as required.
    if x_param=='default':
        x_param=list(data.arrays.keys())[0]
    if y_param=='default':
        y_param=list(data.arrays.keys())[1]
    x_data=data.arrays[x_param]
    y_data=data.arrays[y_param]
    z_data=data.arrays[z_param]
    
    filename = (data.metadata['location'].split("/"))[1]
    if not os.path.exists(exportfolder):
        os.makedirs(exportfolder)
    with open(exportfolder+"/"+filename+".dat", "w") as txt_file:
        for j in range(np.shape(z_data)[0]):
            for k in range(np.shape(z_data)[1]):
                txt_file.write('{} {} {}\n'.format(x_data[j],y_data[j,k],z_data[j,k]))
    print('Exported to {}/{}.dat'.format(exportfolder,filename))

def colourplot(data,figsize=0,cmap=0,labels=0,xlim=0,ylim=0,zlim=0,xmajor=0,xminor=0,ymajor=0,yminor=0,font_size=0,label_size=0):
    plt.rcParams["font.family"] = "Arial"
    plt.rcParams['axes.linewidth'] = 1.5
    if font_size==0:
        font_size=12
    if label_size==0:
        label_size=12

    if figsize==0:
        figsize=(8,8)
    if cmap==0:
        cmap='hot'
    if labels==0:
        labels=['x','y','z']
    
    fig, (ax1, cax)=plt.subplots(nrows=1,ncols=2,figsize=figsize,dpi=300,gridspec_kw={'width_ratios':[1,0.02]}) #This allows us better control over the colourbar. Note you can then 'easily' generalise this to more subplots (see below)
    fig.tight_layout(h_pad=None, w_pad=-2)

    if zlim!=0:
        sdbs=ax1.pcolormesh(data[0],data[1],data[2],cmap=cmap,rasterized=True,linewidth=0,vmin=zlim[0],vmax=zlim[1])
    else:
        sdbs=ax1.pcolormesh(data[0],data[1],data[2],cmap=cmap,rasterized=True,linewidth=0)
    fig.colorbar(sdbs, cax=cax, orientation='vertical')

    cax.yaxis.set_ticks_position('right')
    cax.tick_params(which='major', length=4, width=1, labelsize=label_size)
    cax.set_ylabel(labels[2], fontsize=font_size, labelpad=20, rotation=270)

    ax1.set_xlabel(labels[0], fontsize=font_size, labelpad=10)
    ax1.set_ylabel(labels[1], fontsize=font_size, labelpad=10)
    if xmajor!=0:
        ax1.xaxis.set_major_locator(MultipleLocator(xmajor))
    if xminor!=0:
        ax1.xaxis.set_minor_locator(MultipleLocator(xminor))
    if ymajor!=0:
        ax1.yaxis.set_major_locator(MultipleLocator(ymajor))
    if yminor!=0:
        ax1.yaxis.set_minor_locator(MultipleLocator(yminor))
    ax1.tick_params(axis='both', which='major', direction='out', length=10, width=1, labelsize=label_size)
    ax1.tick_params(axis='both', which='minor', direction='out', length=5, width=1, labelsize=label_size)
    if xlim!=0:
        ax1.xlim(xlim)
    if ylim!=0:
        ax1.ylim(ylim)
    
    return (fig,ax1,cax)
