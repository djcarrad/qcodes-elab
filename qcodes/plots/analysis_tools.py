#Useful functions developed over the years to speed up various analysis tasks

import numpy as np
import glob
import os
import numpy as np
from qcodes.data import data_set
import matplotlib.pyplot as plt
from matplotlib import cm    
from matplotlib.ticker import MultipleLocator
from lmfit.models import LorentzianModel, GaussianModel


def colourplot(data,figsize=0,cmap=0,labels=0,xlim=0,ylim=0,zlim=0,xmajor=0,xminor=0,ymajor=0,yminor=0,font_size=0,label_size=0):
    """
    Make a nice colourplot from a three-dimensional data array using matplotlib. First argument data=[x,y,z]. 
    Arguments: (data,figsize=0,cmap=0,labels=0,xlim=0,ylim=0,zlim=0,xmajor=0,xminor=0,ymajor=0,yminor=0,font_size=0,label_size=0)
    """
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
        ax1.set_xlim(xlim)
    if ylim!=0:
        ax1.set_ylim(ylim)
    
    return (fig,ax1,cax)

def fit_lorentzians(x,y,numofpeaks=None,rough_peak_positions=None,
                    amplitudes=None,sigmas=None,xrange=None,
                    plotlabels=['x', 'y'],plotname='plotname', savefig=False):
   
    #Fits x,y data with lorentzian functions using 'rough_peak_positions' as initial guess positions.
    #One can instead provide the number of peaks, and the fitter will start with an initial guess of evenly spaced peaks.
    #numofpeaks is ignored if rough_peak_positions provided
    #If necessary, the range of the data can be limited, in units of the x data.
    #Custom starting amplitudes (proportional to height) and sigmas (proportional to width) may also be given
    #Returns parameters for each of the peaks fitted, 'peak0' to 'peakN' where N is the number of peaks in rough_peak_positions
    #If savefig set to True, saves the figure with plotname, which should include the filetype.

    if x[0]>x[-1]:
        x=x[::-1]
        y=y[::-1]

    if xrange==None:
        x_clip=x
        y_clip=y
    else:
        min_ind=(np.abs(x - xrange[0])).argmin()
        max_ind=(np.abs(x - xrange[1])).argmin()
        x_clip=x[min_ind:max_ind]
        y_clip=y[min_ind:max_ind]
    
    if rough_peak_positions==None:
        if numofpeaks==None:
            raise ValueError('Please provide either rough_peak_positions or numofpeaks')
        peakspacing=(x_clip.max()-x_clip.min())/numofpeaks
        rough_peak_positions=[i*peakspacing+peakspacing/2+x_clip.min() for i in range(numofpeaks)]
        #print(rough_peak_positions)

    if amplitudes==None: #Guess that the amplitudes will be close to the maximum value of the data
        amplitudes=np.max(y_clip)
    if sigmas==None: #Sigma = FWHM/2, so sigma should be roughly a fourth of the peak spacing. May be much less if peaks not overlapping
        sigmas=np.abs(x_clip[-1]-x_clip[0])/(4*numofpeaks)
        
    peakpos0=rough_peak_positions[0]
    peakpositions=rough_peak_positions[1:]
    
    def add_peak(prefix, center, amplitude=amplitudes, sigma=sigmas):
        peak = LorentzianModel(prefix=prefix)
        pars = peak.make_params()
        pars[prefix + 'center'].set(center)
        pars[prefix + 'amplitude'].set(amplitude, min=0)
        pars[prefix + 'sigma'].set(sigma, min=0)
        return peak, pars

    model = LorentzianModel(prefix='peak0_')
    params = model.make_params()
    params['peak0_center'].set(peakpos0)
    params['peak0_amplitude'].set(amplitudes, min=0)
    params['peak0_sigma'].set(sigmas, min=0)

    for i, cen in enumerate(peakpositions):
        peak, pars = add_peak('peak%d_' % (i+1), cen)
        model = model + peak
        params.update(pars)

    init = model.eval(params, x=x_clip)
    result = model.fit(y_clip, params, x=x_clip)
    components = result.eval_components()

    plt.plot(x_clip, y_clip, label='data')
    plt.plot(x_clip, result.best_fit, label='best fit')
    for i in range(np.shape(rough_peak_positions)[0]):
        plt.plot(x_clip, components['peak'+str(i)+'_'], '--', color='k')
    plt.legend(loc='upper right')
    plt.xlabel(plotlabels[0])
    plt.ylabel(plotlabels[1])
    if savefig==True:
        plt.savefig(plotname, dpi=300, bbox_inches='tight')
    plt.show()
   
    return(result.values)


