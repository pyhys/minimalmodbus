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

test_minimalmodbus: Unittests for the :mod:`minimalmodbus` module.

For each function are these tests performed:

  * Known results
  * Invalid input value
  * Invalid input type

This unittest suite uses a mock/dummy serial port from the module :mod:`dummy_serial`,
so it is possible to test the functionality using previously recorded communication data.

With dummy responses, it is also possible to simulate errors in the communication
from the slave. A few different types of communication errors are tested, as seen in this table.

=====================================  ===================== =================================
Simulated response error               Tested using function Tested using Modbus function code
=====================================  ===================== =================================
No response                            read_bit              2
Wrong CRC in response                  write_register        16
Wrong slave address in response        write_register        16
Wrong function code in response        write_register        16
Slave indicates an error               write_register        16
Wrong byte count in response           read_bit              2
Wrong register address in response     write_register        16
Wrong number of registers in response  write_bit             15
Wrong number of registers in response  write_register        16
Wrong write data in response           write_bit             5
Wrong write data in response           write_register        6
=====================================  ===================== =================================


"""

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"


import sys
import time
import unittest

import minimalmodbus
import dummy_serial

ALSO_TIME_CONSUMING_TESTS = True
"""Set this to :const:`False` to skip the most time consuming tests"""

VERBOSITY = 0
"""Verbosity level for the unit testing. Use value 0 or 2. Note that it only has an effect for Python 2.7 and above."""

SHOW_ERROR_MESSAGES_FOR_ASSERTRAISES = False
"""Set this to :const:`True` for printing the error messages caught by assertRaises().

