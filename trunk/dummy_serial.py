#!/usr/bin/env python
#
#   Copyright 2011 Jonas Berg
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

This Python file was changed (committed) at $Date: 2011-12-18 21:41:02 +0100 (Sun, 18 Dec 2011) $, 
which was $Revision: 79 $.

"""

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"

__revision__  = "$Rev: 79 $"
__date__      = "$Date: 2011-12-18 21:41:02 +0100 (Sun, 18 Dec 2011) $"

import sys


VERBOSE = False
"""Set this to :const:`True` for printing the communication, and also details on the port initialization."""


RESPONSES = {}
"""A dictionary of respones from the dummy serial port. 

The key is the message (string) sent to the dummy serial port, and the item is the response (string) 
from the dummy serial port.

Intended to be monkey-patched in the calling test module.

"""
RESPONSES['EXAMPLEMESSAGE'] = 'EXAMPLERESPONSE'


DEFAULT_RESPONSE = ''
"""Response when no matching message (key) is found in the look-up dictionary.

Might be monkey-patched in the calling test module.

"""


class Serial():
    """Dummy serial port for testing purposes.
    
    Mimics the behavior of a serial port as defined by the `pySerial <http:/pyserial.sourceforge.net/>`_ module.
    
    Args:
        (whatever): The arguments are not used.
        
    Note:
    As the portname argument not is used, only one port on :mod:`dummy_serial` can be used simultaneously.
        
    """
    
    def __init__(self, *args, **kwargs):
        self._latestWrite = ''
        self._isOpen = True
        
        if VERBOSE: 
            _print_out('\nInitializing dummy_serial')
            _print_out('dummy_serial initialization args: ' + repr(args) )
            _print_out('dummy_serial initialization kwargs: ' + repr(kwargs) + '\n')
        
        
    def __repr__(self):
        """String representation of the dummy_serial object"""
        return "{0}.{1}<id=0x{2:x}, open={3}>(latestWrite={4!r})".format(
            self.__module__,
            self.__class__.__name__,
            id(self),
            self._isOpen,
            self._latestWrite,
        )
        

    def open(self):
        """Open a (previously initialized) port on dummy_serial."""
        if VERBOSE:
            _print_out('\nOpening port on dummy_serial\n')
        
        if self._isOpen:
            raise IOError('The port on dummy_serial is already open')
        self._isOpen = True


    def close(self):
        """Close a port on dummy_serial."""
        if VERBOSE:
            _print_out('\nClosing port on dummy_serial\n')
            
        if not self._isOpen:
            raise IOError('The port on dummy_serial is already closed')
        self._isOpen = False

   
    def write(self, inputdata):
        """Write to a port on dummy_serial.
        
        Args:
            inputdata (string/bytes): data for sending to the port on dummy_serial. Will affect the response.
            
        Note that for Python2, the inputdata should be a **string**. For Python3 it should be of type **bytes**.
        """
        inputstring = inputdata
        
        if sys.version_info[0] > 2:
            if not type(inputdata) == bytes:
                raise TypeError('The input must be type bytes. Given:' + repr(inputdata))
            inputstring = str(inputdata, encoding='latin1')
        
        self._latestWrite = inputstring
        
        if VERBOSE:
            _print_out('\nWriting to port on dummy_serial:' + repr(inputstring) + '\n')
            
            
    def read(self, numberOfBytes):
        """Read from a port on dummy_serial.
        
        The response is dependent on what was written last to the port on dummy_serial, 
        and what is defined in the :data:`RESPONSES` dictionary.
        
        Args:
            numberOfBytes (int): For compability with the real function. Not used.
        
        Returns a **string** for Python2 and **bytes** for Python3.
        
        """ 
        
        try:
            returnstring = RESPONSES[self._latestWrite]   
        except:
            returnstring = DEFAULT_RESPONSE    

        if VERBOSE:    
            _print_out('\nReading from port on dummy_serial (max length ' + str(numberOfBytes) + ' bytes)')
            _print_out('dummy_serial latest written data:' + repr(self._latestWrite))
            _print_out('dummy_serial read return data:' + repr(returnstring) + '\n')
                  
        returndata = returnstring
        
        if sys.version_info[0] > 2: # Convert types to make it python3 compatible
            returndata = bytes(returnstring, encoding='latin1')
        
        return returndata

def _print_out( inputstring ):
    """Print the inputstring. To make it compatible with Python2 and Python3."""    
    sys.stdout.write(inputstring + '\n')    

