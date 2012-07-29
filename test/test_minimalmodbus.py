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

This Python file was changed (committed) at $Date$,
which was $Revision$.

"""

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"

__revision__  = "$Rev$"
__date__      = "$Date$"

import sys
import unittest

import minimalmodbus
import dummy_serial

###########################################################
# For showing the error messages caught by assertRaises() #
###########################################################

VERBOSITY = 0
"""Verbosity level for the unit testing. Use value 0 or 2. Note that it only has an effect for Python 2.7 and above."""

SHOW_ERROR_MESSAGES_FOR_ASSERTRAISES = False
"""Set this to :const:`True` for printing the error messages caught by assertRaises().

If set to :const:`True`, any unintentional error messages raised during the processing of the command in :meth:`.assertRaises` are also caught (not counted). It will be printed in the short form, and will show no traceback.  It can also be useful to set :data:`VERBOSITY` = 2.
"""

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


##############################
# Constants for type testing #
##############################

_NOT_INTERGERS = [0.0, 1.0, '1', ['1'], [1], None]

_NOT_NUMERICALS = ['1', ['1'], [1], None, ['\x00\x2d\x00\x58'], ['A', 'B', 'C']]

_NOT_STRINGS =   [1, 0.0, 1.0,      ['1'], [1], None, ['\x00\x2d\x00\x58'], ['A', 'B', 'C'], True, False]

_NOT_BOOLEANS =  ['True', 'False', -1, 1, 2, 0, 8, 9999999, -1.0, 1.0, 0.0, [True], [False], [1], [1.0] ]

_NOT_INTLISTS = [0.0, 1.0, '1', ['1'], None, ['\x00\x2d\x00\x58'], ['A', 'B', 'C'], [1.0], [1.0, 2.0] ]


####################
# Payload handling #
####################

class TestEmbedPayload(ExtendedTestCase):

    knownValues=[
    (2, 2, '123', '\x02\x02123X\xc2'),
    (1, 16, 'ABC', '\x01\x10ABC<E'),
    (0, 5, 'hjl', '\x00\x05hjl\x8b\x9d'),
    ]

    def testKnownValues(self):
        for slaveaddress, functioncode, inputstring, knownresult in self.knownValues:

            result = minimalmodbus._embedPayload(slaveaddress, functioncode, inputstring)
            self.assertEqual(result, knownresult)

    def testWrongSlaveaddressValue(self):
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 248, 16, 'ABC')
        self.assertRaises(ValueError, minimalmodbus._embedPayload, -1, 16, 'ABC')

    def testSlaveaddressNotInteger(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._embedPayload, value, 16, 'ABC')

    def testWrongFunctioncodeValue(self):
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 1, 222, 'ABC')
        self.assertRaises(ValueError, minimalmodbus._embedPayload, 1, -1, 'ABC')

    def testFunctioncodeNotInteger(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._embedPayload, 1, value, 'ABC')

    def testPayloadNotString(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._embedPayload, 1, 16, value)


class TestExtractPayload(ExtendedTestCase):

    knownValues=TestEmbedPayload.knownValues

    def testKnownValues(self):
        for address, functioncode, knownresult, inputstring in self.knownValues:

            result = minimalmodbus._extractPayload(inputstring, address, functioncode )
            self.assertEqual(result, knownresult)

    def testTooShortMessage(self):
        self.assertRaises(ValueError, minimalmodbus._extractPayload, 'A', 2, 2)

    def testWrongSlaveAddress(self):
        for value in [3, 248, -1]:
            self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', value, 2)

    def testSlaveaddressNotInteger(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', value, 2)

    def testErrorindicationFromSlave(self):
        self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x82123q\x02', 2, 2)

    def testWrongFunctionCode(self):
        self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', 2, 3)
        self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x72123B\x02', 2, 2) # Other value in response
        self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', 2, 95)
        self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', 2, -1)
        self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', 2, 128)

    def testFunctionCodeNotInteger(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._extractPayload, '\x02\x02123X\xc2', 2, value)

    def testWrongCrc(self):
        self.assertRaises(ValueError, minimalmodbus._extractPayload, '\x02\x02123X\xc3', 2, 2)


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
    (0.0,  0, False, False, '\x00\x00' ),
    (77.0, 1, False, False, '\x03\x02' ),
    (77.0, 1, True,  False, '\x02\x03' ),
    (770,  0, False, False, '\x03\x02' ),
    (770,  0, True,  False, '\x02\x03' ),
    (770,  0, False,  True, '\x03\x02' ),
    (-1,   0, False,  True, '\xff\xff' ),
    (-1,   1, False,  True, '\xff\xf6' ),
    ]
    #TODO: More! (out of range, negative values etc)

    def testKnownValues(self):
        for inputvalue, numberOfDecimals, LsbFirst, signed, knownstring in self.knownValues:
            resultstring = minimalmodbus._numToTwoByteString(inputvalue, numberOfDecimals, LsbFirst, signed)
            self.assertEqual(resultstring, knownstring)

    def testWrongInputValue(self):
        #TODO: More!
        self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, 77000, 0, False) # Gives DeprecationWarning instead of ValueError for Python 2.6
        self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, -77, 1, False)
        self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, -77, 10, False, True)
        self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, 77, 4, False)
        self.assertRaises(ValueError, minimalmodbus._numToTwoByteString, 77, -1, False)

    def testWrongInputType(self):
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, minimalmodbus._numToTwoByteString, value,  1, False, False)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._numToTwoByteString, 77, value, False, False)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, minimalmodbus._numToTwoByteString, 77,     1, value, False)
            self.assertRaises(TypeError, minimalmodbus._numToTwoByteString, 77,     1, False, value)


class TestTwoByteStringToNum(ExtendedTestCase):

    knownValues=TestNumToTwoByteString.knownValues

    def testKnownValues(self):
        for knownvalue, numberOfDecimals, LsbFirst, signed, bytestring in self.knownValues:
            if not LsbFirst:
                resultvalue = minimalmodbus._twoByteStringToNum(bytestring, numberOfDecimals, signed)
                self.assertEqual(resultvalue, knownvalue)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._twoByteStringToNum, 'ABC', 1)
        self.assertRaises(ValueError, minimalmodbus._twoByteStringToNum, 'A', 1)
        self.assertRaises(ValueError, minimalmodbus._twoByteStringToNum, 'AB', -1)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._twoByteStringToNum, value, 1)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._twoByteStringToNum, 'AB', value)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, minimalmodbus._twoByteStringToNum, '\x03\x02', 1, value)


class TestSanityTwoByteString(ExtendedTestCase):

    knownValues=TestNumToTwoByteString.knownValues

    def testSanity(self):
        for value, numberOfDecimals, LsbFirst, signed, bytestring in self.knownValues:
            if not LsbFirst:
                resultvalue = minimalmodbus._twoByteStringToNum( \
                    minimalmodbus._numToTwoByteString(value, numberOfDecimals, LsbFirst, signed), \
                    numberOfDecimals, signed )
                self.assertEqual(resultvalue, value)

        return #TODO This part is pretty time consuming
        for value in range(0x10000):
            resultvalue = minimalmodbus._twoByteStringToNum( minimalmodbus._numToTwoByteString(value) )
            self.assertEqual(resultvalue, value)


class TestLongToBytestring(ExtendedTestCase):

    # TODO: Include more tests for range etc
    # TODO: More
    knownValues=[
    (0,  False, 2, '\x00\x00\x00\x00'),
    (0,  True,  2, '\x00\x00\x00\x00'),
    (1,  False, 2, '\x00\x00\x00\x01'),
    (2,  False, 2, '\x00\x00\x00\x02'),
    (-1, True,  2, '\xff\xff\xff\xff'),
    ]
    #(1000000,    False, 2),
    #(-200000000, True, 2),
    #(75000,      False, 2),
    #]

    def testKnownValues(self):
        for value, signed, numberOfRegisters, knownstring in self.knownValues:
            resultstring = minimalmodbus._longToBytestring(value, signed, numberOfRegisters)
            self.assertEqual(resultstring, knownstring)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._longToBytestring, 222222222222222, True,  2)
        self.assertRaises(ValueError, minimalmodbus._longToBytestring, -1,              False, 2)
        for numberOfRegisters in [0, 1, 3, 4, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, minimalmodbus._longToBytestring, 1, True, numberOfRegisters)

    def testWrongInputType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._longToBytestring, value, True, 2)
            self.assertRaises(TypeError, minimalmodbus._longToBytestring, 1,     True, value)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, minimalmodbus._longToBytestring, 1, value, 2)


class TestBytestringToLong(ExtendedTestCase):

    knownValues=TestLongToBytestring.knownValues

    def testKnownValues(self):
        for knownvalue, signed, numberOfRegisters, bytestring in self.knownValues:
            resultvalue = minimalmodbus._bytestringToLong(bytestring, signed, numberOfRegisters)
            self.assertEqual(resultvalue, knownvalue)

    def testWrongInputValue(self):
        for inputstring in ['', 'A', 'AA', 'AAA', 'AAAAA']:
            self.assertRaises(ValueError, minimalmodbus._bytestringToLong, inputstring, True, 2)

        for numberOfRegisters in [0, 1, 3, 4, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, minimalmodbus._bytestringToLong, 'AAAA', True, numberOfRegisters)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToLong, value, True, 2)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToLong, 'AAAA', value, 2)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToLong, 'AAAA', True, value)


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

    #TODO:  more. Range?
    knownValues=[
    (1.0,     2, '?\x80\x00\x00'),
    (1,       2, '\x3f\x80\x00\x00'),
    (1.0,     2, '\x3f\x80\x00\x00'),
    (100.0,   2, '\x42\xc8\x00\x00'),
    (1.0e5,   2, '\x47\xc3\x50\x00'),
    (1.0,     4, '\x3f\xf0\x00\x00\x00\x00\x00\x00'),
    (1,       2, '\x3f\x80\x00\x00'), # wikipedia
    (-2,      2, '\xc0\x00\x00\x00'),
    (2,       4, '\x40\x00\x00\x00\x00\x00\x00\x00'),
    (-2,      4, '\xc0\x00\x00\x00\x00\x00\x00\x00'),
    ]

    def testKnownValues(self):
        for value, numberOfRegisters, knownstring in self.knownValues:
            resultstring = minimalmodbus._floatToBytestring(value, numberOfRegisters)
            self.assertEqual(resultstring, knownstring)

    def testWrongInputValue(self):
        #self.assertRaises(ValueError, minimalmodbus._floatToBytestring, 1.1E9999999,  2) #TODO fix!
        for numberOfRegisters in [0, 1, 3, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, minimalmodbus._floatToBytestring, 1.1, numberOfRegisters)

    def testWrongInputType(self):
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, minimalmodbus._floatToBytestring, value, 2)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._floatToBytestring, 1.1, value)


class TestBytestringToFloat(ExtendedTestCase):

    knownValues=TestFloatToBytestring.knownValues

    def testKnownValues(self):
        for knownvalue, numberOfRegisters, bytestring in self.knownValues:
            resultvalue = minimalmodbus._bytestringToFloat(bytestring, numberOfRegisters)
            self.assertAlmostEqual(resultvalue, knownvalue)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._bytestringToFloat, 'A',  2) # TODO more
        for numberOfRegisters in [0, 1, 3, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, minimalmodbus._bytestringToFloat, 'ABCD', numberOfRegisters)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToFloat, value, 2)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToFloat, 1.1, value)


class TestSanityFloat(ExtendedTestCase):

    knownValues = [
    (1,      2),
    (1.0,    2),
    (1.1,    2),
    (-1.1,   2),
    (-1.1,   4),
    (100,    2),
    (100.0,  2),
    (1.0E16, 4),
    (1.5E16, 4),
    ]
    #TODO: More values, adjust AlmostEqual
    # todo knownValues=TestFloatToBytestring.knownValues

    def testSanity(self):
        for value, numberOfRegisters in self.knownValues:
            resultvalue = minimalmodbus._bytestringToFloat( \
                minimalmodbus._floatToBytestring(value, numberOfRegisters), numberOfRegisters)
            self.assertAlmostEqual(resultvalue, value)


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
            self.assertRaises(TypeError, minimalmodbus._valuelistToBytestring, value, 4)
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
        self.assertRaises(ValueError, minimalmodbus._bytestringToValuelist, '', 1)
        self.assertRaises(ValueError, minimalmodbus._bytestringToValuelist, '\x00\x01', 0)
        self.assertRaises(ValueError, minimalmodbus._bytestringToValuelist, '\x00\x01', -1)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToValuelist, value, 1)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToValuelist, 'A', value)


class TestSanityValuelist(ExtendedTestCase):

    knownValues=TestValuelistToBytestring.knownValues

    def testSanity(self):
        for valuelist, numberOfRegisters, bytestring in self.knownValues:
            resultlist = minimalmodbus._bytestringToValuelist( \
                minimalmodbus._valuelistToBytestring(valuelist, numberOfRegisters), numberOfRegisters)
            self.assertEqual(resultlist, valuelist)  #TODO: Is this really functional?


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
        self.assertRaises(ValueError, minimalmodbus._textstringToBytestring, '', 1)
        self.assertRaises(ValueError, minimalmodbus._textstringToBytestring, 'A', -1)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._textstringToBytestring, value, 1)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._textstringToBytestring, 'AB', value)


class TestBytestringToTextstring(ExtendedTestCase):

    knownValues=TestTextstringToBytestring.knownValues

    def testKnownValues(self):
        for knownstring, numberOfRegisters, bytestring in self.knownValues:
            resultstring = minimalmodbus._bytestringToTextstring(bytestring, numberOfRegisters)
            self.assertEqual(resultstring.strip(), knownstring)

    def testWrongInputValue(self):
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, 'A', 1)
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, '', 1)
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, '', 0)
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, 'ABC', 1)
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, 'AB', 0)
        self.assertRaises(ValueError, minimalmodbus._bytestringToTextstring, 'AB', -1)

    def testWrongInputType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToTextstring, value, 1)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._bytestringToTextstring, 'AB', value)


class TestSanityTextstring(ExtendedTestCase):

    knownValues=TestTextstringToBytestring.knownValues

    def testSanity(self):
        for textstring, numberOfRegisters, bytestring in self.knownValues:
            resultstring = minimalmodbus._bytestringToTextstring( \
                minimalmodbus._textstringToBytestring(textstring, numberOfRegisters), numberOfRegisters)
            self.assertEqual( resultstring.strip(), textstring )


class TestBitResponseToValue(ExtendedTestCase):

    def testKnownValues(self):
        self.assertEqual(minimalmodbus._bitResponseToValue('\x00'), 0)
        self.assertEqual(minimalmodbus._bitResponseToValue('\x01'), 1)

    def testWrongValues(self):
        self.assertRaises(ValueError, minimalmodbus._bitResponseToValue, 'ABC' )

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
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 16, 1)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, -1, 1)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 128, 1)

    def testFunctionCodeNotInteger(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._createBitpattern, value, 1)

    def testWrongValue(self):
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 5, 2)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 5, 222)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 5, -1)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 15, 2)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 15, 222)
        self.assertRaises(ValueError, minimalmodbus._createBitpattern, 15, -1)

    def testValueNotInteger(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._createBitpattern, 5, value)
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

    def testNotIntegerInput(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._twosComplement, value, 8)

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


class TestFromTwosComplement(ExtendedTestCase):

    knownValues=TestTwosComplement.knownValues

    def testKnownValues(self):
        for knownresult, bits, x in self.knownValues:

            result = minimalmodbus._fromTwosComplement(x, bits)
            self.assertEqual(result, knownresult)

    def testNotIntegerInput(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._fromTwosComplement, value, 8)
            self.assertRaises(TypeError, minimalmodbus._fromTwosComplement, 1, value)

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


class TestSanityTwosComplement(ExtendedTestCase):

    knownValues = [1, 2, 4, 8, 12, 16]

    def testSanity(self):

        return #TODO

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

    def testNotIntegerInput(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._setBitOn, value, 1)
            self.assertRaises(TypeError, minimalmodbus._setBitOn, 1, value)

    def testNegativeInput(self):
        self.assertRaises(ValueError, minimalmodbus._setBitOn, 1, -1)
        self.assertRaises(ValueError, minimalmodbus._setBitOn, -2, 1)


class TestXOR(ExtendedTestCase):

    knownValues=[
    (1,1,0),
    (2,1,3),
    (5,1,4),
    ]

    def testKnownValues(self):
        for int1, int2, knownresult in self.knownValues:

            result = minimalmodbus._XOR(int1, int2)
            self.assertEqual(result, knownresult)

    def testKnownLoop(self):
        for i in range(10):
            for k in range(10):

                knownresult = i ^ k
                result = minimalmodbus._XOR(i, k)
                self.assertEqual(result, knownresult)

    def testNotIntegerInput(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._XOR, value, 1)
            self.assertRaises(TypeError, minimalmodbus._XOR, 1, value)

    def testNegativeInput(self):
        self.assertRaises(ValueError, minimalmodbus._XOR, 1, -1)
        self.assertRaises(ValueError, minimalmodbus._XOR, -1, 1)


class TestRightshift(ExtendedTestCase):

    knownValues=[
    (9,4,1),
    (5,2,1),
    (6,3,0),
    ]

    def testKnownValues(self):
        for x, knownshifted, knowncarry in self.knownValues:

            resultshifted, resultcarry = minimalmodbus._rightshift(x)

            self.assertEqual(resultshifted, knownshifted)
            self.assertEqual(resultcarry, knowncarry)

    def testKnownLoop(self):
        for x in range(256):

            knownshifted = x >> 1
            knowncarry = x & 1
            resultshifted, resultcarry = minimalmodbus._rightshift(x)

            self.assertEqual(resultshifted, knownshifted)
            self.assertEqual(resultcarry, knowncarry)

    def testNotIntegerInput(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._rightshift, value)

    def testNegativeInput(self):
        self.assertRaises(ValueError, minimalmodbus._rightshift, -1)


############################
# Error checking functions #
############################

class TestCalculateCrcString(ExtendedTestCase):

    knownValues=[
    ('\x02\x07','\x41\x12'), # Example from MODBUS over Serial Line Specification and Implementation Guide V1.02
    ('ABCDE', '\x0fP'),
    ]

    def testKnownValues(self):
        for inputstring, knowncrc in self.knownValues:
            resultcrc = minimalmodbus._calculateCrcString(inputstring)
            self.assertEqual(resultcrc, knowncrc)

    def testNotStringInput(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._calculateCrcString, value)


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
        for value in [ 0.0, 1.0, '1', ['1'], [1] ]: # Note that `None` is allowed
            self.assertRaises(TypeError, minimalmodbus._checkString, 'DEF', minlength=value, maxlength=3,     description='ABC')
            self.assertRaises(TypeError, minimalmodbus._checkString, 'DEF', minlength=3,     maxlength=value, description='ABC')

    def testDescriptionNotString(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkString, 'DEF', minlength=3, maxlength=3, description=value)


class TestCheckInt(ExtendedTestCase):

    def testKnownValues(self):
        minimalmodbus._checkInt(47, minvalue=None, maxvalue=None, description='ABC')
        minimalmodbus._checkInt(47, minvalue=40, maxvalue=50, description='ABC')
        minimalmodbus._checkInt(47, minvalue=-40, maxvalue=50, description='ABC')
        minimalmodbus._checkInt(47, description='ABC', maxvalue=50, minvalue=40)
        minimalmodbus._checkInt(47, minvalue=None, maxvalue=50, description='ABC')
        minimalmodbus._checkInt(47, minvalue=40, maxvalue=None, description='ABC')

    def testTooLargeValue(self):
        self.assertRaises(ValueError, minimalmodbus._checkInt, 47, minvalue=30, maxvalue=40, description='ABC')
        self.assertRaises(ValueError, minimalmodbus._checkInt, 47, maxvalue=46)

    def testTooSmallValue(self):
        self.assertRaises(ValueError, minimalmodbus._checkInt, 47, minvalue=48 )
        self.assertRaises(ValueError, minimalmodbus._checkInt, 47, minvalue=48, maxvalue=None, description='ABC')

    def testInconsistentLimits(self):
        self.assertRaises(ValueError, minimalmodbus._checkInt, 47, minvalue=47, maxvalue=45, description='ABC')

    def testNotIntegerInput(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._checkInt, value, minvalue=40)
        for value in [ 0.0, 1.0, '1', ['1'], [1] ]: # Note that `None` is allowed
            self.assertRaises(TypeError, minimalmodbus._checkInt, 47,    minvalue=value, maxvalue=50,    description='ABC')
            self.assertRaises(TypeError, minimalmodbus._checkInt, 47,    minvalue=40,    maxvalue=value, description='ABC')

    def testDescriptionNotString(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._checkInt, 47, minvalue=40, maxvalue=50, description=value)


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
        for value in ['1', ['1'], [1], ['\x00\x2d\x00\x58'], ['A', 'B', 'C']]: # Note that `None` is allowed
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


###########################################
# Communication using a dummy serial port #
###########################################

class TestDummyCommunication(ExtendedTestCase):

    ## Test fixture ##

    def setUp(self):

        # Prepare a dummy serial port to have proper responses
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'

        # Monkey-patch a dummy serial port for testing purpose
        minimalmodbus.serial.Serial = dummy_serial.Serial

        # Initialize a (dummy) instrument
        minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = False
        self.instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 1) # port name, slave address (in decimal)
        self.instrument.debug = False

    ## Read bit ##

    def testReadBit(self):
        self.assertEqual( self.instrument.read_bit(61),                 1 ) # Functioncode 2
        self.assertEqual( self.instrument.read_bit(61, functioncode=2), 1 )
        self.assertEqual( self.instrument.read_bit(61, 2),              1 )
        self.assertEqual( self.instrument.read_bit(62, functioncode=1), 0 ) # Functioncode 1
        self.assertEqual( self.instrument.read_bit(62, 1),              0 )

    def testReadBitWrongValue(self):
        self.assertRaises(ValueError, self.instrument.read_bit, -1) # Wrong address
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
        self.assertRaises(ValueError, self.instrument.write_bit, 65536, 1) # Wrong address
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

    #TODO: Also negative values!

    def testReadRegister(self):
        self.assertEqual(       self.instrument.read_register(289),       770)
        self.assertEqual(       self.instrument.read_register(5),         184)
        self.assertEqual(       self.instrument.read_register(289, 0),    770)
        self.assertEqual(       self.instrument.read_register(289, 0, 3), 770) # functioncode 3
        self.assertEqual(       self.instrument.read_register(14,  0, 4), 880) # functioncode 4
        self.assertAlmostEqual( self.instrument.read_register(289, 1),    77.0)
        self.assertAlmostEqual( self.instrument.read_register(289, 2),    7.7)

    #instrument.read_register(101, signed=True) # '\x01\x03\x00e\x00\x01\x94\x15'
#instrument.read_register(101) # '\x01\x03\x00e\x00\x01\x94\x15' (same)


    def testReadRegisterWrongValue(self):
        self.assertRaises(ValueError, self.instrument.read_register, -1) # Wrong address
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

    #TODO: Also negative values!

    def testWriteRegister(self):
        self.instrument.write_register(35, 20)
        self.instrument.write_register(35, 20, functioncode = 16)
        self.instrument.write_register(35, 20.0)
        self.instrument.write_register(24, 50)
        self.instrument.write_register(45, 88, functioncode = 6)

        #instrument.write_register(101, 5) # '\x01\x10\x00e\x00\x01\x02\x00\x05o\xa6'
        #instrument.write_register(101, 5, 1) # '\x01\x10\x00e\x00\x01\x02\x002.p'
        #instrument.write_register(101, 5, signed=True) # '\x01\x10\x00e\x00\x01\x02\x00\x05o\xa6' (same)
        #instrument.write_register(101, -5, signed=True)   # '\x01\x10\x00e\x00\x01\x02\xff\xfb\xaf\xd6'
        #instrument.write_register(101, -5, 1, signed=True) # '\x01\x10\x00e\x00\x01\x02\xff\xceo\xc1'


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

    #instrument.read_long(102) # '\x01\x03\x00f\x00\x02$\x14'
    #instrument.read_long(102, signed=True) #'\x01\x03\x00f\x00\x02$\x14' (same)



    ## Write Long ##

    #instrument.write_long(102, 5) # '\x01\x10\x00f\x00\x02\x04\x00\x00\x00\x05\xb5\xae'
    #instrument.write_long(102, -5, signed=True) # '\x01\x10\x00f\x00\x02\x04\xff\xff\xff\xfbu\xfa'
    #instrument.write_long(102, 3, False) '\x01\x10\x00f\x00\x02\x04\x00\x00\x00\x035\xac'
    #instrument.write_long(102, -3, True) '\x01\x10\x00f\x00\x02\x04\xff\xff\xff\xfd\xf5\xf8'


    ## Read Float ##

    #instrument.read_float(103, 3, 2) # '\x01\x03\x00g\x00\x02u\xd4'
    #instrument.read_float(103, 3, 4) # '\x01\x03\x00g\x00\x04\xf5\xd6'


    ## Write Float ##
    # Todo: byte order

    def testWriteFloat(self):
        self.instrument.write_float(103, 1.1)
        self.instrument.write_float(103, 1.1, 4)

    def testWriteFloatWrongValue(self):
        self.assertRaises(ValueError, self.instrument.write_float, -1,     1.1) # Wrong address
        self.assertRaises(ValueError, self.instrument.write_float, 65536,  1.1)
        for value in [-1, 0, 1, 3, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, self.instrument.write_float, 103, 1.1, value) # Wrong number of registers

    def testWriteFloatWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_float, value, 1.1)
            self.assertRaises(TypeError, self.instrument.write_float, 103, 1.1, value)
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, self.instrument.write_float, 103, value)


    ## Read String ##

    def testReadString(self):
        self.assertEqual( self.instrument.read_string(104, 1),    'AB')
        self.assertEqual( self.instrument.read_string(104, 4),    'ABCDEFGH')
        self.assertEqual( self.instrument.read_string(104, 4, 3), 'ABCDEFGH')

    def testReadStringWrongValue(self):
        self.assertRaises(ValueError, self.instrument.read_string, -1) # Wrong address
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
        self.assertRaises(ValueError, self.instrument.write_string, -1,    'A') # Wrong address
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
        self.assertRaises(ValueError, self.instrument.read_registers, -1,    1) # Wrong address
        self.assertRaises(ValueError, self.instrument.read_registers, 65536, 1)
        self.assertRaises(ValueError, self.instrument.read_registers, 105,   -1) # Wrong number of registers
        self.assertRaises(ValueError, self.instrument.read_registers, 105,   256)
        self.assertRaises(ValueError, self.instrument.read_registers, 105,   1,  1) # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_registers, 105,   1,  256)
        self.assertRaises(ValueError, self.instrument.read_registers, 105,   1,  -1)

    def testReadRegistersWrongAddressType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_registers, value, 1)
            self.assertRaises(TypeError, self.instrument.read_registers, 105, value)
            self.assertRaises(TypeError, self.instrument.read_registers, 105, 1, value)


    ## Write Registers ##

    def testWriteRegisters(self):
        self.instrument.write_registers(105, [2])
        self.instrument.write_registers(105, [2, 4, 8])

    def testWriteRegistersWrongValue(self):
        self.assertRaises(ValueError, self.instrument.write_registers, -1,    [2]) # Wrong address
        self.assertRaises(ValueError, self.instrument.write_registers, 65536, [2])
        self.assertRaises(ValueError, self.instrument.write_registers, 105,   []) # Wrong list value
        self.assertRaises(ValueError, self.instrument.write_registers, 105,   [-1])

    def testWriteRegistersWrongType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_registers, value, [2])
        self.assertRaises(TypeError, self.instrument.write_registers,     105,   1)
        self.assertRaises(TypeError, self.instrument.write_registers,     105,   1.0)
        self.assertRaises(TypeError, self.instrument.write_registers,     105,   '[2]')
        self.assertRaises(TypeError, self.instrument.write_registers,     105,   ['2'])


    ## Generic command ##

    # TODO: Change a lot. Negative values, payload

    def testGenericCommand(self):
        self.assertEqual( self.instrument._genericCommand(3, 289), 770 ) # Read register 289
        self.assertEqual( self.instrument._genericCommand(2, 61),  1 ) # Read bit 61

    def testGenericCommandWrongFunctioncode(self):
        self.assertRaises(ValueError, self.instrument._genericCommand, 35, 20)
        self.assertRaises(ValueError, self.instrument._genericCommand, -1, 20)
        self.assertRaises(ValueError, self.instrument._genericCommand, 128, 20)

    def testGenericCommandWrongFunctioncodeType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument._genericCommand, value, 20)

    def testGenericCommandWrongRegisteraddress(self):
        self.assertRaises(ValueError, self.instrument._genericCommand, 3, -1)
        self.assertRaises(ValueError, self.instrument._genericCommand, 3, 65536)

    def testGenericCommandWrongRegisteraddressType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument._genericCommand, 3, value)

    def testGenericCommandWrongValue(self):
        self.assertRaises(ValueError, self.instrument._genericCommand, 3, 20, -1.0)

    def testGenericCommandWrongValueType(self):

        pass # TODO!
        #self.assertRaises(TypeError, self.instrument._genericCommand, 3, 20, [1])
        #self.assertRaises(TypeError, self.instrument._genericCommand, 3, 20, [1.0])
        #self.assertRaises(TypeError, self.instrument._genericCommand, 3, 20, '1')
        #self.assertRaises(TypeError, self.instrument._genericCommand, 3, 20, '1.0')

    def testGenericCommandWrongNumberofdecimals(self):
        self.assertRaises(ValueError, self.instrument._genericCommand, 3, 20, numberOfDecimals=-1)

    def testGenericCommandWrongNumberofdecimalsType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument._genericCommand, 3, 20, numberOfDecimals=value)


    ## Perform command ##

    def testPerformcommandKnownResponse(self):
        self.assertEqual( self.instrument._performCommand(16, 'TESTCOMMAND'), 'TESTCOMMANDRESPONSE')
        self.assertEqual( self.instrument._performCommand(75, 'TESTCOMMAND2'), 'TESTCOMMANDRESPONSE2')
        self.assertEqual( self.instrument._performCommand(2, '\x00\x3d\x00\x01'), '\x01\x01' ) # Read bit register 61 on slave 1 using function code 2.

    def testPerformcommandWrongFunctioncode(self):
        #self.assertRaises(ValueError, self.instrument._performCommand, 35, 'TESTCOMMAND') # Wrong ValueError message (CRC error = 'Not found in dictionary')
        self.assertRaises(ValueError, self.instrument._performCommand, -1, 'TESTCOMMAND')
        self.assertRaises(ValueError, self.instrument._performCommand, 128, 'TESTCOMMAND')

    def testPerformcommandWrongFunctioncodeType(self):
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument._performCommand, value, 'TESTCOMMAND')

    def testPerformcommandWrongPayloadType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, self.instrument._performCommand, 16, value)


    ## Communicate ##

    def testCommunicateKnownResponse(self):
        self.assertEqual( self.instrument._communicate('TESTMESSAGE'), 'TESTRESPONSE' )

    def testCommunicateWrongType(self):
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, self.instrument._communicate, value)

    def testCommunicateNoMessage(self):
        self.assertRaises(ValueError, self.instrument._communicate, '')

    def testCommunicateNoResponse(self):
        self.assertRaises(IOError, self.instrument._communicate, 'MessageForEmptyResponse')


    ## __repr__ ##

    def testRepresentation(self):
        representation = repr(self.instrument)
        self.assertTrue( 'minimalmodbus.Instrument<id=' in representation )
        self.assertTrue( ', address=1, close_port_after_each_call=False, debug=False, serial=dummy_serial.Serial<id=' in representation )
        self.assertTrue( ", open=True>(latestWrite='')>" in representation )


    ## Tear down test fixture ##

    def tearDown(self):
        self.instrument = None
        del(self.instrument)


class TestDummyCommunicationOmegaSlave1(ExtendedTestCase):

    def setUp(self):
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'
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
        dummy_serial.RESPONSES = RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'
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


class TestDummyCommunicationWithPortClosure(ExtendedTestCase):

    def setUp(self):
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'

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
        dummy_serial.RESPONSES = RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'

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
        dummy_serial.RESPONSES = RESPONSES
        dummy_serial.DEFAULT_RESPONSE = 'NotFoundInResponseDictionary'

        minimalmodbus.serial.Serial = dummy_serial.Serial
        minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = False
        self.instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 1) # port name, slave address (in decimal)
        self.instrument.debug = True

    def testReadRegister(self):
        self.assertEqual( self.instrument.read_register(289), 770 )

    def tearDown(self):
        self.instrument = None
        del(self.instrument)


RESPONSES = {}
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
RESPONSES['\x01\x02' + '\x00\x3d\x00\x01' + '(\x06'] = '\x01\x02' + '\x01\x01' + '`H'

# Read bit register 62 on slave 1 using function code 1 #
# ----------------------------------------------------- #
# Message:  Slave address 1, function code 1. Register address 62, 1 coil. CRC.
# Response: Slave address 1, function code 1. 1 byte, value=0. CRC.
RESPONSES['\x01\x01' + '\x00\x3e\x00\x01' + '\x9c\x06'] = '\x01\x01' + '\x01\x00' + 'Q\x88'

# Read bit register 63 on slave 1 using function code 2, slave gives wrong byte count #
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 2. Register address 63, 1 coil. CRC.
# Response: Slave address 1, function code 2. 2 bytes (wrong), value=1. CRC.
RESPONSES['\x01\x02' + '\x00\x3f\x00\x01' + '\x89\xc6'] = '\x01\x02' + '\x02\x01' + '`\xb8'

# Read bit register 64 on slave 1 using function code 2, slave gives no response #
# ------------------------------------------------------------------------------ #
# Message:  Slave address 1, function code 2. Register address 64, 1 coil. CRC.
# Response: (empty string)
RESPONSES['\x01\x02' + '\x00\x40\x00\x01' + '\xb8\x1e'] = ''


#                ##  WRITE BIT  ##

# Write bit register 71 on slave 1 using function code 5 #
# ------------------------------------------------------ #
# Message:  Slave address 1, function code 5. Register address 71, value 1 (FF00). CRC.
# Response: Slave address 1, function code 5. Register address 71, value 1 (FF00). CRC.
RESPONSES['\x01\x05' + '\x00\x47\xff\x00' + '</'] = '\x01\x05' + '\x00\x47\xff\x00' + '</'

# Write bit register 72 on slave 1 using function code 15 #
# ------------------------------------------------------ #
# Message:  Slave address 1, function code 15. Register address 72, 1 bit, 1 byte, value 1 (0100). CRC.
# Response: Slave address 1, function code 15. Register address 72, 1 bit. CRC.
RESPONSES['\x01\x0f' + '\x00\x48\x00\x01\x01\x01' + '\x0fY'] = '\x01\x0f' + '\x00\x48\x00\x01' + '\x14\x1d'

# Write bit register 73 on slave 1 using function code 15, slave gives wrong number of registers #
# ---------------------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 15. Register address 73, 1 bit, 1 byte, value 1 (0100). CRC.
# Response: Slave address 1, function code 15. Register address 73, 2 bits (wrong). CRC.
RESPONSES['\x01\x0f' + '\x00\x49\x00\x01\x01\x01' + '2\x99'] = '\x01\x0f' + '\x00\x49\x00\x02' + '\x05\xdc'

# Write bit register 74 on slave 1 using function code 5, slave gives wrong write data #
# ------------------------------------------------------------------------------------ #
# Message:  Slave address 1, function code 5. Register address 74, value 1 (FF00). CRC.
# Response: Slave address 1, function code 5. Register address 74, value 0 (0000, wrong). CRC.
RESPONSES['\x01\x05' + '\x00\x4a\xff\x00' + '\xad\xec'] = '\x01\x05' + '\x00\x47\x00\x00' + '}\xdf'


#                ##  READ REGISTER  ##

# Read register 289 on slave 1 using function code 3 #
# ---------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 289, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value=770. CRC=14709.
RESPONSES['\x01\x03' + '\x01!\x00\x01' + '\xd5\xfc'] = '\x01\x03' + '\x02\x03\x02' + '\x39\x75'

# Read register 5 on slave 1 using function code 3 #
# ---------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 289, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value=184. CRC
RESPONSES['\x01\x03' + '\x00\x05\x00\x01' + '\x94\x0b'] = '\x01\x03' + '\x02\x00\xb8' + '\xb86'

# Read register 14 on slave 1 using function code 4 #
# --------------------------------------------------#
# Message:  Slave address 1, function code 4. Register address 14, 1 register. CRC.
# Response: Slave address 1, function code 4. 2 bytes, value=880. CRC.
RESPONSES['\x01\x04' + '\x00\x0e\x00\x01' + 'P\t'] = '\x01\x04' + '\x02\x03\x70' + '\xb8$'


#                ##  WRITE REGISTER  ##

# Write value 50 in register 24 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 24, 1 register, 2 bytes, value=50. CRC.
# Response: Slave address 1, function code 16. Register address 24, 1 register. CRC.
RESPONSES['\x01\x10' + '\x00\x18\x00\x01\x02\x002' + '$]']       = '\x01\x10' + '\x00\x18\x00\x01' + '\x81\xce'

# Write value 20 in register 35 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 35, 1 register, 2 bytes, value=20. CRC.
# Response: Slave address 1, function code 16. Register address 35, 1 register. CRC.
RESPONSES['\x01\x10' + '\x00#\x00\x01' + '\x02\x00\x14' + '\xa1\x0c'] = '\x01\x10' + '\x00#\x00\x01' + '\xf0\x03'

# Write value 88 in register 45 on slave 1 using function code 6 #
# ---------------------------------------------------------------#
# Message:  Slave address 1, function code 6. Register address 45, value=88. CRC.
# Response: Slave address 1, function code 6. Register address 45, value=88. CRC.
RESPONSES['\x01\x06' + '\x00\x2d\x00\x58' + '\x189'] = '\x01\x06' + '\x00\x2d\x00\x58' + '\x189'

# Write value 99 in register 51 on slave 1 using function code 16, slave gives wrong CRC #
# ---------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 51, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 1, function code 16. Register address 51, 1 register. Wrong CRC.
RESPONSES['\x01\x10' + '\x00\x33\x00\x01' + '\x02\x00\x63' + '\xe3\xba'] = '\x01\x10' + '\x00\x33\x00\x01' + 'AB'

# Write value 99 in register 52 on slave 1 using function code 16, slave gives wrong number of registers #
# -------------------------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 52, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 1, function code 16. Register address 52, 2 registers (wrong). CRC.
RESPONSES['\x01\x10' + '\x00\x34\x00\x01' + '\x02\x00\x63' + '\xe2\r'] = '\x01\x10' + '\x00\x34\x00\x02' + '\x00\x06'

# Write value 99 in register 53 on slave 1 using function code 16, slave gives wrong register address #
# ----------------------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 53, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 1, function code 16. Register address 54 (wrong), 1 register. CRC.
RESPONSES['\x01\x10' + '\x00\x35\x00\x01' + '\x02\x00\x63' + '\xe3\xdc'] = '\x01\x10' + '\x00\x36\x00\x01' + '\xe1\xc7'

# Write value 99 in register 54 on slave 1 using function code 16, slave gives wrong slave address #
# ------------------------------------------------------------------------------------------------ #
# Message:  Slave address 1, function code 16. Register address 54, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 2 (wrong), function code 16. Register address 54, 1 register. CRC.
RESPONSES['\x01\x10' + '\x00\x36\x00\x01' + '\x02\x00\x63' + '\xe3\xef'] = '\x02\x10' + '\x00\x36\x00\x01' + '\xe1\xf4'

# Write value 99 in register 55 on slave 1 using function code 16, slave gives wrong functioncode #
# ----------------------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 16. Register address 55, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 1, function code 6 (wrong). Register address 55, 1 register. CRC.
RESPONSES['\x01\x10' + '\x00\x37\x00\x01' + '\x02\x00\x63' + '\xe2>'] = '\x01\x06' + '\x00\x37\x00\x01' + '\xf9\xc4'

# Write value 99 in register 56 on slave 1 using function code 16, slave gives wrong functioncode (indicates an error) #
# -------------------------------------------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 16. Register address 56, 1 register, 2 bytes, value=99. CRC.
# Response: Slave address 1, function code 144 (wrong). Register address 56, 1 register. CRC.
RESPONSES['\x01\x10' + '\x00\x38\x00\x01' + '\x02\x00\x63' + '\xe2\xc1'] = '\x01\x90' + '\x00\x38\x00\x01' + '\x81\xda'

# Write value 99 in register 55 on slave 1 using function code 6, slave gives wrong write data #
# -------------------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 6. Register address 55, value=99. CRC.
# Response: Slave address 1, function code 6. Register address 55, value=98 (wrong). CRC.
RESPONSES['\x01\x06' + '\x00\x37\x00\x63' + 'x-'] = '\x01\x06' + '\x00\x37\x00\x62' + '\xb9\xed'


#                ##  READ LONG ##
# TODO: More!
#instrument.read_long(102) # '\x01\x03\x00f\x00\x02$\x14'
RESPONSES['\x01\x03' + '\x00\f\x00\x02' + '$\x14'] = ''#'\x01\x06' + '\x00\x37\x00\x62' + '\xb9\xed'


#                ##  WRITE LONG ##
# TODO: More!
#instrument.write_long(102, 3, False) '\x01\x10\x00f\x00\x02\x04\x00\x00\x00\x035\xac'
#instrument.write_long(102, -3, True) '\x01\x10\x00f\x00\x02\x04\xff\xff\xff\xfd\xf5\xf8'



#                ##  READ FLOAT ##
# TODO: More!


#                ##  WRITE FLOAT ##
# TODO: More!

# Write value 1.1 to address 103 (2 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 103, 2 registers, 4 bytes, value=? . CRC.
# Response: Slave address 1, function code 16. Register address 103, 2 registers. CRC.
RESPONSES['\x01\x10' + '\x00g\x00\x02\x04?\x8c\xcc\xcd' + '\xed\x0b'] = '\x01\x10' + '\x00g\x00\x02' + '\xf0\x17'

# Write value 1.1 to address 103 (4 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 103, 4 registers, 8 bytes, value=? . CRC.
# Response: Slave address 1, function code 16. Register address 103, 4 registers. CRC.
RESPONSES['\x01\x10' + '\x00g\x00\x04\x08?\xf1\x99\x99\x99\x99\x99\x9a' + 'u\xf7'] = '\x01\x10' + '\x00g\x00\x04' + 'p\x15'


#                ##  READ STRING  ##
# TODO: More!

# Read from address 104 (1 register) on slave 1 using function code 3 #
# ------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 104, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value = 'AB'.  CRC.
RESPONSES['\x01\x03' + '\x00h\x00\x01' + '\x05\xd6'] = '\x01\x03' + '\x02AB' + '\x08%'


# Read from address 104 (4 registers) on slave 1 using function code 3 #
# ------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 104, 4 registers. CRC.
# Response: Slave address 1, function code 3.  8 bytes, value = 'ABCDEFGH'.  CRC.
RESPONSES['\x01\x03' + '\x00h\x00\x04' + '\xc5\xd5'] = '\x01\x03' + '\x08ABCDEFGH' + '\x0b\xcc'


#                ##  WRITE STRING  ##
# TODO: More!

# Write value 'A' to address 104 (1 register) on slave 1 using function code 16 #
# ------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 104, 1 register, 2 bytes, value='A ' . CRC.
# Response: Slave address 1, function code 16. Register address 104, 1 register. CRC.
RESPONSES['\x01\x10' + '\x00h\x00\x01\x02A ' + '\x9f0'] = '\x01\x10' + '\x00h\x00\x01' + '\x80\x15'

# Write value 'A' to address 104 (4 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 104, 4 registers, 8 bytes, value='A       ' . CRC.
# Response: Slave address 1, function code 16. Register address 104, 2 registers. CRC.
RESPONSES['\x01\x10' + '\x00h\x00\x04\x08A       ' + '\xa7\xae'] = '\x01\x10' + '\x00h\x00\x04' + '@\x16'

# Write value 'ABCDEFGH' to address 104 (4 registers) on slave 1 using function code 16 #
# --------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 104, 4 registers, 8 bytes, value='ABCDEFGH' . CRC.
# Response: Slave address 1, function code 16. Register address 104, 4 registers. CRC.
RESPONSES['\x01\x10' + '\x00h\x00\x04\x08ABCDEFGH' + 'I>'] = '\x01\x10' + '\x00h\x00\x04' + '@\x16'


#                ##  READ REGISTERS  ##
# TODO: More!

# Read from address 105 (1 register) on slave 1 using function code 3 #
# --------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 105, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value = 16.  CRC.
RESPONSES['\x01\x03' + '\x00i\x00\x01' + 'T\x16'] = '\x01\x03' + '\x02\x00\x10' + '\xb9\x88'

# Read from address 105 (3 registers) on slave 1 using function code 3 #
# ---------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 105, 3 registers. CRC.
# Response: Slave address 1, function code 3. 6 bytes, value = 16, 32, 64. CRC.
RESPONSES['\x01\x03' + '\x00i\x00\x03' + '\xd5\xd7'] =  '\x01\x03' + '\x06\x00\x10\x00\x20\x00\x40' + '\xe0\x8c'


#                ##  WRITE REGISTERS  ##

# Write value [2] to address 105 (1 register) on slave 1 using function code 16 #
# ------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 105, 1 register, 2 bytes, value=2 . CRC.
# Response: Slave address 1, function code 16. Register address 105, 1 register. CRC.
RESPONSES['\x01\x10' + '\x00i\x00\x01\x02\x00\x02' + '.\xa8'] = '\x01\x10' + '\x00i\x00\x01' + '\xd1\xd5'

# Write value [2, 4, 8] to address 105 (3 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 105, 3 register, 6 bytes, value=2, 4, 8. CRC.
# Response: Slave address 1, function code 16. Register address 105, 3 registers. CRC.
RESPONSES['\x01\x10' + '\x00i\x00\x03\x06\x00\x02\x00\x04\x00\x08' + '\x0c\xd6'] = '\x01\x10' + '\x00i\x00\x03' + 'P\x14'


#                ##  OTHER RESPONSES  ##

# Retrieve an empty response (for testing the _communicate method) #
# ---------------------------------------------------------------- #
RESPONSES['MessageForEmptyResponse'] = ''

# Retrieve an known response (for testing the _communicate method) #
# ---------------------------------------------------------------- #
RESPONSES['TESTMESSAGE'] = 'TESTRESPONSE'

# Retrieve an known response (for testing the _performCommand method) #
# ---------------------------------------------------------------- #
RESPONSES['\x01\x10TESTCOMMAND\x08B'] = '\x01\x10TESTCOMMANDRESPONSE\xb4,'
RESPONSES['\x01\x4bTESTCOMMAND2\x18\xc8'] = '\x01\x4bTESTCOMMANDRESPONSE2K\x8c'


## Recorded data from OmegaCN7500 ##
####################################

# Slave address 1, read_bit(2068) Response value 1.
RESPONSES['\x01\x02\x08\x14\x00\x01\xfb\xae'] ='\x01\x02\x01\x01`H'

# Slave address 1, write_bit(2068, 0)
RESPONSES['\x01\x05\x08\x14\x00\x00\x8f\xae'] ='\x01\x05\x08\x14\x00\x00\x8f\xae'

# Slave address 1, write_bit(2068, 1)
RESPONSES['\x01\x05\x08\x14\xff\x00\xce^'] ='\x01\x05\x08\x14\xff\x00\xce^'

# Slave address 1, read_register(4097, 1) Response value 823.6
RESPONSES['\x01\x03\x10\x01\x00\x01\xd1\n'] ='\x01\x03\x02 ,\xa0Y'

# Slave address 1, write_register(4097, 700.0, 1)
RESPONSES['\x01\x10\x10\x01\x00\x01\x02\x1bX\xbdJ'] ='\x01\x10\x10\x01\x00\x01T\xc9'

# Slave address 1, write_register(4097, 823.6, 1)
RESPONSES['\x01\x10\x10\x01\x00\x01\x02 ,\xae]'] ='\x01\x10\x10\x01\x00\x01T\xc9'

# Slave address 10, read_bit(2068) Response value 1
RESPONSES['\n\x02\x08\x14\x00\x01\xfa\xd5'] = '\n\x02\x01\x01bl'

# Slave address 10, write_bit(2068, 0)
RESPONSES['\n\x05\x08\x14\x00\x00\x8e\xd5'] ='\n\x05\x08\x14\x00\x00\x8e\xd5'

# Slave address 10, write_bit(2068, 1)
RESPONSES['\n\x05\x08\x14\xff\x00\xcf%'] ='\n\x05\x08\x14\xff\x00\xcf%'

# Slave address 10, read_register(4096, 1) Response value 25.0
RESPONSES['\n\x03\x10\x00\x00\x01\x81\xb1'] ='\n\x03\x02\x00\xfa\x9d\xc6'

# Slave address 10, read_register(4097, 1) Response value 325.8
RESPONSES['\n\x03\x10\x01\x00\x01\xd0q'] ='\n\x03\x02\x0c\xba\x996'

# Slave address 10, write_register(4097, 325.8, 1)
RESPONSES['\n\x10\x10\x01\x00\x01\x02\x0c\xbaA\xc3'] ='\n\x10\x10\x01\x00\x01U\xb2'

# Slave address 10, write_register(4097, 20.0, 1)
RESPONSES['\n\x10\x10\x01\x00\x01\x02\x00\xc8\xc4\xe6'] ='\n\x10\x10\x01\x00\x01U\xb2'

# Slave address 10, write_register(4097, 200.0, 1)
RESPONSES['\n\x10\x10\x01\x00\x01\x02\x07\xd0\xc6\xdc'] ='\n\x10\x10\x01\x00\x01U\xb2'


#################
# Run the tests #
#################

if __name__ == '__main__':
    try:
        unittest.main(verbosity=VERBOSITY)
    except TypeError:
        unittest.main() # For compatibility with Python2.6

    # suite = unittest.TestLoader().loadTestsFromTestCase(TestDummyCommunicationWithPortClosure)
    # unittest.TextTestRunner(verbosity=VERBOSITY).run(suite)

    # print repr(minimalmodbus._calculateCrcString('\x01\x4bTESTCOMMAND2'))


