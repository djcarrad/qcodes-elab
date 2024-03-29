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
from Jupyter notebooks and jupyter lab, but can also be used from Spyder, traditional terminal-based
shells and in stand-alone scripts. The features in `qcodes.utils.magic` 
are exclusively for Jupyter notebooks.

If you would only like to load data associated with qcodes-elab measurements, you may like to
simply install qcodesloader: https://github.com/djcarrad/qcodes-loader

Docs
====
Check out the wiki https://github.com/djcarrad/qcodes-elab/wiki for an introduction. The 
accompanying jupyter notebooks are under 'tutorials'. As of yet, there is no separate, comprehensive
documentation; this is high on the to-do list. However, all the code is quite well self-documented and 
everything is open source. If you need to know which arguments a function takes, or which capabilities 
an instrument driver has, just open up the file! Or ask a friend

Install
=======

- Install anaconda from anaconda website: if you want to be able to call python from the command line, you should add the anaconda PATH to environment variables during install

- Install git: https://git-scm.com/download/win

- Open the newly installed git bash, navigate to the desired folder (usually cd C:/git), and clone the repository

	cd C:/git

	git clone https://github.com/djcarrad/qcodes-elab.git qcodes-elab

- Now open the Anaconda prompt and type:

	conda create –n qcodes python
	
	activate qcodes
	
	pip install –e *path to repository*

- Optionally install useful packages from the anaconda prompt:

	pip install zhinst scipy jupyterlab tqdm

You can now run qcodes in jupyter notebook or jupyter lab by opening the anaconda prompt, and typing

	activate qcodes
	
	jupyter notebook

or

	jupyter lab
	
Additionally...
---------------

- If you are going to use VISA instruments (e.g. ones that communicate via GPIB, USB, RS232) you should install the NI VISA and GPIB(488.2) backends from the National Instruments website

- If the qcodes install fails, you may need to install Visual Studio C++ build tools. https://visualstudio.microsoft.com/downloads/ --> Tools for Visual Studio --> Build Tools for Visual Studio.
	
	
Updating
--------
Open git bash, navigate to the install folder (usually cd C:/git/qcodes-elab), and use 

	git pull
Status
======
As of 18/10/2022, latest versions of all packages required by qcodes are working, except:
Ipykernel must be version 6.9 if plot windows should stay open when restarting the kernel. 
Documentation is non-existent so this would be very hard to fix as far as I can tell.

On the to-do list is improving analysis functions, such as tighter integration with InspectraGadget
and incorporation of fitting tools.

If there is a feature that you desire, feel free to contact me, damonc@dtu.dk. We can try to make it happen together!

License
=======

See `License <https://github.com/QCoDeS/Qcodes/tree/master/LICENSE.rst>`__.
