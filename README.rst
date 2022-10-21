QCoDeS-elab version
===================================

QCoDeS is a Python-based data acquisition framework developed by the
Copenhagen / Delft / Sydney / Microsoft quantum computing consortium.
This is NOT the main version. You can find that here: https://qcodes.github.io/

The elab version was forked from version 0.1.11 of qcodes, and is designed to preserve 
key capabilites:

- a text based data set

- live plotting using 'qplot' developed by Merlin von Soosten.

In addition, new features have been added to streamline data acquisition and the generation 
of metadata files, data loading and analysis, and extra flexibility in setpoints for loops.

QCoDeS-elab is compatible with Python 3.5+. It is primarily intended for use
from Jupyter notebooks, but can be used from Spyder, traditional terminal-based
shells and in stand-alone scripts as well. The features in `qcodes.utils.magic` 
are exclusively for Jupyter notebooks.

Docs
====
Check out the wiki https://github.com/djcarrad/qcodes-elab/wiki for an introduction.
There is no separate, comprehensive documentation, however, all the code is quite well 
self-documented and everything is open source. If you need to know which arguments a 
function takes, or which capabilities an instrument driver has, just open up the file! Or ask a friend

Install
=======

Install anaconda from anaconda website: if you want to be able to call python from 
the command line, you should add the anaconda PATH to environment variables during install

Install NI VISA and GPIB(488.2) backend from National Instruments website

Install Visual Studio C++ build tools. https://visualstudio.microsoft.com/downloads/ --> Tools for Visual Studio --> Build Tools for Visual Studio.

Install git

Clone the qcodes-elab repository. In git bash, navigate to the desired folder, and use git clone https://github.com/djcarrad/qcodes-elab

In the Anaconda prompt:
	conda create –n qcodes python
	
	activate qcodes
	
	pip install –e *path to repository*

Optionally install useful packages:
	pip install zhinst scipy jupyterlab tqdm
	
Status
------
As of 18/10/2022, latest versions of all packages required by qcodes are working, except:
Ipykernel must be version 6.9 if plot windows should stay open when restarting the kernel. 
Documentation is non-existent so this would be very hard to fix as far as I can tell.

On the to-do list is improving analysis functions, such as tighter integration with InspectraGadget
and incorporation of fitting tools.

License
=======

See `License <https://github.com/QCoDeS/Qcodes/tree/master/LICENSE.rst>`__.
