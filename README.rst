QCoDeS
===================================

QCoDeS is a Python-based data acquisition framework developed by the
Copenhagen / Delft / Sydney / Microsoft quantum computing consortium.

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

Status
------
Some aspects of qcodes-elab have fallen out of compatibiliy with  current packages, 
specifically, pyqtgraph and ipykernel. The current setup file accounts for this, but
catching up is a near-term goal, and keeping up to date a longer term goal.

Install
=======

Install anaconda from anaconda website: if you want to be able to call python from 
the command line, you should add the anaconda PATH to environment variables during install

Install NI VISA and GPIB(488.2) backend from National Instruments website

Download/clone the qcodes-elab repository

In the Anaconda prompt:
	conda create –n qcodes python
	activate qcodes
	pip install –e *path to repository*

Optionally install useful packages:
	pip install zhinst scipy jupyterlab tqdm

Docs
====

License
=======

See `License <https://github.com/QCoDeS/Qcodes/tree/master/LICENSE.rst>`__.