If set to :const:`True`, any unintentional error messages raised during the processing of the command in :meth:`.assertRaises` are also caught (not counted). It will be printed in the short form, and will show no traceback.  It can also be useful to set :data:`VERBOSITY` = 2.
"""

_LARGE_NUMBER_OF_BYTES = 1000

# For compatibility with Python2.6
_VERSION_LIMIT = 0x02070000    
_runTestsForNewVersion = sys.hexversion >= _VERSION_LIMIT  

###########################################################
# For showing the error messages caught by assertRaises() #
# and to implement a better assertAlmostEqual()           #
###########################################################

class _NonexistantError(Exception):
    pass

class ExtendedTestCase(unittest.TestCase):
    """Overriding the assertRaises() method to be able to print the error message.

    Use :data:`test_minimalmodbus.SHOW_ERROR_MESSAGES_FOR_ASSERTRAISES` = :const:`True`
    in order to use this option. It can also be useful to set :data:`test_minimalmodbus.VERBOSITY` = 2.

    Based on http://stackoverflow.com/questions/8672754/how-to-show-the-error-messages-caught-by-assertraises-in-unittest-in-python2-7

    """

    def assertRaises(self, excClass, callableObj, *args, **kwargs):
        """Prints the caught error message (if :data:`SHOW_ERROR_MESSAGES_FOR_ASSERTRAISES` is :const:`True`)."""
        if SHOW_ERROR_MESSAGES_FOR_ASSERTRAISES:
            try:
                unittest.TestCase.assertRaises(self, _NonexistantError, callableObj, *args, **kwargs)
            except:
                minimalmodbus._print_out( '\n    ' + repr(sys.exc_info()[1]) )
        else:
            unittest.TestCase.assertRaises(self, excClass, callableObj, *args, **kwargs)

    def assertAlmostEqualRatio(self, first, second, epsilon = 1.000001):
        """A function to compare floats, with ratio instead of difference.
        
        Args:
            * first (float): Input argument for comparison
            * second (float): Input argument for comparison
            * epsilon (float): Largest allowed ratio of largest to smallest of the two input arguments
        
        """
        if first == second:
            return 
            
        if (first < 0 and second >= 0) or (first >= 0 and second < 0):
            raise AssertionError('The arguments have different signs: {0!r} and {1!r}'.format(first, second))
        
        ratio = max(first, second)/float(min(first, second))
        if ratio > epsilon:
            raise AssertionError('The arguments are not equal: {0!r} and {1!r}. Epsilon is {2!r}.'.\
                format(first, second, epsilon))

##############################
# Constants for type testing #
##############################

_NOT_INTERGERS_OR_NONE = [0.0, 1.0, '1', ['1'], [1], ['\x00\x2d\x00\x58'], ['A', 'B', 'C']]
_NOT_INTERGERS = _NOT_INTERGERS_OR_NONE + [None]

_NOT_NUMERICALS_OR_NONE = ['1', ['1'], [1], ['\x00\x2d\x00\x58'], ['A', 'B', 'C']]
_NOT_NUMERICALS = _NOT_NUMERICALS_OR_NONE + [None]

_NOT_STRINGS_OR_NONE = [1, 0.0, 1.0,      ['1'], [1], ['\x00\x2d\x00\x58'], ['A', 'B', 'C'], True, False]
_NOT_STRINGS = _NOT_STRINGS_OR_NONE + [None]

_NOT_BOOLEANS =  ['True', 'False', -1, 1, 2, 0, 8, 9999999, -1.0, 1.0, 0.0, [True], [False], [1], [1.0] ]

_NOT_INTLISTS = [0, 1, 2, -1, True, False, 0.0, 1.0, '1', ['1'], None, ['\x00\x2d\x00\x58'], ['A', 'B', 'C'], [1.0], [1.0, 2.0] ]


####################
# Payload handling #
####################

class TestEmbedPayload(ExtendedTestCase):

    knownValues=[
    (2, 2,  'rtu',   '123', '\x02\x02123X\xc2'),
    (1, 16, 'rtu',   'ABC', '\x01\x10ABC<E'),
    (0, 5,  'rtu',   'hjl', '\x00\x05hjl\x8b\x9d'),
    (1, 3,  'rtu',   '\x01\x02\x03', '\x01\x03\x01\x02\x03\t%'),
    (1, 3,  'ascii', '123', ':010331323366\r\n'),
    (4, 5,  'ascii', '\x01\x02\x03', ':0405010203F1\r\n'),
    (2, 2,  'ascii', '123', ':020231323366\r\n'),
    ]

    def testKnownValues(self):
        for slaveaddress, functioncode, mode, inputstring, knownresult in self.knownValues:

            result = minimalmodbus._embedPayload(slaveaddress, mode, functioncode, inputstring)
            self.assertEqual(result, knownresult)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 248, 'rtu',   16,  'ABC') # Wrong slave address
        self.assertRaises(ValueError, minimalmodbus._embedPayload, -1,  'rtu',   16,  'ABC')
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 248, 'ascii', 16,  'ABC')
        self.assertRaises(ValueError, minimalmodbus._embedPayload, -1,  'ascii', 16,  'ABC')
        
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 1, 'rtuu',  16,  'ABC') # Wrong Modbus mode
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 1, 'RTU',   16,  'ABC')
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 1, 'ASCII', 16,  'ABC')
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 1, 'asci',  16,  'ABC')
        
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 1,   'rtu',   222, 'ABC') # Wrong function code
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 1,   'rtu',   -1,  'ABC')
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 1,   'ascii', 222, 'ABC')
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 1,   'ascii', -1,  'ABC')
        
    def testWrongInputType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._embedPayload, value, 'rtu',   16,    'ABC')
            self.assertRaises(TypeError, minimalmodbus._embedPayload, value, 'ascii', 16,    'ABC')
            self.assertRaises(TypeError, minimalmodbus._embedPayload, 1,     'rtu',   value, 'ABC')
            self.assertRaises(TypeError, minimalmodbus._embedPayload, 1,     'ascii', value, 'ABC')
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._embedPayload, 1,     value,   16,    'ABC')
            self.assertRaises(TypeError, minimalmodbus._embedPayload, 1,     'rtu',   16,    value)
            self.assertRaises(TypeError, minimalmodbus._embedPayload, 1,     'ascii', 16,    value)


class TestExtractPayload(ExtendedTestCase):

    knownValues = TestEmbedPayload.knownValues

    def testKnownValues(self):
        for slaveaddress, functioncode, mode, knownresult, inputstring in self.knownValues:
            result = minimalmodbus._extractPayload(inputstring, slaveaddress, mode, functioncode)
            self.assertEqual(result, knownresult)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x02123X\xc3',     2,     'rtu',   2) # Wrong CRC from slave
        self.assertRaises(ValueError, minimalmodbus._extractPayload, ':0202313233F1\r\n',    2,     'ascii', 2) # Wrong LRC from slave
        self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x82123q\x02',     2,     'rtu',   2) # Error indication from slave
        self.assertRaises(ValueError, minimalmodbus._extractPayload, ':0282313233E6\r\n',    2,     'ascii', 2)
        self.assertRaises(ValueError, minimalmodbus._extractPayload, 'ABC',                  2,     'rtu',   2) # Too short message from slave
        self.assertRaises(ValueError, minimalmodbus._extractPayload, 'ABCDEFGH',             2,     'ascii', 2)
        self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x72123B\x02',     2,     'rtu',   2) # Wrong functioncode from slave
        self.assertRaises(ValueError, minimalmodbus._extractPayload, ':020431323364\r\n',    2,     'ascii', 2)
        self.assertRaises(ValueError, minimalmodbus._extractPayload, '020231323366\r\n',     2,     'ascii', 2) # Missing ASCII header
        self.assertRaises(ValueError, minimalmodbus._extractPayload, ':020231323366',        2,     'ascii', 2) # Wrong ASCII footer
        self.assertRaises(ValueError, minimalmodbus._extractPayload, ':020231323366\r',      2,     'ascii', 2)
        self.assertRaises(ValueError, minimalmodbus._extractPayload, ':020231323366\n',      2,     'ascii', 2)
        self.assertRaises(ValueError, minimalmodbus._extractPayload, ':02023132366\r\n',     2,     'ascii', 2) # Odd number of ASCII payload characters
        
        for value in [3, 95, 128, 248, -1]:
            self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', value, 'rtu',   2) # Wrong slave address
            self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', 2,     'rtu',   value) # Wrong functioncode
        
        for value in ['RTU', 'ASCII', 'asc', '', ' ']:
            self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', 2,      value,  2) # Wrong mode
        
    def testWrongInputType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', value, 'rtu',   2) # Wrong slaveaddress type
            self.assertRaises(TypeError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', value, 'ascii', 2)
            self.assertRaises(TypeError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', 2,     'rtu',   value)  # Wrong functioncode type
            self.assertRaises(TypeError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', 2,     'ascii', value)
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._extractPayload, value,              2,     'rtu',   2) # Wrong message
            self.assertRaises(TypeError, minimalmodbus._extractPayload, value,              2,     'ascii', 2) 
            self.assertRaises(TypeError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', 2,     value,   2) # Wrong mode
            
            
class TestSanityEmbedExtractPayload(ExtendedTestCase):

    knownValues = TestEmbedPayload.knownValues

    def testKnownValues(self):
        for slaveaddress, functioncode, mode, payload, message in self.knownValues:
            embeddedResult  = minimalmodbus._embedPayload(slaveaddress, mode, functioncode, payload)
            extractedResult = minimalmodbus._extractPayload(embeddedResult, slaveaddress, mode, functioncode)
            self.assertEqual(extractedResult, payload)
            
    def testRange(self):
        for i in range(110):
            payload = str(i)

            embeddedResultRtu  = minimalmodbus._embedPayload(2, 'rtu', 6, payload)
            extractedResultRtu = minimalmodbus._extractPayload(embeddedResultRtu, 2, 'rtu', 6)
            self.assertEqual(extractedResultRtu, payload)
            
            embeddedResultAscii  = minimalmodbus._embedPayload(2, 'ascii', 6, payload)
            extractedResultAscii = minimalmodbus._extractPayload(embeddedResultAscii, 2, 'ascii', 6)
            self.assertEqual(extractedResultAscii, payload)
            

############################################
## Serial communication utility functions ##
############################################

class TestPredictResponseSize(ExtendedTestCase):    
    
    knownValues = [
    ('rtu',  1,     '\x00\x3e\x00\x01', 6),
    ('rtu',  1,     '\x00\x3e\x00\x07', 6),
    ('rtu',  1,     '\x00\x3e\x00\x08', 6),
    ('rtu',  1,     '\x00\x3e\x00\x09', 7),
    ('rtu',  3,     'AB\x00\x07', 19),
    ('rtu',  4,     'AB\x00\x07', 19),
    ('rtu',  4,     'AB\x01\x07', 531),
    ('rtu',  5,     '\x00\x47\xff\x00', 8),
    ('rtu',  16,    '\x00\x48\x00\x01\x01\x01', 8),
    ('ascii',  1,   '\x00\x3e\x00\x01', 13),
    ('ascii',  1,   '\x00\x3e\x00\x07', 13),
    ('ascii',  1,   '\x00\x3e\x00\x08', 13),
    ('ascii',  1,   '\x00\x3e\x00\x09', 15),
    ('ascii',  3,   'AB\x00\x07', 39),
    ('ascii',  4,   'AB\x00\x07', 39),
    ('ascii',  4,   'AB\x01\x07', 1063),
    ('ascii',  5,   '\x00\x47\xff\x00', 17),
    ('ascii',  16,  '\x00\x48\x00\x01\x01\x01', 17),
    ]
    
    def testKnownValues(self):
        for mode, functioncode, payloadToSlave, knownvalue in self.knownValues:
            resultvalue = minimalmodbus._predictResponseSize(mode, functioncode, payloadToSlave)
            self.assertEqual(resultvalue, knownvalue)

    def testRecordedRtuMessages(self):            
        ## Use the dictionary where the key is the 'message', and the item is the 'response'
        for message in GOOD_RTU_RESPONSES:
            slaveaddress = ord(message[0])
            functioncode = ord(message[1])
            payloadToSlave = minimalmodbus._extractPayload(message, slaveaddress, 'rtu', functioncode)
            result = minimalmodbus._predictResponseSize('rtu', functioncode, payloadToSlave)
            
            responseFromSlave = GOOD_RTU_RESPONSES[message]
            self.assertEqual(result, len(responseFromSlave))

    def testRecordedAsciiMessages(self):    
        ## Use the dictionary where the key is the 'message', and the item is the 'response'
        for message in GOOD_ASCII_RESPONSES:
            slaveaddress = int(message[1:3])
            functioncode = int(message[3:5])
            payloadToSlave = minimalmodbus._extractPayload(message, slaveaddress, 'ascii', functioncode)
            result = minimalmodbus._predictResponseSize('ascii', functioncode, payloadToSlave)
            
            responseFromSlave = GOOD_ASCII_RESPONSES[message]
            self.assertEqual(result, len(responseFromSlave))
     
    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._predictResponseSize, 'asciiii',    6,      'ABCD') # Wrong mode
        self.assertRaises(ValueError, minimalmodbus._predictResponseSize, 'ascii',      999,    'ABCD') # Wrong function code
        self.assertRaises(ValueError, minimalmodbus._predictResponseSize, 'rtu',        999,    'ABCD') # Wrong function code
        self.assertRaises(ValueError, minimalmodbus._predictResponseSize, 'ascii',      1,      'ABC')  # Too short message
        self.assertRaises(ValueError, minimalmodbus._predictResponseSize, 'rtu',        1,      'ABC')  # Too short message
        self.assertRaises(ValueError, minimalmodbus._predictResponseSize, 'ascii',      1,      'AB')   # Too short message
        self.assertRaises(ValueError, minimalmodbus._predictResponseSize, 'ascii',      1,      'A')    # Too short message
        self.assertRaises(ValueError, minimalmodbus._predictResponseSize, 'ascii',      1,      '')     # Too short message

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._predictResponseSize, value, 1, 'ABCD')
            self.assertRaises(TypeError, minimalmodbus._predictResponseSize, 'rtu', 1, value)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._predictResponseSize, 'rtu', value, 'ABCD')
            

class TestCalculateMinimumSilentPeriod(ExtendedTestCase):

    knownValues=[
    (2400,      0.016), 
    (2400.0,    0.016),
    (4800,      0.008),
    (9600,      0.004),
    (19200,     0.002), 
    (38400,     0.001),
    (115200,    0.00033)
    ]
    
    def testKnownValues(self):
        for baudrate, knownresult in self.knownValues:
            result = minimalmodbus._calculate_minimum_silent_period(baudrate)
            self.assertAlmostEqualRatio(result, knownresult, 1.02) # Allow 2% deviation from listed known values

    def testWrongInputValue(self):
        for value in [-2400, -2400.0, -1, -0.5 , 0, 0.5, 0.9]:
            self.assertRaises(ValueError, minimalmodbus._calculate_minimum_silent_period, value)

    def testWrongInputType(self):
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, minimalmodbus._calculate_minimum_silent_period, value)


##############################
# String and num conversions #
##############################

class TestNumToOneByteString(ExtendedTestCase):

    knownValues=[
    (0, '\x00' ),
    (7, '\x07' ),
    (255, '\xff' ),
    ]

    def testKnownValues(self):
        for inputvalue, knownstring in self.knownValues:
            resultstring = minimalmodbus._numToOneByteString( inputvalue )
            self.assertEqual(resultstring, knownstring)

    def testKnownLoop(self):
        for value in range(256):
            knownstring = chr(value)
            resultstring = minimalmodbus._numToOneByteString(value)
            self.assertEqual(resultstring, knownstring)

    def testWrongInput(self):
        self.assertRaises(ValueError, minimalmodbus._numToOneByteString, -1)
        self.assertRaises(ValueError, minimalmodbus._numToOneByteString, 256)

    def testWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._numToOneByteString, value)


class TestNumToTwoByteString(ExtendedTestCase):

    knownValues=[
    (0.0,    0, False, False, '\x00\x00'), # Range 0-65535
    (0,      0, False, False, '\x00\x00'), 
    (0,      0, True,  False, '\x00\x00'), 
    (77.0,   1, False, False, '\x03\x02'),
    (77.0,   1, True,  False, '\x02\x03'),
    (770,    0, False, False, '\x03\x02'),
    (770,    0, True,  False, '\x02\x03'),
    (65535,  0, False, False, '\xff\xff'),
    (65535,  0, True,  False, '\xff\xff'),
    (770,    0, False, True,  '\x03\x02'), # Range -32768 to 32767 
    (77.0,   1, False, True,  '\x03\x02'),
    (0.0,    0, False, True,  '\x00\x00'),
    (0.0,    3, False, True,  '\x00\x00'),
    (-1,     0, False, True,  '\xff\xff'),
    (-1,     1, False, True,  '\xff\xf6'),
    (-77,    0, False, True,  '\xff\xb3'),
    (-770,   0, False, True,  '\xfc\xfe'),
    (-77,    1, False, True,  '\xfc\xfe'),
    (-32768, 0, False, True,  '\x80\x00'),
    (32767,  0, False, True,  '\x7f\xff'),
    ]

    def testKnownValues(self):
        for inputvalue, numberOfDecimals, LsbFirst, signed, knownstring in self.knownValues:
            resultstring = minimalmodbus._numToTwoByteString(inputvalue, numberOfDecimals, LsbFirst, signed)
            self.assertEqual(resultstring, knownstring)

    def testWrongInputValue(self):
        for LsbFirst in [False, True]:
            # Range 0-65535
            self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, 77,    -1, LsbFirst)
            if _runTestsForNewVersion:  # For compatibility with Python2.6
                self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, 77000, 0,  LsbFirst) # Gives DeprecationWarning instead of ValueError for Python 2.6
                self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, 65536, 0,  LsbFirst)
                self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, 77,    4,  LsbFirst)
                self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, -1,    0,  LsbFirst)
                self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, -77,   1,  LsbFirst)
            
            # Range -32768 to 32767
            self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, 77,     -1, LsbFirst, True)
            if _runTestsForNewVersion:  # For compatibility with Python2.6
                self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, -77000, 0,  LsbFirst, True) # Gives DeprecationWarning instead of ValueError for Python 2.6
                self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, -32769, 0,  LsbFirst, True)
                self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, 32768,  0,  LsbFirst, True)
                self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, 77000,  0,  LsbFirst, True)
                self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, 77,     4,  LsbFirst, True)
                self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, -77,    4,  LsbFirst, True)
            

    def testWrongInputType(self):
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, minimalmodbus._numToTwoByteString, value, 1,     False, False)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._numToTwoByteString, 77,    value, False, False)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, minimalmodbus._numToTwoByteString, 77,    1,     value, False)
            self.assertRaises(TypeError, minimalmodbus._numToTwoByteString, 77,    1,     False, value)


class TestTwoByteStringToNum(ExtendedTestCase):

    knownValues=TestNumToTwoByteString.knownValues

    def testKnownValues(self):
        for knownvalue, numberOfDecimals, LsbFirst, signed, bytestring in self.knownValues:
            if not LsbFirst:
                resultvalue = minimalmodbus._twoByteStringToNum(bytestring, numberOfDecimals, signed)
                self.assertEqual(resultvalue, knownvalue)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._twoByteStringToNum, 'ABC', 1)
        self.assertRaises(ValueError, minimalmodbus._twoByteStringToNum, 'A',   1)
        self.assertRaises(ValueError, minimalmodbus._twoByteStringToNum, 'AB',  -1)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._twoByteStringToNum, value,      1)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._twoByteStringToNum, 'AB',       value)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, minimalmodbus._twoByteStringToNum, '\x03\x02', 1,     value)


class TestSanityTwoByteString(ExtendedTestCase):

    knownValues=TestNumToTwoByteString.knownValues

    def testSanity(self):
        for value, numberOfDecimals, LsbFirst, signed, bytestring in self.knownValues:
            if not LsbFirst:
                resultvalue = minimalmodbus._twoByteStringToNum( \
                    minimalmodbus._numToTwoByteString(value, numberOfDecimals, LsbFirst, signed), \
                    numberOfDecimals, signed )
                self.assertEqual(resultvalue, value)

        if ALSO_TIME_CONSUMING_TESTS:
            for value in range(0x10000):
                resultvalue = minimalmodbus._twoByteStringToNum( minimalmodbus._numToTwoByteString(value) )
                self.assertEqual(resultvalue, value)


class TestLongToBytestring(ExtendedTestCase):

    knownValues=[
    (0,           False, 2, '\x00\x00\x00\x00'),
    (0,           True,  2, '\x00\x00\x00\x00'),
    (1,           False, 2, '\x00\x00\x00\x01'),
    (1,           True,  2, '\x00\x00\x00\x01'),
    (2,           False, 2, '\x00\x00\x00\x02'),
    (2,           True,  2, '\x00\x00\x00\x02'),
    (75000,       False, 2, '\x00\x01\x24\xf8'),
    (75000,       True,  2, '\x00\x01\x24\xf8'),    
    (1000000,     False, 2, '\x00\x0f\x42\x40'),
    (1000000,     True,  2, '\x00\x0f\x42\x40'),
    (2147483647,  False, 2, '\x7f\xff\xff\xff'),
    (2147483647,  True,  2, '\x7f\xff\xff\xff'),
    (2147483648,  False, 2, '\x80\x00\x00\x00'),
    (4294967295,  False, 2, '\xff\xff\xff\xff'),
    (-1,          True,  2, '\xff\xff\xff\xff'),
    (-2147483648, True,  2, '\x80\x00\x00\x00'),
    (-200000000,  True,  2, '\xf4\x14\x3e\x00'),
    ]

    def testKnownValues(self):
        for value, signed, numberOfRegisters, knownstring in self.knownValues:
            resultstring = minimalmodbus._longToBytestring(value, signed, numberOfRegisters)
            self.assertEqual(resultstring, knownstring)

    def testWrongInputValue(self):
        if _runTestsForNewVersion:  # For compatibility with Python2.6
            self.assertRaises(ValueError, minimalmodbus._longToBytestring, -1,              False, 2) # Range 0 to 4294967295
            self.assertRaises(ValueError, minimalmodbus._longToBytestring, 4294967296,      False, 2)
            self.assertRaises(ValueError, minimalmodbus._longToBytestring, -2147483649,     True,  2) # Range -2147483648 to 2147483647
            self.assertRaises(ValueError, minimalmodbus._longToBytestring, 2147483648,      True,  2)
            self.assertRaises(ValueError, minimalmodbus._longToBytestring, 222222222222222, True,  2)
        
        for numberOfRegisters in [0, 1, 3, 4, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, minimalmodbus._longToBytestring, 1,           True,  numberOfRegisters)

    def testWrongInputType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._longToBytestring, value, True, 2)
            self.assertRaises(TypeError, minimalmodbus._longToBytestring, 1,     True, value)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, minimalmodbus._longToBytestring, 1,     value, 2)


class TestBytestringToLong(ExtendedTestCase):

    knownValues=TestLongToBytestring.knownValues

    def testKnownValues(self):
        for knownvalue, signed, numberOfRegisters, bytestring in self.knownValues:
            resultvalue = minimalmodbus._bytestringToLong(bytestring, signed, numberOfRegisters)
            self.assertEqual(resultvalue, knownvalue)

    def testWrongInputValue(self):
        for inputstring in ['', 'A', 'AA', 'AAA', 'AAAAA']:
            self.assertRaises(ValueError, minimalmodbus._bytestringToLong, inputstring, True,  2)
        for numberOfRegisters in [0, 1, 3, 4, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, minimalmodbus._bytestringToLong, 'AAAA',      True,  numberOfRegisters)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToLong, value,        True,  2)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToLong, 'AAAA',       value, 2)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToLong, 'AAAA',       True,  value)


class TestSanityLong(ExtendedTestCase):

    knownValues=TestLongToBytestring.knownValues

    def testSanity(self):
        for value, signed, numberOfRegisters, bytestring in self.knownValues:
            resultvalue = minimalmodbus._bytestringToLong( \
                minimalmodbus._longToBytestring(value, signed, numberOfRegisters), signed, numberOfRegisters)
            self.assertEqual(resultvalue, value)


class TestFloatToBytestring(ExtendedTestCase):

    # Use this online calculator:
    # http://babbage.cs.qc.cuny.edu/IEEE-754/index.xhtml

    # See also examples in
    # http://en.wikipedia.org/wiki/Single-precision_floating-point_format
    # http://en.wikipedia.org/wiki/Double-precision_floating-point_format

    knownValues=[
    (1,       2, '\x3f\x80\x00\x00'),
    (1.0,     2, '\x3f\x80\x00\x00'), # wikipedia
    (1.0,     2, '?\x80\x00\x00'),
    (1.1,     2, '\x3f\x8c\xcc\xcd'),
    (100,     2, '\x42\xc8\x00\x00'),
    (100.0,   2, '\x42\xc8\x00\x00'),
    (1.0e5,   2, '\x47\xc3\x50\x00'),
    (1.1e9,   2, '\x4e\x83\x21\x56'),
    (1.0e16,  2, '\x5a\x0e\x1b\xca'),
    (1.5e16,  2, '\x5a\x55\x29\xaf'),
    (3.65e30, 2, '\x72\x38\x47\x25'),
    (-1.1,    2, '\xbf\x8c\xcc\xcd'),
    (-2,      2, '\xc0\x00\x00\x00'),
    (-3.6e30, 2, '\xf2\x35\xc0\xe9'),
    (1.0,     4, '\x3f\xf0\x00\x00\x00\x00\x00\x00'),
    (2,       4, '\x40\x00\x00\x00\x00\x00\x00\x00'),
    (1.1e9,   4, '\x41\xd0\x64\x2a\xc0\x00\x00\x00'),
    (3.65e30, 4, '\x46\x47\x08\xe4\x9e\x2f\x4d\x62'),
    (2.42e300,4, '\x7e\x4c\xe8\xa5\x67\x1f\x46\xa0'), 
    (-1.1,    4, '\xbf\xf1\x99\x99\x99\x99\x99\x9a'),
    (-2,      4, '\xc0\x00\x00\x00\x00\x00\x00\x00'),
    (-3.6e30, 4, '\xc6\x46\xb8\x1d\x1a\x43\xb2\x06'), 
    ]

    def testKnownValues(self):
        for value, numberOfRegisters, knownstring in self.knownValues:
            resultstring = minimalmodbus._floatToBytestring(value, numberOfRegisters)
            self.assertEqual(resultstring, knownstring)
        self.assertEqual(minimalmodbus._floatToBytestring(1.5e999, 2), '\x7f\x80\x00\x00') # +inf

    def testWrongInputValue(self):
        # Note: Out of range will not necessarily raise any error, instead it will indicate +inf etc.
        for numberOfRegisters in [0, 1, 3, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, minimalmodbus._floatToBytestring, 1.1, numberOfRegisters)

    def testWrongInputType(self):
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, minimalmodbus._floatToBytestring, value, 2)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._floatToBytestring, 1.1,   value)


class TestBytestringToFloat(ExtendedTestCase):

    knownValues=TestFloatToBytestring.knownValues

    def testKnownValues(self):
        for knownvalue, numberOfRegisters, bytestring in self.knownValues:
            resultvalue = minimalmodbus._bytestringToFloat(bytestring, numberOfRegisters)
            self.assertAlmostEqualRatio(resultvalue, knownvalue)

    def testWrongInputValue(self):
        for bytestring in ['', 'A', 'AB', 'ABC', 'ABCDE', 'ABCDEF', 'ABCDEFG']:
            self.assertRaises(ValueError, minimalmodbus._bytestringToFloat, bytestring, 2)
            self.assertRaises(ValueError, minimalmodbus._bytestringToFloat, bytestring, 4)
        for numberOfRegisters in [0, 1, 3, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, minimalmodbus._bytestringToFloat, 'ABCD',     numberOfRegisters)
            self.assertRaises(ValueError, minimalmodbus._bytestringToFloat, 'ABCDEFGH', numberOfRegisters)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToFloat, value, 2)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToFloat, 1.1,   value)


class TestSanityFloat(ExtendedTestCase):

    knownValues=TestFloatToBytestring.knownValues

    def testSanity(self):
        for value, numberOfRegisters, knownstring in self.knownValues:
            resultvalue = minimalmodbus._bytestringToFloat( \
                minimalmodbus._floatToBytestring(value, numberOfRegisters), numberOfRegisters)
            self.assertAlmostEqualRatio(resultvalue, value)


class TestValuelistToBytestring(ExtendedTestCase):

    knownValues=[
    ([1],             1, '\x00\x01'),
    ([0, 0],          2, '\x00\x00\x00\x00'),
    ([1, 2],          2, '\x00\x01\x00\x02'),
    ([1, 256],        2, '\x00\x01\x01\x00'),
    ([1, 2, 3, 4],    4, '\x00\x01\x00\x02\x00\x03\x00\x04'),
    ([1, 2, 3, 4, 5], 5, '\x00\x01\x00\x02\x00\x03\x00\x04\x00\x05'),
    ]

    def testKnownValues(self):
        for value, numberOfRegisters, knownstring in self.knownValues:
            resultstring = minimalmodbus._valuelistToBytestring(value, numberOfRegisters)
            self.assertEqual(resultstring, knownstring)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._valuelistToBytestring, [1, 2, 3, 4], 1)
        self.assertRaises(ValueError, minimalmodbus._valuelistToBytestring, [1, 2, 3, 4], -4)

    def testWrongInputType(self):
        for value in _NOT_INTLISTS:
            self.assertRaises(TypeError, minimalmodbus._valuelistToBytestring, value,        4)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._valuelistToBytestring, [1, 2, 3, 4], value)


class TestBytestringToValuelist(ExtendedTestCase):

    knownValues=TestValuelistToBytestring.knownValues

    def testKnownValues(self):
        for knownlist, numberOfRegisters, bytestring in self.knownValues:
            resultlist = minimalmodbus._bytestringToValuelist(bytestring, numberOfRegisters)
            self.assertEqual(resultlist, knownlist)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._bytestringToValuelist, '\x00\x01\x00\x02', 1)
        self.assertRaises(ValueError, minimalmodbus._bytestringToValuelist, '',                 1)
        self.assertRaises(ValueError, minimalmodbus._bytestringToValuelist, '\x00\x01',         0)
        self.assertRaises(ValueError, minimalmodbus._bytestringToValuelist, '\x00\x01',         -1)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToValuelist, value, 1)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToValuelist, 'A',   value)


class TestSanityValuelist(ExtendedTestCase):

    knownValues=TestValuelistToBytestring.knownValues

    def testSanity(self):
        for valuelist, numberOfRegisters, bytestring in self.knownValues:
            resultlist = minimalmodbus._bytestringToValuelist( \
                minimalmodbus._valuelistToBytestring(valuelist, numberOfRegisters), numberOfRegisters)
            self.assertEqual(resultlist, valuelist)

class TestTextstringToBytestring(ExtendedTestCase):

    knownValues = [
        ('A',    1, 'A '),
        ('AB',   1, 'AB'),
        ('ABC',  2, 'ABC '),
        ('ABCD', 2, 'ABCD'),
        ('A',    16, 'A'+' '*31),
        ('A',    32, 'A'+' '*63),
        ]

    def testKnownValues(self):
        for textstring, numberOfRegisters, knownstring in self.knownValues:
            resultstring = minimalmodbus._textstringToBytestring(textstring, numberOfRegisters)
            self.assertEqual(resultstring, knownstring)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._textstringToBytestring, 'ABC', 1)
        self.assertRaises(ValueError, minimalmodbus._textstringToBytestring, '',    1)
        self.assertRaises(ValueError, minimalmodbus._textstringToBytestring, 'A',   -1)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._textstringToBytestring, value, 1)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._textstringToBytestring, 'AB',  value)


class TestBytestringToTextstring(ExtendedTestCase):

    knownValues=TestTextstringToBytestring.knownValues

    def testKnownValues(self):
        for knownstring, numberOfRegisters, bytestring in self.knownValues:
            resultstring = minimalmodbus._bytestringToTextstring(bytestring, numberOfRegisters)
            self.assertEqual(resultstring.strip(), knownstring)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, 'A',   1)
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, '',    1)
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, '',    0)
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, 'ABC', 1)
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, 'AB',  0)
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, 'AB',  -1)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToTextstring, value, 1)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToTextstring, 'AB',  value)


class TestSanityTextstring(ExtendedTestCase):

    knownValues=TestTextstringToBytestring.knownValues

    def testSanity(self):
        for textstring, numberOfRegisters, bytestring in self.knownValues:
            resultstring = minimalmodbus._bytestringToTextstring( \
                minimalmodbus._textstringToBytestring(textstring, numberOfRegisters), numberOfRegisters)
            self.assertEqual( resultstring.strip(), textstring )


class TestPack(ExtendedTestCase):

    knownValues=[        
        (-77,         '>h', '\xff\xb3'), # (Signed) short (2 bytes)
        (-1,          '>h', '\xff\xff'),
        (-770,        '>h', '\xfc\xfe'),
        (-32768,      '>h', '\x80\x00'),
        (32767,       '>h', '\x7f\xff'),
        (770,         '>H', '\x03\x02'), # Unsigned short (2 bytes)
        (65535,       '>H', '\xff\xff'),        
        (75000,       '>l', '\x00\x01\x24\xf8'),  # (Signed) long (4 bytes)
        (-1,          '>l',  '\xff\xff\xff\xff'),
        (-2147483648, '>l',  '\x80\x00\x00\x00'),
        (-200000000,  '>l',  '\xf4\x14\x3e\x00'),
        (1,           '>L', '\x00\x00\x00\x01'), # Unsigned long (4 bytes)
        (75000,       '>L', '\x00\x01\x24\xf8'),
        (2147483648,  '>L', '\x80\x00\x00\x00'),
        (2147483647,  '>L', '\x7f\xff\xff\xff'),
        (1.0,         '>f', '\x3f\x80\x00\x00'), # Float (4 bytes)
        (1.0e5,       '>f', '\x47\xc3\x50\x00'),
        (1.0e16,      '>f', '\x5a\x0e\x1b\xca'),
        (3.65e30,     '>f', '\x72\x38\x47\x25'),
        (-2,          '>f', '\xc0\x00\x00\x00'),
        (-3.6e30,     '>f', '\xf2\x35\xc0\xe9'),
        (1.0,         '>d', '\x3f\xf0\x00\x00\x00\x00\x00\x00'), # Double (8 bytes)
        (2,           '>d', '\x40\x00\x00\x00\x00\x00\x00\x00'),
        (1.1e9,       '>d', '\x41\xd0\x64\x2a\xc0\x00\x00\x00'),
        (3.65e30,     '>d', '\x46\x47\x08\xe4\x9e\x2f\x4d\x62'),
        (2.42e300,    '>d', '\x7e\x4c\xe8\xa5\x67\x1f\x46\xa0'), 
        (-1.1,        '>d', '\xbf\xf1\x99\x99\x99\x99\x99\x9a'),
        (-2,          '>d', '\xc0\x00\x00\x00\x00\x00\x00\x00'),
        ]
    
    def testKnownValues(self):
        for value, formatstring, knownstring in self.knownValues:
            resultstring = minimalmodbus._pack(formatstring, value)
            self.assertEqual(resultstring, knownstring)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._pack, 'ABC',  35)
        self.assertRaises(ValueError, minimalmodbus._pack, '',     35)
        if _runTestsForNewVersion:  # For Python2.6 compatibility
            self.assertRaises(ValueError, minimalmodbus._pack, '>H',  -35)
            self.assertRaises(ValueError, minimalmodbus._pack, '>L',  -35)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._pack, value, 1)
        for value in ['1', ['1'], [1], ['\x00\x2d\x00\x58'], ['A', 'B', 'C'], 'ABC']:
            self.assertRaises(ValueError, minimalmodbus._pack, '>h',  value)
        

class TestUnpack(ExtendedTestCase):

    knownValues=TestPack.knownValues

    def testKnownValues(self):
        for knownvalue, formatstring, bytestring in self.knownValues:
            resultvalue = minimalmodbus._unpack(formatstring, bytestring)
            self.assertAlmostEqualRatio(resultvalue, knownvalue)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._unpack, 'ABC', '\xff\xb3')
        self.assertRaises(ValueError, minimalmodbus._unpack, '',    '\xff\xb3')
        self.assertRaises(ValueError, minimalmodbus._unpack, '>h',  '')

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._unpack, value, '\xff\xb3')
            self.assertRaises(TypeError, minimalmodbus._unpack, '>h',  value)


class TestSanityPackUnpack(ExtendedTestCase):

    knownValues=TestPack.knownValues

    def testSanity(self):
        for value, formatstring, bytestring in self.knownValues:
            resultstring = minimalmodbus._pack(formatstring, minimalmodbus._unpack(formatstring, bytestring))
            self.assertEqual(resultstring, bytestring)


class TestHexencode(ExtendedTestCase):

    knownValues=[     
        ('',        False, ''),   
        ('7',       False, '37'),
        ('J',       False, '4A'),
        ('\x5d',    False, '5D'),
        ('\x04',    False, '04'),
        ('\x04\x5d',False, '045D'),
        ('mn',      False, '6D6E'),
        ('Katt1',   False, '4B61747431'),
        ('',        True,  ''),   
        ('7',       True,  '37'),
        ('J',       True,  '4A'),
        ('\x5d',    True,  '5D'),
        ('\x04',    True,  '04'),
        ('\x04\x5d',True,  '04 5D'),
        ('mn',      True,  '6D 6E'),
        ('Katt1',   True,  '4B 61 74 74 31'),
        ]
    
    def testKnownValues(self):
        for value, insert_spaces, knownstring in self.knownValues:
            resultstring = minimalmodbus._hexencode(value, insert_spaces)
            self.assertEqual(resultstring, knownstring)

    def testWrongInputValue(self):
        pass
        
    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._hexencode, value)


class TestHexdecode(ExtendedTestCase):

    knownValues=TestHexencode.knownValues

    def testKnownValues(self):
        for knownstring, insert_spaces, value in self.knownValues:
            if not insert_spaces:
                resultstring = minimalmodbus._hexdecode(value)
                self.assertEqual(resultstring, knownstring)
            
        self.assertEqual(minimalmodbus._hexdecode('4A'), 'J')
        self.assertEqual(minimalmodbus._hexdecode('4a'), 'J')

    def testAllowLowercase(self):
        minimalmodbus._hexdecode('Aa')
        minimalmodbus._hexdecode('aa23')
        
    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._hexdecode, 'A')
        self.assertRaises(ValueError, minimalmodbus._hexdecode, 'AAA')
        self.assertRaises(TypeError, minimalmodbus._hexdecode, 'AG')
        
    def testWrongInputType(self):
        for value in _NOT_STRINGS:
                self.assertRaises(TypeError, minimalmodbus._hexdecode, value)


class TestSanityHexencodeHexdecode(ExtendedTestCase):

    knownValues=TestHexencode.knownValues

    def testKnownValues(self):
        for value, insert_spaces, knownstring in self.knownValues:
            if not insert_spaces:
                resultstring = minimalmodbus._hexdecode(minimalmodbus._hexencode(value))
                self.assertEqual(resultstring, value)

    def testKnownValuesLoop(self):
        """Loop through all bytestrings of length two."""
        if ALSO_TIME_CONSUMING_TESTS:
            RANGE_VALUE = 256
            for i in range(RANGE_VALUE):
                for j in range(RANGE_VALUE):
                    bytestring = chr(i) + chr(j)
                    resultstring = minimalmodbus._hexdecode(minimalmodbus._hexencode(bytestring))
                    self.assertEqual(resultstring, bytestring)


class TestBitResponseToValue(ExtendedTestCase):

    def testKnownValues(self):
        self.assertEqual(minimalmodbus._bitResponseToValue('\x00'), 0)
        self.assertEqual(minimalmodbus._bitResponseToValue('\x01'), 1)

    def testWrongValues(self):
        self.assertRaises(ValueError, minimalmodbus._bitResponseToValue, 'ABC')   # Too long string
        self.assertRaises(ValueError, minimalmodbus._bitResponseToValue, 'A')     # Wrong string
        self.assertRaises(ValueError, minimalmodbus._bitResponseToValue, '\x03')  # Wrong string

    def testWrongType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._bitResponseToValue, value)


class TestCreateBitPattern(ExtendedTestCase):

    knownValues=[
    (5,  0, '\x00\x00'),
    (5,  1, '\xff\x00' ),
    (15, 0, '\x00'),
    (15, 1, '\x01'),
    ]

    def testKnownValues(self):
        for functioncode, value, knownresult in self.knownValues:
            resultvalue = minimalmodbus._createBitpattern(functioncode, value)
            self.assertEqual(resultvalue, knownresult)

    def testWrongFunctionCode(self):
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 16,  1)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, -1,  1)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 128, 1)

    def testFunctionCodeNotInteger(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._createBitpattern, value, 1)

    def testWrongValue(self):
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 5,  2)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 5,  222)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 5,  -1)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 15, 2)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 15, 222)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 15, -1)

    def testValueNotInteger(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._createBitpattern, 5,  value)
            self.assertRaises(TypeError, minimalmodbus._createBitpattern, 15, value)


############################
# Test number manipulation #
############################

class TestTwosComplement(ExtendedTestCase):

    knownValues=[
    (0,       8, 0),
    (1,       8, 1),
    (127,     8, 127),
    (-128,    8, 128),
    (-127,    8, 129),
    (-1,      8, 255),
    (0,      16, 0),
    (1,      16, 1),
    (32767,  16, 32767),
    (-32768, 16, 32768),
    (-32767, 16, 32769),
    (-1,     16, 65535),
    ]

    def testKnownValues(self):
        for x, bits, knownresult in self.knownValues:

            result = minimalmodbus._twosComplement(x, bits)
            self.assertEqual(result, knownresult)

    def testOutOfRange(self):
        self.assertRaises(ValueError, minimalmodbus._twosComplement, 128,     8)
        self.assertRaises(ValueError, minimalmodbus._twosComplement, 1000000, 8)
        self.assertRaises(ValueError, minimalmodbus._twosComplement, -129,    8)
        self.assertRaises(ValueError, minimalmodbus._twosComplement, 32768,   16)
        self.assertRaises(ValueError, minimalmodbus._twosComplement, 1000000, 16)
        self.assertRaises(ValueError, minimalmodbus._twosComplement, -32769,  16)
        self.assertRaises(ValueError, minimalmodbus._twosComplement, 1,       0)
        self.assertRaises(ValueError, minimalmodbus._twosComplement, 1,       -1)
        self.assertRaises(ValueError, minimalmodbus._twosComplement, 1,       -2)
        self.assertRaises(ValueError, minimalmodbus._twosComplement, 1,       -100)

    def testWrongInputType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._twosComplement, value, 8)

class TestFromTwosComplement(ExtendedTestCase):

    knownValues=TestTwosComplement.knownValues

    def testKnownValues(self):
        for knownresult, bits, x in self.knownValues:

            result = minimalmodbus._fromTwosComplement(x, bits)
            self.assertEqual(result, knownresult)

    def testOutOfRange(self):
        self.assertRaises(ValueError, minimalmodbus._fromTwosComplement, 256,     8)
        self.assertRaises(ValueError, minimalmodbus._fromTwosComplement, 1000000, 8)
        self.assertRaises(ValueError, minimalmodbus._fromTwosComplement, -1,      8)
        self.assertRaises(ValueError, minimalmodbus._fromTwosComplement, 65536,   16)
        self.assertRaises(ValueError, minimalmodbus._fromTwosComplement, 1000000, 16)
        self.assertRaises(ValueError, minimalmodbus._fromTwosComplement, -1,      16)
        self.assertRaises(ValueError, minimalmodbus._fromTwosComplement, 1,       0)
        self.assertRaises(ValueError, minimalmodbus._fromTwosComplement, 1,       -1)
        self.assertRaises(ValueError, minimalmodbus._fromTwosComplement, 1,       -2)
        self.assertRaises(ValueError, minimalmodbus._fromTwosComplement, 1,       -100)

    def testWrongInputType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._fromTwosComplement, value, 8)
            self.assertRaises(TypeError, minimalmodbus._fromTwosComplement, 1,     value)

class TestSanityTwosComplement(ExtendedTestCase):

    knownValues = [1, 2, 4, 8, 12, 16]

    def testSanity(self):

        if ALSO_TIME_CONSUMING_TESTS:
            for bits in self.knownValues:
                for x in range(2**bits):
                    resultvalue = minimalmodbus._twosComplement( minimalmodbus._fromTwosComplement(x, bits), bits )
                    self.assertEqual(resultvalue, x)


#########################
# Test bit manipulation #
#########################

class TestSetBitOn(ExtendedTestCase):

    knownValues=[
    (4,0,5),
    (4,1,6),
    (1,1,3),
    ]

    def testKnownValues(self):
        for x, bitnum, knownresult in self.knownValues:

            result = minimalmodbus._setBitOn(x, bitnum)
            self.assertEqual(result, knownresult)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._setBitOn, 1,  -1)
        self.assertRaises(ValueError, minimalmodbus._setBitOn, -2, 1)

    def testWrongInputType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._setBitOn, value, 1)
            self.assertRaises(TypeError, minimalmodbus._setBitOn, 1,     value)

############################
# Error checking functions #
############################

class TestCalculateCrcString(ExtendedTestCase):

    knownValues=[
    ('\x02\x07','\x41\x12'), # Example from MODBUS over Serial Line Specification and Implementation Guide V1.02
    ('ABCDE', '\x0fP'),
    ]

    def testKnownValues(self):
        for inputstring, knownresult in self.knownValues:
            resultstring  = minimalmodbus._calculateCrcString(inputstring)
            self.assertEqual(resultstring, knownresult)

    def testCalculationTime(self):
        teststrings = [minimalmodbus._numToTwoByteString(i) for i in range(2**16)]
        minimalmodbus._print_out("\n\n   Measuring CRC calculation time. Running {} calculations ...".format(
                                    len(teststrings)))
        start_time = time.time()
        for teststring in teststrings:
            minimalmodbus._calculateCrcString(teststring)
        calculation_time = time.time() - start_time
        minimalmodbus._print_out("CRC calculation time: {} calculations took {:.3f} s ({} s per calculation)\n\n".format(
                                    len(teststrings), calculation_time, calculation_time/float(len(teststrings))))

    def testNotStringInput(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._calculateCrcString, value)
            
            
class TestCalculateLrcString(ExtendedTestCase):

    knownValues=[
    ('ABCDE', '\xb1'),
    ('\x02\x30\x30\x31\x23\x03','\x47'), # From C# example on http://en.wikipedia.org/wiki/Longitudinal_redundancy_check
    ]

    def testKnownValues(self):
        for inputstring, knownresult in self.knownValues:
            resultstring = minimalmodbus._calculateLrcString(inputstring)
            self.assertEqual(resultstring, knownresult)

    def testNotStringInput(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._calculateLrcString, value)


class TestCheckFunctioncode(ExtendedTestCase):

    def testCorrectFunctioncode(self):
        minimalmodbus._checkFunctioncode( 4, [4, 5] )

    def testCorrectFunctioncodeNoRange(self):
        minimalmodbus._checkFunctioncode( 4, None )
        minimalmodbus._checkFunctioncode( 75, None )

    def testWrongFunctioncode(self):
        self.assertRaises(ValueError, minimalmodbus._checkFunctioncode, 3, [4, 5])
        self.assertRaises(ValueError, minimalmodbus._checkFunctioncode, 3, [])

    def testWrongFunctioncodeNoRange(self):
        self.assertRaises(ValueError, minimalmodbus._checkFunctioncode, 1000, None)
        self.assertRaises(ValueError, minimalmodbus._checkFunctioncode, -1, None)

    def testWrongFunctioncodeType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._checkFunctioncode, value, [4, 5])

    def testWrongFunctioncodeListValues(self):
        self.assertRaises(ValueError, minimalmodbus._checkFunctioncode, -1, [-1, 5])
        self.assertRaises(ValueError, minimalmodbus._checkFunctioncode, 128, [4, 128])

    def testWrongListType(self):
        self.assertRaises(TypeError,  minimalmodbus._checkFunctioncode, 4, 4)
        self.assertRaises(TypeError,  minimalmodbus._checkFunctioncode, 4, 'ABC')
        self.assertRaises(TypeError,  minimalmodbus._checkFunctioncode, 4, (4, 5))
        self.assertRaises(ValueError, minimalmodbus._checkFunctioncode, 4, [4, -23])
        self.assertRaises(ValueError, minimalmodbus._checkFunctioncode, 4, [4, 128])
        self.assertRaises(TypeError,  minimalmodbus._checkFunctioncode, 4, [4, '5'])
        self.assertRaises(TypeError,  minimalmodbus._checkFunctioncode, 4, [4, None])
        self.assertRaises(TypeError,  minimalmodbus._checkFunctioncode, 4, [4, [5]])
        self.assertRaises(TypeError,  minimalmodbus._checkFunctioncode, 4, [4.0, 5])


class TestCheckSlaveaddress(ExtendedTestCase):

    def testKnownValues(self):
        minimalmodbus._checkSlaveaddress( 0 )
        minimalmodbus._checkSlaveaddress( 1 )
        minimalmodbus._checkSlaveaddress( 10 )
        minimalmodbus._checkSlaveaddress( 247 )

    def testWrongValues(self):
        self.assertRaises(ValueError, minimalmodbus._checkSlaveaddress, -1)
        self.assertRaises(ValueError, minimalmodbus._checkSlaveaddress, 248)

    def testNotIntegerInput(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._checkSlaveaddress, value)


class TestCheckMode(ExtendedTestCase):

    def testKnownValues(self):
        minimalmodbus._checkMode('ascii')
        minimalmodbus._checkMode('rtu')

    def testWrongValues(self):
        self.assertRaises(ValueError, minimalmodbus._checkMode, 'asc')
        self.assertRaises(ValueError, minimalmodbus._checkMode, 'ASCII')
        self.assertRaises(ValueError, minimalmodbus._checkMode, 'RTU')
        self.assertRaises(ValueError, minimalmodbus._checkMode, '')
        self.assertRaises(ValueError, minimalmodbus._checkMode, 'ascii ')
        self.assertRaises(ValueError, minimalmodbus._checkMode, ' rtu')

    def testNotIntegerInput(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkMode, value)


class TestCheckRegisteraddress(ExtendedTestCase):

    def testKnownValues(self):
        minimalmodbus._checkRegisteraddress( 0 )
        minimalmodbus._checkRegisteraddress( 1 )
        minimalmodbus._checkRegisteraddress( 10 )
        minimalmodbus._checkRegisteraddress( 65535 )

    def testWrongValues(self):
        self.assertRaises(ValueError, minimalmodbus._checkRegisteraddress, -1)
        self.assertRaises(ValueError, minimalmodbus._checkRegisteraddress, 65536)

    def testWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._checkRegisteraddress, value)


class TestCheckResponseNumberOfBytes(ExtendedTestCase):

    def testCorrectNumberOfBytes(self):
        minimalmodbus._checkResponseByteCount('\x02\x03\x02')

    def testWrongNumberOfBytes(self):
        self.assertRaises(ValueError, minimalmodbus._checkResponseByteCount, '\x03\x03\x02')
        self.assertRaises(ValueError, minimalmodbus._checkResponseByteCount, 'ABC')

    def testNotStringInput(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkResponseByteCount, value)


class TestCheckResponseRegisterAddress(ExtendedTestCase):

    def testCorrectResponseRegisterAddress(self):
        minimalmodbus._checkResponseRegisterAddress( '\x00\x2d\x00\x58', 45)
        minimalmodbus._checkResponseRegisterAddress( '\x00\x18\x00\x01', 24)
        minimalmodbus._checkResponseRegisterAddress( '\x00\x47\xff\x00', 71)
        minimalmodbus._checkResponseRegisterAddress( '\x00\x48\x00\x01', 72)

    def testWrongResponseRegisterAddress(self):
        self.assertRaises(ValueError, minimalmodbus._checkResponseRegisterAddress, '\x00\x2d\x00\x58', 46)

    def testTooShortString(self):
        self.assertRaises(ValueError, minimalmodbus._checkResponseRegisterAddress, '\x00', 46)

    def testNotString(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkResponseRegisterAddress, value, 45)

    def testWrongAddress(self):
        self.assertRaises(ValueError, minimalmodbus._checkResponseRegisterAddress, '\x00\x2d\x00\x58', -2)
        self.assertRaises(ValueError, minimalmodbus._checkResponseRegisterAddress, '\x00\x2d\x00\x58', 65536)

    def testAddressNotInteger(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._checkResponseRegisterAddress, '\x00\x2d\x00\x58', value)


class TestCheckResponseNumberOfRegisters(ExtendedTestCase):

    def testCorrectResponseNumberOfRegisters(self):
        minimalmodbus._checkResponseNumberOfRegisters( '\x00\x18\x00\x01', 1 )
        minimalmodbus._checkResponseNumberOfRegisters( '\x00#\x00\x01',    1 )
        minimalmodbus._checkResponseNumberOfRegisters( '\x00\x34\x00\x02', 2 )

    def testWrongResponseNumberOfRegisters(self):
        self.assertRaises(ValueError, minimalmodbus._checkResponseNumberOfRegisters, '\x00#\x00\x01', 4 )

    def testTooShortString(self):
        self.assertRaises(ValueError, minimalmodbus._checkResponseNumberOfRegisters, '\x00', 1 )

    def testNotString(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkResponseNumberOfRegisters, value, 1 )

    def testWrongResponseNumberOfRegistersRange(self):
        self.assertRaises(ValueError, minimalmodbus._checkResponseNumberOfRegisters, '\x00\x18\x00\x00', 0 )
        self.assertRaises(ValueError, minimalmodbus._checkResponseNumberOfRegisters, '\x00\x18\x00\x01', -1 )
        self.assertRaises(ValueError, minimalmodbus._checkResponseNumberOfRegisters, '\x00\x18\x00\x01', 65536 )

    def testNumberOfRegistersNotInteger(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._checkResponseNumberOfRegisters, '\x00\x18\x00\x01', value )


class TestCheckResponseWriteData(ExtendedTestCase):

    def testCorrectResponseWritedata(self):
        minimalmodbus._checkResponseWriteData('\x00\x2d\x00\x58', '\x00\x58')
        minimalmodbus._checkResponseWriteData('\x00\x2d\x00\x58', minimalmodbus._numToTwoByteString(88))
        minimalmodbus._checkResponseWriteData('\x00\x47\xff\x00', '\xff\x00')
        minimalmodbus._checkResponseWriteData('\x00\x47\xff\x00', minimalmodbus._numToTwoByteString(65280))
        minimalmodbus._checkResponseWriteData('\x00\x2d\x00\x58ABCDEFGHIJKLMNOP', '\x00\x58')

    def testWrongResponseWritedata(self):
        self.assertRaises(ValueError, minimalmodbus._checkResponseWriteData, '\x00\x2d\x00\x58', '\x00\x59')
        self.assertRaises(ValueError, minimalmodbus._checkResponseWriteData, '\x00\x2d\x00\x58', minimalmodbus._numToTwoByteString(89))
        self.assertRaises(ValueError, minimalmodbus._checkResponseWriteData, '\x00\x47\xff\x00', '\xff\x01')

    def testNotString(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkResponseWriteData, value, '\x00\x58')
            self.assertRaises(TypeError, minimalmodbus._checkResponseWriteData, '\x00\x2d\x00\x58', value)

    def testTooShortString(self):
        self.assertRaises(ValueError, minimalmodbus._checkResponseWriteData, '\x00\x58', '\x00\x58')
        self.assertRaises(ValueError, minimalmodbus._checkResponseWriteData, '', '\x00\x58')
        self.assertRaises(ValueError, minimalmodbus._checkResponseWriteData, '\x00\x2d\x00\x58', '\x58')
        self.assertRaises(ValueError, minimalmodbus._checkResponseWriteData, '\x00\x2d\x00\x58', '')

    def testTooLongString(self):
        self.assertRaises(ValueError, minimalmodbus._checkResponseWriteData, '\x00\x2d\x00\x58', '\x00\x58\x00')


class TestCheckString(ExtendedTestCase):

    def testKnownValues(self):
        minimalmodbus._checkString('DEF', minlength=3, maxlength=3, description='ABC' )
        minimalmodbus._checkString('DEF', minlength=0, maxlength=100, description='ABC' )

    def testTooShort(self):
        self.assertRaises(ValueError, minimalmodbus._checkString, 'DE',  minlength=3,  maxlength=3, description='ABC')
        self.assertRaises(ValueError, minimalmodbus._checkString, 'DEF', minlength=10, maxlength=3, description='ABC')

    def testTooLong(self):
        self.assertRaises(ValueError, minimalmodbus._checkString, 'DEFG', minlength=1, maxlength=3, description='ABC')

    def testInconsistentLengthlimits(self):
        self.assertRaises(ValueError, minimalmodbus._checkString, 'DEFG', minlength=4,  maxlength=3, description='ABC')
        self.assertRaises(ValueError, minimalmodbus._checkString, 'DEF',  minlength=-3, maxlength=3, description='ABC')
        self.assertRaises(ValueError, minimalmodbus._checkString, 'DEF',  minlength=3,  maxlength=-3, description='ABC')

    def testInputNotString(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkString, value,    minlength=3, maxlength=3, description='ABC')

    def testNotIntegerInput(self):
        for value in _NOT_INTERGERS_OR_NONE:
            self.assertRaises(TypeError, minimalmodbus._checkString, 'DEF', minlength=value, maxlength=3,     description='ABC')
            self.assertRaises(TypeError, minimalmodbus._checkString, 'DEF', minlength=3,     maxlength=value, description='ABC')

    def testDescriptionNotString(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkString, 'DEF', minlength=3, maxlength=3, description=value)


class TestCheckInt(ExtendedTestCase):

    def testKnownValues(self):
        minimalmodbus._checkInt(47, minvalue=None,  maxvalue=None, description='ABC')
        minimalmodbus._checkInt(47, minvalue=40,    maxvalue=50, description='ABC')
        minimalmodbus._checkInt(47, minvalue=-40,   maxvalue=50, description='ABC')
        minimalmodbus._checkInt(47, description='ABC', maxvalue=50, minvalue=40)
        minimalmodbus._checkInt(47, minvalue=None,  maxvalue=50, description='ABC')
        minimalmodbus._checkInt(47, minvalue=40,     maxvalue=None, description='ABC')

    def testTooLargeValue(self):
        self.assertRaises(ValueError, minimalmodbus._checkInt, 47, minvalue=30, maxvalue=40, description='ABC')
        self.assertRaises(ValueError, minimalmodbus._checkInt, 47, maxvalue=46)

    def testTooSmallValue(self):
        self.assertRaises(ValueError, minimalmodbus._checkInt, 47, minvalue=48)
        self.assertRaises(ValueError, minimalmodbus._checkInt, 47, minvalue=48, maxvalue=None, description='ABC')

    def testInconsistentLimits(self):
        self.assertRaises(ValueError, minimalmodbus._checkInt, 47, minvalue=47, maxvalue=45, description='ABC')

    def testWrongInputType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._checkInt, value, minvalue=40)
        for value in _NOT_INTERGERS_OR_NONE:
            self.assertRaises(TypeError, minimalmodbus._checkInt, 47,    minvalue=value, maxvalue=50,    description='ABC')
            self.assertRaises(TypeError, minimalmodbus._checkInt, 47,    minvalue=40,    maxvalue=value, description='ABC')
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkInt, 47,    minvalue=40,    maxvalue=50,    description=value)


class TestCheckNumerical(ExtendedTestCase):

    def testKnownValues(self):
        minimalmodbus._checkNumerical(47, minvalue=None, maxvalue=None, description='ABC')
        minimalmodbus._checkNumerical(47, minvalue=40, maxvalue=50, description='ABC')
        minimalmodbus._checkNumerical(47, minvalue=-40, maxvalue=50, description='ABC')
        minimalmodbus._checkNumerical(47, description='ABC', maxvalue=50, minvalue=40)
        minimalmodbus._checkNumerical(47, minvalue=None, maxvalue=50, description='ABC')
        minimalmodbus._checkNumerical(47, minvalue=40, maxvalue=None, description='ABC')
        minimalmodbus._checkNumerical(47.0, minvalue=40)
        minimalmodbus._checkNumerical(47, minvalue=40.0, maxvalue=50, description='ABC')
        minimalmodbus._checkNumerical(47.0, minvalue=40, maxvalue=None, description='ABC' )
        minimalmodbus._checkNumerical(47.0, minvalue=40.0, maxvalue=50.0, description='ABC' )

    def testTooLargeValue(self):
        self.assertRaises(ValueError, minimalmodbus._checkNumerical, 47.0, minvalue=30, maxvalue=40, description='ABC')
        self.assertRaises(ValueError, minimalmodbus._checkNumerical, 47.0, minvalue=30.0, maxvalue=40.0, description='ABC')
        self.assertRaises(ValueError, minimalmodbus._checkNumerical, 47, maxvalue=46.0)
        self.assertRaises(ValueError, minimalmodbus._checkNumerical, 47.0, maxvalue=46.0)
        self.assertRaises(ValueError, minimalmodbus._checkNumerical, 47.0, maxvalue=46)

    def testTooSmallValue(self):
        self.assertRaises(ValueError, minimalmodbus._checkNumerical, 47.0, minvalue=48)
        self.assertRaises(ValueError, minimalmodbus._checkNumerical, 47.0, minvalue=48.0)
        self.assertRaises(ValueError, minimalmodbus._checkNumerical, 47, minvalue=48.0)
        self.assertRaises(ValueError, minimalmodbus._checkNumerical, 47, minvalue=48, maxvalue=None, description='ABC')

    def testInconsistentLimits(self):
        self.assertRaises(ValueError, minimalmodbus._checkNumerical, 47, minvalue=47, maxvalue=45, description='ABC')
        self.assertRaises(ValueError, minimalmodbus._checkNumerical, 47.0, minvalue=47.0, maxvalue=45.0, description='ABC')

    def testNotNumericInput(self):
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, minimalmodbus._checkNumerical, value, minvalue=40.0)
        for value in _NOT_NUMERICALS_OR_NONE:
            self.assertRaises(TypeError, minimalmodbus._checkNumerical, 47.0,  minvalue=value, maxvalue=50.0,  description='ABC')
            self.assertRaises(TypeError, minimalmodbus._checkNumerical, 47.0,  minvalue=40.0,  maxvalue=value, description='ABC')

    def testDescriptionNotString(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkNumerical, 47.0, minvalue=40, maxvalue=50, description=value)


class TestCheckBool(ExtendedTestCase):

    def testKnownValues(self):
        minimalmodbus._checkBool(True, description='ABC')
        minimalmodbus._checkBool(False, description='ABC')

    def testWrongType(self):
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, minimalmodbus._checkBool, value, description='ABC')
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkBool, True, description=value)


#####################
# Development tools #
#####################

class TestGetDiagnosticString(ExtendedTestCase):

    def testReturnsString(self):

        resultstring = minimalmodbus._getDiagnosticString()
        self.assertTrue( len(resultstring) > 100) # For Python 2.6 compatibility

class TestPrintOut(ExtendedTestCase):

    def testKnownValues(self):
        minimalmodbus._print_out('ABCDEFGHIJKL')

    def testInputNotString(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._print_out, value)


# TODO: TestInterpretRawMessage

# TODO: TestInterpretPayload

###########################################
# Communication using a dummy serial port #
###########################################

class TestDummyCommunication(ExtendedTestCase):


    ## Test fixture ##

    def setUp(self):

        # Prepare a dummy serial port to have proper responses
        dummy_serial.VERBOSE = False 
        dummy_serial.RESPONSES = RTU_RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'
        dummy_serial.DEFAULT_TIMEOUT = 0.01

        # Monkey-patch a dummy serial port for testing purpose
        minimalmodbus.serial.Serial = dummy_serial.Serial

        # Initialize a (dummy) instrument
        minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = False
        self.instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 1, minimalmodbus.MODE_RTU) # port name, slave address (in decimal)
        self.instrument.debug = False


    ## Read bit ##

    def testReadBit(self):
        self.assertEqual( self.instrument.read_bit(61),                 1 ) # Functioncode 2
        self.assertEqual( self.instrument.read_bit(61, functioncode=2), 1 )
        self.assertEqual( self.instrument.read_bit(61, 2),              1 )
        self.assertEqual( self.instrument.read_bit(62, functioncode=1), 0 ) # Functioncode 1
        self.assertEqual( self.instrument.read_bit(62, 1),              0 )

    def testReadBitWrongValue(self):
        self.assertRaises(ValueError, self.instrument.read_bit, -1) # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_bit, 65536)
        self.assertRaises(ValueError, self.instrument.read_bit, 62,   0) # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_bit, 62,   -1)
        self.assertRaises(ValueError, self.instrument.read_bit, 62,   128)

    def testReadBitWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_bit, value)
            self.assertRaises(TypeError, self.instrument.read_bit, 62,   value)

    def testReadBitWithWrongByteCountResponse(self):
        self.assertRaises(ValueError, self.instrument.read_bit, 63) # Functioncode 2. Slave gives wrong byte count.

    def testReadBitWithNoResponse(self):
        self.assertRaises(IOError, self.instrument.read_bit, 64) # Functioncode 2. Slave gives no response.


    ## Write bit ##

    def testWriteBit(self):
        self.instrument.write_bit(71, 1)
        self.instrument.write_bit(71, 1, 5)
        self.instrument.write_bit(71, 1, functioncode=5)
        self.instrument.write_bit(72, 1, 15)
        self.instrument.write_bit(72, 1, functioncode=15)

    def testWriteBitWrongValue(self):
        self.assertRaises(ValueError, self.instrument.write_bit, 65536, 1) # Wrong register address
        self.assertRaises(ValueError, self.instrument.write_bit, -1,    1)
        self.assertRaises(ValueError, self.instrument.write_bit, 71,    10) # Wrong bit value
        self.assertRaises(ValueError, self.instrument.write_bit, 71,    -5)
        self.assertRaises(ValueError, self.instrument.write_bit, 71,    10, 5)
        self.assertRaises(ValueError, self.instrument.write_bit, 71,    1,  6) # Wrong function code
        self.assertRaises(ValueError, self.instrument.write_bit, 71,    1,  -1)
        self.assertRaises(ValueError, self.instrument.write_bit, 71,    1,  0)
        self.assertRaises(ValueError, self.instrument.write_bit, 71,    1,  128)

    def testWriteBitWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_bit, value, 1)
            self.assertRaises(TypeError, self.instrument.write_bit, 71,    value)
            self.assertRaises(TypeError, self.instrument.write_bit, 71,    1,     value)

    def testWriteBitWithWrongRegisternumbersResponse(self):
        self.assertRaises(ValueError, self.instrument.write_bit, 73, 1, functioncode=15) # Slave gives wrong number of registers

    def testWriteBitWithWrongWritedataResponse(self):
        self.assertRaises(ValueError, self.instrument.write_bit, 74, 1) # Slave gives wrong write data


    ## Read register ##

    def testReadRegister(self):
        self.assertEqual(       self.instrument.read_register(289),              770)
        self.assertEqual(       self.instrument.read_register(5),                184)
        self.assertEqual(       self.instrument.read_register(289, 0),           770)
        self.assertEqual(       self.instrument.read_register(289, 0, 3),        770) # functioncode 3
        self.assertEqual(       self.instrument.read_register(14,  0, 4),        880) # functioncode 4
        self.assertAlmostEqual( self.instrument.read_register(289, 1),           77.0)
        self.assertAlmostEqual( self.instrument.read_register(289, 2),           7.7)
        self.assertEqual(       self.instrument.read_register(101),              65531) 
        self.assertEqual(       self.instrument.read_register(101, signed=True), -5) 

    def testReadRegisterWrongValue(self):
        self.assertRaises(ValueError, self.instrument.read_register, -1) # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_register, -1,   0,  3)
        self.assertRaises(ValueError, self.instrument.read_register, 65536)
        self.assertRaises(ValueError, self.instrument.read_register, 289,  -1)    # Wrong number of decimals
        self.assertRaises(ValueError, self.instrument.read_register, 289,  100)
        self.assertRaises(ValueError, self.instrument.read_register, 289,  0,  5) # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_register, 289,  0,  -4)

    def testReadRegisterWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_register, value, 0,    3)
            self.assertRaises(TypeError, self.instrument.read_register, 289,   value)
            self.assertRaises(TypeError, self.instrument.read_register, 289,   0,    value)


    ## Write register ##

    def testWriteRegister(self):
        self.instrument.write_register(35, 20)
        self.instrument.write_register(35, 20, functioncode = 16)
        self.instrument.write_register(35, 20.0)
        self.instrument.write_register(24, 50)
        self.instrument.write_register(45, 88, functioncode = 6)
        self.instrument.write_register(101, 5) 
        self.instrument.write_register(101, 5, signed=True) 
        self.instrument.write_register(101, 5, 1) 
        self.instrument.write_register(101, -5, signed=True)  
        self.instrument.write_register(101, -5, 1, signed=True) 

    def testWriteRegisterWithDecimals(self):
        self.instrument.write_register(35, 2.0, 1)
        self.instrument.write_register(45, 8.8, 1, functioncode = 6)

    def testWriteRegisterWrongValue(self):
        self.assertRaises(ValueError, self.instrument.write_register, -1,    20) # Wrong address
        self.assertRaises(ValueError, self.instrument.write_register, 65536, 20)
        self.assertRaises(ValueError, self.instrument.write_register, 35,    -1)  # Wrong register value
        self.assertRaises(ValueError, self.instrument.write_register, 35,    65536)
        self.assertRaises(ValueError, self.instrument.write_register, 35,    20, -1) # Wrong number of decimals
        self.assertRaises(ValueError, self.instrument.write_register, 35,    20, 100)
        self.assertRaises(ValueError, self.instrument.write_register, 35,    20,     functioncode = 12 ) # Wrong function code
        self.assertRaises(ValueError, self.instrument.write_register, 35,    20,     functioncode = -4 )
        self.assertRaises(ValueError, self.instrument.write_register, 35,    20,     functioncode = 129 )

    def testWriteRegisterWrongType(self):
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, self.instrument.write_register, value, 20)
            self.assertRaises(TypeError, self.instrument.write_register, 35,    value)
            self.assertRaises(TypeError, self.instrument.write_register, 35,    20,    value)
            self.assertRaises(TypeError, self.instrument.write_register, 35,    20,    functioncode = value)

    def testWriteRegisterWithWrongCrcResponse(self):
        self.assertRaises(ValueError, self.instrument.write_register, 51, 99) # Slave gives wrong CRC
        
    def testWriteRegisterSuppressErrorMessageAtWrongCRC(self):
        try:
            self.instrument.write_register(51, 99) # Slave gives wrong CRC
        except ValueError:
            minimalmodbus._print_out('Minimalmodbus: An error was suppressed.')

    def testWriteRegisterWithWrongSlaveaddressResponse(self):
        self.assertRaises(ValueError, self.instrument.write_register, 54, 99) # Slave gives wrong slaveaddress

    def testWriteRegisterWithWrongFunctioncodeResponse(self):
        self.assertRaises(ValueError, self.instrument.write_register, 55, 99) # Slave gives wrong functioncode
        self.assertRaises(ValueError, self.instrument.write_register, 56, 99) # Slave indicates an error

    def testWriteRegisterWithWrongRegisteraddressResponse(self):
        self.assertRaises(ValueError, self.instrument.write_register, 53, 99) # Slave gives wrong registeraddress

    def testWriteRegisterWithWrongRegisternumbersResponse(self):
        self.assertRaises(ValueError, self.instrument.write_register, 52, 99) # Slave gives wrong number of registers

    def testWriteRegisterWithWrongWritedataResponse(self):
        self.assertRaises(ValueError, self.instrument.write_register, 55, 99, functioncode = 6) # Functioncode 6. Slave gives wrong write data.


    ## Read Long ##
    
    def testReadLong(self):
        self.assertEqual( self.instrument.read_long(102),              4294967295)
        self.assertEqual( self.instrument.read_long(102, signed=True), -1)

    def testReadLongWrongValue(self):
        self.assertRaises(ValueError, self.instrument.read_long, -1) # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_long, 65536)
        self.assertRaises(ValueError, self.instrument.read_long, 102,  1)  # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_long, 102,  -1)  
        self.assertRaises(ValueError, self.instrument.read_long, 102,  256)  

    def testReadLongWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_long, value)
            self.assertRaises(TypeError, self.instrument.read_long, 102,   value)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, self.instrument.read_long, 102,   signed=value)


    ## Write Long ##

    def testWriteLong(self):
        self.instrument.write_long(102, 5)
        self.instrument.write_long(102, 5,  signed=True)
        self.instrument.write_long(102, -5, signed=True)
        self.instrument.write_long(102, 3,  False)
        self.instrument.write_long(102, -3, True)

    def testWriteLongWrongValue(self):
        self.assertRaises(ValueError, self.instrument.write_long, -1,    5) # Wrong register address
        self.assertRaises(ValueError, self.instrument.write_long, 65536, 5)
        self.assertRaises(ValueError, self.instrument.write_long, 102,   888888888888888888888)  # Wrong value to write to slave
        if _runTestsForNewVersion:  # For Python2.6 compatibility
            self.assertRaises(ValueError, self.instrument.write_long, 102,   -5, signed=False)  # Wrong value to write to slave

    def testWriteLongWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_long, value, 5)
            self.assertRaises(TypeError, self.instrument.write_long, 102,   value)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, self.instrument.write_long, 102,   5,     signed=value)
            

    ## Read Float ##

    def testReadFloat(self):
        self.assertEqual( self.instrument.read_float(103),       1.0 )
        self.assertEqual( self.instrument.read_float(103, 3),    1.0 )
        self.assertEqual( self.instrument.read_float(103, 3, 2), 1.0 )
        self.assertEqual( self.instrument.read_float(103, 3, 4), -2.0 )
        self.assertAlmostEqualRatio( self.instrument.read_float(103, 4, 2), 3.65e30 ) # Function code 4
        
    def testReadFloatWrongValue(self):
        self.assertRaises(ValueError, self.instrument.read_float, -1) # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_float, -1,    3) 
        self.assertRaises(ValueError, self.instrument.read_float, -1,    3,  2) 
        self.assertRaises(ValueError, self.instrument.read_float, 65536)
        self.assertRaises(ValueError, self.instrument.read_float, 103,   1)  # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_float, 103,   -1)  
        self.assertRaises(ValueError, self.instrument.read_float, 103,   256)  
        for value in [-1, 0, 1, 3, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, self.instrument.read_float, 103, 3,  value) # Wrong number of registers

    def testReadFloatWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_float, value, 3,     2)
            self.assertRaises(TypeError, self.instrument.read_float, 103,   value, 2)
            self.assertRaises(TypeError, self.instrument.read_float, 103,   3,     value)


    ## Write Float ##

    def testWriteFloat(self):
        self.instrument.write_float(103, 1.1)
        self.instrument.write_float(103, 1.1, 4)

    def testWriteFloatWrongValue(self):
        self.assertRaises(ValueError, self.instrument.write_float, -1,     1.1) # Wrong register address
        self.assertRaises(ValueError, self.instrument.write_float, 65536,  1.1)
        for value in [-1, 0, 1, 3, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, self.instrument.write_float, 103, 1.1, value) # Wrong number of registers

    def testWriteFloatWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_float, value, 1.1)
            self.assertRaises(TypeError, self.instrument.write_float, 103,   1.1, value)
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, self.instrument.write_float, 103,   value)


    ## Read String ##

    def testReadString(self):
        self.assertEqual( self.instrument.read_string(104, 1),    'AB')
        self.assertEqual( self.instrument.read_string(104, 4),    'ABCDEFGH')
        self.assertEqual( self.instrument.read_string(104, 4, 3), 'ABCDEFGH')

    def testReadStringWrongValue(self):
        self.assertRaises(ValueError, self.instrument.read_string, -1) # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_string, 65536)
        self.assertRaises(ValueError, self.instrument.read_string, 104,  -1) # Wrong number of registers
        self.assertRaises(ValueError, self.instrument.read_string, 104,  256)
        self.assertRaises(ValueError, self.instrument.read_string, 104,  4,  1)  # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_string, 104,  4,  -1)
        self.assertRaises(ValueError, self.instrument.read_string, 104,  4,  256)

    def testReadStringWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_string, value, 1)
            self.assertRaises(TypeError, self.instrument.read_string, value, 4)
            self.assertRaises(TypeError, self.instrument.read_string, 104,   value)
            self.assertRaises(TypeError, self.instrument.read_string, 104,   4,     value)


    ## Write String ##

    def testWriteString(self):
        self.instrument.write_string(104, 'A', 1)
        self.instrument.write_string(104, 'A', 4)
        self.instrument.write_string(104, 'ABCDEFGH', 4)

    def testWriteStringWrongValue(self):
        self.assertRaises(ValueError, self.instrument.write_string, -1,    'A') # Wrong register address
        self.assertRaises(ValueError, self.instrument.write_string, 65536, 'A')
        self.assertRaises(ValueError, self.instrument.write_string, 104,   'AAA',       1) # Too long string
        self.assertRaises(ValueError, self.instrument.write_string, 104,   'ABCDEFGHI', 4)
        self.assertRaises(ValueError, self.instrument.write_string, 104,   'A',         -1) # Wrong number of registers
        self.assertRaises(ValueError, self.instrument.write_string, 104,   'A',         256)

    def testWriteStringWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_string, value, 'A')
            self.assertRaises(TypeError, self.instrument.write_string, 104,   'A',   value)
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, self.instrument.write_string, 104,   value, 4)


    ## Read Registers ##

    def testReadRegisters(self):
        self.assertEqual( self.instrument.read_registers(105, 1), [16] )
        self.assertEqual( self.instrument.read_registers(105, 3), [16, 32, 64] )

    def testReadRegistersWrongValue(self):
        self.assertRaises(ValueError, self.instrument.read_registers, -1,    1) # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_registers, 65536, 1)
        self.assertRaises(ValueError, self.instrument.read_registers, 105,   -1) # Wrong number of registers
        self.assertRaises(ValueError, self.instrument.read_registers, 105,   256)
        self.assertRaises(ValueError, self.instrument.read_registers, 105,   1,  1) # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_registers, 105,   1,  256)
        self.assertRaises(ValueError, self.instrument.read_registers, 105,   1,  -1)

    def testReadRegistersWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_registers, value, 1)
            self.assertRaises(TypeError, self.instrument.read_registers, 105,   value)
            self.assertRaises(TypeError, self.instrument.read_registers, 105,   1,     value)


    ## Write Registers ##

    def testWriteRegisters(self):
        self.instrument.write_registers(105, [2])
        self.instrument.write_registers(105, [2, 4, 8])

    def testWriteRegistersWrongValue(self):
        self.assertRaises(ValueError, self.instrument.write_registers, -1,    [2]) # Wrong register address
        self.assertRaises(ValueError, self.instrument.write_registers, 65536, [2])
        self.assertRaises(ValueError, self.instrument.write_registers, 105,   []) # Wrong list value
        self.assertRaises(ValueError, self.instrument.write_registers, 105,   [-1])

    def testWriteRegistersWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_registers, value, [2])
        for value in _NOT_INTLISTS:
            self.assertRaises(TypeError, self.instrument.write_registers,  105,  value)


    ## Generic command ##

    def testGenericCommand(self):   
        
        # write_bit(71, 1)
        self.instrument._genericCommand(5,  71, value=1)
        
        # write_register(35, 20)
        self.instrument._genericCommand(16, 35, value=20)
        
        # write_register(45, 88)
        self.instrument._genericCommand(6, 45, value=88) 
        
        # write_long(102, 5)
        self.instrument._genericCommand(16, 102, value=5, numberOfRegisters=2, payloadformat='long')
        
        # write_float(103, 1.1)
        self.instrument._genericCommand(16, 103, value=1.1, numberOfRegisters=2, payloadformat='float')
        
        # write_string(104, 'A', 1)
        self.instrument._genericCommand(16, 104, value='A', numberOfRegisters=1, payloadformat='string')
        
        # write_registers(105, [2, 4, 8])
        self.instrument._genericCommand(16, 105, value=[2, 4, 8], numberOfRegisters=3, payloadformat='registers') 
        
        # read_register(289)
        self.assertEqual( self.instrument._genericCommand(3, 289), 770)   
                               
         # read_bit(61)
        self.assertEqual( self.instrument._genericCommand(2, 61), 1)
                        
        # read_register(101, signed = True)
        self.assertEqual( self.instrument._genericCommand(3, 101, signed=True), -5) 
        
        # read_register(289, 1)
        self.assertAlmostEqual( self.instrument._genericCommand(3, 289, numberOfDecimals=1), 77.0)         
        
        # read_long(102)
        self.assertEqual(   self.instrument._genericCommand(3, 102, numberOfRegisters=2, payloadformat='long'),      
                            4294967295)   
        
        # read_float(103)
        self.assertAlmostEqual( self.instrument._genericCommand(3, 103, numberOfRegisters=2, payloadformat='float'),     
                                1.0)          
                                
        # read_string(104, 1)
        self.assertEqual(   self.instrument._genericCommand(3, 104, numberOfRegisters=1, payloadformat='string'),    
                            'AB')          
                            
        # read_registers(105, 3) 
        self.assertEqual(   self.instrument._genericCommand(3, 105, numberOfRegisters=3, payloadformat='registers'), 
                            [16, 32, 64]) 
                
    def testGenericCommandWrongValue(self):        
        self.assertRaises(ValueError, self.instrument._genericCommand, 35,  289) # Wrong functioncode
        self.assertRaises(ValueError, self.instrument._genericCommand, -1,  289)
        self.assertRaises(ValueError, self.instrument._genericCommand, 128, 289)
        self.assertRaises(ValueError, self.instrument._genericCommand, 3,   -1) # Wrong registeraddress
        self.assertRaises(ValueError, self.instrument._genericCommand, 3,   65536)
        self.assertRaises(ValueError, self.instrument._genericCommand, 3,   289, numberOfDecimals=-1)
        self.assertRaises(ValueError, self.instrument._genericCommand, 3,   289, numberOfRegisters=-1)
        self.assertRaises(ValueError, self.instrument._genericCommand, 3,   289, payloadformat='ABC')
        
    def testGenericCommandWrongValueCombinations(self):     
        # Bit
        self.assertRaises(ValueError, self.instrument._genericCommand,  5,  71, value=1,         numberOfRegisters=2) 
        
        # Register
        self.assertRaises(TypeError,  self.instrument._genericCommand,  6,  45, value='a')
        self.assertRaises(ValueError, self.instrument._genericCommand,  6,  45, value=88,        numberOfRegisters=2)
        self.assertRaises(ValueError, self.instrument._genericCommand, 16,  35, value=20,        numberOfRegisters=2) 
        
        # Float
        self.assertRaises(TypeError,  self.instrument._genericCommand, 16, 105, value=[2, 4, 8], numberOfRegisters=2, payloadformat='float') 
        self.assertRaises(TypeError,  self.instrument._genericCommand, 16, 105, value='ABC',     numberOfRegisters=2, payloadformat='float') 
        self.assertRaises(ValueError, self.instrument._genericCommand, 16, 105, value=None,      numberOfRegisters=2, payloadformat='float') 
        self.assertRaises(ValueError, self.instrument._genericCommand, 16, 105, value=3.3,       numberOfRegisters=2, payloadformat='float', numberOfDecimals=1) 
        self.assertRaises(ValueError, self.instrument._genericCommand, 16, 105, value=3.3,       numberOfRegisters=2, payloadformat='float', signed=True) 
        
        # String
        self.assertRaises(ValueError, self.instrument._genericCommand, 1,  104, value='A',   numberOfRegisters=1, payloadformat='string')
        self.assertRaises(ValueError, self.instrument._genericCommand, 16, 104, value='ABC', numberOfRegisters=1, payloadformat='string')
        self.assertRaises(ValueError, self.instrument._genericCommand, 16, 104, value=None,  numberOfRegisters=1, payloadformat='string')
        self.assertRaises(TypeError,  self.instrument._genericCommand, 16, 104, value=22,    numberOfRegisters=1, payloadformat='string')
        self.assertRaises(ValueError, self.instrument._genericCommand, 16, 104, value='A',   numberOfRegisters=1, payloadformat='string', signed=True)
        self.assertRaises(ValueError, self.instrument._genericCommand, 16, 104, value='A',   numberOfRegisters=1, payloadformat='string', numberOfDecimals=1)        
        
        # Registers
        self.assertRaises(TypeError,  self.instrument._genericCommand, 16, 105, value=1,         numberOfRegisters=1, payloadformat='registers')
        self.assertRaises(TypeError,  self.instrument._genericCommand, 16, 105, value='A',       numberOfRegisters=1, payloadformat='registers')
        self.assertRaises(ValueError, self.instrument._genericCommand, 16, 105, value=[2, 4, 8], numberOfRegisters=1, payloadformat='registers')
        self.assertRaises(ValueError, self.instrument._genericCommand, 16, 105, value=None,     numberOfRegisters=3, payloadformat='registers') 
        self.assertRaises(ValueError, self.instrument._genericCommand, 16, 105, value=[2, 4, 8], numberOfRegisters=3, payloadformat='registers', signed=True) 
        self.assertRaises(ValueError, self.instrument._genericCommand, 16, 105, value=[2, 4, 8], numberOfRegisters=3, payloadformat='registers', numberOfDecimals=1)
        
    def testGenericCommandWrongType(self):  
        # Note: The parameter 'value' type is dependent on the other parameters. See tests above.
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument._genericCommand,  value, 289)  # Function code
            self.assertRaises(TypeError, self.instrument._genericCommand,  3,     value) # Register address
            self.assertRaises(TypeError, self.instrument._genericCommand,  3,     289,    numberOfDecimals=value)
            self.assertRaises(TypeError, self.instrument._genericCommand,  3,     289,    numberOfRegisters=value)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, self.instrument._genericCommand,  3,     289,    signed=value)
        for value in _NOT_STRINGS_OR_NONE:
            self.assertRaises(ValueError, self.instrument._genericCommand, 3,     289,    payloadformat=value)


    ## Perform command ##

    def testPerformcommandKnownResponse(self):
        self.assertEqual( self.instrument._performCommand(16, 'TESTCOMMAND'), 'TRsp') # Total response length should be 8 bytes
        self.assertEqual( self.instrument._performCommand(75, 'TESTCOMMAND2'), 'TESTCOMMANDRESPONSE2')
        self.assertEqual( self.instrument._performCommand(2, '\x00\x3d\x00\x01'), '\x01\x01' ) # Read bit register 61 on slave 1 using function code 2.

    def testPerformcommandWrongSlaveResponse(self):
        self.assertRaises(ValueError, self.instrument._performCommand, 1,  'TESTCOMMAND') # Wrong slave address in response
        self.assertRaises(ValueError, self.instrument._performCommand, 2,  'TESTCOMMAND') # Wrong function code in response
        self.assertRaises(ValueError, self.instrument._performCommand, 3,  'TESTCOMMAND') # Wrong crc in response
        self.assertRaises(ValueError, self.instrument._performCommand, 4,  'TESTCOMMAND') # Too short response message from slave
        self.assertRaises(ValueError, self.instrument._performCommand, 5,  'TESTCOMMAND') # Error indication from slave
        
    def testPerformcommandWrongInputValue(self):
        self.assertRaises(ValueError, self.instrument._performCommand, -1,  'TESTCOMMAND') # Wrong function code
        self.assertRaises(ValueError, self.instrument._performCommand, 128, 'TESTCOMMAND')

    def testPerformcommandWrongInputType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument._performCommand, value, 'TESTCOMMAND')
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, self.instrument._performCommand, 16,     value)


    ## Communicate ##

    def testCommunicateKnownResponse(self):
        self.assertEqual( self.instrument._communicate('TESTMESSAGE', _LARGE_NUMBER_OF_BYTES), 'TESTRESPONSE' )

    def testCommunicateWrongType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, self.instrument._communicate, value, _LARGE_NUMBER_OF_BYTES)

    def testCommunicateNoMessage(self):
        self.assertRaises(ValueError, self.instrument._communicate, '', _LARGE_NUMBER_OF_BYTES)

    def testCommunicateNoResponse(self):
        self.assertRaises(IOError, self.instrument._communicate, 'MessageForEmptyResponse', _LARGE_NUMBER_OF_BYTES)

    def testCommunicateLocalEcho(self):
        self.instrument.handle_local_echo = True
        self.assertEqual( self.instrument._communicate('TESTMESSAGE2', _LARGE_NUMBER_OF_BYTES), 'TESTRESPONSE2' )

    def testCommunicateWrongLocalEcho(self):
        self.instrument.handle_local_echo = True
        self.assertRaises(IOError, self.instrument._communicate, 'TESTMESSAGE3', _LARGE_NUMBER_OF_BYTES)
        
    ## __repr__ ##

    def testRepresentation(self):
        representation = repr(self.instrument)
        self.assertTrue( 'minimalmodbus.Instrument<id=' in representation )
        self.assertTrue( ', address=1, mode=rtu, close_port_after_each_call=False, precalculate_read_size=True, debug=False, serial=dummy_serial.Serial<id=' in representation )
        self.assertTrue( ", open=True>(port=" in representation )


    ## Test the dummy serial port itself ##
    
    def testReadPortClosed(self):
        self.instrument.serial.close()
        self.assertRaises(IOError, self.instrument.serial.read, 1000)

    def testWritePortClosed(self):
        self.instrument.serial.close()
        self.assertRaises(IOError, self.instrument.write_bit, 71, 1)

    def testPortAlreadyOpen(self):
        self.assertRaises(IOError, self.instrument.serial.open)

    def testPortAlreadyClosed(self):
        self.instrument.serial.close()
        self.assertRaises(IOError, self.instrument.serial.close)


    ## Tear down test fixture ##

    def tearDown(self):
        self.instrument = None
        del(self.instrument)


class TestDummyCommunicationOmegaSlave1(ExtendedTestCase):

    def setUp(self):
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'
        dummy_serial.DEFAULT_TIMEOUT = 0.01
        minimalmodbus.serial.Serial = dummy_serial.Serial
        minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = False
        self.instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 1) # port name, slave address (in decimal)

    def testReadBit(self):
        self.assertEqual( self.instrument.read_bit(2068), 1 )

    def testWriteBit(self):
        self.instrument.write_bit(2068, 0)
        self.instrument.write_bit(2068, 1)

    def testReadRegister(self):
        self.assertAlmostEqual( self.instrument.read_register(4097, 1), 823.6 )

    def testWriteRegister(self):
        self.instrument.write_register(4097, 700.0, 1)
        self.instrument.write_register(4097, 823.6, 1)

    def tearDown(self):
        self.instrument = None
        del(self.instrument)


class TestDummyCommunicationOmegaSlave10(ExtendedTestCase):

    def setUp(self):
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'
        dummy_serial.DEFAULT_TIMEOUT = 0.01
        minimalmodbus.serial.Serial = dummy_serial.Serial
        minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = False
        self.instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 10) # port name, slave address (in decimal)

    def testReadBit(self):
        self.assertEqual( self.instrument.read_bit(2068), 1 )

    def testWriteBit(self):
        self.instrument.write_bit(2068, 0)
        self.instrument.write_bit(2068, 1)

    def testReadRegister(self):
        self.assertAlmostEqual( self.instrument.read_register(4096, 1), 25.0 )
        self.assertAlmostEqual( self.instrument.read_register(4097, 1), 325.8 )

    def testWriteRegister(self):
        self.instrument.write_register(4097, 325.8, 1)
        self.instrument.write_register(4097, 20.0, 1)
        self.instrument.write_register(4097, 200.0, 1)

    def tearDown(self):
        self.instrument = None
        del(self.instrument)


class TestDummyCommunicationDTB4824_RTU(ExtendedTestCase):

    def setUp(self):
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'
        dummy_serial.DEFAULT_TIMEOUT = 0.01
        minimalmodbus.serial.Serial = dummy_serial.Serial
        minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = False
        self.instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 7) # port name, slave address (in decimal)
    
    def testReadBit(self):
        self.assertEqual( self.instrument.read_bit(0x0800), 0) # LED AT
        self.assertEqual( self.instrument.read_bit(0x0801), 0) # LED Out1
        self.assertEqual( self.instrument.read_bit(0x0802), 0) # LED Out2
        self.assertEqual( self.instrument.read_bit(0x0814), 0) # RUN/STOP

    def testWriteBit(self):
        self.instrument.write_bit(0x0810, 1) # "Communication write in enabled".
        self.instrument.write_bit(0x0814, 0) # STOP
        self.instrument.write_bit(0x0814, 1) # RUN
        
    def testReadBits(self):
        self.assertEqual( self.instrument._performCommand(2, '\x08\x10\x00\x09'), '\x02\x07\x00') 

    def testReadRegister(self):
        self.assertEqual( self.instrument.read_register(0x1000), 64990) # Process value (PV)
        self.assertAlmostEqual( self.instrument.read_register(0x1001, 1), 80.0 ) # Setpoint (SV).
        self.assertEqual( self.instrument.read_register(0x1004), 14) # Sensor type.
        self.assertEqual( self.instrument.read_register(0x1005), 1) # Control method
        self.assertEqual( self.instrument.read_register(0x1006), 0) # Heating/cooling selection.
        self.assertAlmostEqual( self.instrument.read_register(0x1012, 1), 0.0 ) # Output 1
        self.assertAlmostEqual( self.instrument.read_register(0x1013, 1), 0.0 ) # Output 2
        self.assertEqual( self.instrument.read_register(0x1023), 0) # System alarm setting
        self.assertEqual( self.instrument.read_register(0x102A), 0) # LED status
        self.assertEqual( self.instrument.read_register(0x102B), 15) # Pushbutton status
        self.assertEqual( self.instrument.read_register(0x102F), 400) # Firmware version

    def testReadRegisters(self):
        self.assertEqual( self.instrument.read_registers(0x1000, 2), [64990, 350]) # Process value (PV) and setpoint (SV).

    def testWriteRegister(self):
        self.instrument.write_register(0x1001, 0x0320, functioncode=6) # Setpoint of 80.0 degrees
        self.instrument.write_register(0x1001, 25, 1,  functioncode=6) # Setpoint

    def tearDown(self):
        self.instrument = None
        del(self.instrument)

class TestDummyCommunicationDTB4824_ASCII(ExtendedTestCase):

    def setUp(self):
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = ASCII_RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'
        dummy_serial.DEFAULT_TIMEOUT = 0.01
        minimalmodbus.serial.Serial = dummy_serial.Serial
        minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = False
        self.instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 7, 'ascii') # port name, slave address (in decimal), mode
    
    def testReadBit(self):
        self.assertEqual( self.instrument.read_bit(0x0800), 0) # LED AT
        self.assertEqual( self.instrument.read_bit(0x0801), 1) # LED Out1
        self.assertEqual( self.instrument.read_bit(0x0802), 0) # LED Out2
        self.assertEqual( self.instrument.read_bit(0x0814), 1) # RUN/STOP

    def testWriteBit(self):
        self.instrument.write_bit(0x0810, 1) # "Communication write in enabled".
        self.instrument.write_bit(0x0814, 0) # STOP
        self.instrument.write_bit(0x0814, 1) # RUN
        
    def testReadBits(self):
        self.assertEqual( self.instrument._performCommand(2, '\x08\x10\x00\x09'), '\x02\x17\x00') 

    def testReadRegister(self):
        self.assertEqual( self.instrument.read_register(0x1000), 64990) # Process value (PV)
        self.assertAlmostEqual( self.instrument.read_register(0x1001, 1), 80.0 ) # Setpoint (SV).
        self.assertEqual( self.instrument.read_register(0x1004), 14) # Sensor type.
        self.assertEqual( self.instrument.read_register(0x1005), 1) # Control method
        self.assertEqual( self.instrument.read_register(0x1006), 0) # Heating/cooling selection.
        self.assertAlmostEqual( self.instrument.read_register(0x1012, 1), 100.0 ) # Output 1
        self.assertAlmostEqual( self.instrument.read_register(0x1013, 1), 0.0 ) # Output 2
        self.assertEqual( self.instrument.read_register(0x1023), 0) # System alarm setting
        self.assertEqual( self.instrument.read_register(0x102A), 64) # LED status
        self.assertEqual( self.instrument.read_register(0x102B), 15) # Pushbutton status
        self.assertEqual( self.instrument.read_register(0x102F), 400) # Firmware version

    def testReadRegisters(self):
        self.assertEqual( self.instrument.read_registers(0x1000, 2), [64990, 350]) # Process value (PV) and setpoint (SV).

    def testWriteRegister(self):
        self.instrument.write_register(0x1001, 0x0320, functioncode=6) # Setpoint of 80.0 degrees
        self.instrument.write_register(0x1001, 25, 1,  functioncode=6) # Setpoint

    def tearDown(self):
        self.instrument = None
        del(self.instrument)

class TestDummyCommunicationWithPortClosure(ExtendedTestCase):

    def setUp(self):
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'
        dummy_serial.DEFAULT_TIMEOUT = 0.01
        minimalmodbus.serial.Serial = dummy_serial.Serial
        minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True # Mimic a WindowsXP serial port
        self.instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 1) # port name, slave address (in decimal)

    def testReadRegisterSeveralTimes(self):
        self.assertEqual( self.instrument.read_register(289), 770 )
        self.assertEqual( self.instrument.read_register(289), 770 )
        self.assertEqual( self.instrument.read_register(289), 770 )

    def testPortAlreadyOpen(self):
        self.assertEqual( self.instrument.read_register(289), 770 )
        self.instrument.serial.open()
        self.assertRaises(IOError, self.instrument.read_register, 289)

    def testPortAlreadyClosed(self):
        self.assertEqual( self.instrument.read_register(289), 770 )
        self.assertRaises(IOError, self.instrument.serial.close)

    def tearDown(self):
        try:
            self.instrument.serial.close()
        except:
            pass
        self.instrument = None
        del(self.instrument)


class TestVerboseDummyCommunicationWithPortClosure(ExtendedTestCase):

    def setUp(self):
        dummy_serial.VERBOSE = True
        dummy_serial.RESPONSES = RTU_RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'
        dummy_serial.DEFAULT_TIMEOUT = 0.01
        minimalmodbus.serial.Serial = dummy_serial.Serial
        minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True # Mimic a WindowsXP serial port
        self.instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 1) # port name, slave address (in decimal)

    def testReadRegister(self):
        self.assertEqual( self.instrument.read_register(289), 770 )

    def tearDown(self):
        try:
            self.instrument.serial.close()
        except:
            pass
        self.instrument = None
        del(self.instrument)


class TestDummyCommunicationDebugmode(ExtendedTestCase):

    def setUp(self):
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'
        dummy_serial.DEFAULT_TIMEOUT = 0.01
        minimalmodbus.serial.Serial = dummy_serial.Serial
        minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = False
        self.instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 1) # port name, slave address (in decimal)
        self.instrument.debug = True

    def testReadRegister(self):
        self.assertEqual( self.instrument.read_register(289), 770 )

    def tearDown(self):
        self.instrument = None
        del(self.instrument)

class TestDummyCommunicationHandleLocalEcho(ExtendedTestCase):

    def setUp(self):
        dummy_serial.VERBOSE = True
        dummy_serial.RESPONSES = RTU_RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'
        dummy_serial.DEFAULT_TIMEOUT = 0.01
        minimalmodbus.serial.Serial = dummy_serial.Serial
        minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = False
        self.instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 20) # port name, slave address (in decimal)
        self.instrument.debug = True
        self.instrument.handle_local_echo = True

    def testReadRegister(self):
        self.assertEqual( self.instrument.read_register(289), 770 )

    def testReadRegisterWrongEcho(self):
        self.assertRaises(IOError, self.instrument.read_register, 290)

    def tearDown(self):
        self.instrument = None
        del(self.instrument)



RTU_RESPONSES = {}
GOOD_RTU_RESPONSES = {}
WRONG_RTU_RESPONSES = {}
ASCII_RESPONSES = {}
GOOD_ASCII_RESPONSES = {}
WRONG_ASCII_RESPONSES = {}
"""A dictionary of respones from a dummy instrument.