def fit_gaussians(x,y,numofpeaks=None,rough_peak_positions=None,
                    amplitudes=None,sigmas=None,xrange=None,
                    plotlabels=['x', 'y'],plotname='plotname',savefig=False):
   
    #Fits x,y data with lorentzian functions using 'rough_peak_positions' as initial guess positions.
    #One can instead provide the number of peaks, and the fitter will start with an initial guess of evenly spaced peaks.
    #numofpeaks is ignored if rough_peak_positions provided
    #If necessary, the range of the data can be limited by xrange, in units of the data.
    #Custom starting amplitudes (proportional to height) and sigmas (proportional to width) may also be given
    #Returns parameters for each of the peaks fitted, 'peak0' to 'peakN' where N is the number of peaks in rough_peak_positions
    #If savefig set to True, saves the figure with plotname, which should include the filetype.
   
    if x[0]>x[-1]:
        x=x[::-1]
        y=y[::-1]

    if xrange==None:
        x_clip=x
        y_clip=y

    else:
        min_ind=(np.abs(x - xrange[0])).argmin()
        max_ind=(np.abs(x - xrange[1])).argmin()
        x_clip=x[min_ind:max_ind]
        y_clip=y[min_ind:max_ind]
    
    if rough_peak_positions==None:
        if numofpeaks==None:
            raise ValueError('Please provide either rough_peak_positions or numofpeaks')
        peakspacing=(x_clip.max()-x_clip.min())/numofpeaks
        rough_peak_positions=[i*peakspacing+peakspacing/2+x_clip.min() for i in range(numofpeaks)]
        #print(rough_peak_positions)

    if amplitudes==None: #Guess that the amplitudes will be close to the maximum value of the data
        amplitudes=np.max(y_clip)
    if sigmas==None: #Sigma = FWHM/2, so sigma should be roughly a fourth of the peak spacing. May be much less if peaks not overlapping
        sigmas=np.abs(x_clip[-1]-x_clip[0])/(4*numofpeaks)
        
    peakpos0=rough_peak_positions[0]
    peakpositions=rough_peak_positions[1:]
    
    def add_peak(prefix, center, amplitude=amplitudes, sigma=sigmas):
        peak = GaussianModel(prefix=prefix)
        pars = peak.make_params()
        pars[prefix + 'center'].set(center)
        pars[prefix + 'amplitude'].set(amplitude, min=0)
        pars[prefix + 'sigma'].set(sigma, min=0)
        return peak, pars

    model = GaussianModel(prefix='peak0_')
    params = model.make_params()
    params['peak0_center'].set(peakpos0)
    params['peak0_amplitude'].set(amplitudes, min=0)
    params['peak0_sigma'].set(sigmas, min=0)

    for i, cen in enumerate(peakpositions):
        peak, pars = add_peak('peak%d_' % (i+1), cen)
        model = model + peak
        params.update(pars)

    init = model.eval(params, x=x_clip)
    result = model.fit(y_clip, params, x=x_clip)
    components = result.eval_components()

    plt.plot(x_clip, y_clip, label='data')
    plt.plot(x_clip, result.best_fit, label='best fit')
    for i in range(np.shape(rough_peak_positions)[0]):
        plt.plot(x_clip, components['peak'+str(i)+'_'], '--', color='k')
    plt.xlabel(plotlabels[0])
    plt.ylabel(plotlabels[1])
    plt.legend(loc='upper right')
    if savefig==True:
        plt.savefig(plotname, dpi=300, bbox_inches='tight')
    plt.show()
   
    return(result.values)

#The below will be deprecated at some point, since Inspectra Gadget is working well.
def IGconvert(listofnumbers,z_param='conductance',x_param='default',y_param='default',datafolder='data',exportfolder="inspectragadget"):
    '''
    convert many xyz qcodes datasets to three column data files for loading in InSpectra Gadget
    x and y default to the the 'set' parameters in qcodes data. z defaults to conductance. change as required.
    listofnumbers is a list of strings, in the format used in the file name, e.g. "#004"
    Since qcodes defaults to 3 digit numbers, problems will arise with more than 999 data sets. Including the character after the number should help
    Arguments: (listofnumbers,z_param='conductance',x_param='default',y_param='default',datafolder='data',exportfolder="inspectragadget")
    '''
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
    '''
    Export a previously loaded qcodes dataset to three column data files for loading in InSpectra Gadget
    x and y default to the the 'set' parameters in qcodes data. z defaults to conductance. change as required.
    Arguments: (data,z_param='conductance',x_param='default',y_param='default',exportfolder="inspectragadget")
    '''
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