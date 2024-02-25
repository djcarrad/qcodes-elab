#Useful functions developed over the years to speed up various analysis tasks

import numpy as np
import glob
import os
from qcodes.data import data_set
import matplotlib.pyplot as plt
from matplotlib import cm    
from matplotlib.ticker import MultipleLocator
                    
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

def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    r"""Smooth (and optionally differentiate) data with a Savitzky-Golay filter.
    The Savitzky-Golay filter removes high frequency noise from data.
    It has the advantage of preserving the original shape and
    features of the signal better than other types of filtering
    approaches, such as moving averages techniques.
    Parameters
    ----------
    y : array_like, shape (N,)
        the values of the time history of the signal.
    window_size : int
        the length of the window. Must be an odd integer number.
    order : int
        the order of the polynomial used in the filtering.
        Must be less then `window_size` - 1.
    deriv: int
        the order of the derivative to compute (default = 0 means only smoothing)
    Returns
    -------
    ys : ndarray, shape (N)
        the smoothed signal (or it's n-th derivative).
    Notes
    -----
    The Savitzky-Golay is a type of low-pass filter, particularly
    suited for smoothing noisy data. The main idea behind this
    approach is to make for each point a least-square fit with a
    polynomial of high order over a odd-sized window centered at
    the point.
    Examples
    --------
    t = np.linspace(-4, 4, 500)
    y = np.exp( -t**2 ) + np.random.normal(0, 0.05, t.shape)
    ysg = savitzky_golay(y, window_size=31, order=4)
    import matplotlib.pyplot as plt
    plt.plot(t, y, label='Noisy signal')
    plt.plot(t, np.exp(-t**2), 'k', lw=1.5, label='Original signal')
    plt.plot(t, ysg, 'r', label='Filtered signal')
    plt.legend()
    plt.show()
    References
    ----------
    .. [1] A. Savitzky, M. J. E. Golay, Smoothing and Differentiation of
       Data by Simplified Least Squares Procedures. Analytical
       Chemistry, 1964, 36 (8), pp 1627-1639.
    .. [2] Numerical Recipes 3rd Edition: The Art of Scientific Computing
       W.H. Press, S.A. Teukolsky, W.T. Vetterling, B.P. Flannery
       Cambridge University Press ISBN-13: 9780521880688
    """
    import numpy as np
    from math import factorial
    
    try:
        window_size = np.abs(int(window_size))
        order = np.abs(int(order))
    except (ValueError, msg):
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')