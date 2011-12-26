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

test_omegacn7500: Unittests for omegacn7500

This Python file was changed (committed) at $Date$, 
which was $Revision$.

"""

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"

__revision__  = "$Rev$"
__date__      = "$Date$"

import omegacn7500
import unittest
import dummy_serial

###########################################
# Communication using a dummy serial port #
###########################################

class TestDummyCommunicationSlave1(unittest.TestCase):

    def setUp(self):   
    
        # Prepare a dummy serial port to have proper responses
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInDictionary'

        # Monkey-patch a dummy serial port for testing purpose
        omegacn7500.minimalmodbus.serial.Serial = dummy_serial.Serial

        # Initialize a (dummy) instrument
        self.instrument = omegacn7500.OmegaCN7500('DUMMYPORTNAME', 1)
        self.instrument._debug = False

    def testReadPv1(self):
        self.assertAlmostEqual( self.instrument.get_pv(), 24.6 )

    def testRun(self):
        self.instrument.run()
    
    def testStop(self):
        self.instrument.stop()
    
    def testIsRunning(self):
        self.assertFalse( self.instrument.is_running() )

    def testGetSetpoint(self):
        self.assertAlmostEqual( self.instrument.get_setpoint(), 100)

    def testSetSetpoint(self):
        self.instrument.set_setpoint(100)

    def testGetControlMode(self):   
        self.assertEqual( self.instrument.get_control_mode(), 'PID')
    
    def testSetControlMode(self):   
        self.instrument.set_control_mode(3)

    def testGetStartPatternNo(self):       
        self.assertEqual( self.instrument.get_start_pattern_no(), 2)
    
    
class TestDummyCommunicationSlave10(unittest.TestCase):

    def setUp(self):   
        dummy_serial.RESPONSES = RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInDictionary'
        omegacn7500.minimalmodbus.serial.Serial = dummy_serial.Serial
        self.instrument = omegacn7500.OmegaCN7500('DUMMYPORTNAME', 10)

    def testReadPv1(self):
        self.assertAlmostEqual( self.instrument.get_pv(), 25.9 )

    def testRun(self):
        self.instrument.run()
    
    def testStop(self):
        self.instrument.stop()
    
    def testIsRunning(self):
        self.assertFalse( self.instrument.is_running() )

    def testGetSetpoint(self):
        self.assertAlmostEqual( self.instrument.get_setpoint(), 100)

    def testSetSetpoint(self):
        self.instrument.set_setpoint(100)
        
    def testGetControlMode(self):   
        self.assertEqual( self.instrument.get_control_mode(), 'PID')
    
    def testSetControlMode(self):   
        self.instrument.set_control_mode(3)

    def testGetStartPatternNo(self):       
        self.assertEqual( self.instrument.get_start_pattern_no(), 2)
    
    # ABOVE
    
    

    
RESPONSES = {}
"""A dictionary of respones from a dummy Omega CN7500 instrument. 

The key is the message (string) sent to the serial port, and the item is the response (string) 
from the dummy serial port.

"""


## Recorded data from OmegaCN7500 ##
####################################

# Slave address 1, get_pv()
RESPONSES['\x01\x03\x10\x00\x00\x01\x80\xca'] = '\x01\x03\x02\x00\xf68\x02'

# Slave address 1, run()
RESPONSES['\x01\x05\x08\x14\xff\x00\xce^'] = '\x01\x05\x08\x14\xff\x00\xce^'
    
# Slave address 1, stop()
RESPONSES['\x01\x05\x08\x14\x00\x00\x8f\xae'] = '\x01\x05\x08\x14\x00\x00\x8f\xae'
    
# Slave address 1, is_running()
RESPONSES['\x01\x02\x08\x14\x00\x01\xfb\xae'] = '\x01\x02\x01\x00\xa1\x88'
   
# Slave address 1, get_setpoint()
RESPONSES['\x01\x03\x10\x01\x00\x01\xd1\n'] = '\x01\x03\x02\x03\xe8\xb8\xfa'
    
# Slave address 1, set_setpoint()    
RESPONSES['\x01\x10\x10\x01\x00\x01\x02\x03\xe8\xb6\xfe'] = '\x01\x10\x10\x01\x00\x01T\xc9'

# Slave address 1, get_control_mode()        
RESPONSES['\x01\x03\x10\x05\x00\x01\x90\xcb'] = '\x01\x03\x02\x00\x00\xb8D'    

# Slave address 1, set_control_mode()  
RESPONSES['\x01\x10\x10\x05\x00\x01\x02\x00\x03\xf7\xc5'] = '\x01\x10\x10\x05\x00\x01\x15\x08'

# Slave address 1, get_start_pattern_no()
RESPONSES['\x01\x03\x100\x00\x01\x80\xc5'] = '\x01\x03\x02\x00\x029\x85'




# Slave address 10, get_pv()
RESPONSES['\n\x03\x10\x00\x00\x01\x81\xb1'] = '\n\x03\x02\x01\x03\\\x14'

# Slave address 10, run()
RESPONSES['\n\x05\x08\x14\xff\x00\xcf%'] = '\n\x05\x08\x14\xff\x00\xcf%'
    
# Slave address 10, stop()
RESPONSES['\n\x05\x08\x14\x00\x00\x8e\xd5'] = '\n\x05\x08\x14\x00\x00\x8e\xd5'
    
# Slave address 10, is_running()
RESPONSES['\n\x02\x08\x14\x00\x01\xfa\xd5'] = '\n\x02\x01\x00\xa3\xac'   
    
# Slave address 10, get_setpoint()
RESPONSES['\n\x03\x10\x01\x00\x01\xd0q'] = '\n\x03\x02\x03\xe8\x1d;'
    
# Slave address 10, set_setpoint()    
RESPONSES['\n\x10\x10\x01\x00\x01\x02\x03\xe8\xc5\xce'] = '\n\x10\x10\x01\x00\x01U\xb2'

# Slave address 10, get_control_mode()        
RESPONSES['\n\x03\x10\x05\x00\x01\x91\xb0'] = '\n\x03\x02\x00\x00\x1d\x85' 

# Slave address 10, set_control_mode()  
RESPONSES['\n\x10\x10\x05\x00\x01\x02\x00\x03\x84\xf5'] = '\n\x10\x10\x05\x00\x01\x14s'

# Slave address 10, get_start_pattern_no()
RESPONSES['\n\x03\x100\x00\x01\x81\xbe'] = '\n\x03\x02\x00\x02\x9cD'




    
if __name__ == '__main__':
    unittest.main()  
    #dummyexperiment()