The key is the message (string) sent to the serial port, and the item is the response (string)
from the dummy serial port.

"""
# Note that the string 'AAAAAAA' might be easier to read if grouped,
# like 'AA' + 'AAAA' + 'A' for the initial part (address etc) + payload + CRC.


#                ##  READ BIT  ##

# Read bit register 61 on slave 1 using function code 2. Also for testing _performCommand() #
# ----------------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 2. Register address 61, 1 coil. CRC.
# Response: Slave address 1, function code 2. 1 byte, value=1. CRC.
GOOD_RTU_RESPONSES['\x01\x02' + '\x00\x3d\x00\x01' + '(\x06'] = '\x01\x02' + '\x01\x01' + '`H'

# Read bit register 62 on slave 1 using function code 1 #
# ----------------------------------------------------- #
# Message:  Slave address 1, function code 1. Register address 62, 1 coil. CRC.
# Response: Slave address 1, function code 1. 1 byte, value=0. CRC.
GOOD_RTU_RESPONSES['\x01\x01' + '\x00\x3e\x00\x01' + '\x9c\x06'] = '\x01\x01' + '\x01\x00' + 'Q\x88'

# Read bit register 63 on slave 1 using function code 2, slave gives wrong byte count #
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 2. Register address 63, 1 coil. CRC.
# Response: Slave address 1, function code 2. 2 bytes (wrong), value=1. CRC.
WRONG_RTU_RESPONSES['\x01\x02' + '\x00\x3f\x00\x01' + '\x89\xc6'] = '\x01\x02' + '\x02\x01' + '`\xb8'

# Read bit register 64 on slave 1 using function code 2, slave gives no response #
# ------------------------------------------------------------------------------ #
# Message:  Slave address 1, function code 2. Register address 64, 1 coil. CRC.
# Response: (empty string)
WRONG_RTU_RESPONSES['\x01\x02' + '\x00\x40\x00\x01' + '\xb8\x1e'] = ''


#                ##  WRITE BIT  ##

# Write bit register 71 on slave 1 using function code 5 #
# ------------------------------------------------------ #
# Message:  Slave address 1, function code 5. Register address 71, value 1 (FF00). CRC.
# Response: Slave address 1, function code 5. Register address 71, value 1 (FF00). CRC.
GOOD_RTU_RESPONSES['\x01\x05' + '\x00\x47\xff\x00' + '</'] = '\x01\x05' + '\x00\x47\xff\x00' + '</'

# Write bit register 72 on slave 1 using function code 15 #
# ------------------------------------------------------ #
# Message:  Slave address 1, function code 15. Register address 72, 1 bit, 1 byte, value 1 (0100). CRC.
# Response: Slave address 1, function code 15. Register address 72, 1 bit. CRC.
GOOD_RTU_RESPONSES['\x01\x0f' + '\x00\x48\x00\x01\x01\x01' + '\x0fY'] = '\x01\x0f' + '\x00\x48\x00\x01' + '\x14\x1d'

# Write bit register 73 on slave 1 using function code 15, slave gives wrong number of registers #
# ---------------------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 15. Register address 73, 1 bit, 1 byte, value 1 (0100). CRC.
# Response: Slave address 1, function code 15. Register address 73, 2 bits (wrong). CRC.
WRONG_RTU_RESPONSES['\x01\x0f' + '\x00\x49\x00\x01\x01\x01' + '2\x99'] = '\x01\x0f' + '\x00\x49\x00\x02' + '\x05\xdc'

# Write bit register 74 on slave 1 using function code 5, slave gives wrong write data #
# ------------------------------------------------------------------------------------ #
# Message:  Slave address 1, function code 5. Register address 74, value 1 (FF00). CRC.
# Response: Slave address 1, function code 5. Register address 74, value 0 (0000, wrong). CRC.
WRONG_RTU_RESPONSES['\x01\x05' + '\x00\x4a\xff\x00' + '\xad\xec'] = '\x01\x05' + '\x00\x47\x00\x00' + '}\xdf'


#                ##  READ REGISTER  ##

# Read register 289 on slave 1 using function code 3 #
# ---------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 289, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value=770. CRC=14709.
GOOD_RTU_RESPONSES['\x01\x03' + '\x01!\x00\x01' + '\xd5\xfc'] = '\x01\x03' + '\x02\x03\x02' + '\x39\x75'

# Read register 5 on slave 1 using function code 3 #
# ---------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 289, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value=184. CRC
GOOD_RTU_RESPONSES['\x01\x03' + '\x00\x05\x00\x01' + '\x94\x0b'] = '\x01\x03' + '\x02\x00\xb8' + '\xb86'

# Read register 14 on slave 1 using function code 4 #
# --------------------------------------------------#
# Message:  Slave address 1, function code 4. Register address 14, 1 register. CRC.
# Response: Slave address 1, function code 4. 2 bytes, value=880. CRC.
GOOD_RTU_RESPONSES['\x01\x04' + '\x00\x0e\x00\x01' + 'P\t'] = '\x01\x04' + '\x02\x03\x70' + '\xb8$'

# Read register 101 on slave 1 using function code 3 #
# ---------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 101, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value=-5 or 65531 (depending on interpretation). CRC
GOOD_RTU_RESPONSES['\x01\x03' + '\x00e\x00\x01' + '\x94\x15'] = '\x01\x03' + '\x02\xff\xfb' + '\xb87'

# Read register 201 on slave 1 using function code 3 #
# ---------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 201, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value=9. CRC
GOOD_RTU_RESPONSES['\x01\x03' + '\x00\xc9\x00\x01' + 'T4'] = '\x01\x03' + '\x02\x00\x09' + 'xB'

# Read register 202 on slave 1 using function code 3. Too long response #
# ----------------------------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 202, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes (wrong!), value=9. CRC
WRONG_RTU_RESPONSES['\x01\x03' + '\x00\xca\x00\x01' + '\xa44'] = '\x01\x03' + '\x02\x00\x00\x09' + '\x84t'

# Read register 203 on slave 1 using function code 3. Too short response #
# ----------------------------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 203, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes (wrong!), value=9. CRC
WRONG_RTU_RESPONSES['\x01\x03' + '\x00\xcb\x00\x01' + '\xf5\xf4'] = '\x01\x03' + '\x02\x09' + '0\xbe'


#                ##  WRITE REGISTER  ##

# Write value 50 in register 24 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 24, 1 register, 2 bytes, value=50. CRC.
# Response: Slave address 1, function code 16. Register address 24, 1 register. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00\x18\x00\x01\x02\x002' + '$]'] = '\x01\x10' + '\x00\x18\x00\x01' + '\x81\xce'

# Write value 20 in register 35 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 35, 1 register, 2 bytes, value=20. CRC.
# Response: Slave address 1, function code 16. Register address 35, 1 register. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00#\x00\x01' + '\x02\x00\x14' + '\xa1\x0c'] = '\x01\x10' + '\x00#\x00\x01' + '\xf0\x03'

# Write value 88 in register 45 on slave 1 using function code 6 #
# ---------------------------------------------------------------#
# Message:  Slave address 1, function code 6. Register address 45, value=88. CRC.
# Response: Slave address 1, function code 6. Register address 45, value=88. CRC.
GOOD_RTU_RESPONSES['\x01\x06' + '\x00\x2d\x00\x58' + '\x189'] = '\x01\x06' + '\x00\x2d\x00\x58' + '\x189'

# Write value 5 in register 101 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 101, 1 register, 2 bytes, value=5. CRC.
# Response: Slave address 1, function code 16. Register address 101, 1 register. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00e\x00\x01\x02\x00\x05' + 'o\xa6'] = '\x01\x10' + '\x00e\x00\x01' + '\x11\xd6'

# Write value 50 in register 101 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 101, 1 register, 2 bytes, value=5. CRC.
# Response: Slave address 1, function code 16. Register address 101, 1 register. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00e\x00\x01\x02\x002' + '.p'] = '\x01\x10' + '\x00e\x00\x01' + '\x11\xd6'

# Write value -5 in register 101 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 101, 1 register, 2 bytes, value=-5. CRC.
# Response: Slave address 1, function code 16. Register address 101, 1 register. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00e\x00\x01\x02\xff\xfb' + '\xaf\xd6'] = '\x01\x10' + '\x00e\x00\x01' + '\x11\xd6'

# Write value -50 in register 101 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 101, 1 register, 2 bytes, value=-50. CRC.
# Response: Slave address 1, function code 16. Register address 101, 1 register. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00e\x00\x01\x02\xff\xce' + 'o\xc1'] = '\x01\x10' + '\x00e\x00\x01' + '\x11\xd6'

# Write value 99 in register 51 on slave 1 using function code 16, slave gives wrong CRC #
# ---------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 51, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 1, function code 16. Register address 51, 1 register. Wrong CRC.
WRONG_RTU_RESPONSES['\x01\x10' + '\x00\x33\x00\x01' + '\x02\x00\x63' + '\xe3\xba'] = '\x01\x10' + '\x00\x33\x00\x01' + 'AB'

# Write value 99 in register 52 on slave 1 using function code 16, slave gives wrong number of registers #
# -------------------------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 52, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 1, function code 16. Register address 52, 2 registers (wrong). CRC.
WRONG_RTU_RESPONSES['\x01\x10' + '\x00\x34\x00\x01' + '\x02\x00\x63' + '\xe2\r'] = '\x01\x10' + '\x00\x34\x00\x02' + '\x00\x06'

# Write value 99 in register 53 on slave 1 using function code 16, slave gives wrong register address #
# ----------------------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 53, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 1, function code 16. Register address 54 (wrong), 1 register. CRC.
WRONG_RTU_RESPONSES['\x01\x10' + '\x00\x35\x00\x01' + '\x02\x00\x63' + '\xe3\xdc'] = '\x01\x10' + '\x00\x36\x00\x01' + '\xe1\xc7'

# Write value 99 in register 54 on slave 1 using function code 16, slave gives wrong slave address #
# ------------------------------------------------------------------------------------------------ #
# Message:  Slave address 1, function code 16. Register address 54, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 2 (wrong), function code 16. Register address 54, 1 register. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00\x36\x00\x01' + '\x02\x00\x63' + '\xe3\xef'] = '\x02\x10' + '\x00\x36\x00\x01' + '\xe1\xf4'

# Write value 99 in register 55 on slave 1 using function code 16, slave gives wrong functioncode #
# ----------------------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 16. Register address 55, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 1, function code 6 (wrong). Register address 55, 1 register. CRC.
WRONG_RTU_RESPONSES['\x01\x10' + '\x00\x37\x00\x01' + '\x02\x00\x63' + '\xe2>'] = '\x01\x06' + '\x00\x37\x00\x01' + '\xf9\xc4'

# Write value 99 in register 56 on slave 1 using function code 16, slave gives wrong functioncode (indicates an error) #
# -------------------------------------------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 16. Register address 56, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 1, function code 144 (wrong). Register address 56, 1 register. CRC.
WRONG_RTU_RESPONSES['\x01\x10' + '\x00\x38\x00\x01' + '\x02\x00\x63' + '\xe2\xc1'] = '\x01\x90' + '\x00\x38\x00\x01' + '\x81\xda'

# Write value 99 in register 55 on slave 1 using function code 6, slave gives wrong write data #
# -------------------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 6. Register address 55, value=99. CRC.
# Response: Slave address 1, function code 6. Register address 55, value=98 (wrong). CRC.
WRONG_RTU_RESPONSES['\x01\x06' + '\x00\x37\x00\x63' + 'x-'] = '\x01\x06' + '\x00\x37\x00\x62' + '\xb9\xed'


#                ##  READ LONG ##

# Read long (2 registers, starting at 102) on slave 1 using function code 3 #
# --------------------------------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 289, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, value=-1 or 4294967295 (depending on interpretation). CRC
GOOD_RTU_RESPONSES['\x01\x03' + '\x00f\x00\x02' + '$\x14'] = '\x01\x03' + '\x04\xff\xff\xff\xff' + '\xfb\xa7'


#                ##  WRITE LONG ##

# Write long (2 registers, starting at 102) on slave 1 using function code 16, with value 5. #
# -------------------------------------------------------------------------------------------#
# Message: Slave address 1, function code 16. Register address 102, 2 registers, 4 bytes, value=5. CRC.
# Response: Slave address 1, function code 16. Register address 102, 2 registers. CRC
GOOD_RTU_RESPONSES['\x01\x10' + '\x00f\x00\x02\x04\x00\x00\x00\x05' + '\xb5\xae'] = '\x01\x10' + '\x00f\x00\x02' + '\xa1\xd7'

# Write long (2 registers, starting at 102) on slave 1 using function code 16, with value -5. #
# --------------------------------------------------------------------------------------------#
# Message: Slave address 1, function code 16. Register address 102, 2 registers, 4 bytes, value=-5. CRC.
# Response: Slave address 1, function code 16. Register address 102, 2 registers. CRC
GOOD_RTU_RESPONSES['\x01\x10' + '\x00f\x00\x02\x04\xff\xff\xff\xfb' + 'u\xfa'] = '\x01\x10' + '\x00f\x00\x02' + '\xa1\xd7'

# Write long (2 registers, starting at 102) on slave 1 using function code 16, with value 3. #
# -------------------------------------------------------------------------------------------#
# Message: Slave address 1, function code 16. Register address 102, 2 registers, 4 bytes, value=3. CRC.
# Response: Slave address 1, function code 16. Register address 102, 2 registers. CRC
GOOD_RTU_RESPONSES['\x01\x10' + '\x00f\x00\x02\x04\x00\x00\x00\x03' + '5\xac'] = '\x01\x10' + '\x00f\x00\x02' + '\xa1\xd7'

# Write long (2 registers, starting at 102) on slave 1 using function code 16, with value -3. #
# --------------------------------------------------------------------------------------------#
# Message: Slave address 1, function code 16. Register address 102, 2 registers, 4 bytes, value=-3. CRC.
# Response: Slave address 1, function code 16. Register address 102, 2 registers. CRC
GOOD_RTU_RESPONSES['\x01\x10' + '\x00f\x00\x02\x04\xff\xff\xff\xfd' + '\xf5\xf8'] = '\x01\x10' + '\x00f\x00\x02' + '\xa1\xd7'


#                ##  READ FLOAT ##

# Read float from address 103 (2 registers) on slave 1 using function code 3 #
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 103, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, value=1.0. CRC.
GOOD_RTU_RESPONSES['\x01\x03' + '\x00g\x00\x02' + 'u\xd4'] = '\x01\x03' + '\x04\x3f\x80\x00\x00' + '\xf7\xcf'

# Read float from address 103 (2 registers) on slave 1 using function code 4 #
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 4. Register address 103, 2 registers. CRC.
# Response: Slave address 1, function code 4. 4 bytes, value=3.65e30. CRC.
GOOD_RTU_RESPONSES['\x01\x04' + '\x00g\x00\x02' + '\xc0\x14'] = '\x01\x04' + '\x04\x72\x38\x47\x25' + '\x93\x1a'

# Read float from address 103 (4 registers) on slave 1 using function code 3 #
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 103, 4 registers. CRC.
# Response: Slave address 1, function code 3. 8 bytes, value=-2.0 CRC.
GOOD_RTU_RESPONSES['\x01\x03' + '\x00g\x00\x04' + '\xf5\xd6'] = '\x01\x03' + '\x08\xc0\x00\x00\x00\x00\x00\x00\x00' + '\x99\x87'


#                ##  WRITE FLOAT ##

# Write float 1.1 to address 103 (2 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 103, 2 registers, 4 bytes, value=1.1 . CRC.
# Response: Slave address 1, function code 16. Register address 103, 2 registers. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00g\x00\x02\x04?\x8c\xcc\xcd' + '\xed\x0b'] = '\x01\x10' + '\x00g\x00\x02' + '\xf0\x17'

# Write float 1.1 to address 103 (4 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 103, 4 registers, 8 bytes, value=1.1 . CRC.
# Response: Slave address 1, function code 16. Register address 103, 4 registers. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00g\x00\x04\x08?\xf1\x99\x99\x99\x99\x99\x9a' + 'u\xf7'] = '\x01\x10' + '\x00g\x00\x04' + 'p\x15'


#                ##  READ STRING  ##

# Read string from address 104 (1 register) on slave 1 using function code 3 #
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 104, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value = 'AB'.  CRC.
GOOD_RTU_RESPONSES['\x01\x03' + '\x00h\x00\x01' + '\x05\xd6'] = '\x01\x03' + '\x02AB' + '\x08%'

# Read string from address 104 (4 registers) on slave 1 using function code 3 #
# ----------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 104, 4 registers. CRC.
# Response: Slave address 1, function code 3.  8 bytes, value = 'ABCDEFGH'.  CRC.
GOOD_RTU_RESPONSES['\x01\x03' + '\x00h\x00\x04' + '\xc5\xd5'] = '\x01\x03' + '\x08ABCDEFGH' + '\x0b\xcc'


#                ##  WRITE STRING  ##

# Write string 'A' to address 104 (1 register) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 104, 1 register, 2 bytes, value='A ' . CRC.
# Response: Slave address 1, function code 16. Register address 104, 1 register. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00h\x00\x01\x02A ' + '\x9f0'] = '\x01\x10' + '\x00h\x00\x01' + '\x80\x15'

# Write string 'A' to address 104 (4 registers) on slave 1 using function code 16 #
# --------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 104, 4 registers, 8 bytes, value='A       ' . CRC.
# Response: Slave address 1, function code 16. Register address 104, 2 registers. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00h\x00\x04\x08A       ' + '\xa7\xae'] = '\x01\x10' + '\x00h\x00\x04' + '@\x16'

# Write string 'ABCDEFGH' to address 104 (4 registers) on slave 1 using function code 16 #
# ---------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 104, 4 registers, 8 bytes, value='ABCDEFGH' . CRC.
# Response: Slave address 1, function code 16. Register address 104, 4 registers. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00h\x00\x04\x08ABCDEFGH' + 'I>'] = '\x01\x10' + '\x00h\x00\x04' + '@\x16'


#                ##  READ REGISTERS  ##

# Read from address 105 (1 register) on slave 1 using function code 3 #
# --------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 105, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value = 16.  CRC.
GOOD_RTU_RESPONSES['\x01\x03' + '\x00i\x00\x01' + 'T\x16'] = '\x01\x03' + '\x02\x00\x10' + '\xb9\x88'

# Read from address 105 (3 registers) on slave 1 using function code 3 #
# ---------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 105, 3 registers. CRC.
# Response: Slave address 1, function code 3. 6 bytes, value = 16, 32, 64. CRC.
GOOD_RTU_RESPONSES['\x01\x03' + '\x00i\x00\x03' + '\xd5\xd7'] =  '\x01\x03' + '\x06\x00\x10\x00\x20\x00\x40' + '\xe0\x8c'


#                ##  WRITE REGISTERS  ##

# Write value [2] to address 105 (1 register) on slave 1 using function code 16 #
# ------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 105, 1 register, 2 bytes, value=2 . CRC.
# Response: Slave address 1, function code 16. Register address 105, 1 register. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00i\x00\x01\x02\x00\x02' + '.\xa8'] = '\x01\x10' + '\x00i\x00\x01' + '\xd1\xd5'

# Write value [2, 4, 8] to address 105 (3 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 105, 3 register, 6 bytes, value=2, 4, 8. CRC.
# Response: Slave address 1, function code 16. Register address 105, 3 registers. CRC.
GOOD_RTU_RESPONSES['\x01\x10' + '\x00i\x00\x03\x06\x00\x02\x00\x04\x00\x08' + '\x0c\xd6'] = '\x01\x10' + '\x00i\x00\x03' + 'P\x14'


#                ##  OTHER RESPONSES  ##

# Retrieve an empty response (for testing the _communicate method) #
# ---------------------------------------------------------------- #
WRONG_RTU_RESPONSES['MessageForEmptyResponse'] = ''

# Retrieve an known response (for testing the _communicate method) #
# ---------------------------------------------------------------- #
WRONG_RTU_RESPONSES['TESTMESSAGE'] = 'TESTRESPONSE'

# Retrieve an known response with local echo (for testing the _communicate method) #
# ---------------------------------------------------------------- #
WRONG_RTU_RESPONSES['TESTMESSAGE2'] = 'TESTMESSAGE2TESTRESPONSE2'

# Retrieve a response with wrong local echo (for testing the _communicate method) #
# ---------------------------------------------------------------- #
WRONG_RTU_RESPONSES['TESTMESSAGE3'] = 'TESTMeSSAGE3TESTRESPONSE3'

# Retrieve an known response (for testing the _performCommand method) #
# ---------------------------------------------------------------- #
WRONG_RTU_RESPONSES['\x01\x10TESTCOMMAND\x08B']     = '\x01\x10TRspU<' # Response should be 8 bytes
WRONG_RTU_RESPONSES['\x01\x4bTESTCOMMAND2\x18\xc8'] = '\x01\x4bTESTCOMMANDRESPONSE2K\x8c'
WRONG_RTU_RESPONSES['\x01\x01TESTCOMMAND4~']        = '\x02\x01TESTCOMMANDRESPONSEx]'    # Wrong slave address in response
WRONG_RTU_RESPONSES['\x01\x02TESTCOMMAND0z']        = '\x01\x03TESTCOMMANDRESPONSE2\x8c' # Wrong function code in response
WRONG_RTU_RESPONSES['\x01\x03TESTCOMMAND\xcd\xb9']  = '\x01\x03TESTCOMMANDRESPONSEab'    # Wrong CRC in response
WRONG_RTU_RESPONSES['\x01\x04TESTCOMMAND8r']        = 'A'                                # Too short response message
WRONG_RTU_RESPONSES['\x01\x05TESTCOMMAND\xc5\xb1']  = '\x01\x85TESTCOMMANDRESPONSE\xa54' # Error indication from slave


# Handle local echo: Read register 289 on slave 20 using function code 3 #
# ---------------------------------------------------------------------- #
# Message:  Slave address 20, function code 3. Register address 289, 1 register. CRC.
# Response: Echo. Slave address 20, function code 3. 2 bytes, value=770. CRC.
WRONG_RTU_RESPONSES['\x14\x03' + '\x01!\x00\x01' + '\xd79'] = \
    ('\x14\x03' + '\x01!\x00\x01' + '\xd79') + '\x14\x03' + '\x02\x03\x02' + '4\xb6'

# Handle local echo: Read register 290 on slave 20 using function code 3. Wrong echo #
# ---------------------------------------------------------------------------------- #
# Message:  Slave address 20, function code 3. Register address 290, 1 register. CRC.
# Response: Wrong echo. Slave address 20, function code 3. 2 bytes, value=770. CRC.

WRONG_RTU_RESPONSES['\x14\x03' + '\x01\x22\x00\x01' + '\x27\x39'] = \
    ('\x14\x03' + '\x01\x22\x00\x02' + '\x27\x39') + '\x14\x03' + '\x02\x03\x02' + '4\xb6'



## Recorded data from OmegaCN7500 ##
####################################
# (Sorted by slave address, register address)

# Slave address 1, read_bit(2068) Response value 1.
GOOD_RTU_RESPONSES['\x01\x02\x08\x14\x00\x01\xfb\xae'] ='\x01\x02\x01\x01`H'

# Slave address 1, write_bit(2068, 0)
GOOD_RTU_RESPONSES['\x01\x05\x08\x14\x00\x00\x8f\xae'] ='\x01\x05\x08\x14\x00\x00\x8f\xae'

# Slave address 1, write_bit(2068, 1)
GOOD_RTU_RESPONSES['\x01\x05\x08\x14\xff\x00\xce^'] ='\x01\x05\x08\x14\xff\x00\xce^'

# Slave address 1, read_register(4097, 1) Response value 823.6
GOOD_RTU_RESPONSES['\x01\x03\x10\x01\x00\x01\xd1\n'] ='\x01\x03\x02 ,\xa0Y'

# Slave address 1, write_register(4097, 700.0, 1)
GOOD_RTU_RESPONSES['\x01\x10\x10\x01\x00\x01\x02\x1bX\xbdJ'] ='\x01\x10\x10\x01\x00\x01T\xc9'

# Slave address 1, write_register(4097, 823.6, 1)
GOOD_RTU_RESPONSES['\x01\x10\x10\x01\x00\x01\x02 ,\xae]'] ='\x01\x10\x10\x01\x00\x01T\xc9'

# Slave address 10, read_bit(2068) Response value 1
GOOD_RTU_RESPONSES['\n\x02\x08\x14\x00\x01\xfa\xd5'] = '\n\x02\x01\x01bl'

# Slave address 10, write_bit(2068, 0)
GOOD_RTU_RESPONSES['\n\x05\x08\x14\x00\x00\x8e\xd5'] ='\n\x05\x08\x14\x00\x00\x8e\xd5'

# Slave address 10, write_bit(2068, 1)
GOOD_RTU_RESPONSES['\n\x05\x08\x14\xff\x00\xcf%'] ='\n\x05\x08\x14\xff\x00\xcf%'

# Slave address 10, read_register(4096, 1) Response value 25.0
GOOD_RTU_RESPONSES['\n\x03\x10\x00\x00\x01\x81\xb1'] ='\n\x03\x02\x00\xfa\x9d\xc6'

# Slave address 10, read_register(4097, 1) Response value 325.8
GOOD_RTU_RESPONSES['\n\x03\x10\x01\x00\x01\xd0q'] ='\n\x03\x02\x0c\xba\x996'

# Slave address 10, write_register(4097, 325.8, 1)
GOOD_RTU_RESPONSES['\n\x10\x10\x01\x00\x01\x02\x0c\xbaA\xc3'] ='\n\x10\x10\x01\x00\x01U\xb2'

# Slave address 10, write_register(4097, 20.0, 1)
GOOD_RTU_RESPONSES['\n\x10\x10\x01\x00\x01\x02\x00\xc8\xc4\xe6'] ='\n\x10\x10\x01\x00\x01U\xb2'

# Slave address 10, write_register(4097, 200.0, 1)
GOOD_RTU_RESPONSES['\n\x10\x10\x01\x00\x01\x02\x07\xd0\xc6\xdc'] ='\n\x10\x10\x01\x00\x01U\xb2'


## Recorded RTU data from Delta DTB4824 ##
##########################################
# (Sorted by register number)

# Slave address 7, read_bit(0x0800). This is LED AT.
# Response value 0
GOOD_RTU_RESPONSES['\x07\x02\x08\x00\x00\x01\xbb\xcc'] = '\x07\x02\x01\x00\xa1\x00'
    
# Slave address 7, read_bit(0x0801). This is LED Out1.
# Response value 0
GOOD_RTU_RESPONSES['\x07\x02\x08\x01\x00\x01\xea\x0c'] = '\x07\x02\x01\x00\xa1\x00' 

# Slave address 7, read_bit(0x0802). This is LED Out2.
# Response value 0
GOOD_RTU_RESPONSES['\x07\x02\x08\x02\x00\x01\x1a\x0c'] = '\x07\x02\x01\x00\xa1\x00' 

# Slave address 7, write_bit(0x0810, 1) This is "Communication write in enabled".
GOOD_RTU_RESPONSES['\x07\x05\x08\x10\xff\x00\x8f\xf9'] = '\x07\x05\x08\x10\xff\x00\x8f\xf9'

# Slave address 7, _performCommand(2, '\x08\x10\x00\x09'). This is reading 9 bits starting at 0x0810.
# Response value '\x02\x07\x00'
GOOD_RTU_RESPONSES['\x07\x02\x08\x10\x00\t\xbb\xcf'] = '\x07\x02\x02\x07\x003\x88'

# Slave address 7, read_bit(0x0814). This is RUN/STOP setting.
# Response value 0
GOOD_RTU_RESPONSES['\x07\x02\x08\x14\x00\x01\xfb\xc8'] = '\x07\x02\x01\x00\xa1\x00'

# Slave address 7, write_bit(0x0814, 0). This is STOP.
GOOD_RTU_RESPONSES['\x07\x05\x08\x14\x00\x00\x8f\xc8'] = '\x07\x05\x08\x14\x00\x00\x8f\xc8'

# Slave address 7, write_bit(0x0814, 1). This is RUN.
GOOD_RTU_RESPONSES['\x07\x05\x08\x14\xff\x00\xce8'] = '\x07\x05\x08\x14\xff\x00\xce8'

# Slave address 7, read_registers(0x1000, 2). This is process value (PV) and setpoint (SV).
# Response value [64990, 350]
GOOD_RTU_RESPONSES['\x07\x03\x10\x00\x00\x02\xc0\xad'] = '\x07\x03\x04\xfd\xde\x01^M\xcd'

# Slave address 7, read_register(0x1000). This is process value (PV).
# Response value 64990
GOOD_RTU_RESPONSES['\x07\x03\x10\x00\x00\x01\x80\xac'] = '\x07\x03\x02\xfd\xde\xf0\x8c'

# Slave address 7, read_register(0x1001, 1). This is setpoint (SV).
# Response value 80.0
GOOD_RTU_RESPONSES['\x07\x03\x10\x01\x00\x01\xd1l'] = '\x07\x03\x02\x03 1l'

# Slave address 7, write_register(0x1001, 25, 1, functioncode=6)
GOOD_RTU_RESPONSES['\x07\x06\x10\x01\x00\xfa\\\xef'] = '\x07\x06\x10\x01\x00\xfa\\\xef'

# Slave address 7, write_register(0x1001, 0x0320, functioncode=6) # Write value 800 to register 0x1001.
# This is a setpoint of 80.0 degrees (Centigrades, dependent on setting).
GOOD_RTU_RESPONSES['\x07\x06\x10\x01\x03 \xdd\x84'] = '\x07\x06\x10\x01\x03 \xdd\x84'

# Slave address 7, read_register(0x1004). This is sensor type.
# Response value 14
GOOD_RTU_RESPONSES['\x07\x03\x10\x04\x00\x01\xc1m'] = '\x07\x03\x02\x00\x0e\xb1\x80'   

# Slave address 7, read_register(0x1005) This is control method.
# Response value 1
GOOD_RTU_RESPONSES['\x07\x03\x10\x05\x00\x01\x90\xad'] = '\x07\x03\x02\x00\x01\xf1\x84'   

# Slave address 7, read_register(0x1006). This is heating/cooling selection.
# Response value 0
GOOD_RTU_RESPONSES['\x07\x03\x10\x06\x00\x01`\xad'] = '\x07\x03\x02\x00\x000D' 
    
# Slave address 7, read_register(0x1012, 1). This is output 1.    
# Response value 0.0
GOOD_RTU_RESPONSES['\x07\x03\x10\x12\x00\x01 \xa9'] = '\x07\x03\x02\x00\x000D'

# Slave address 7, read_register(0x1013, 1). This is output 2.    
# Response value 0.0
GOOD_RTU_RESPONSES['\x07\x03\x10\x13\x00\x01qi'] = '\x07\x03\x02\x00\x000D'

# Slave address 7, read_register(0x1023). This is system alarm setting.
# Response value 0
GOOD_RTU_RESPONSES['\x07\x03\x10#\x00\x01qf'] = '\x07\x03\x02\x00\x000D'

# Slave address 7, read_register(0x102A). This is LED status.
# Response value 0
GOOD_RTU_RESPONSES['\x07\x03\x10*\x00\x01\xa1d'] = '\x07\x03\x02\x00\x000D'

# Slave address 7, read_register(0x102B). This is pushbutton status.
# Response value 15
GOOD_RTU_RESPONSES['\x07\x03\x10+\x00\x01\xf0\xa4'] = '\x07\x03\x02\x00\x0fp@'

# Slave address 7, read_register(0x102F). This is firmware version.
# Response value 400
GOOD_RTU_RESPONSES['\x07\x03\x10/\x00\x01\xb1e'] = '\x07\x03\x02\x01\x901\xb8'


## Recorded ASCII data from Delta DTB4824 ##
############################################
# (Sorted by register number)

# Slave address 7, read_bit(0x0800). This is LED AT.
# Response value 0
GOOD_ASCII_RESPONSES[':070208000001EE\r\n'] = ':07020100F6\r\n'

# Slave address 7, read_bit(0x0801). This is LED Out1.
# Response value 1
GOOD_ASCII_RESPONSES[':070208010001ED\r\n'] = ':07020101F5\r\n' 

# Slave address 7, read_bit(0x0802). This is LED Out2.
# Response value 0
GOOD_ASCII_RESPONSES[':070208020001EC\r\n'] = ':07020100F6\r\n'

# Slave address 7, _performCommand(2, '\x08\x10\x00\x09'). This is reading 9 bits starting at 0x0810.
# Response value '\x02\x17\x00'
GOOD_ASCII_RESPONSES[':070208100009D6\r\n'] = ':0702021700DE\r\n'

# Slave address 7, write_bit(0x0810, 1) This is "Communication write in enabled".
GOOD_ASCII_RESPONSES[':07050810FF00DD\r\n'] = ':07050810FF00DD\r\n'

# Slave address 7, read_bit(0x0814). This is RUN/STOP setting.
# Response value 1
GOOD_ASCII_RESPONSES[':070208140001DA\r\n'] = ':07020101F5\r\n'

# Slave address 7, write_bit(0x0814, 0). This is STOP.
GOOD_ASCII_RESPONSES[':070508140000D8\r\n'] = ':070508140000D8\r\n'

# Slave address 7, write_bit(0x0814, 1). This is RUN.
GOOD_ASCII_RESPONSES[':07050814FF00D9\r\n'] = ':07050814FF00D9\r\n'

# Slave address 7, read_registers(0x1000, 2). This is process value (PV) and setpoint (SV).
# Response value [64990, 350]
GOOD_ASCII_RESPONSES[':070310000002E4\r\n'] = ':070304FDDE015EB8\r\n'

# Slave address 7, read_register(0x1000). This is process value (PV).
# Response value 64990
GOOD_ASCII_RESPONSES[':070310000001E5\r\n'] = ':070302FDDE19\r\n'

# Slave address 7, read_register(0x1001, 1). This is setpoint (SV).
# Response value 80.0
GOOD_ASCII_RESPONSES[':070310010001E4\r\n'] = ':0703020320D1\r\n'

# Slave address 7, write_register(0x1001, 25, 1, functioncode=6)
GOOD_ASCII_RESPONSES[':0706100100FAE8\r\n'] = ':0706100100FAE8\r\n'

# Slave address 7, write_register(0x1001, 0x0320, functioncode=6) # Write value 800 to register 0x1001.
# This is a setpoint of 80.0 degrees (Centigrades, dependent on setting).
GOOD_ASCII_RESPONSES[':070610010320BF\r\n'] = ':070610010320BF\r\n'

# Slave address 7, read_register(0x1004). This is sensor type.
# Response value 14
GOOD_ASCII_RESPONSES[':070310040001E1\r\n'] = ':070302000EE6\r\n'

# Slave address 7, read_register(0x1005) This is control method.
# Response value 1
GOOD_ASCII_RESPONSES[':070310050001E0\r\n'] = ':0703020001F3\r\n'

# Slave address 7, read_register(0x1006). This is heating/cooling selection.
# Response value 0
GOOD_ASCII_RESPONSES[':070310060001DF\r\n'] = ':0703020000F4\r\n'

# Slave address 7, read_register(0x1012, 1). This is output 1.    
# Response value 100.0
GOOD_ASCII_RESPONSES[':070310120001D3\r\n'] = ':07030203E809\r\n'

# Slave address 7, read_register(0x1013, 1). This is output 2.    
# Response value 0.0
GOOD_ASCII_RESPONSES[':070310130001D2\r\n'] = ':0703020000F4\r\n'

# Slave address 7, read_register(0x1023). This is system alarm setting.
# Response value 0
GOOD_ASCII_RESPONSES[':070310230001C2\r\n'] = ':0703020000F4\r\n'

# Slave address 7, read_register(0x102A). This is LED status.
# Response value 64
GOOD_ASCII_RESPONSES[':0703102A0001BB\r\n'] = ':0703020040B4\r\n'

# Slave address 7, read_register(0x102B). This is pushbutton status.
# Response value 15
GOOD_ASCII_RESPONSES[':0703102B0001BA\r\n'] = ':070302000FE5\r\n'

# Slave address 7, read_register(0x102F). This is firmware version.
# Response value 400
GOOD_ASCII_RESPONSES[':0703102F0001B6\r\n'] = ':070302019063\r\n'


#######################
# Group recorded data #
#######################

RTU_RESPONSES.update(WRONG_RTU_RESPONSES)
RTU_RESPONSES.update(GOOD_RTU_RESPONSES)
ASCII_RESPONSES.update(WRONG_ASCII_RESPONSES)
ASCII_RESPONSES.update(GOOD_ASCII_RESPONSES)

#################
# Run the tests #
#################

if __name__ == '__main__':

        ## Run all tests ##
    
    unittest.main(verbosity=VERBOSITY)
    
    
        ## Run a test class ##
    
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestDummyCommunicationHandleLocalEcho)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestCalculateCrcString)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestHexdecode)
    
    #unittest.TextTestRunner(verbosity=2).run(suite)


        ## Run a single test ##
    
    #suite = unittest.TestSuite()
    #suite.addTest(TestDummyCommunication("testReadLong"))
    #suite.addTest(TestDummyCommunication("testCommunicateWrongLocalEcho"))
    #unittest.TextTestRunner(verbosity=2).run(suite)
    
    
        ## Run individual commands ##
    
    #print repr(minimalmodbus._calculateCrcString('\x01\x4bTESTCOMMAND2'))

