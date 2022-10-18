"""Serial instrument driver based on pyserial."""
import serial
import logging
import time

from .base import Instrument
import qcodes.utils.validators as vals


class SerialInstrument(Instrument):

    # """
    # Base class for all instruments using visa connections.

    # Args:
    #     name (str): What this instrument is called locally.

    #     address (str): The visa resource name to use to connect.
    #         Optionally includes '@<backend>' at the end. For example,
    #         'ASRL2' will open COM2 with the default NI backend, but
    #         'ASRL2@py' will open COM2 using pyvisa-py. Note that qcodes
    #         does not install (or even require) ANY backends, it is up to
    #         the user to do that. see eg:
    #         http://pyvisa.readthedocs.org/en/stable/names.html

    #     timeout (number): seconds to allow for responses. Default 5.

    #     terminator: Read termination character(s) to look for. Default ''.

    #     server_name (str): Name of the InstrumentServer to use. By default
    #         uses 'GPIBServer' for all GPIB instruments, 'SerialServer' for
    #         serial port instruments, and 'VisaServer' for all others.

    #         Use ``None`` to run locally - but then this instrument will not
    #         work with qcodes Loops or other multiprocess procedures.

    #     metadata (Optional[Dict]): additional static metadata to add to this
    #         instrument's JSON snapshot.

    # See help for ``qcodes.Instrument`` for additional information on writing
    # instrument subclasses.

    # Attributes:
    #     serial_handle (pyvisa.resources.Resource): The communication channel.
    # """

    def __init__(self, name, address=None, baudrate=9600, timeout=5, stopbits=1, terminator='', **kwargs):
        super().__init__(name, **kwargs)

        self._baudrate = baudrate
        self._timeout = timeout
        # self.timeout = timeout
        self._stopbits = stopbits
        self.set_address(address)
        self.set_terminator(terminator)

    @classmethod
    def default_server_name(cls, **kwargs):

        return 'SerialServer'


    def set_address(self, address):
        """
        Change the address for this instrument.

        Args:
            address: The visa resource name to use to connect.
                Optionally includes '@<backend>' at the end. For example,
                'ASRL2' will open COM2 with the default NI backend, but
                'ASRL2@py' will open COM2 using pyvisa-py. Note that qcodes
                does not install (or even require) ANY backends, it is up to
                the user to do that.
                see eg: http://pyvisa.readthedocs.org/en/stable/names.html
        """
        # in case we're changing the address - close the old handle first
        if getattr(self, 'serial_handle', None):
            self.serial_handle.close()

        self.serial_handle = serial.Serial(address)
        self.serial_handle.baudrate = self._baudrate
        self.serial_handle.timeout = self._timeout
        self.serial_handle.stopbits = self._stopbits

        self._address = address

    def set_timeout(self, timeout=None):
        """
        Change the read timeout for the socket.

        Args:
            timeout (number): Seconds to allow for responses.
        """
        self._timeout = timeout

        if getattr(self, 'serial_handle', None):
                    self.serial_handle.timeout = self._timeout


    def set_terminator(self, terminator):
        """
        Change the read terminator to use.

        Args:
            terminator (str): Character(s) to look for at the end of a read.
                eg. '\r\n'.
        """
        # self.serial_handle.read_termination = terminator
        self._terminator = terminator

    # def _set_visa_timeout(self, timeout):
    #     if timeout is None:
    #         self.serial_handle.timeout = None
    #     else:
    #         # pyvisa uses milliseconds but we use seconds
    #         self.serial_handle.timeout = timeout * 1000.0

    # def _get_visa_timeout(self):
    #     timeout_ms = self.serial_handle.timeout
    #     if timeout_ms is None:
    #         return None
    #     else:
    #         # pyvisa uses milliseconds but we use seconds
    #         return timeout_ms / 1000

    def close(self):
        """Disconnect and irreversibly tear down the instrument."""
        if getattr(self, 'serial_handle', None):
            self.serial_handle.close()
        super().close()



    def write(self, cmd):
        """
        Write a command string with NO response to the hardware.

        Subclasses that transform ``cmd`` should override this method, and in
        it call ``super().write(new_cmd)``. Subclasses that define a new
        hardware communication should instead override ``write_raw``.

        Args:
            cmd (str): the string to send to the instrument

        Raises:
            Exception: wraps any underlying exception with extra context,
                including the command and the instrument.
        """
        try:
            self.write_raw((cmd+self._terminator).encode('ascii'))
        except Exception as e:
            e.args = e.args + ('writing ' + repr(cmd) + ' to ' + repr(self),)
            raise e


    def write_raw(self, cmd):
        """
        Low-level interface to ``serial_handle.write``.

        Args:
            cmd (str): The command to send to the instrument.
        """
        self.serial_handle.write(cmd)
        # self.check_error(ret_code)

    def read_raw(self, size=200):
        return self.serial_handle.read(size)

    def read(self):
        rep = self.serial_handle.read_all()
        return rep.decode('ascii').strip()

    def read_until(self):
        rep = self.serial_handle.read_until(self._terminator.encode('ascii'))
        return rep.decode('ascii').strip()

    def ask(self, cmd):
        self.write(cmd)
        # time.sleep(0.02)
        return self.read_until()

    def ask_raw(self, cmd):
        """
        Low-level interface to ``serial_handle.ask``.

        Args:
            cmd (str): The command to send to the instrument.

        Returns:
            str: The instrument's response.
        """
        self.write_raw(cmd)
        return self.read_raw()

    def snapshot_base(self, update=False):
        """
        State of the instrument as a JSON-compatible dict.

        Args:
            update (bool): If True, update the state by querying the
                instrument. If False, just use the latest values in memory.

        Returns:
            dict: base snapshot
        """
        snap = super().snapshot_base(update=update)

        snap['address'] = self._address
        snap['terminator'] = self._terminator
        snap['timeout'] = self._timeout

        return snap
