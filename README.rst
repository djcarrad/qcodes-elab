QCoDeS-elab version
===================================
This package is no longer supported. You should migrate to `qcodes++ <http://qcodespp.github.io>`__

Once you have installed qcodes++, you can update your code in the following way:

Replace ``import qcodes as qc`` with ``import qcodespp as qc`` such that calls to top-level functions e.g. qc.Parameter will be imported from qcodes++.

Similarly, if you have done e.g. ``from qcodes import Parameter``, you should change this to ``from qcodespp import Parameter``

For lower-level functions, the situation is a bit different. This is because qcodes-elab was a installed as qcodes, and existed independent from `QCoDeS <http://qcodes.github.io>`__. That is not the case any longer. qcodes++ is installed `alongside` QCoDeS, meaning that references to ``qcodes`` in code will reference mainline QCoDeS. However, this should only really apply to instrument drivers. If the driver still exists in qcodes++, then replace e.g.

``from qcodes.instrument_drivers.tektronix.QDevil.QDac2 import QDAC2`` with

``from qcodespp.instrument_drivers.tektronix.QDevil.QDac2 import QDAC2``

Otherwise, leave it as importing from qcodes to import the QCoDeS driver.

This more or less applies to all other lower level classes/functions. If the object still exists in qcodes++, import it from there. Otherwise, fall back on importing from QCoDeS.

From there, the code should behave exactly the same, except for....

Breaking changes
----------------
It is no longer necessary to define a ``Parameter`` data_type, e.g. ``str`` or ``float``, and ``Parameter.__init__`` therefore no longer accepts the argument ``data_type``.

Module ``plots`` has been renamed ``plotting`` to not conflict with QCoDeS. Likely most relevant if you have imported the ``analysis_tools``. Now they are at ``qcodespp.plotting.analysis_tools``
