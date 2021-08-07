#
#   Copyright 2019 Jonas Berg
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
"""

.. moduleauthor:: Jonas Berg

dummy_serial: A dummy/mock implementation of a serial port for testing purposes.

"""
__author__ = "Jonas Berg"
__license__ = "Apache License, Version 2.0"

import sys
import time
from typing import Optional, Union

DEFAULT_TIMEOUT = 0.01
"""The default timeot value in seconds. Used if not set by the constructor."""


DEFAULT_BAUDRATE = 19200
"""The default baud rate. Used if not set by the constructor."""


VERBOSE = False
"""Set this to :const:`True` for printing the communication, and also details on the port initialization.

Might be monkey-patched in the calling test module.

"""


RESPONSES = {}
"""A dictionary of respones from the dummy serial port.

The key is the message (string) sent to the dummy serial port, and the item is the response (string)
from the dummy serial port.

Intended to be monkey-patched in the calling test module.

"""
RESPONSES["EXAMPLEREQUEST"] = "EXAMPLERESPONSE"


DEFAULT_RESPONSE = "NotFoundInResponseDictionary"
"""Response when no matching message (key) is found in the look-up dictionary.

Should not be an empty string, as that is interpreted as "no data available on port".

Might be monkey-patched in the calling test module.

"""

NO_DATA_PRESENT = ""


class Serial:
    """Dummy (mock) serial port for testing purposes.

    Mimics the behavior of a serial port as defined by the `pySerial <https://github.com/pyserial/pyserial>`_ module.

    Args:
        * port:
        * timeout:

    Note:
    As the portname argument not is used properly, only one port on :mod:`dummy_serial` can be used simultaneously.

    """

    port: Optional[str]  # Serial port name.
    timeout: float
    baudrate: int
    _initial_port_name: Optional[str]  # Initial name given to the serial port
    _waiting_data: str  # TODO
    _isOpen: bool

    def __init__(
        self,
        port: Optional[str],
        baudrate: int = DEFAULT_BAUDRATE,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: Union[int, float] = 1,
        timeout: Optional[float] = None,
        xonxoff: bool = False,
        rtscts: bool = False,
        write_timeout: Optional[float] = None,
        dsrdtr: bool = False,
        inter_byte_timeout: Optional[float] = None,
    ) -> None:
        self._waiting_data = NO_DATA_PRESENT
        self._isOpen = True
        self.port = port  # Serial port name.
        self._initial_port_name = self.port  # Initial name given to the serial port

        self.timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
        self.baudrate = baudrate

        if VERBOSE:
            print("\nDummy_serial: Initializing")
            print(
                "dummy_serial initialization. Port: {0} Baud rate: {1} Timeout {2}".format(
                    self.port, self.baudrate, self.timeout
                )
            )

    def __repr__(self) -> str:
        """String representation of the dummy_serial object"""
        return "{0}.{1}<id=0x{2:x}, open={3}>(port={4!r}, timeout={5!r}, waiting_data={6!r})".format(
            self.__module__,
            self.__class__.__name__,
            id(self),
            self._isOpen,
            self.port,
            self.timeout,
            self._waiting_data,
        )

    @property
    def is_open(self) -> bool:
        return self._isOpen

    def reset_input_buffer(self) -> None:
        pass

    def reset_output_buffer(self) -> None:
        pass

    def open(self) -> None:
        """Open a (previously initialized) port on dummy_serial."""
        if VERBOSE:
            print("\nDummy_serial: Opening port\n")

        if self._isOpen:
            raise IOError("Dummy_serial: The port is already open")

        self._isOpen = True
        self.port = self._initial_port_name

    def close(self) -> None:
        """Close a port on dummy_serial."""
        if VERBOSE:
            print("\nDummy_serial: Closing port\n")

        if not self._isOpen:
            raise IOError("Dummy_serial: The port is already closed")

        self._isOpen = False
        self.port = None

    def write(self, inputdata: bytes) -> int:
        """Write to a port on dummy_serial.

        Args:
            inputdata: data for sending to the port on dummy_serial. Will affect the response
            for subsequent read operations.

        Returns:
            Number of bytes written

        """
        if VERBOSE:
            print("\nDummy_serial: Writing to port. Given:" + repr(inputdata) + "\n")

        if not type(inputdata) == bytes:
            raise TypeError("The input must be type bytes. Given:" + repr(inputdata))
        inputstring = str(inputdata, encoding="latin1")

        if not self._isOpen:
            raise IOError(
                "Dummy_serial: Trying to write, but the port is not open. Given:"
                + repr(inputdata)
            )

        # Look up which data that should be waiting for subsequent read commands
        try:
            response = RESPONSES[inputstring]
        except:
            response = DEFAULT_RESPONSE
        self._waiting_data = response

        return len(inputstring)

    def read(self, numberOfBytes: int) -> bytes:
        """Read from a port on dummy_serial.

        The response is dependent on what was written last to the port on dummy_serial,
        and what is defined in the :data:`RESPONSES` dictionary.

        Args:
            numberOfBytes (int): For compability with the real function.

        Returns a **string** for Python2 and **bytes** for Python3.

        If the response is shorter than numberOfBytes, it will sleep for timeout.
        If the response is longer than numberOfBytes, it will return only numberOfBytes bytes.

        """
        if VERBOSE:
            print(
                "\nDummy_serial: Reading from port (max length {!r} bytes)".format(
                    numberOfBytes
                )
            )

        if numberOfBytes < 0:
            raise IOError(
                "Dummy_serial: The numberOfBytes to read must not be negative. Given: {!r}".format(
                    numberOfBytes
                )
            )

        if not self._isOpen:
            raise IOError("Dummy_serial: Trying to read, but the port is not open.")

        # Do the actual reading from the waiting data, and simulate the influence of numberOfBytes

        if self._waiting_data == DEFAULT_RESPONSE:
            returnstring = self._waiting_data
        elif numberOfBytes == len(self._waiting_data):
            returnstring = self._waiting_data
            self._waiting_data = NO_DATA_PRESENT
        elif numberOfBytes < len(self._waiting_data):
            if VERBOSE:
                print(
                    "Dummy_serial: The numberOfBytes to read is smaller than the available data. "
                    + "Some bytes will be kept for later. Available data: {!r} (length = {}), numberOfBytes: {}".format(
                        self._waiting_data, len(self._waiting_data), numberOfBytes
                    )
                )
            returnstring = self._waiting_data[:numberOfBytes]
            self._waiting_data = self._waiting_data[numberOfBytes:]
        else:  # Wait for timeout, as we have asked for more data than available
            if VERBOSE:
                print(
                    "Dummy_serial: The numberOfBytes to read is larger than the available data. "
                    + "Will sleep until timeout. Available  data: {!r} (length = {}), numberOfBytes: {}".format(
                        self._waiting_data, len(self._waiting_data), numberOfBytes
                    )
                )
            time.sleep(self.timeout)
            returnstring = self._waiting_data
            self._waiting_data = NO_DATA_PRESENT

        # TODO Adapt the behavior to better mimic the Windows behavior

        if VERBOSE:
            print(
                "Dummy_serial read return data: {!r} (has length {})\n".format(
                    returnstring, len(returnstring)
                )
            )

        return bytes(returnstring, encoding="latin1")
