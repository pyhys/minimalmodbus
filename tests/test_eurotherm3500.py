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

Uses a dummy serial port from the module :py:mod:`dummy_serial`.

"""

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"


import unittest

import eurotherm3500
import dummy_serial

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

    ## Read PV ##

    def testReadPv1(self):
        self.assertAlmostEqual( self.instrument.get_pv_loop1(), 77.0 )

    def testReadPv2(self):
        self.assertAlmostEqual( self.instrument.get_pv_loop2(), 19.2 )

    def testReadPv3(self):
        self.assertAlmostEqual( self.instrument.get_pv_module3(), 19.2 )

    def testReadPv4(self):
        self.assertAlmostEqual( self.instrument.get_pv_module4(), 19.4 )

    def testReadPv6(self):
        self.assertAlmostEqual( self.instrument.get_pv_module6(), 18.7 )
    
    ## Read and write SP and SP change rate ##
    
    def testReadSp1(self):
        self.assertAlmostEqual( self.instrument.get_sp_loop1(), 18.4 )
   
    def testWriteSp1(self):
        self.instrument.set_sp_loop1(5)
   
    def testReadSp1Target(self):
        self.assertAlmostEqual( self.instrument.get_sptarget_loop1(), 0 )
   
    def testReadSp2(self):
        self.assertAlmostEqual( self.instrument.get_sp_loop2(), 18.4 )    
 
    def testIsSprate1Disabled(self):
        self.assertFalse( self.instrument.is_sprate_disabled_loop1() )

    def testReadSprate1(self):
        self.assertAlmostEqual( self.instrument.get_sprate_loop1(), 30.0 )
   
    def testWriteSprate1(self):
        self.instrument.set_sprate_loop1(20)

    def testEnableSprate1(self):
        self.instrument.enable_sprate_loop1() 

    def testDisableSprate1(self):
        self.instrument.disable_sprate_loop1() 

    ## Read OP ##
 
    def testReadOp1(self):
        self.assertAlmostEqual( self.instrument.get_op_loop1(), 0.0 ) 

    def testReadOp2(self):
        self.assertAlmostEqual( self.instrument.get_op_loop2(), 0.0 ) 
    
    ## Read alarms ##
    
    def testReadAlarm1Threshold(self):
        self.assertAlmostEqual( self.instrument.get_threshold_alarm1(), 620 )   
    
    def testReadAlarmSummary(self):
        self.assertTrue( self.instrument.is_set_alarmsummary() )   
    
    ## Read controller state ##
    
    def testLoop1Manual(self):
        self.assertFalse( self.instrument.is_manual_loop1() )      
     
    def testLoop1Inhibited(self):
        self.assertTrue( self.instrument.is_inhibited_loop1() )         
    
    
RESPONSES = {}
"""A dictionary of respones from a dummy Eurotherm 3500 instrument. 

The key is the message (string) sent to the serial port, and the item is the response (string) 
from the dummy serial port.

