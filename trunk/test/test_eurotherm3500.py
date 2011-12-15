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

test_eurotherm3500: Unittests for eurotherm3500

This Python file was changed (committed) at $Date: 2011-11-20 09:50:35 +0100 (Sun, 20 Nov 2011) $, 
which was $Revision: 72 $.

"""

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"

__revision__  = "$Rev: 72 $"
__date__      = "$Date: 2011-11-20 09:50:35 +0100 (Sun, 20 Nov 2011) $"

import eurotherm3500
import unittest
import dummy_serial

def dummyexperiment():
    print 'TEST: EUROTHERM 3500'

    # Monkey-patch a dummy serial port for testing purpose
    dummy_serial.VERBOSE = False
    dummy_serial.RESPONSES = RESPONSES
    eurotherm3500.minimalmodbus.serial.Serial = dummy_serial.Serial

    # Create a dummy instrument
    instrument = eurotherm3500.Eurotherm3500('DUMMYPORTNAME', 1)
    instrument._debug = True
    
    print instrument.get_pv_loop1() 
    quit()
    
###########################################
# Communication using a dummy serial port #
###########################################

class TestDummyCommunication(unittest.TestCase):

    def setUp(self):   
    
        # Prepare a dummy serial port to have proper responses
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RESPONSES

        # Monkey-patch a dummy serial port for testing purpose
        eurotherm3500.minimalmodbus.serial.Serial = dummy_serial.Serial

        # Initialize a (dummy) instrument
        self.instrument = eurotherm3500.Eurotherm3500('DUMMYPORTNAME', 1)
        self.instrument._debug = False

    def testReadPv1(self):
        self.assertEqual( self.instrument.get_pv_loop1(), 77.0 )

    
    
RESPONSES = {}
"""A dictionary of respones from a dummy Eurotherm 3500 instrument. 

The key is the message (string) sent to the serial port, and the item is the response (string) 
from the dummy serial port.

"""
# Note that the string 'AAAAAAA' might be easier to read if grouped, 
# like 'AA' + 'AAAA' + 'A' for the initial part (address etc) + payload + CRC.


# get_pv_loop1: Read register 289 on slave 1 using function code 3 #
# -----------------------------------------------------------------#
# Message:  slave address 1, function code 3, register address 289, 1 register, CRC. 
# Response: slave address 1, function code 3, 2 bytes, value=770, CRC=14709
RESPONSES['\x01\x03' + '\x01!\x00\x01' + '\xd5\xfc'] = '\x01\x03' + '\x02\x03\x02' + '\x39\x75'

    
if __name__ == '__main__':
    unittest.main()  
    #dummyexperiment()
