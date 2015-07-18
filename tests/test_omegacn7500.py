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

Uses a dummy serial port from the module :py:mod:`dummy_serial`.

"""

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"


import sys
import unittest

import omegacn7500
import dummy_serial


class TestCalculateRegisterAddress(unittest.TestCase):

    knownValues=[
    ('setpoint',    0, 0,       8192), # registertype, patternnumber, stepnumber, knownresult
    ('setpoint',    1, 0,       8200),
    ('time',        0, 0,       8320),
    ('time',        0, 1,       8321),
    ('time',        1, 0,       8328),
    ('actualstep',  0, None,    4160),
    ('actualstep',  0, 0,       4160),
    ('actualstep',  1, None,    4161),
    ('actualstep',  1, 0,       4161),
    ('actualstep',  1, 5,       4161), # Stepnumber should have no effect.
    ('cycles',      0, None,    4176),
    ('cycles',      1, None,    4177),
    ('linkpattern', 0, None,    4192),
    ('linkpattern', 1, None,    4193),
    ]

    def testKnownValues(self):
        for registertype, patternnumber, stepnumber, knownresult in self.knownValues:
            
            resultvalue = omegacn7500._calculateRegisterAddress(registertype, patternnumber, stepnumber)
            self.assertEqual(resultvalue, knownresult)      

    def testWrongValues(self):
        self.assertRaises(ValueError, omegacn7500._calculateRegisterAddress, 'ABC',         0, 0)
        self.assertRaises(ValueError, omegacn7500._calculateRegisterAddress, 'setpoint',    -1, 0)
        self.assertRaises(ValueError, omegacn7500._calculateRegisterAddress, 'setpoint',    8, 0)
        self.assertRaises(ValueError, omegacn7500._calculateRegisterAddress, 'setpoint',    0, -1)
        self.assertRaises(ValueError, omegacn7500._calculateRegisterAddress, 'setpoint',    0, 8)
          
    def testWrongType(self):
        self.assertRaises(ValueError, omegacn7500._calculateRegisterAddress, 0,             0, 0) # Note: Raises value error
        self.assertRaises(ValueError, omegacn7500._calculateRegisterAddress, 1.0,           0, 0)
        self.assertRaises(ValueError, omegacn7500._calculateRegisterAddress, None,          0, 0)
        self.assertRaises(ValueError, omegacn7500._calculateRegisterAddress, ['setpoint'],  0, 0)
        self.assertRaises(TypeError, omegacn7500._calculateRegisterAddress, 'setpoint', 0.0,  0)   
        self.assertRaises(TypeError, omegacn7500._calculateRegisterAddress, 'setpoint', [0],  0) 
        self.assertRaises(TypeError, omegacn7500._calculateRegisterAddress, 'setpoint', None, 0) 
        self.assertRaises(TypeError, omegacn7500._calculateRegisterAddress, 'setpoint', 0,    0.0) 
        self.assertRaises(TypeError, omegacn7500._calculateRegisterAddress, 'setpoint', 0,    [0]) 


class TestCheckPatternNumber(unittest.TestCase):

    def testKnownResults(self):
        omegacn7500._checkPatternNumber(0)
        omegacn7500._checkPatternNumber(3)
        omegacn7500._checkPatternNumber(7)

    def testWrongValue(self):
        self.assertRaises(ValueError, omegacn7500._checkPatternNumber, -1)
        self.assertRaises(ValueError, omegacn7500._checkPatternNumber, 8)
        self.assertRaises(ValueError, omegacn7500._checkPatternNumber, 99)
        self.assertRaises(ValueError, omegacn7500._checkPatternNumber, 12345)

    def testWrongType(self):
        self.assertRaises(TypeError, omegacn7500._checkPatternNumber, '1')
        self.assertRaises(TypeError, omegacn7500._checkPatternNumber, 1.0)
        self.assertRaises(TypeError, omegacn7500._checkPatternNumber, [1])
        self.assertRaises(TypeError, omegacn7500._checkPatternNumber, None)


class TestCheckStepNumber(unittest.TestCase):

    def testKnownResults(self):
        omegacn7500._checkStepNumber(0)
        omegacn7500._checkStepNumber(3)
        omegacn7500._checkStepNumber(7)

    def testWrongValue(self):
        self.assertRaises(ValueError, omegacn7500._checkStepNumber, -1)
        self.assertRaises(ValueError, omegacn7500._checkStepNumber, 8)
        self.assertRaises(ValueError, omegacn7500._checkStepNumber, 99)
        self.assertRaises(ValueError, omegacn7500._checkStepNumber, 12345)

    def testWrongType(self):
        self.assertRaises(TypeError, omegacn7500._checkStepNumber, '1')
        self.assertRaises(TypeError, omegacn7500._checkStepNumber, 1.0)
        self.assertRaises(TypeError, omegacn7500._checkStepNumber, [1])
        self.assertRaises(TypeError, omegacn7500._checkStepNumber, None)


class TestCheckSetpointValue(unittest.TestCase):
    
    def testKnownResults(self):
        omegacn7500._checkSetpointValue(900, 1000)
        omegacn7500._checkSetpointValue(900.0, 1000.0)
        
    def testWrongValue(self):
        self.assertRaises(ValueError, omegacn7500._checkSetpointValue, 900, 800)
        self.assertRaises(ValueError, omegacn7500._checkSetpointValue, 900.0, 800.0)
        self.assertRaises(ValueError, omegacn7500._checkSetpointValue, -100, 800)
        self.assertRaises(ValueError, omegacn7500._checkSetpointValue, 900, -800)

    def testWrongType(self):
        self.assertRaises(TypeError, omegacn7500._checkSetpointValue, '900', 1000)
        self.assertRaises(TypeError, omegacn7500._checkSetpointValue, [900], 1000)
        self.assertRaises(TypeError, omegacn7500._checkSetpointValue, None, 1000)
        self.assertRaises(TypeError, omegacn7500._checkSetpointValue, 900, '1000')
        self.assertRaises(TypeError, omegacn7500._checkSetpointValue, 900, [1000])
        self.assertRaises(TypeError, omegacn7500._checkSetpointValue, 900, None)
    
    
class TestCheckTimeValue(unittest.TestCase):
    
    def testKnownResults(self):
        omegacn7500._checkTimeValue(75, 99)
        omegacn7500._checkTimeValue(75.0, 99.0)

    def testWrongValue(self):
        self.assertRaises(ValueError, omegacn7500._checkTimeValue, 75, 10)
        self.assertRaises(ValueError, omegacn7500._checkTimeValue, -5, 10)
        self.assertRaises(ValueError, omegacn7500._checkTimeValue, -75, 10)
        self.assertRaises(ValueError, omegacn7500._checkTimeValue, 75.0, 10.0)
        self.assertRaises(ValueError, omegacn7500._checkTimeValue, -5.0, 10.0)
        self.assertRaises(ValueError, omegacn7500._checkTimeValue, -75.0, 10.0)
        self.assertRaises(ValueError, omegacn7500._checkTimeValue, 5, -10)
        self.assertRaises(ValueError, omegacn7500._checkTimeValue, 75, -10)
        self.assertRaises(ValueError, omegacn7500._checkTimeValue, 5.0, -10.0)
        self.assertRaises(ValueError, omegacn7500._checkTimeValue, 75.0, -10.0)        

    def testWrongType(self):
        self.assertRaises(TypeError, omegacn7500._checkTimeValue, '75', 99)
        self.assertRaises(TypeError, omegacn7500._checkTimeValue, [75], 99)
        self.assertRaises(TypeError, omegacn7500._checkTimeValue, None, 99)
        self.assertRaises(TypeError, omegacn7500._checkTimeValue, 75, '99')
        self.assertRaises(TypeError, omegacn7500._checkTimeValue, 75, [99])
        self.assertRaises(TypeError, omegacn7500._checkTimeValue, 75, None)


###########################################
# Communication using a dummy serial port #
###########################################

class TestDummyCommunication_Slave1(unittest.TestCase):
    """Testing using dummy communication, with data recorded for slaveaddress = 1
    
    Most of the tests are for making sure that the communication details are OK.
    
    For some examples of testing the methods for argument value errors or
    argument type errors, see the :meth:`.testSetControlModeWithWrongValue` and 
    :meth:`.testSetControlModeWithWrongValueType` methods.

    """

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

    def testSetControlModeWithWrongValue(self):   
        self.assertRaises(ValueError, self.instrument.set_control_mode, 4)
        self.assertRaises(ValueError, self.instrument.set_control_mode, -1)

    def testSetControlModeWithWrongValueType(self):   
        self.assertRaises(TypeError, self.instrument.set_control_mode, 3.0)
        self.assertRaises(TypeError, self.instrument.set_control_mode, [3])
        self.assertRaises(TypeError, self.instrument.set_control_mode, '3')
        self.assertRaises(TypeError, self.instrument.set_control_mode, None)

    def testGetStartPatternNo(self):       
        self.assertEqual( self.instrument.get_start_pattern_no(), 2)
    
    def testSetStartPatternNo(self):  
        self.instrument.set_start_pattern_no(2)
    
    def testGetPatternStepSetpoint(self): 
        self.assertAlmostEqual( self.instrument.get_pattern_step_setpoint(0, 3), 333.3)
    
    def testSetPatternStepSetpoint(self): 
        self.instrument.set_pattern_step_setpoint(0, 3, 333.3)
        self.instrument.set_pattern_step_setpoint(0, 3, 40)
    
    def testGetPatternStepTime(self): 
        self.assertAlmostEqual( self.instrument.get_pattern_step_time(0, 3), 45) 
    
    def testSetPatternStepTime(self): 
        self.instrument.set_pattern_step_time(0, 3, 45) 
        self.instrument.set_pattern_step_time(0, 3, 40) 
    
    def testGetPatternActualStep(self): 
        self.assertEqual( self.instrument.get_pattern_actual_step(0), 7 )
    
    def testSetPatternActualStep(self): 
        self.instrument.set_pattern_actual_step(0, 7)
    
    def testGetPatternAdditionalCycles(self): 
        self.assertEqual( self.instrument.get_pattern_additional_cycles(0), 4) 
    
    def testSetPatternAdditionalCycles(self): 
        self.instrument.set_pattern_additional_cycles(0, 4) 
        self.instrument.set_pattern_additional_cycles(0, 2) 
    
    def testGetPatternLinkToPattern(self): 
        self.assertEqual( self.instrument.get_pattern_link_topattern(0), 1)
    
    def testSetPatternLinkToPattern(self): 
        self.instrument.set_pattern_link_topattern(0, 1)
        
    def testGetAllPatternVariables(self):  # TODO: Change this to proper assertEqual   
        _print_out( '\nSlave address 1:' )     
        _print_out( self.instrument.get_all_pattern_variables(0) )

    def testSetAllPatternVariables(self):       
        self.instrument.set_all_pattern_variables(0,
            10, 10, 
            20, 20,
            30, 30, 
            40, 40,
            50, 50,
            60, 60, 
            70, 70, 
            80, 80, 
            7, 4, 1)         


class TestDummyCommunication_Slave10(unittest.TestCase):
    """Testing using dummy communication, with data recorded for slaveaddress = 10

    """

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
    
    def testSetStartPatternNo(self):  
        self.instrument.set_start_pattern_no(2)
    
    def testGetPatternStepSetpoint(self): 
        self.assertEqual( self.instrument.get_pattern_step_setpoint(0, 3), 333.3)
    
    def testSetPatternStepSetpoint(self): 
        self.instrument.set_pattern_step_setpoint(0, 3, 333.3)
        self.instrument.set_pattern_step_setpoint(0, 3, 40)
    
    def testGetPatternStepTime(self): 
        self.assertAlmostEqual( self.instrument.get_pattern_step_time(0, 3), 45)
    
    def testSetPatternStepTime(self): 
        self.instrument.set_pattern_step_time(0, 3, 45) 
        self.instrument.set_pattern_step_time(0, 3, 40) 
    
    def testGetPatternActualStep(self): 
        self.assertEqual( self.instrument.get_pattern_actual_step(0), 7)
    
    def testSetPatternActualStep(self): 
        self.instrument.set_pattern_actual_step(0, 7)
    
    def testGetPatternAdditionalCycles(self): 
        self.assertEqual( self.instrument.get_pattern_additional_cycles(0), 4)
    
    def testSetPatternAdditionalCycles(self): 
        self.instrument.set_pattern_additional_cycles(0, 4)
        self.instrument.set_pattern_additional_cycles(0, 2)
    
    def testGetPatternLinkToPattern(self): 
        self.assertEqual( self.instrument.get_pattern_link_topattern(0), 1)
    
    def testSetPatternLinkToPattern(self): 
        self.instrument.set_pattern_link_topattern(0, 1)
    
    def testGetAllPatternVariables(self):   # TODO: Change this to proper assertEqual
        _print_out( '\nSlave address 10:' )     
        _print_out( self.instrument.get_all_pattern_variables(0) )
        
        
    def testSetAllPatternVariables(self):       
        self.instrument.set_all_pattern_variables(0,
            10, 10, 
            20, 20,
            30, 30, 
            40, 40,
            50, 50,
            60, 60, 
            70, 70, 
            80, 80, 
            7, 4, 1)         

        
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
#RESPONSES['\x01\x03\x10\x05\x00\x01\x90\xcb'] = '\x01\x03\x02\x00\x09xB'  # Use this for testing wrong controlmode

# Slave address 1, set_control_mode()  
RESPONSES['\x01\x10\x10\x05\x00\x01\x02\x00\x03\xf7\xc5'] = '\x01\x10\x10\x05\x00\x01\x15\x08'

# Slave address 1, get_start_pattern_no()
RESPONSES['\x01\x03\x100\x00\x01\x80\xc5'] = '\x01\x03\x02\x00\x029\x85'

# Slave address 1, set_start_pattern_no()
RESPONSES['\x01\x10\x100\x00\x01\x02\x00\x023\xa0'] = '\x01\x10\x100\x00\x01\x05\x06'

# Slave address 1, set_pattern_step_setpoint() Pattern 0, step 3, value 333.3. See also below. 
RESPONSES['\x01\x10 \x03\x00\x01\x02\r\x05C2'] = '\x01\x10 \x03\x00\x01\xfa\t'

# Slave address 1, set_pattern_step_time() Pattern 0, step 3, value 45. See also below. 
RESPONSES['\x01\x10 \x83\x00\x01\x02\x00-X|'] = '\x01\x10 \x83\x00\x01\xfb\xe1'

# Slave address 1, set_pattern_additional_cycles() Pattern 0, value 4. See also below. 
RESPONSES['\x01\x10\x10P\x00\x01\x02\x00\x04\xba\x02'] = '\x01\x10\x10P\x00\x01\x05\x18'

# Slave address 1, get_all_pattern_variables() 
# --- Valid for pattern 0 ---
# SP0: 10   Time0: 10 
# SP1: 20   Time1: 20
# SP2: 30   Time2: 30
# SP3: 333  Time3: 45
# SP4: 50   Time4: 50
# SP5: 60   Time5: 60
# SP6: 70   Time6: 70
# SP7: 80   Time7: 80
# Actual step:      7
# Add'l cycles:     4
# Linked pattern:   1
RESPONSES['\x01\x03 \x00\x00\x01\x8f\xca'] = '\x01\x03\x02\x00d\xb9\xaf' # SP0
RESPONSES['\x01\x03 \x01\x00\x01\xde\n']   = '\x01\x03\x02\x00\xc8\xb9\xd2'
RESPONSES['\x01\x03 \x02\x00\x01.\n']      = '\x01\x03\x02\x01,\xb8\t'
RESPONSES['\x01\x03 \x03\x00\x01\x7f\xca'] = '\x01\x03\x02\r\x05|\xd7'
RESPONSES['\x01\x03 \x04\x00\x01\xce\x0b'] = '\x01\x03\x02\x01\xf4\xb8S'
RESPONSES['\x01\x03 \x05\x00\x01\x9f\xcb'] = '\x01\x03\x02\x02X\xb8\xde'
RESPONSES['\x01\x03 \x06\x00\x01o\xcb']    = '\x01\x03\x02\x02\xbc\xb8\x95'
RESPONSES['\x01\x03 \x07\x00\x01>\x0b']    = '\x01\x03\x02\x03 \xb9l'

RESPONSES['\x01\x03 \x80\x00\x01\x8e"']    = '\x01\x03\x02\x00\n8C' # Time0
RESPONSES['\x01\x03 \x81\x00\x01\xdf\xe2'] = '\x01\x03\x02\x00\x14\xb8K'
RESPONSES['\x01\x03 \x82\x00\x01/\xe2']    = '\x01\x03\x02\x00\x1e8L'
RESPONSES['\x01\x03 \x83\x00\x01~"']       = '\x01\x03\x02\x00-xY'
RESPONSES['\x01\x03 \x84\x00\x01\xcf\xe3'] = '\x01\x03\x02\x0029\x91'
RESPONSES['\x01\x03 \x85\x00\x01\x9e#']    = '\x01\x03\x02\x00<\xb8U'
RESPONSES['\x01\x03 \x86\x00\x01n#']       = '\x01\x03\x02\x00F9\xb6'
RESPONSES['\x01\x03 \x87\x00\x01?\xe3']    = '\x01\x03\x02\x00P\xb8x'

RESPONSES['\x01\x03\x10@\x00\x01\x81\x1e'] = '\x01\x03\x02\x00\x07\xf9\x86' # Actual step
RESPONSES['\x01\x03\x10P\x00\x01\x80\xdb'] = '\x01\x03\x02\x00\x04\xb9\x87' # Cycles
RESPONSES['\x01\x03\x10`\x00\x01\x80\xd4'] = '\x01\x03\x02\x00\x01y\x84'    # Linked pattern

# Slave address 1, set_all_pattern_variables()
# --- Valid for pattern 0 ---
RESPONSES['\x01\x10 \x00\x00\x01\x02\x00d\x86y']       = '\x01\x10 \x00\x00\x01\n\t'     # SP0
RESPONSES['\x01\x10 \x01\x00\x01\x02\x00\xc8\x87\xd5'] = '\x01\x10 \x01\x00\x01[\xc9'
RESPONSES['\x01\x10 \x02\x00\x01\x02\x01,\x86=']       = '\x01\x10 \x02\x00\x01\xab\xc9'
RESPONSES['\x01\x10 \x03\x00\x01\x02\x01\x90\x86]']    = '\x01\x10 \x03\x00\x01\xfa\t'   # SP3, value 40
RESPONSES['\x01\x10 \x04\x00\x01\x02\x01\xf4\x86\x01'] = '\x01\x10 \x04\x00\x01K\xc8'
RESPONSES['\x01\x10 \x05\x00\x01\x02\x02X\x87]']       = '\x01\x10 \x05\x00\x01\x1a\x08'
RESPONSES['\x01\x10 \x06\x00\x01\x02\x02\xbc\x87%']    = '\x01\x10 \x06\x00\x01\xea\x08'
RESPONSES['\x01\x10 \x07\x00\x01\x02\x03 \x87\r']      = '\x01\x10 \x07\x00\x01\xbb\xc8'

RESPONSES['\x01\x10 \x80\x00\x01\x02\x00\n\x18U']      = '\x01\x10 \x80\x00\x01\x0b\xe1' # Time0
RESPONSES['\x01\x10 \x81\x00\x01\x02\x00\x14\x99\x8c'] = '\x01\x10 \x81\x00\x01Z!'
RESPONSES['\x01\x10 \x82\x00\x01\x02\x00\x1e\x19\xb8'] = '\x01\x10 \x82\x00\x01\xaa!' 
RESPONSES['\x01\x10 \x83\x00\x01\x02\x00(\x98\x7f']    = '\x01\x10 \x83\x00\x01\xfb\xe1' # Time3, value 40
RESPONSES['\x01\x10 \x84\x00\x01\x02\x002\x18\x03']    = '\x01\x10 \x84\x00\x01J '
RESPONSES['\x01\x10 \x85\x00\x01\x02\x00<\x98\x16']    = '\x01\x10 \x85\x00\x01\x1b\xe0'
RESPONSES['\x01\x10 \x86\x00\x01\x02\x00F\x19\xc6']    = '\x01\x10 \x86\x00\x01\xeb\xe0'
RESPONSES['\x01\x10 \x87\x00\x01\x02\x00P\x99\xd9']    = '\x01\x10 \x87\x00\x01\xba '

RESPONSES['\x01\x10\x10@\x00\x01\x02\x00\x07\xf8\x93'] = '\x01\x10\x10@\x00\x01\x04\xdd' # Actual step
RESPONSES['\x01\x10\x10P\x00\x01\x02\x00\x02:\x00']    = '\x01\x10\x10P\x00\x01\x05\x18' # Cycles, value 2
RESPONSES['\x01\x10\x10`\x00\x01\x02\x00\x01\x7f\xf1'] = '\x01\x10\x10`\x00\x01\x05\x17' # Linked pattern

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

# Slave address 10, set_start_pattern_no()
RESPONSES['\n\x10\x100\x00\x01\x02\x00\x02@\x90'] = '\n\x10\x100\x00\x01\x04}'

# Slave address 10, set_pattern_step_setpoint() Pattern 0, step 3, value 333.3. See also below. 
RESPONSES['\n\x10 \x03\x00\x01\x02\r\x050\x02'] = '\n\x10 \x03\x00\x01\xfbr'

# Slave address 10, set_pattern_step_time() Pattern 0, step 3, value 45. See also below. 
RESPONSES['\n\x10 \x83\x00\x01\x02\x00-+L'] = '\n\x10 \x83\x00\x01\xfa\x9a'

# Slave address 10, set_pattern_additional_cycles() Pattern 0, value 4. See also below. 
RESPONSES['\n\x10\x10P\x00\x01\x02\x00\x04\xc92'] = '\n\x10\x10P\x00\x01\x04c'

# Slave address 10, get_all_pattern_variables() 
# --- Valid for pattern 0 ---
# SP0: 10   Time0: 10 
# SP1: 20   Time1: 20
# SP2: 30   Time2: 30
# SP3: 333  Time3: 45
# SP4: 50   Time4: 50
# SP5: 60   Time5: 60
# SP6: 70   Time6: 70
# SP7: 80   Time7: 80
# Actual step:      7
# Add'l cycles:     4
# Linked pattern:   1
RESPONSES['\n\x03 \x00\x00\x01\x8e\xb1'] = '\n\x03\x02\x00d\x1cn' # SP0
RESPONSES['\n\x03 \x01\x00\x01\xdfq']    = '\n\x03\x02\x00\xc8\x1c\x13'
RESPONSES['\n\x03 \x02\x00\x01/q']       = '\n\x03\x02\x01,\x1d\xc8'
RESPONSES['\n\x03 \x03\x00\x01~\xb1']    = '\n\x03\x02\r\x05\xd9\x16'
RESPONSES['\n\x03 \x04\x00\x01\xcfp']    = '\n\x03\x02\x01\xf4\x1d\x92'
RESPONSES['\n\x03 \x05\x00\x01\x9e\xb0'] = '\n\x03\x02\x02X\x1d\x1f'
RESPONSES['\n\x03 \x06\x00\x01n\xb0']    = '\n\x03\x02\x02\xbc\x1dT'
RESPONSES['\n\x03 \x07\x00\x01?p']       = '\n\x03\x02\x03 \x1c\xad'

RESPONSES['\n\x03 \x80\x00\x01\x8fY']    = '\n\x03\x02\x00\n\x9d\x82' # Time0
RESPONSES['\n\x03 \x81\x00\x01\xde\x99'] = '\n\x03\x02\x00\x14\x1d\x8a'
RESPONSES['\n\x03 \x82\x00\x01.\x99']    = '\n\x03\x02\x00\x1e\x9d\x8d'
RESPONSES['\n\x03 \x83\x00\x01\x7fY']    = '\n\x03\x02\x00-\xdd\x98'
RESPONSES['\n\x03 \x84\x00\x01\xce\x98'] = '\n\x03\x02\x002\x9cP'
RESPONSES['\n\x03 \x85\x00\x01\x9fX']    = '\n\x03\x02\x00<\x1d\x94'
RESPONSES['\n\x03 \x86\x00\x01oX']       = '\n\x03\x02\x00F\x9cw'
RESPONSES['\n\x03 \x87\x00\x01>\x98']    = '\n\x03\x02\x00P\x1d\xb9'

RESPONSES['\n\x03\x10@\x00\x01\x80e']    = '\n\x03\x02\x00\x07\\G'   # Actual step
RESPONSES['\n\x03\x10P\x00\x01\x81\xa0'] = '\n\x03\x02\x00\x04\x1cF' # Cycles
RESPONSES['\n\x03\x10`\x00\x01\x81\xaf'] = '\n\x03\x02\x00\x01\xdcE' # Linked pattern

# Slave address 10, set_all_pattern_variables()
# --- Valid for pattern 0 ---
RESPONSES['\n\x10 \x00\x00\x01\x02\x00d\xf5I']       = '\n\x10 \x00\x00\x01\x0br'    # SP0
RESPONSES['\n\x10 \x01\x00\x01\x02\x00\xc8\xf4\xe5'] = '\n\x10 \x01\x00\x01Z\xb2'
RESPONSES['\n\x10 \x02\x00\x01\x02\x01,\xf5\r']      = '\n\x10 \x02\x00\x01\xaa\xb2'
RESPONSES['\n\x10 \x03\x00\x01\x02\x01\x90\xf5m']    =  '\n\x10 \x03\x00\x01\xfbr'   # SP3, value 40
RESPONSES['\n\x10 \x04\x00\x01\x02\x01\xf4\xf51']    = '\n\x10 \x04\x00\x01J\xb3'
RESPONSES['\n\x10 \x05\x00\x01\x02\x02X\xf4m']       = '\n\x10 \x05\x00\x01\x1bs'
RESPONSES['\n\x10 \x06\x00\x01\x02\x02\xbc\xf4\x15'] = '\n\x10 \x06\x00\x01\xebs'
RESPONSES['\n\x10 \x07\x00\x01\x02\x03 \xf4=']       = '\n\x10 \x07\x00\x01\xba\xb3'

RESPONSES['\n\x10 \x80\x00\x01\x02\x00\nke']         = '\n\x10 \x80\x00\x01\n\x9a'   # Time0
RESPONSES['\n\x10 \x81\x00\x01\x02\x00\x14\xea\xbc'] = '\n\x10 \x81\x00\x01[Z'
RESPONSES['\n\x10 \x82\x00\x01\x02\x00\x1ej\x88']    = '\n\x10 \x82\x00\x01\xabZ'
RESPONSES['\n\x10 \x83\x00\x01\x02\x00(\xebO']       = '\n\x10 \x83\x00\x01\xfa\x9a' # Time3, value 40
RESPONSES['\n\x10 \x84\x00\x01\x02\x002k3']          = '\n\x10 \x84\x00\x01K['
RESPONSES['\n\x10 \x85\x00\x01\x02\x00<\xeb&']       = '\n\x10 \x85\x00\x01\x1a\x9b'
RESPONSES['\n\x10 \x86\x00\x01\x02\x00Fj\xf6']       = '\n\x10 \x86\x00\x01\xea\x9b'
RESPONSES['\n\x10 \x87\x00\x01\x02\x00P\xea\xe9']    = '\n\x10 \x87\x00\x01\xbb['

RESPONSES['\n\x10\x10@\x00\x01\x02\x00\x07\x8b\xa3'] = '\n\x10\x10@\x00\x01\x05\xa6' # Actual step
RESPONSES['\n\x10\x10P\x00\x01\x02\x00\x02I0']       = '\n\x10\x10P\x00\x01\x04c'    # Cycles, value 2 
RESPONSES['\n\x10\x10`\x00\x01\x02\x00\x01\x0c\xc1'] = '\n\x10\x10`\x00\x01\x04l'    # Linked pattern


def _print_out( inputstring ):
    """Print the inputstring. To make it compatible with Python2 and Python3."""    
    sys.stdout.write(inputstring + '\n')  
    
    
if __name__ == '__main__':
    unittest.main() 