"""
# Note that the string 'AAAAAAA' might be easier to read if grouped, 
# like 'AA' + 'AAAA' + 'A' for the initial part (address etc) + payload + CRC.


# get_sp_loop1(): Return value 18.4
RESPONSES['\x01\x03' + '\x00\x05\x00\x01' + '\x94\x0b'] = '\x01\x03' + '\x02\x00\xb8' + '\xb86'

# get_sptarget_loop1(): Return value 0
RESPONSES['\x01\x03' + '\x00\x02\x00\x01' + '%\xca']    = '\x01\x03' + '\x02\x00\x00' + '\xb8D'

# get_sp_loop2(): Return value 18.4
RESPONSES['\x01\x03' + '\x04\x05\x00\x01' + '\x95;']    = '\x01\x03' + '\x02\x00\xb8' + '\xb86'

# is_sprate_disabled_loop1(): Return value False
RESPONSES['\x01\x03' + '\x00N\x00\x01' + '\xe4\x1d']    = '\x01\x03' + '\x02\x00\x00' + '\xb8D'

# get_sprate_loop1(): Return value 30.0
RESPONSES['\x01\x03' + '\x00#\x00\x01' + 'u\xc0']       = '\x01\x03' + '\x02\x01,' + '\xb8\t'

# get_op_loop1(): Return value 0.0
RESPONSES['\x01\x03' + '\x00U\x00\x01' + '\x94\x1a']    = '\x01\x03' + '\x02\x00\x00' + '\xb8D'

# get_op_loop2(): Return value 0.0            
RESPONSES['\x01\x03' + '\x04U\x00\x01' + '\x95*']       = '\x01\x03' + '\x02\x00\x00' + '\xb8D'

# get_threshold_alarm1(): Return value 620.0
RESPONSES['\x01\x03' + '(\x01\x00\x01' + '\xdcj']       = '\x01\x03' + '\x02\x188' + '\xb3\x96'

# is_set_alarmsummary(): Return value True
RESPONSES["\x01\x03" + "'\xe5\x00\x01\x9fI"]            =  '\x01\x03' + '\x02\x00\x01' + 'y\x84'

# is_manual_loop1(): Return value False
RESPONSES['\x01\x03' + '\x01\x11\x00\x01' + '\xd5\xf3'] = '\x01\x03' + '\x02\x00\x00' + '\xb8D'

# is_inhibited_loop1(): Return value True
RESPONSES['\x01\x03' + '\x01\x0c\x00\x01' + 'E\xf5']    = '\x01\x03' + '\x02\x00\x01' + 'y\x84'

# get_pv_loop1(): Return value 18.5
# RESPONSES['\x01\x03\x01!\x00\x01\xd5\xfc'] = '\x01\x03\x02\x00\xb9y\xf6'

# get_pv_loop1: Return value 77.0
# -----------------------------------------------------------------#
# Message:  slave address 1, function code 3, register address 289, 1 register, CRC. 
# Response: slave address 1, function code 3, 2 bytes, value=770, CRC=14709
RESPONSES['\x01\x03' + '\x01!\x00\x01' + '\xd5\xfc']    = '\x01\x03' + '\x02\x03\x02' + '\x39\x75'

# get_pv_loop2(): Return value 19.2 
RESPONSES['\x01\x03' + '\x05!\x00\x01' + '\xd4\xcc']    = '\x01\x03' + '\x02\x00\xc0' + '\xb8\x14'

# get_pv_module3(): Return value 19.2  
RESPONSES['\x01\x03' + '\x01r\x00\x01' + '%\xed']       = '\x01\x03' + '\x02\x00\xc0' + '\xb8\x14'

# get_pv_module4(): Return value 19.4  
RESPONSES['\x01\x03' + '\x01u\x00\x01' + '\x94,']       = '\x01\x03' + '\x02\x00\xc2' + '9\xd5'

# get_pv_module6(): Return value 18.7  
RESPONSES['\x01\x03' + '\x01{\x00\x01' + '\xf5\xef']    = '\x01\x03' + '\x02\x00\xbb' + '\xf87'

# set_sp_loop1(5)
RESPONSES['\x01\x10' + '\x00\x18\x00\x01\x02\x002' + '$]']       = '\x01\x10' + '\x00\x18\x00\x01' + '\x81\xce'

# set_sprate_loop1(20)
RESPONSES['\x01\x10' + '\x00#\x00\x01\x02\x00\xc8' + '\xa0\x95'] = '\x01\x10' + '\x00#\x00\x01' + '\xf0\x03'

# enable_sprate_loop1() 
RESPONSES['\x01\x10' + '\x00N\x00\x01\x02\x00\x00' + '\xa9\xbe'] = '\x01\x10' + '\x00N\x00\x01' + 'a\xde'

# disable_sprate_loop1() 
RESPONSES['\x01\x10' + '\x00N\x00\x01\x02\x00\x01' + 'h~']       = '\x01\x10' + '\x00N\x00\x01' + 'a\xde'
    
    
if __name__ == '__main__':
    unittest.main()  
