#!/usr/bin/env python
#
#   Copyright 2012 Jonas Berg
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

.. moduleauthor:: Jonas Berg <pyhys@users.sourceforge.net>

dummy_serial: A dummy/mock implementation of a serial port for testing purposes.

"""

__author__  = 'Jonas Berg'
__email__   = 'pyhys@users.sourceforge.net'
__license__ = 'Apache License, Version 2.0'


import sys
import time

DEFAULT_TIMEOUT = 5
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
RESPONSES['EXAMPLEREQUEST'] = 'EXAMPLERESPONSE'


DEFAULT_RESPONSE = 'NONE'
"""Response when no matching message (key) is found in the look-up dictionary.

Should not be an empty string, as that is interpreted as "no data available on port".

Might be monkey-patched in the calling test module.

"""

NO_DATA_PRESENT = ''

class Serial():
    """Dummy (mock) serial port for testing purposes.

    Mimics the behavior of a serial port as defined by the `pySerial <http://pyserial.sourceforge.net/>`_ module.

    Args:
        * port:
        * timeout:

    Note:
    As the portname argument not is used properly, only one port on :mod:`dummy_serial` can be used simultaneously.

    """

    def __init__(self, *args, **kwargs):
        self._waiting_data = NO_DATA_PRESENT
        self._isOpen = True
        self.port = kwargs['port']  # Serial port name.
        self.initial_port_name = self.port  # Initial name given to the serial port
        try:
            self.timeout = kwargs['timeout']
        except:
            self.timeout = DEFAULT_TIMEOUT
        try:
            self.baudrate = kwargs['baudrate']
        except:
            self.baudrate = DEFAULT_BAUDRATE

        if VERBOSE:
            _print_out('\nDummy_serial: Initializing')
            _print_out('dummy_serial initialization args: ' + repr(args) )
            _print_out('dummy_serial initialization kwargs: ' + repr(kwargs) + '\n')

    def __repr__(self):
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

    def open(self):
        """Open a (previously initialized) port on dummy_serial."""
        if VERBOSE:
            _print_out('\nDummy_serial: Opening port\n')

        if self._isOpen:
            raise IOError('Dummy_serial: The port is already open')
            
        self._isOpen = True
        self.port = self.initial_port_name

    def close(self):
        """Close a port on dummy_serial."""
        if VERBOSE:
            _print_out('\nDummy_serial: Closing port\n')

        if not self._isOpen:
            raise IOError('Dummy_serial: The port is already closed')
            
        self._isOpen = False
        self.port = None


    def write(self, inputdata):
        """Write to a port on dummy_serial.

        Args:
            inputdata (string/bytes): data for sending to the port on dummy_serial. Will affect the response 
            for subsequent read operations.

        Note that for Python2, the inputdata should be a **string**. For Python3 it should be of type **bytes**.
        
        """
        if VERBOSE:
            _print_out('\nDummy_serial: Writing to port. Given:' + repr(inputdata) + '\n')
            
        if sys.version_info[0] > 2:
            if not type(inputdata) == bytes:
                raise TypeError('The input must be type bytes. Given:' + repr(inputdata))
            inputstring = str(inputdata, encoding='latin1')
        else:
            inputstring = inputdata

        if not self._isOpen:
            raise IOError('Dummy_serial: Trying to write, but the port is not open. Given:' + repr(inputdata))

        # Look up which data that should be waiting for subsequent read commands
        try:
            response = RESPONSES[inputstring]
        except:
            response = DEFAULT_RESPONSE
        self._waiting_data = response


    def read(self, numberOfBytes):
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
            _print_out('\nDummy_serial: Reading from port (max length {!r} bytes)'.format(numberOfBytes))
        
        if numberOfBytes < 0:
            raise IOError('Dummy_serial: The numberOfBytes to read must not be negative. Given: {!r}'.format(numberOfBytes))
        
        if not self._isOpen:
            raise IOError('Dummy_serial: Trying to read, but the port is not open.')

        # Do the actual reading from the waiting data, and simulate the influence of numberOfBytes

        if self._waiting_data == DEFAULT_RESPONSE:
            returnstring = self._waiting_data 
        elif numberOfBytes == len(self._waiting_data):
            returnstring = self._waiting_data 
            self._waiting_data = NO_DATA_PRESENT
        elif numberOfBytes < len(self._waiting_data):
            if VERBOSE:
                _print_out('Dummy_serial: The numberOfBytes to read is smaller than the available data. ' + \
                    'Some bytes will be kept for later. Available data: {!r} (length = {}), numberOfBytes: {}'.format( \
                    self._waiting_data, len(self._waiting_data), numberOfBytes))
            returnstring = self._waiting_data[:numberOfBytes]
            self._waiting_data = self._waiting_data[numberOfBytes:]
        else: # Wait for timeout, as we have asked for more data than available
            if VERBOSE:
                _print_out('Dummy_serial: The numberOfBytes to read is larger than the available data. ' + \
                    'Will sleep until timeout. Available  data: {!r} (length = {}), numberOfBytes: {}'.format( \
                    self._waiting_data, len(self._waiting_data), numberOfBytes))
            time.sleep(self.timeout)
            returnstring = self._waiting_data 
            self._waiting_data = NO_DATA_PRESENT
        
        # TODO Adapt the behavior to better mimic the Windows behavior
        
        if VERBOSE:
            _print_out('Dummy_serial read return data: {!r} (has length {})\n'.format(returnstring, len(returnstring)))

        if sys.version_info[0] > 2: # Convert types to make it python3 compatible
            return bytes(returnstring, encoding='latin1')
        else:
            return returnstring


def _print_out( inputstring ):
    """Print the inputstring. To make it compatible with Python2 and Python3."""
    sys.stdout.write(inputstring + '\n')

