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

This Python file was changed (committed) at $Date$, 
which was $Revision$.

"""

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"

__revision__  = "$Rev$"
__date__      = "$Date$"


VERBOSE = False
"""Set this to True for printing the communication, and also details on the port initialization."""

DEFAULT_RESPONSE = ''
"""Response when no matching message (key) is found in the look-up dictionary."""

RESPONSES = {}
"""A dictionary of respones from the dummy serial port. 

The key is the message (string) sent to the dummy serial port, and the item is the response (string) 
from the dummy serial port.

Intended to be monkey-patched in the calling test module.

"""
RESPONSES['EXAMPLEMESSAGE'] = 'EXAMPLERESPONSE'


class Serial():
    """Dummy serial port for testing purposes.
    
    Instrument class for talking to instruments (slaves) via the Modbus RTU protocol (via RS485 or RS232).

    Args:
        (whatever): The arguments are not used.
        
    """
    
    def __init__(self, *args, **kwargs):
        self.latestWrite = ''
        
        if VERBOSE:
            print
            print 'Initializing dummy_serial'
            print 'args:'
            print args
            print 'kwargs:'
            print kwargs        
            print
   
   
    def write(self, inputstring):
        """Write to the dummy serial port.
        
        Args:
            inputstring (int): String for sending to the dummy serial port. Will affect the response.
            
        """
        self.latestWrite = inputstring
        
        if VERBOSE:
            print
            print 'Writing to dummy_serial:', repr(inputstring)
            print 
            
            
    def read(self, numberOfBytes):
        """Read from the dummy serial port.
        
        The response is dependent on what was written last to the dummy serial port, 
        and what is defined in the RESPONSES dictionary.
        
        Args:
            numberOfBytes (int): For compability with the real function. Not used.
        
        """ 
        try:
            returnvalue = RESPONSES[self.latestWrite]   
        except:
            returnvalue = DEFAULT_RESPONSE    

        if VERBOSE:    
            print
            print 'Reading from dummy_serial:'
            print 'Max length:', numberOfBytes
            print 'Latest written data:', repr(self.latestWrite)
            print 'Return value:', repr(returnvalue)
            print
                  
        return returnvalue



