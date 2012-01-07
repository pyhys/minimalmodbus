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
"""Set this to True for printing the communication, and also details on the port initialization."""


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
        self.latestWrite = ''
        self.is_open = True
        
        if VERBOSE: 
            _print_out('\nInitializing dummy_serial')
            _print_out('dummy_serial initialization args: ' + repr(args) )
            _print_out('dummy_serial initialization kwargs: ' + repr(kwargs) + '\n')
        
        
    def open(self):
        """Open a (previously initialized) port on dummy_serial."""
        if VERBOSE:
            _print_out('\nOpening port on dummy_serial\n')
        
        if self.is_open:
            raise IOError('The port on dummy_serial is already open')
        self.is_open = True


    def close(self):
        """Close a port on dummy_serial."""
        if VERBOSE:
            _print_out('\nClosing port on dummy_serial\n')
            
        if not self.is_open:
            raise IOError('The port on dummy_serial is already closed')
        self.is_open = False

   
    def write(self, inputstring):
        """Write to a port on dummy_serial.
        
        Args:
            inputstring (int): String for sending to the port on dummy_serial. Will affect the response.
            
        """
        self.latestWrite = inputstring
        
        if VERBOSE:
            _print_out('\nWriting to port on dummy_serial:' + repr(inputstring) + '\n')
            
            
    def read(self, numberOfBytes):
        """Read from a port on dummy_serial.
        
        The response is dependent on what was written last to the port on dummy_serial, 
        and what is defined in the :data:`RESPONSES` dictionary.
        
        Args:
            numberOfBytes (int): For compability with the real function. Not used.
        
        """ 
        
        try:
            returnvalue = RESPONSES[self.latestWrite]   
        except:
            returnvalue = DEFAULT_RESPONSE    

        if VERBOSE:    
            _print_out('\nReading from port on dummy_serial (max length ' + str(numberOfBytes) + ' bytes)')
            _print_out('dummy_serial latest written data:' + repr(self.latestWrite))
            _print_out('dummy_serial read return data:' + repr(returnvalue) + '\n')
                  
        return returnvalue

def _print_out( inputstring ):
    """Print the inputstring. To make it compatible with Python2 and Python3."""    
    sys.stdout.write(inputstring + '\n')    

