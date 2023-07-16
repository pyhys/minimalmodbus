#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Copyright 2023 Jonas Berg
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

.. moduleauthor:: Jonas Berg

test_minimalmodbus: Unittests for the :mod:`minimalmodbus` module.

For each function are these tests performed:

  * Known results
  * Invalid input value
  * Invalid input type

This unittest suite uses a mock/dummy serial port from the module :mod:`dummy_serial`,
so it is possible to test the functionality using previously recorded
communication data.

With dummy responses, it is also possible to simulate errors in the communication
from the slave. A few different types of communication errors are tested, as seen
in this table.

=====================================  ===================== =========================
Simulated response error               Tested using function Tested with function code
=====================================  ===================== =========================
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
=====================================  ===================== =========================

"""
__author__ = "Jonas Berg"
__license__ = "Apache License, Version 2.0"

import sys
import time
from typing import Any, Callable, Dict, Tuple, Type, Union
import unittest

sys.path.append(".")

import tests.dummy_serial as dummy_serial  # noqa: E402
import minimalmodbus  # noqa: E402
from minimalmodbus import IllegalRequestError  # noqa: E402
from minimalmodbus import InvalidResponseError  # noqa: E402
from minimalmodbus import NegativeAcknowledgeError  # noqa: E402
from minimalmodbus import NoResponseError  # noqa: E402
from minimalmodbus import SlaveDeviceBusyError  # noqa: E402
from minimalmodbus import SlaveReportedException  # noqa: E402

from minimalmodbus import _Payloadformat  # noqa: E402
from minimalmodbus import BYTEORDER_BIG  # noqa: E402
from minimalmodbus import BYTEORDER_BIG_SWAP  # noqa: E402
from minimalmodbus import BYTEORDER_LITTLE  # noqa: E402
from minimalmodbus import BYTEORDER_LITTLE_SWAP  # noqa: E402

VERBOSITY = 0
"""Verbosity level for the unit testing.

Use value 0 or 2. Note that it only has an effect for Python 2.7 and above.
"""

SHOW_ERROR_MESSAGES_FOR_ASSERTRAISES = False
"""Set this to :const:`True` for printing the error messages caught by assertRaises().

If set to :const:`True`, any unintentional error messages raised during the
processing of the command in :meth:`.assertRaises` are also caught (not counted).
It will be printed in the short form, and will show no traceback.
It can also be useful to set :data:`VERBOSITY` = 2.
"""

_LARGE_NUMBER_OF_BYTES = 1000


###########################################################
# For showing the error messages caught by assertRaises() #
# and to implement a better assertAlmostEqual()           #
###########################################################


class _NonexistantError(Exception):
    pass


class ExtendedTestCase(unittest.TestCase):
    """Overriding the assertRaises() method to be able to print the error message.

    Use :data:`test_minimalmodbus.SHOW_ERROR_MESSAGES_FOR_ASSERTRAISES` = :const:`True`
    in order to use this option. It can also be useful to set
    :data:`test_minimalmodbus.VERBOSITY` = 2.

    Based on https://stackoverflow.com/questions/8672754/
    how-to-show-the-error-messages-caught-by-assertraises-in-unittest-in-python2-7
    """

    def assertRaises(  # type: ignore
        self,
        excClass: Union[Type[BaseException], Tuple[Type[BaseException], ...]],
        callableObj: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Prints the caught error message
        (if :data:`SHOW_ERROR_MESSAGES_FOR_ASSERTRAISES` is :const:`True`)."""
        if SHOW_ERROR_MESSAGES_FOR_ASSERTRAISES:
            try:
                unittest.TestCase.assertRaises(
                    self, _NonexistantError, callableObj, *args, **kwargs
                )
            except Exception:
                print("\n    " + repr(sys.exc_info()[1]))
        else:
            unittest.TestCase.assertRaises(self, excClass, callableObj, *args, **kwargs)

    def assertAlmostEqualRatio(
        self, first: float, second: float, epsilon: float = 1.000001
    ) -> None:
        """A function to compare floats, with ratio instead of "number_of_places".

        This is slightly different than the standard unittest.assertAlmostEqual()

        Args:
            * first: Input argument for comparison
            * second: Input argument for comparison
            * epsilon: Largest allowed ratio of largest to smallest of the two
              input arguments
        """
        if first == second:
            return

        if (first < 0 and second >= 0) or (first >= 0 and second < 0):
            raise AssertionError(
                "The arguments have different signs: {0!r} and {1!r}".format(
                    first, second
                )
            )

        ratio = max(first, second) / float(min(first, second))
        if ratio > epsilon:
            raise AssertionError(
                "The arguments are not "
                + "equal: {0!r} and {1!r}. Epsilon is {2!r}.".format(
                    first, second, epsilon
                )
            )


##############################
# Constants for type testing #
##############################

_NOT_INTERGERS_OR_NONE = [
    0.0,
    1.0,
    "1",
    b"1",
    ["1"],
    [b"1"],
    [1],
    ["\x00\x2d\x00\x58"],
    ["A", "B", "C"],
]
_NOT_INTERGERS = _NOT_INTERGERS_OR_NONE + [None]

_NOT_NUMERICALS_OR_NONE = [
    "1",
    b"1",
    ["1"],
    [b"1"],
    [1],
    ["\x00\x2d\x00\x58"],
    ["A", "B", "C"],
]
_NOT_NUMERICALS = _NOT_NUMERICALS_OR_NONE + [None]

_NOT_STRINGS_OR_NONE = [
    1,
    0.0,
    1.0,
    b"1",
    ["1"],
    [b"1"],
    [1],
    ["\x00\x2d\x00\x58"],
    ["A", "B", "C"],
    True,
    False,
]
_NOT_STRINGS = _NOT_STRINGS_OR_NONE + [None]

_NOT_BYTES_OR_NONE = [
    1,
    0.0,
    1.0,
    "1",
    ["1"],
    [1],
    "ABC",
    ["\x00\x2d\x00\x58"],
    ["A", "B", "C"],
    True,
    False,
]
_NOT_BYTES = _NOT_BYTES_OR_NONE + [None]

_NOT_BOOLEANS = [
    "True",
    "False",
    b"1",
    [b"1"],
    -1,
    1,
    2,
    0,
    8,
    9999999,
    -1.0,
    1.0,
    0.0,
    [True],
    [False],
    [1],
    [1.0],
]

_NOT_INTLISTS = [
    0,
    1,
    2,
    -1,
    True,
    False,
    0.0,
    1.0,
    "1",
    ["1"],
    b"1",
    [b"1"],
    None,
    ["\x00\x2d\x00\x58"],
    ["A", "B", "C"],
    [1.0],
    [1.0, 2.0],
]


####################
# Payload handling #
####################


class TestCreatePayload(ExtendedTestCase):
    def testKnownValues(self) -> None:
        # read_bit(61, functioncode=2)
        self.assertEqual(
            minimalmodbus._create_payload(
                2, 61, None, 0, 0, 1, False, BYTEORDER_BIG, _Payloadformat.BIT
            ),
            b"\x00\x3D\x00\x01",
        )

        # read_bit(62, functioncode=1)
        self.assertEqual(
            minimalmodbus._create_payload(
                1, 62, None, 0, 0, 1, False, BYTEORDER_BIG, _Payloadformat.BIT
            ),
            b"\x00\x3E\x00\x01",
        )

        # write_bit(71, 1, functioncode=5)
        self.assertEqual(
            minimalmodbus._create_payload(
                5, 71, 1, 0, 0, 1, False, BYTEORDER_BIG, _Payloadformat.BIT
            ),
            b"\x00\x47\xFF\x00",
        )

        # read_bits(196, 22, functioncode=2)
        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        self.assertEqual(
            minimalmodbus._create_payload(
                2, 196, None, 0, 0, 22, False, BYTEORDER_BIG, _Payloadformat.BITS
            ),
            b"\x00\xC4\x00\x16",
        )

        # read_bits(19, 19, functioncode=1)
        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        self.assertEqual(
            minimalmodbus._create_payload(
                1, 19, None, 0, 0, 19, False, BYTEORDER_BIG, _Payloadformat.BITS
            ),
            b"\x00\x13\x00\x13",
        )

        # write_bits(19, [1, 0, 1, 1, 0, 0, 1, 1, 1, 0])
        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        self.assertEqual(
            minimalmodbus._create_payload(
                15,
                19,
                [1, 0, 1, 1, 0, 0, 1, 1, 1, 0],
                0,
                0,
                10,
                False,
                BYTEORDER_BIG,
                _Payloadformat.BITS,
            ),
            b"\x00\x13\x00\x0A\x02\xCD\x01",
        )

        # read_register(289, 0, functioncode=3)
        self.assertEqual(
            minimalmodbus._create_payload(
                3, 289, None, 0, 1, 0, False, BYTEORDER_BIG, _Payloadformat.REGISTER
            ),
            b"\x01\x21\x00\x01",
        )

        # read_register(14, 0, functioncode=4)
        self.assertEqual(
            minimalmodbus._create_payload(
                4, 14, None, 0, 1, 0, False, BYTEORDER_BIG, _Payloadformat.REGISTER
            ),
            b"\x00\x0E\x00\x01",
        )

        # write_register(35, 20, functioncode = 16)
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 35, 20, 0, 1, 0, False, BYTEORDER_BIG, _Payloadformat.REGISTER
            ),
            b"\x00\x23\x00\x01\x02\x00\x14",
        )

        # write_register(45, 88, functioncode = 6)
        self.assertEqual(
            minimalmodbus._create_payload(
                6, 45, 88, 0, 1, 0, False, BYTEORDER_BIG, _Payloadformat.REGISTER
            ),
            b"\x00\x2D\x00\x58",
        )

        # write_register(101, -5, signed=True)
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 101, -5, 0, 1, 0, True, BYTEORDER_BIG, _Payloadformat.REGISTER
            ),
            b"\x00\x65\x00\x01\x02\xFF\xFB",
        )

        # write_register(101, -5, 1, signed=True)
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 101, -5, 1, 1, 0, True, BYTEORDER_BIG, _Payloadformat.REGISTER
            ),
            b"\x00\x65\x00\x01\x02\xFF\xCE",
        )

        # read_long(102)
        self.assertEqual(
            minimalmodbus._create_payload(
                3, 102, None, 0, 2, 0, False, BYTEORDER_BIG, _Payloadformat.LONG
            ),
            b"\x00\x66\x00\x02",
        )

        # read_long(102, functioncode=4)
        self.assertEqual(
            minimalmodbus._create_payload(
                4, 102, None, 0, 2, 0, False, BYTEORDER_BIG, _Payloadformat.LONG
            ),
            b"\x00\x66\x00\x02",
        )

        # read_long(256)
        self.assertEqual(
            minimalmodbus._create_payload(
                3, 256, None, 0, 2, 0, False, BYTEORDER_BIG, _Payloadformat.LONG
            ),
            b"\x01\x00\x00\x02",
        )
        # read_long(256, number_of_registers=4)
        self.assertEqual(
            minimalmodbus._create_payload(
                3, 256, None, 0, 4, 0, False, BYTEORDER_BIG, _Payloadformat.LONG
            ),
            b"\x01\x00\x00\x04",
        )

        # write_long(102, 5)
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 102, 5, 0, 2, 0, False, BYTEORDER_BIG, _Payloadformat.LONG
            ),
            b"\x00\x66\x00\x02\x04\x00\x00\x00\x05",
        )

        # write_long(102, 5,  signed=True)
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 102, 5, 0, 2, 0, True, BYTEORDER_BIG, _Payloadformat.LONG
            ),
            b"\x00\x66\x00\x02\x04\x00\x00\x00\x05",
        )

        # write_long(102, -5, signed=True)
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 102, -5, 0, 2, 0, True, BYTEORDER_BIG, _Payloadformat.LONG
            ),
            b"\x00\x66\x00\x02\x04\xFF\xFF\xFF\xFB",
        )

        # write_long(102, -5, signed=True, number_of_registers=4)
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 102, -5, 0, 4, 0, True, BYTEORDER_BIG, _Payloadformat.LONG
            ),
            b"\x00\x66\x00\x04\x08\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFB",
        )

        # read_float(103, functioncode=3, number_of_registers=2)
        self.assertEqual(
            minimalmodbus._create_payload(
                3, 103, None, 0, 2, 0, False, BYTEORDER_BIG, _Payloadformat.FLOAT
            ),
            b"\x00\x67\x00\x02",
        )

        # read_float(103, functioncode=3, number_of_registers=4)
        self.assertEqual(
            minimalmodbus._create_payload(
                3, 103, None, 0, 4, 0, False, BYTEORDER_BIG, _Payloadformat.FLOAT
            ),
            b"\x00\x67\x00\x04",
        )

        # read_float(103, functioncode=4, number_of_registers=2)
        self.assertEqual(
            minimalmodbus._create_payload(
                4, 103, None, 0, 2, 0, False, BYTEORDER_BIG, _Payloadformat.FLOAT
            ),
            b"\x00\x67\x00\x02",
        )

        # write_float(103, 1.1, number_of_registers=2)   OK compare to recorded data
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 103, 1.1, 0, 2, 0, False, BYTEORDER_BIG, _Payloadformat.FLOAT
            ),
            b"\x00\x67\x00\x02\x04\x3F\x8C\xCC\xCD",
        )

        # write_float(103, 1.1, number_of_registers=4)   OK compare to recorded data
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 103, 1.1, 0, 4, 0, False, BYTEORDER_BIG, _Payloadformat.FLOAT
            ),
            b"\x00\x67\x00\x04\x08\x3F\xF1\x99\x99\x99\x99\x99\x9A",
        )

        # read_string(104, 1)
        self.assertEqual(
            minimalmodbus._create_payload(
                3, 104, None, 0, 1, 0, False, BYTEORDER_BIG, _Payloadformat.STRING
            ),
            b"\x00\x68\x00\x01",
        )

        # read_string(104, 4)
        self.assertEqual(
            minimalmodbus._create_payload(
                3, 104, None, 0, 4, 0, False, BYTEORDER_BIG, _Payloadformat.STRING
            ),
            b"\x00\x68\x00\x04",
        )

        # read_string(104, 4, functioncode=4)
        self.assertEqual(
            minimalmodbus._create_payload(
                4, 104, None, 0, 4, 0, False, BYTEORDER_BIG, _Payloadformat.STRING
            ),
            b"\x00\x68\x00\x04",
        )

        # write_string(104, 'A', 1)
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 104, "A", 0, 1, 0, False, BYTEORDER_BIG, _Payloadformat.STRING
            ),
            b"\x00\x68\x00\x01\x02A ",
        )

        # write_string(104, 'A', 4)
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 104, "A", 0, 4, 0, False, BYTEORDER_BIG, _Payloadformat.STRING
            ),
            b"\x00\x68\x00\x04\x08A       ",
        )

        # write_string(104, 'ABCDEFGH', 4)
        self.assertEqual(
            minimalmodbus._create_payload(
                16,
                104,
                "ABCDEFGH",
                0,
                4,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.STRING,
            ),
            b"\x00\x68\x00\x04\x08ABCDEFGH",
        )

        # read_registers(105, 1)
        self.assertEqual(
            minimalmodbus._create_payload(
                3, 105, None, 0, 1, 0, False, BYTEORDER_BIG, _Payloadformat.REGISTERS
            ),
            b"\x00\x69\x00\x01",
        )

        # read_registers(105, 3)
        self.assertEqual(
            minimalmodbus._create_payload(
                3, 105, None, 0, 3, 0, False, BYTEORDER_BIG, _Payloadformat.REGISTERS
            ),
            b"\x00\x69\x00\x03",
        )

        # read_registers(105, 7, functioncode=4)
        self.assertEqual(
            minimalmodbus._create_payload(
                4, 105, None, 0, 7, 0, False, BYTEORDER_BIG, _Payloadformat.REGISTERS
            ),
            b"\x00\x69\x00\x07",
        )

        # write_registers(105, [2])
        self.assertEqual(
            minimalmodbus._create_payload(
                16, 105, [2], 0, 1, 0, False, BYTEORDER_BIG, _Payloadformat.REGISTERS
            ),
            b"\x00\x69\x00\x01\x02\x00\x02",
        )

        # write_registers(105, [2, 4, 8])
        self.assertEqual(
            minimalmodbus._create_payload(
                16,
                105,
                [2, 4, 8],
                0,
                3,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.REGISTERS,
            ),
            b"\x00\x69\x00\x03\x06\x00\x02\x00\x04\x00\x08",
        )

    def testWrongValues(self) -> None:
        # NOTE: Most of the error checking is done in other methods
        self.assertRaises(
            ValueError,
            minimalmodbus._create_payload,
            25,  # Wrong on purpose
            104,
            "A",
            0,
            4,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.STRING,
        )

        self.assertRaises(
            ValueError,
            minimalmodbus._create_payload,
            15,
            104,
            "ABC",  # Wrong on purpose
            0,
            4,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.BITS,
        )

        self.assertRaises(
            ValueError,
            minimalmodbus._create_payload,
            16,
            104,
            [1, 0, 1],  # Wrong on purpose
            0,
            1,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.BITS,  # Wrong on purpose
        )


class TestParsePayload(ExtendedTestCase):
    def testKnownValues(self) -> None:
        # read_bit(61, functioncode=2)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x01\x01",
                2,
                61,
                None,
                0,
                0,
                1,
                False,
                BYTEORDER_BIG,
                _Payloadformat.BIT,
            ),
            1,
        )

        # read_bit(62, functioncode=1)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x01\x00",
                1,
                62,
                None,
                0,
                0,
                1,
                False,
                BYTEORDER_BIG,
                _Payloadformat.BIT,
            ),
            0,
        )

        # write_bit(71, 1, functioncode=5)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00\x47\xff\x00",
                5,
                71,
                1,
                0,
                0,
                1,
                False,
                BYTEORDER_BIG,
                _Payloadformat.BIT,
            ),
            None,
        )

        # write_bit(72, 1, functioncode=15)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00\x48\x00\x01",
                15,
                72,
                1,
                0,
                0,
                1,
                False,
                BYTEORDER_BIG,
                _Payloadformat.BIT,
            ),
            None,
        )

        # read_bits(196, 22, functioncode=2)
        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x03\xAC\xDB\x35",
                2,
                196,
                None,
                0,
                0,
                22,
                False,
                BYTEORDER_BIG,
                _Payloadformat.BITS,
            ),
            [0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1],
        )

        # read_bits(19, 19, functioncode=1)
        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x03\xCD\x6B\x05",
                1,
                19,
                None,
                0,
                0,
                19,
                False,
                BYTEORDER_BIG,
                _Payloadformat.BITS,
            ),
            [1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
        )

        # write_bits(19, [1, 0, 1, 1, 0, 0, 1, 1, 1, 0])
        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00\x13\x00\x0A",
                15,
                19,
                [1, 0, 1, 1, 0, 0, 1, 1, 1, 0],
                0,
                0,
                10,
                False,
                BYTEORDER_BIG,
                _Payloadformat.BITS,
            ),
            None,
        )

        # read_register(289, 0, functioncode=3)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x02\x03\x02",
                3,
                289,
                None,
                0,
                1,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.REGISTER,
            ),
            770,
        )

        # read_register(14, 0, functioncode=4)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x02\x03\x70",
                4,
                14,
                None,
                0,
                1,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.REGISTER,
            ),
            880,
        )

        # write_register(35, 20, functioncode = 16)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00#\x00\x01",
                16,
                35,
                20,
                0,
                1,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.REGISTER,
            ),
            None,
        )

        # write_register(45, 88, functioncode = 6)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00\x2d\x00\x58",
                6,
                45,
                88,
                0,
                1,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.REGISTER,
            ),
            None,
        )

        # write_register(101, -5, signed=True)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00e\x00\x01",
                16,
                101,
                -5,
                0,
                1,
                0,
                True,
                BYTEORDER_BIG,
                _Payloadformat.REGISTER,
            ),
            None,
        )

        # read_long(102)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x04\xff\xff\xff\xff",
                3,
                102,
                None,
                0,
                2,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.LONG,
            ),
            4294967295,
        )

        # read_long(102, signed=True)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x04\xff\xff\xff\xff",
                3,
                102,
                None,
                0,
                2,
                0,
                True,
                BYTEORDER_BIG,
                _Payloadformat.LONG,
            ),
            -1,
        )

        # write_long(102, 5)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00f\x00\x02",
                16,
                102,
                5,
                0,
                2,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.LONG,
            ),
            None,
        )

        # write_long(102, -5, signed=True)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00f\x00\x02",
                16,
                102,
                -5,
                0,
                2,
                0,
                True,
                BYTEORDER_BIG,
                _Payloadformat.LONG,
            ),
            None,
        )

        # read_float(103, functioncode=3, number_of_registers=2)
        parsed_value = minimalmodbus._parse_payload(
            b"\x04\x3f\x80\x00\x00",
            3,
            103,
            None,
            0,
            2,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.FLOAT,
        )
        assert isinstance(parsed_value, float)
        self.assertAlmostEqual(
            parsed_value,
            1.0,
        )

        # read_float(103, functioncode=3, number_of_registers=4)
        parsed_value = minimalmodbus._parse_payload(
            b"\x08\xc0\x00\x00\x00\x00\x00\x00\x00",
            3,
            103,
            None,
            0,
            4,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.FLOAT,
        )
        assert isinstance(parsed_value, float)
        self.assertAlmostEqual(
            parsed_value,
            -2.0,
        )

        # read_float(103, functioncode=4, number_of_registers=2)
        parsed_value = minimalmodbus._parse_payload(
            b"\x04\x72\x38\x47\x25",
            4,
            103,
            None,
            0,
            2,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.FLOAT,
        )
        assert isinstance(parsed_value, float)
        self.assertAlmostEqualRatio(
            parsed_value,
            3.65e30,
        )

        # write_float(103, 1.1, number_of_registers=2)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00g\x00\x02",
                16,
                103,
                1.1,
                0,
                2,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.FLOAT,
            ),
            None,
        )

        # write_float(103, 1.1, number_of_registers=4)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00g\x00\x04",
                16,
                103,
                1.1,
                0,
                4,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.FLOAT,
            ),
            None,
        )

        # read_string(104, 1)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x02AB",
                3,
                104,
                None,
                0,
                1,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.STRING,
            ),
            "AB",
        )

        # read_string(104, 4)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x08ABCDEFGH",
                3,
                104,
                None,
                0,
                4,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.STRING,
            ),
            "ABCDEFGH",
        )

        # write_string(104, 'A', 1)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00h\x00\x01",
                16,
                104,
                "A",
                0,
                1,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.STRING,
            ),
            None,
        )

        # write_string(104, 'A', 4)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00h\x00\x04",
                16,
                104,
                "A",
                0,
                4,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.STRING,
            ),
            None,
        )

        # write_string(104, 'ABCDEFGH', 4)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00h\x00\x04",
                16,
                104,
                "ABCDEFGH",
                0,
                4,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.STRING,
            ),
            None,
        )

        # read_registers(105, 1)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x02\x00\x10",
                3,
                105,
                None,
                0,
                1,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.REGISTERS,
            ),
            [16],
        )

        # read_registers(105, 3)
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x06\x00\x10\x00\x20\x00\x40",
                3,
                105,
                None,
                0,
                3,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.REGISTERS,
            ),
            [16, 32, 64],
        )

        # write_registers(105, [2])
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00i\x00\x01",
                16,
                105,
                [2],
                0,
                1,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.REGISTERS,
            ),
            None,
        )

        # write_registers(105, [2, 4, 8])
        self.assertEqual(
            minimalmodbus._parse_payload(
                b"\x00i\x00\x03",
                16,
                105,
                [2, 4, 8],
                0,
                3,
                0,
                False,
                BYTEORDER_BIG,
                _Payloadformat.REGISTERS,
            ),
            None,
        )

    def testInvalidPayloads(self) -> None:
        # read_bit(63, functioncode=2)  # Slave gives wrong byte count
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x02\x01",
            2,
            63,
            None,
            0,
            0,
            1,
            False,
            BYTEORDER_BIG,
            _Payloadformat.BIT,
        )

        # write_bit(73, 1, functioncode=15)  # Slave gives wrong number of registers
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x00\x49\x00\x02",
            15,
            73,
            1,
            0,
            0,
            1,
            False,
            BYTEORDER_BIG,
            _Payloadformat.BIT,
        )

        # write_bit(74, 1, functioncode=5)  # Slave gives wrong write data
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x00\x47\x00\x00",
            5,
            74,
            1,
            0,
            0,
            1,
            False,
            BYTEORDER_BIG,
            _Payloadformat.BIT,
        )

        # write_bit(73, 1, functioncode=15)  # Slave gives wrong number of registers
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x00\x49\x00\x02",
            15,
            73,
            1,
            0,
            0,
            1,
            False,
            BYTEORDER_BIG,
            _Payloadformat.BIT,
        )

        # write_bit(74, 1, functioncode=5)  # Slave gives wrong write data (address)
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x00\x47\x00\x00",
            5,
            74,
            1,
            0,
            0,
            1,
            False,
            BYTEORDER_BIG,
            _Payloadformat.BIT,
        )

        # read_bits(196, 22, functioncode=2)  # Wrong number of bits
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x03\xAC\xDB\x35",
            2,
            196,
            None,
            0,
            0,
            7,
            False,
            BYTEORDER_BIG,
            _Payloadformat.REGISTER,
        )

        # read_register(202, 0, functioncode=3)  # Slave gives too long response
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x02\x00\x00\x09",
            3,
            202,
            None,
            0,
            1,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.REGISTER,
        )

        # read_register(203, 0, functioncode=3)  # Slave gives too short response
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x02\x09",
            3,
            203,
            None,
            0,
            1,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.REGISTER,
        )

        # write_register(52, 99, functioncode = 16)
        # Slave gives wrong number of registers
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x00\x34\x00\x02",
            16,
            52,
            99,
            0,
            1,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.REGISTER,
        )

        # write_register(53, 99, functioncode = 16)
        # Slave gives wrong register address
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x00\x36\x00\x01",
            16,
            53,
            99,
            0,
            1,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.REGISTER,
        )

        # write_register(55, 99, functioncode = 6)  # Slave gives wrong write data
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x00\x36\x00\x01",
            6,
            55,
            99,
            0,
            1,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.REGISTER,
        )

        # read_registers(105, 3)  # wrong number of registers
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._parse_payload,
            b"\x06\x00\x10\x00\x20\x00\x40",
            3,
            105,
            None,
            0,
            4,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.REGISTERS,
        )

        # wrong functioncode
        self.assertRaises(
            ValueError,
            minimalmodbus._parse_payload,
            b"ABC",
            10,
            105,
            None,
            0,
            4,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.REGISTERS,
        )

        # wrong functioncode and payload combination
        self.assertRaises(
            ValueError,
            minimalmodbus._parse_payload,
            b"\x01\x01",
            1,
            105,
            None,
            0,
            1,
            1,
            False,
            BYTEORDER_BIG,
            _Payloadformat.REGISTER,  # Wrong on purpose
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._parse_payload,
            b"\x02\x00\x01",
            3,
            105,
            None,
            0,
            1,
            0,
            False,
            BYTEORDER_BIG,
            _Payloadformat.BITS,  # Wrong on purpose
        )


class TestEmbedPayload(ExtendedTestCase):
    known_values = [
        (2, 2, "rtu", b"123", b"\x02\x02123X\xc2"),
        (1, 16, "rtu", b"ABC", b"\x01\x10ABC<E"),
        (0, 5, "rtu", b"hjl", b"\x00\x05hjl\x8b\x9d"),
        (1, 3, "rtu", b"\x01\x02\x03", b"\x01\x03\x01\x02\x03\t%"),
        (1, 3, "ascii", b"123", b":010331323366\r\n"),
        (4, 5, "ascii", b"\x01\x02\x03", b":0405010203F1\r\n"),
        (2, 2, "ascii", b"123", b":020231323366\r\n"),
    ]

    def testKnownValues(self) -> None:
        for (
            slaveaddress,
            functioncode,
            mode,
            inputpayload,
            known_result,
        ) in self.known_values:
            result = minimalmodbus._embed_payload(
                slaveaddress, mode, functioncode, inputpayload
            )
            self.assertEqual(result, known_result)

    def testWrongInputValue(self) -> None:
        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, 256, "rtu", 16, b"ABC"
        )  # Wrong slave address
        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, -1, "rtu", 16, b"ABC"
        )
        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, 256, "ascii", 16, b"ABC"
        )
        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, -1, "ascii", 16, b"ABC"
        )

        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, 1, "rtuu", 16, b"ABC"
        )  # Wrong Modbus mode
        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, 1, "RTU", 16, b"ABC"
        )
        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, 1, "ASCII", 16, b"ABC"
        )
        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, 1, "asci", 16, b"ABC"
        )

        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, 1, "rtu", 222, b"ABC"
        )  # Wrong function code
        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, 1, "rtu", -1, b"ABC"
        )
        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, 1, "ascii", 222, b"ABC"
        )
        self.assertRaises(
            ValueError, minimalmodbus._embed_payload, 1, "ascii", -1, b"ABC"
        )

    def testWrongInputType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError, minimalmodbus._embed_payload, value, "rtu", 16, b"ABC"
            )
            self.assertRaises(
                TypeError, minimalmodbus._embed_payload, value, "ascii", 16, b"ABC"
            )
            self.assertRaises(
                TypeError, minimalmodbus._embed_payload, 1, "rtu", value, b"ABC"
            )
            self.assertRaises(
                TypeError, minimalmodbus._embed_payload, 1, "ascii", value, b"ABC"
            )
        for value in _NOT_STRINGS:
            self.assertRaises(
                TypeError, minimalmodbus._embed_payload, 1, value, 16, b"ABC"
            )
        for value in _NOT_BYTES:
            self.assertRaises(
                TypeError, minimalmodbus._embed_payload, 1, "rtu", 16, value
            )
            self.assertRaises(
                TypeError, minimalmodbus._embed_payload, 1, "ascii", 16, value
            )


class TestExtractPayload(ExtendedTestCase):
    known_values = TestEmbedPayload.known_values

    def testKnownValues(self) -> None:
        for (
            slaveaddress,
            functioncode,
            mode,
            known_result,
            inputbytes,
        ) in self.known_values:
            result = minimalmodbus._extract_payload(
                inputbytes, slaveaddress, mode, functioncode
            )
            self.assertEqual(result, known_result)

    def testWrongInputValue(self) -> None:
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._extract_payload,
            b"\x02\x02123X\xc3",
            2,
            "rtu",
            2,
        )  # Wrong CRC from slave
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._extract_payload,
            b":0202313233F1\r\n",
            2,
            "ascii",
            2,
        )  # Wrong LRC from slave
        self.assertRaises(
            SlaveReportedException,
            minimalmodbus._extract_payload,
            b"\x02\x82123q\x02",
            2,
            "rtu",
            2,
        )  # Error indication from slave
        self.assertRaises(
            SlaveReportedException,
            minimalmodbus._extract_payload,
            b":0282313233E6\r\n",
            2,
            "ascii",
            2,
        )
        self.assertRaises(
            InvalidResponseError, minimalmodbus._extract_payload, b"ABC", 2, "rtu", 2
        )  # Too short message from slave
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._extract_payload,
            b"ABCDEFGH",
            2,
            "ascii",
            2,
        )
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._extract_payload,
            b"\x02\x72123B\x02",
            2,
            "rtu",
            2,
        )  # Wrong functioncode from slave
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._extract_payload,
            b":020431323364\r\n",
            2,
            "ascii",
            2,
        )
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._extract_payload,
            b"020231323366\r\n",
            2,
            "ascii",
            2,
        )  # Missing ASCII header
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._extract_payload,
            b":020231323366",
            2,
            "ascii",
            2,
        )  # Wrong ASCII footer
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._extract_payload,
            b":020231323366\r",
            2,
            "ascii",
            2,
        )
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._extract_payload,
            b":020231323366\n",
            2,
            "ascii",
            2,
        )
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._extract_payload,
            b":02023132366\r\n",
            2,
            "ascii",
            2,
        )  # Odd number of ASCII payload characters

        for value in [256, -1]:
            self.assertRaises(
                ValueError,
                minimalmodbus._extract_payload,
                b"\x02\x02123X\xc2",
                value,
                "rtu",
                2,
            )  # Invalid slave address
        for value in [3, 95, 128]:
            self.assertRaises(
                InvalidResponseError,
                minimalmodbus._extract_payload,
                b"\x02\x02123X\xc2",
                value,
                "rtu",
                2,
            )  # Wrong slave address
        for value in [128, 256, -1]:
            self.assertRaises(
                ValueError,
                minimalmodbus._extract_payload,
                b"\x02\x02123X\xc2",
                2,
                "rtu",
                value,
            )  # Invalid functioncode
        for value in [3, 95, 127]:
            self.assertRaises(
                InvalidResponseError,
                minimalmodbus._extract_payload,
                b"\x02\x02123X\xc2",
                2,
                "rtu",
                value,
            )  # Wrong functioncode

        for value_str in ["RTU", "ASCII", "asc", "", " "]:
            self.assertRaises(
                ValueError,
                minimalmodbus._extract_payload,
                b"\x02\x02123X\xc2",
                2,
                value_str,
                2,
            )  # Wrong mode

    def testWrongInputType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError,
                minimalmodbus._extract_payload,
                b"\x02\x02123X\xc2",
                value,
                "rtu",
                2,
            )  # Wrong slaveaddress type
            self.assertRaises(
                TypeError,
                minimalmodbus._extract_payload,
                b"\x02\x02123X\xc2",
                value,
                "ascii",
                2,
            )
            self.assertRaises(
                TypeError,
                minimalmodbus._extract_payload,
                b"\x02\x02123X\xc2",
                2,
                "rtu",
                value,
            )  # Wrong functioncode type
            self.assertRaises(
                TypeError,
                minimalmodbus._extract_payload,
                b"\x02\x02123X\xc2",
                2,
                "ascii",
                value,
            )
        for value in _NOT_BYTES:
            self.assertRaises(
                TypeError, minimalmodbus._extract_payload, value, 2, "rtu", 2
            )  # Wrong message
            self.assertRaises(
                TypeError, minimalmodbus._extract_payload, value, 2, "ascii", 2
            )
        for value in _NOT_STRINGS:
            self.assertRaises(
                TypeError,
                minimalmodbus._extract_payload,
                b"\x02\x02123X\xc2",
                2,
                value,
                2,
            )  # Wrong mode


class TestSanityEmbedExtractPayload(ExtendedTestCase):
    known_values = TestEmbedPayload.known_values

    def testKnownValues(self) -> None:
        for slaveaddress, functioncode, mode, payload, _ in self.known_values:
            embeddedResult = minimalmodbus._embed_payload(
                slaveaddress, mode, functioncode, payload
            )
            extractedResult = minimalmodbus._extract_payload(
                embeddedResult, slaveaddress, mode, functioncode
            )
            self.assertEqual(extractedResult, payload)

    def testRange(self) -> None:
        for i in range(110):
            payload = str(i).encode("ascii")

            embeddedResultRtu = minimalmodbus._embed_payload(2, "rtu", 6, payload)
            extractedResultRtu = minimalmodbus._extract_payload(
                embeddedResultRtu, 2, "rtu", 6
            )
            self.assertEqual(extractedResultRtu, payload)

            embeddedResultAscii = minimalmodbus._embed_payload(2, "ascii", 6, payload)
            extractedResultAscii = minimalmodbus._extract_payload(
                embeddedResultAscii, 2, "ascii", 6
            )
            self.assertEqual(extractedResultAscii, payload)


##########################################
# Serial communication utility functions #
##########################################


class TestPredictResponseSize(ExtendedTestCase):
    known_values = [
        ("rtu", 1, b"\x00\x3e\x00\x01", 6),
        ("rtu", 1, b"\x00\x3e\x00\x07", 6),
        ("rtu", 1, b"\x00\x3e\x00\x08", 6),
        ("rtu", 1, b"\x00\x3e\x00\x09", 7),
        ("rtu", 2, b"\x00\x3e\x00\x09", 7),
        ("rtu", 3, b"AB\x00\x07", 19),
        ("rtu", 4, b"AB\x00\x07", 19),
        ("rtu", 4, b"AB\x01\x07", 531),
        ("rtu", 5, b"\x00\x47\xff\x00", 8),
        ("rtu", 6, b"\x00\x47\xFF\xFF", 8),
        ("rtu", 16, b"\x00\x48\x00\x01\x01\x01", 8),
        ("ascii", 1, b"\x00\x3e\x00\x01", 13),
        ("ascii", 1, b"\x00\x3e\x00\x07", 13),
        ("ascii", 1, b"\x00\x3e\x00\x08", 13),
        ("ascii", 1, b"\x00\x3e\x00\x09", 15),
        ("ascii", 3, b"AB\x00\x07", 39),
        ("ascii", 4, b"AB\x00\x07", 39),
        ("ascii", 4, b"AB\x01\x07", 1063),
        ("ascii", 5, b"\x00\x47\xff\x00", 17),
        ("ascii", 16, b"\x00\x48\x00\x01\x01\x01", 17),
    ]

    def testKnownValues(self) -> None:
        for mode, functioncode, payload_to_slave, known_value in self.known_values:
            resultvalue = minimalmodbus._predict_response_size(
                mode, functioncode, payload_to_slave
            )
            self.assertEqual(resultvalue, known_value)

    def testRecordedRtuMessages(self) -> None:
        # Use the dictionary where the key is the 'message', and the
        # item is the 'response'
        for message in GOOD_RTU_RESPONSES:
            slaveaddress = message[0]
            functioncode = message[1]
            payload_to_slave = minimalmodbus._extract_payload(
                message, slaveaddress, "rtu", functioncode
            )
            result = minimalmodbus._predict_response_size(
                "rtu", functioncode, payload_to_slave
            )

            responseFromSlave = GOOD_RTU_RESPONSES[message]
            self.assertEqual(result, len(responseFromSlave))

    def testRecordedAsciiMessages(self) -> None:
        # Use the dictionary where the key is the 'message', and the item
        # is the 'response'
        for message in GOOD_ASCII_RESPONSES:
            slaveaddress = int(message[1:3])
            functioncode = int(message[3:5])
            payload_to_slave = minimalmodbus._extract_payload(
                message, slaveaddress, "ascii", functioncode
            )
            result = minimalmodbus._predict_response_size(
                "ascii", functioncode, payload_to_slave
            )

            responseFromSlave = GOOD_ASCII_RESPONSES[message]
            self.assertEqual(result, len(responseFromSlave))

    def testWrongInputValue(self) -> None:
        # Wrong mode
        self.assertRaises(
            ValueError, minimalmodbus._predict_response_size, "asciiii", 6, b"ABCD"
        )
        # Wrong function code
        self.assertRaises(
            ValueError, minimalmodbus._predict_response_size, "ascii", 35, b"ABCD"
        )
        # Wrong function code
        self.assertRaises(
            ValueError, minimalmodbus._predict_response_size, "rtu", 35, b"ABCD"
        )
        # Too short message
        self.assertRaises(
            ValueError, minimalmodbus._predict_response_size, "ascii", 1, b"ABC"
        )
        # Too short message
        self.assertRaises(
            ValueError, minimalmodbus._predict_response_size, "rtu", 1, b"ABC"
        )
        # Too short message
        self.assertRaises(
            ValueError, minimalmodbus._predict_response_size, "ascii", 1, b"AB"
        )
        # Too short message
        self.assertRaises(
            ValueError, minimalmodbus._predict_response_size, "ascii", 1, b"A"
        )
        # Too short message
        self.assertRaises(
            ValueError, minimalmodbus._predict_response_size, "ascii", 1, b""
        )

    def testWrongInputType(self) -> None:
        for value in _NOT_STRINGS:
            self.assertRaises(
                TypeError, minimalmodbus._predict_response_size, value, 1, b"ABCD"
            )
        for value in _NOT_BYTES:
            self.assertRaises(
                TypeError, minimalmodbus._predict_response_size, "rtu", 1, value
            )
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError, minimalmodbus._predict_response_size, "rtu", value, b"ABCD"
            )


class TestCalculateMinimumSilentPeriod(ExtendedTestCase):
    known_values = [
        (2400, 0.016),
        (2400.0, 0.016),
        (4800, 0.008),
        (9600, 0.004),
        (19200, 0.002),
        (38400, 0.00175),
        (57600, 0.00175),
        (115200, 0.00175),
        (128000, 0.00175),
        (230400, 0.00175),
        (4000000, 0.00175),
    ]

    def testKnownValues(self) -> None:
        for baudrate, known_result in self.known_values:
            result = minimalmodbus._calculate_minimum_silent_period(baudrate)
            self.assertAlmostEqualRatio(
                result, known_result, 1.02
            )  # Allow 2% deviation from listed known values

    def testWrongInputValue(self) -> None:
        for value in [-2400, -2400.0, -1, -0.5, 0, 0.5, 0.9]:
            self.assertRaises(
                ValueError, minimalmodbus._calculate_minimum_silent_period, value
            )

    def testWrongInputType(self) -> None:
        for value in _NOT_NUMERICALS:
            self.assertRaises(
                TypeError, minimalmodbus._calculate_minimum_silent_period, value
            )


##############################
# String and num conversions #
##############################


class TestNumToOneByte(ExtendedTestCase):
    known_values = [
        (0, b"\x00"),
        (7, b"\x07"),
        (255, b"\xff"),
    ]

    def testKnownValues(self) -> None:
        for inputvalue, knownbyte in self.known_values:
            result = minimalmodbus._num_to_one_byte(inputvalue)
            self.assertEqual(result, knownbyte)

    def testKnownLoop(self) -> None:
        for value in range(256):
            knownbyte = value.to_bytes(1, "little")
            result = minimalmodbus._num_to_one_byte(value)
            self.assertEqual(result, knownbyte)

    def testWrongInput(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._num_to_one_byte, -1)
        self.assertRaises(ValueError, minimalmodbus._num_to_one_byte, 256)

    def testWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._num_to_one_byte, value)


class TestNumToTwoBytes(ExtendedTestCase):
    known_values = [
        (0.0, 0, False, False, b"\x00\x00"),  # Range 0-65535
        (0, 0, False, False, b"\x00\x00"),
        (0, 0, True, False, b"\x00\x00"),
        (77.0, 1, False, False, b"\x03\x02"),
        (77.0, 1, True, False, b"\x02\x03"),
        (770, 0, False, False, b"\x03\x02"),
        (770, 0, True, False, b"\x02\x03"),
        (65535, 0, False, False, b"\xff\xff"),
        (65535, 0, True, False, b"\xff\xff"),
        (770, 0, False, True, b"\x03\x02"),  # Range -32768 to 32767
        (77.0, 1, False, True, b"\x03\x02"),
        (0.0, 0, False, True, b"\x00\x00"),
        (0.0, 3, False, True, b"\x00\x00"),
        (-1, 0, False, True, b"\xff\xff"),
        (-1, 1, False, True, b"\xff\xf6"),
        (-77, 0, False, True, b"\xff\xb3"),
        (-770, 0, False, True, b"\xfc\xfe"),
        (-77, 1, False, True, b"\xfc\xfe"),
        (-32768, 0, False, True, b"\x80\x00"),
        (32767, 0, False, True, b"\x7f\xff"),
    ]

    def testKnownValues(self) -> None:
        for (
            inputvalue,
            number_of_decimals,
            lsb_first,
            signed,
            known_bytes,
        ) in self.known_values:
            resultbytes = minimalmodbus._num_to_two_bytes(
                inputvalue, number_of_decimals, lsb_first, signed
            )
            self.assertEqual(resultbytes, known_bytes)

    def testWrongInputValue(self) -> None:
        for lsb_first in [False, True]:
            # Range 0-65535
            self.assertRaises(
                ValueError, minimalmodbus._num_to_two_bytes, 77, -1, lsb_first
            )
            self.assertRaises(
                ValueError, minimalmodbus._num_to_two_bytes, 77, 11, lsb_first
            )
            self.assertRaises(
                ValueError,
                minimalmodbus._num_to_two_bytes,
                77000,
                0,
                lsb_first,
            )  # Gives DeprecationWarning instead of ValueError for Python 2.6
            self.assertRaises(
                ValueError,
                minimalmodbus._num_to_two_bytes,
                65536,
                0,
                lsb_first,
            )
            self.assertRaises(
                ValueError, minimalmodbus._num_to_two_bytes, 77, 4, lsb_first
            )
            self.assertRaises(
                ValueError, minimalmodbus._num_to_two_bytes, -1, 0, lsb_first
            )
            self.assertRaises(
                ValueError, minimalmodbus._num_to_two_bytes, -77, 1, lsb_first
            )

            # Range -32768 to 32767
            self.assertRaises(
                ValueError,
                minimalmodbus._num_to_two_bytes,
                77,
                -1,
                lsb_first,
                True,
            )
            self.assertRaises(
                ValueError,
                minimalmodbus._num_to_two_bytes,
                -77000,
                0,
                lsb_first,
                True,
            )
            self.assertRaises(
                ValueError,
                minimalmodbus._num_to_two_bytes,
                -32769,
                0,
                lsb_first,
                True,
            )
            self.assertRaises(
                ValueError,
                minimalmodbus._num_to_two_bytes,
                32768,
                0,
                lsb_first,
                True,
            )
            self.assertRaises(
                ValueError,
                minimalmodbus._num_to_two_bytes,
                77000,
                0,
                lsb_first,
                True,
            )
            self.assertRaises(
                ValueError,
                minimalmodbus._num_to_two_bytes,
                77,
                4,
                lsb_first,
                True,
            )
            self.assertRaises(
                ValueError,
                minimalmodbus._num_to_two_bytes,
                -77,
                4,
                lsb_first,
                True,
            )

    def testWrongInputType(self) -> None:
        value: Any = None
        for value in _NOT_NUMERICALS:
            self.assertRaises(
                TypeError, minimalmodbus._num_to_two_bytes, value, 1, False, False
            )
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError, minimalmodbus._num_to_two_bytes, 77, value, False, False
            )
        for value in _NOT_BOOLEANS:
            self.assertRaises(
                TypeError, minimalmodbus._num_to_two_bytes, 77, 1, value, False
            )
            self.assertRaises(
                TypeError, minimalmodbus._num_to_two_bytes, 77, 1, False, value
            )


class TestTwoBytesToNum(ExtendedTestCase):
    known_values = TestNumToTwoBytes.known_values

    def testKnownValues(self) -> None:
        for (
            known_value,
            number_of_decimals,
            lsb_first,
            signed,
            inputbytes,
        ) in self.known_values:
            if not lsb_first:
                resultvalue = minimalmodbus._two_bytes_to_num(
                    inputbytes, number_of_decimals, signed
                )
                self.assertEqual(resultvalue, known_value)

    def testWrongInputValue(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._two_bytes_to_num, b"ABC", 1)
        self.assertRaises(ValueError, minimalmodbus._two_bytes_to_num, b"A", 1)
        self.assertRaises(ValueError, minimalmodbus._two_bytes_to_num, b"AB", -1)
        self.assertRaises(ValueError, minimalmodbus._two_bytes_to_num, b"AB", 11)

    def testWrongInputType(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, minimalmodbus._two_bytes_to_num, value, 1)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._two_bytes_to_num, b"AB", value)
        for value in _NOT_BOOLEANS:
            self.assertRaises(
                TypeError, minimalmodbus._two_bytes_to_num, b"\x03\x02", 1, value
            )


class TestSanityTwoBytes(ExtendedTestCase):
    known_values = TestNumToTwoBytes.known_values

    def testSanity(self) -> None:
        for (
            value,
            number_of_decimals,
            lsb_first,
            signed,
            _,
        ) in self.known_values:
            if not lsb_first:
                resultvalue = minimalmodbus._two_bytes_to_num(
                    minimalmodbus._num_to_two_bytes(
                        value, number_of_decimals, lsb_first, signed
                    ),
                    number_of_decimals,
                    signed,
                )
                self.assertEqual(resultvalue, value)

        for value in range(0x10000):
            resultvalue = minimalmodbus._two_bytes_to_num(
                minimalmodbus._num_to_two_bytes(value)
            )
            self.assertEqual(resultvalue, value)


class TestBytesToBits(ExtendedTestCase):
    known_values = [
        (b"\x00", 1, [0]),
        (b"\x01", 1, [1]),
        (b"\x02", 2, [0, 1]),
        (b"\x03", 2, [1, 1]),
        (b"\x04", 3, [0, 0, 1]),
        (b"\x08", 4, [0, 0, 0, 1]),
        (b"\x10", 5, [0, 0, 0, 0, 1]),
        (b"\x20", 6, [0, 0, 0, 0, 0, 1]),
        (b"\x40", 7, [0, 0, 0, 0, 0, 0, 1]),
        (b"\x80", 8, [0, 0, 0, 0, 0, 0, 0, 1]),
        (b"\x00\x01", 9, [0, 0, 0, 0, 0, 0, 0, 0, 1]),
        (b"\x00\x02", 10, [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
        (b"\x00\x00\x01", 17, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
        (b"\x00\x00\x02", 18, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]),
        (
            b"\x00\x00\x02",
            19,
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        ),
        (b"\x01", 1, [1]),
        (b"\x01", 2, [1, 0]),
        (b"\x01", 3, [1, 0, 0]),
        (b"\x01", 4, [1, 0, 0, 0]),
        (b"\x01", 5, [1, 0, 0, 0, 0]),
        (b"\x01", 6, [1, 0, 0, 0, 0, 0]),
        (b"\x01", 7, [1, 0, 0, 0, 0, 0, 0]),
        (b"\x01", 8, [1, 0, 0, 0, 0, 0, 0, 0]),
        (b"\x01\x00", 9, [1, 0, 0, 0, 0, 0, 0, 0, 0]),
        (b"\x01\x00", 10, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
        (b"\x01\x00", 16, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
        (b"\x01\x00\x00", 17, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
        (b"\x01\x00\x00", 18, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        (
            b"\xCD\x6B\x05",
            19,
            [1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
        ),
        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        (
            b"\xAC\xDB\x35",
            22,
            [0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1],
        ),
        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        (b"\xCD\x01", 10, [1, 0, 1, 1, 0, 0, 1, 1, 1, 0]),
    ]

    def testKnownValues(self) -> None:
        for inputbytes, number_of_bits, expected_result in self.known_values:
            assert len(expected_result) == number_of_bits
            result = minimalmodbus._bytes_to_bits(inputbytes, number_of_bits)
            self.assertEqual(result, expected_result)

    def testWrongValues(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._bytes_to_bits, b"\x01\x02", 3)


class TestBitsToBytes(ExtendedTestCase):
    known_values = TestBytesToBits.known_values

    def testKnownValues(self) -> None:
        for known_result, __, bitlist in self.known_values:
            result = minimalmodbus._bits_to_bytes(bitlist)
            self.assertEqual(result, known_result)

    def testWrongValues(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._bits_to_bytes, [1, 0, 3])
        self.assertRaises(TypeError, minimalmodbus._bits_to_bytes, 1)


class TestBitToBytes(ExtendedTestCase):
    known_values = [
        (0, b"\x00\x00"),
        (1, b"\xff\x00"),
    ]

    def testKnownValues(self) -> None:
        for value, known_result in self.known_values:
            resultvalue = minimalmodbus._bit_to_bytes(value)
            self.assertEqual(resultvalue, known_result)

    def testWrongValue(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._bit_to_bytes, 2)
        self.assertRaises(ValueError, minimalmodbus._bit_to_bytes, 222)
        self.assertRaises(ValueError, minimalmodbus._bit_to_bytes, -1)

    def testValueNotInteger(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._bit_to_bytes, value)


class TestCalculateNumberOfBytesForBits(ExtendedTestCase):
    known_values = [
        (0, 0),
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 1),
        (5, 1),
        (6, 1),
        (7, 1),
        (8, 1),
        (9, 2),
        (10, 2),
        (11, 2),
        (12, 2),
        (13, 2),
        (14, 2),
        (15, 2),
        (16, 2),
        (17, 3),
    ]

    def testKnownValues(self) -> None:
        for bits, known_result in self.known_values:
            resultvalue = minimalmodbus._calculate_number_of_bytes_for_bits(bits)
            self.assertEqual(resultvalue, known_result)


class TestLongToBytes(ExtendedTestCase):
    known_values = [
        (0, 2, True, BYTEORDER_BIG, b"\x00\x00\x00\x00"),
        (1, 2, False, BYTEORDER_BIG, b"\x00\x00\x00\x01"),
        (1, 2, True, BYTEORDER_BIG, b"\x00\x00\x00\x01"),
        (2, 2, False, BYTEORDER_BIG, b"\x00\x00\x00\x02"),
        (2, 2, True, BYTEORDER_BIG, b"\x00\x00\x00\x02"),
        (75000, 2, False, BYTEORDER_BIG, b"\x00\x01\x24\xf8"),
        (75000, 2, True, BYTEORDER_BIG, b"\x00\x01\x24\xf8"),
        (1000000, 2, False, BYTEORDER_BIG, b"\x00\x0f\x42\x40"),
        (1000000, 2, True, BYTEORDER_BIG, b"\x00\x0f\x42\x40"),
        (2147483647, 2, False, BYTEORDER_BIG, b"\x7f\xff\xff\xff"),
        (2147483647, 2, True, BYTEORDER_BIG, b"\x7f\xff\xff\xff"),
        (2147483648, 2, False, BYTEORDER_BIG, b"\x80\x00\x00\x00"),
        (4294967295, 2, False, BYTEORDER_BIG, b"\xff\xff\xff\xff"),
        (-1, 2, True, BYTEORDER_BIG, b"\xff\xff\xff\xff"),
        (-2147483648, 2, True, BYTEORDER_BIG, b"\x80\x00\x00\x00"),
        (-200000000, 2, True, BYTEORDER_BIG, b"\xf4\x14\x3e\x00"),
        # Example from https://www.simplymodbus.ca/FAQ.htm
        (2923517522, 2, False, BYTEORDER_BIG, b"\xAE\x41\x56\x52"),
        # Example from https://www.simplymodbus.ca/FAQ.htm
        (-1371449774, 2, True, BYTEORDER_BIG, b"\xAE\x41\x56\x52"),
        # Example from https://www.simplymodbus.ca/FAQ.htm
        (2923517522, 2, False, BYTEORDER_LITTLE, b"\x52\x56\x41\xAE"),
        # Example from https://www.simplymodbus.ca/FAQ.htm (the byteorder is not named)
        (2923517522, 2, False, BYTEORDER_LITTLE_SWAP, b"\x56\x52\xAE\x41"),
        # Example from https://www.simplymodbus.ca/FAQ.htm (the byteorder is not named)
        (2923517522, 2, False, BYTEORDER_BIG_SWAP, b"\x41\xAE\x52\x56"),
        (0, 4, True, BYTEORDER_BIG, b"\x00\x00\x00\x00\x00\x00\x00\x00"),
        (0, 4, False, BYTEORDER_BIG, b"\x00\x00\x00\x00\x00\x00\x00\x00"),
        (1, 4, True, BYTEORDER_BIG, b"\x00\x00\x00\x00\x00\x00\x00\x01"),
        (1, 4, False, BYTEORDER_BIG, b"\x00\x00\x00\x00\x00\x00\x00\x01"),
        (-1, 4, True, BYTEORDER_BIG, b"\xff\xff\xff\xff\xff\xff\xff\xff"),
    ]

    def testKnownValues(self) -> None:
        for value, num_registers, signed, byteorder, known_bytes in self.known_values:
            resultbytes = minimalmodbus._long_to_bytes(
                value, signed, num_registers, byteorder
            )
            self.assertEqual(resultbytes, known_bytes)

    def testWrongInputValue(self) -> None:
        self.assertRaises(
            ValueError, minimalmodbus._long_to_bytes, -1, False, 2
        )  # Range 0 to 4294967295
        self.assertRaises(
            ValueError, minimalmodbus._long_to_bytes, 4294967296, False, 2
        )
        self.assertRaises(
            ValueError, minimalmodbus._long_to_bytes, -2147483649, True, 2
        )  # Range -2147483648 to 2147483647
        self.assertRaises(ValueError, minimalmodbus._long_to_bytes, 2147483648, True, 2)
        self.assertRaises(
            ValueError, minimalmodbus._long_to_bytes, 222222222222222, True, 2
        )

        for number_of_registers in [0, 1, 3, 5, 6, 7, 8, 9, 16]:
            self.assertRaises(
                ValueError,
                minimalmodbus._long_to_bytes,
                1,
                True,
                number_of_registers,
            )

    def testWrongInputType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._long_to_bytes, value, True, 2)
            self.assertRaises(TypeError, minimalmodbus._long_to_bytes, 1, True, value)
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, minimalmodbus._long_to_bytes, 1, value, 2)


class TestBytesToLong(ExtendedTestCase):
    known_values = TestLongToBytes.known_values

    def testKnownValues(self) -> None:
        for (
            known_value,
            num_registers,
            signed,
            byteorder,
            inputbytes,
        ) in self.known_values:
            resultvalue = minimalmodbus._bytes_to_long(
                inputbytes, signed, num_registers, byteorder
            )
            self.assertEqual(resultvalue, known_value)

    def testWrongInputValue(self) -> None:
        for inputbytes in [b"", b"A", b"AA", b"AAA", b"AAAAA"]:
            self.assertRaises(
                ValueError, minimalmodbus._bytes_to_long, inputbytes, True, 2
            )
        for inputbytes in [
            b"",
            b"A",
            b"AA",
            b"AAA",
            b"AAAA",
            b"AAAAA",
            b"AAAAA",
            b"AAAAAAA",
            b"AAAAAAAAA",
        ]:
            self.assertRaises(
                ValueError, minimalmodbus._bytes_to_long, inputbytes, True, 4
            )
        for number_of_registers in [0, 1, 3, 4, 5, 6, 7, 8, 16]:
            self.assertRaises(
                ValueError,
                minimalmodbus._bytes_to_long,
                b"AAAA",
                True,
                number_of_registers,
            )

    def testWrongInputType(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, minimalmodbus._bytes_to_long, value, True, 2)
        for value in _NOT_BOOLEANS:
            self.assertRaises(
                TypeError, minimalmodbus._bytes_to_long, b"AAAA", value, 2
            )
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError, minimalmodbus._bytes_to_long, b"AAAA", True, value
            )


class TestSanityLong(ExtendedTestCase):
    known_values = TestLongToBytes.known_values

    def testSanity(self) -> None:
        for value, num_registers, signed, byteorder, _ in self.known_values:
            resultvalue = minimalmodbus._bytes_to_long(
                minimalmodbus._long_to_bytes(value, signed, num_registers, byteorder),
                signed,
                num_registers,
                byteorder,
            )
            self.assertEqual(resultvalue, value)


class TestFloatToBytes(ExtendedTestCase):
    # Use this online calculator:
    # https://www.h-schmidt.net/FloatConverter/IEEE754.html

    # See also examples in
    # http://en.wikipedia.org/wiki/Single-precision_floating-point_format
    # http://en.wikipedia.org/wiki/Double-precision_floating-point_format

    known_values = [
        (1, 2, BYTEORDER_BIG, b"\x3f\x80\x00\x00"),
        (1.0, 2, BYTEORDER_BIG, b"\x3f\x80\x00\x00"),  # wikipedia
        (1.0, 2, BYTEORDER_BIG, b"?\x80\x00\x00"),
        (1.1, 2, BYTEORDER_BIG, b"\x3f\x8c\xcc\xcd"),
        (100, 2, BYTEORDER_BIG, b"\x42\xc8\x00\x00"),
        (100.0, 2, BYTEORDER_BIG, b"\x42\xc8\x00\x00"),
        (1.0e5, 2, BYTEORDER_BIG, b"\x47\xc3\x50\x00"),
        (1.1e9, 2, BYTEORDER_BIG, b"\x4e\x83\x21\x56"),
        (1.0e16, 2, BYTEORDER_BIG, b"\x5a\x0e\x1b\xca"),
        (1.5e16, 2, BYTEORDER_BIG, b"\x5a\x55\x29\xaf"),
        (3.65e30, 2, BYTEORDER_BIG, b"\x72\x38\x47\x25"),
        (-1.1, 2, BYTEORDER_BIG, b"\xbf\x8c\xcc\xcd"),
        (-2, 2, BYTEORDER_BIG, b"\xc0\x00\x00\x00"),
        (-3.6e30, 2, BYTEORDER_BIG, b"\xf2\x35\xc0\xe9"),
        (1.0, 4, BYTEORDER_BIG, b"\x3f\xf0\x00\x00\x00\x00\x00\x00"),
        (2, 4, BYTEORDER_BIG, b"\x40\x00\x00\x00\x00\x00\x00\x00"),
        (1.1e9, 4, BYTEORDER_BIG, b"\x41\xd0\x64\x2a\xc0\x00\x00\x00"),
        (3.65e30, 4, BYTEORDER_BIG, b"\x46\x47\x08\xe4\x9e\x2f\x4d\x62"),
        (2.42e300, 4, BYTEORDER_BIG, b"\x7e\x4c\xe8\xa5\x67\x1f\x46\xa0"),
        (-1.1, 4, BYTEORDER_BIG, b"\xbf\xf1\x99\x99\x99\x99\x99\x9a"),
        (-2, 4, BYTEORDER_BIG, b"\xc0\x00\x00\x00\x00\x00\x00\x00"),
        (-3.6e30, 4, BYTEORDER_BIG, b"\xc6\x46\xb8\x1d\x1a\x43\xb2\x06"),
        (-3.6e30, 4, BYTEORDER_LITTLE, b"\x06\xb2\x43\x1a\x1d\xb8\x46\xc6"),
        (-3.6e30, 4, BYTEORDER_BIG_SWAP, b"\x46\xc6\x1d\xb8\x43\x1a\x06\xb2"),
        (-3.6e30, 4, BYTEORDER_LITTLE_SWAP, b"\xb2\x06\x1a\x43\xb8\x1d\xc6\x46"),
        # Example from https://www.simplymodbus.ca/FAQ.htm (truncated float on page)
        (-4.3959787e-11, 2, BYTEORDER_BIG, b"\xAE\x41\x56\x52"),
        # Shifted byte positions manually
        (-4.3959787e-11, 2, BYTEORDER_LITTLE, b"\x52\x56\x41\xAE"),
        # Shifted byte positions manually
        (-4.3959787e-11, 2, BYTEORDER_BIG_SWAP, b"\x41\xAE\x52\x56"),
        # Shifted byte positions manually
        (-4.3959787e-11, 2, BYTEORDER_LITTLE_SWAP, b"\x56\x52\xAE\x41"),
        # Calculated by  https://www.h-schmidt.net/FloatConverter/IEEE754.html
        (123456.00, 2, BYTEORDER_BIG, b"\x47\xF1\x20\x00"),
        # Example from https://store.chipkin.com/articles/how-real-floating-point-
        #         and-32-bit-data-is-encoded-in-modbus-rtu-messages
        #         Byte order = "No swap"
        (123456.00, 2, BYTEORDER_LITTLE, b"\x00\x20\xF1\x47"),
    ]

    def testKnownValues(self) -> None:
        for value, number_of_registers, byteorder, known_bytes in self.known_values:
            resultbytes = minimalmodbus._float_to_bytes(
                value, number_of_registers, byteorder
            )
            self.assertEqual(resultbytes, known_bytes)
        self.assertEqual(
            minimalmodbus._float_to_bytes(1.5e999, 2), b"\x7f\x80\x00\x00"
        )  # +inf

    def testWrongInputValue(self) -> None:
        # Note: Out of range will not necessarily raise any error, instead it
        # will indicate +inf etc.
        for number_of_registers in [0, 1, 3, 5, 6, 7, 8, 9, 16]:
            self.assertRaises(
                ValueError, minimalmodbus._float_to_bytes, 1.1, number_of_registers
            )

    def testWrongInputType(self) -> None:
        value: Any = None
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, minimalmodbus._float_to_bytes, value, 2)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._float_to_bytes, 1.1, value)


class TestBytesToFloat(ExtendedTestCase):
    known_values = TestFloatToBytes.known_values

    def testKnownValues(self) -> None:
        for (
            known_value,
            number_of_registers,
            byteorder,
            inputbytes,
        ) in self.known_values:
            resultvalue = minimalmodbus._bytes_to_float(
                inputbytes, number_of_registers, byteorder
            )
            self.assertAlmostEqualRatio(resultvalue, known_value)

    def testWrongInputValue(self) -> None:
        for inputbytes in [
            b"",
            b"A",
            b"AB",
            b"ABC",
            # Not 4 bytes
            b"ABCDE",
            b"ABCDEF",
            b"ABCDEFG",
            # Not 8 bytes
            b"ABCDEFGHI",
        ]:
            self.assertRaises(ValueError, minimalmodbus._bytes_to_float, inputbytes, 2)
            self.assertRaises(ValueError, minimalmodbus._bytes_to_float, inputbytes, 4)
        for number_of_registers in [0, 1, 3, 5, 6, 7, 8, 9, 16]:
            self.assertRaises(
                ValueError,
                minimalmodbus._bytes_to_float,
                b"ABCD",
                number_of_registers,
            )
            self.assertRaises(
                ValueError,
                minimalmodbus._bytes_to_float,
                b"ABCDEFGH",
                number_of_registers,
            )

    def testWrongInputType(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, minimalmodbus._bytes_to_float, value, 2)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._bytes_to_float, 1.1, value)


class TestSanityFloat(ExtendedTestCase):
    known_values = TestFloatToBytes.known_values

    def testSanity(self) -> None:
        for value, number_of_registers, byteorder, _ in self.known_values:
            resultvalue = minimalmodbus._bytes_to_float(
                minimalmodbus._float_to_bytes(value, number_of_registers, byteorder),
                number_of_registers,
                byteorder,
            )
            self.assertAlmostEqualRatio(resultvalue, value)


class TestValuelistToBytes(ExtendedTestCase):
    known_values = [
        ([1], 1, b"\x00\x01"),
        ([0, 0], 2, b"\x00\x00\x00\x00"),
        ([1, 2], 2, b"\x00\x01\x00\x02"),
        ([1, 256], 2, b"\x00\x01\x01\x00"),
        ([1, 2, 3, 4], 4, b"\x00\x01\x00\x02\x00\x03\x00\x04"),
        ([1, 2, 3, 4, 5], 5, b"\x00\x01\x00\x02\x00\x03\x00\x04\x00\x05"),
    ]

    def testKnownValues(self) -> None:
        for value, number_of_registers, known_bytes in self.known_values:
            resultbytes = minimalmodbus._valuelist_to_bytes(value, number_of_registers)
            self.assertEqual(resultbytes, known_bytes)

    def testWrongInputValue(self) -> None:
        self.assertRaises(
            ValueError, minimalmodbus._valuelist_to_bytes, [-1, 2, 3, 4], 4
        )
        self.assertRaises(
            ValueError, minimalmodbus._valuelist_to_bytes, [1, 2, 3, 4], 1
        )
        self.assertRaises(
            ValueError, minimalmodbus._valuelist_to_bytes, [1, 2, 3, 4], -4
        )

    def testWrongInputType(self) -> None:
        for value in _NOT_INTLISTS:
            self.assertRaises(TypeError, minimalmodbus._valuelist_to_bytes, value, 4)
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError, minimalmodbus._valuelist_to_bytes, [1, 2, 3, 4], value
            )


class TestBytesToValuelist(ExtendedTestCase):
    known_values = TestValuelistToBytes.known_values

    def testKnownValues(self) -> None:
        for knownlist, number_of_registers, inputbytes in self.known_values:
            resultlist = minimalmodbus._bytes_to_valuelist(
                inputbytes, number_of_registers
            )
            self.assertEqual(resultlist, knownlist)

    def testWrongInputValue(self) -> None:
        self.assertRaises(
            ValueError, minimalmodbus._bytes_to_valuelist, b"\x00\x01\x00\x02", 1
        )
        self.assertRaises(ValueError, minimalmodbus._bytes_to_valuelist, b"", 1)
        self.assertRaises(ValueError, minimalmodbus._bytes_to_valuelist, b"\x00\x01", 0)
        self.assertRaises(
            ValueError, minimalmodbus._bytes_to_valuelist, b"\x00\x01", -1
        )

    def testWrongInputType(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, minimalmodbus._bytes_to_valuelist, value, 1)
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._bytes_to_valuelist, b"A", value)


class TestSanityValuelist(ExtendedTestCase):
    known_values = TestValuelistToBytes.known_values

    def testSanity(self) -> None:
        for valuelist, number_of_registers, _ in self.known_values:
            resultlist = minimalmodbus._bytes_to_valuelist(
                minimalmodbus._valuelist_to_bytes(valuelist, number_of_registers),
                number_of_registers,
            )
            self.assertEqual(resultlist, valuelist)


class TestTextstringToBytes(ExtendedTestCase):
    known_values = [
        ("A", 1, b"A "),
        ("AB", 1, b"AB"),
        ("ABC", 2, b"ABC "),
        ("ABCD", 2, b"ABCD"),
        ("A", 16, b"A" + b" " * 31),
        ("A", 32, b"A" + b" " * 63),
        ("A" * 246, 123, b"A" * 246),
    ]

    def testKnownValues(self) -> None:
        for textstring, number_of_registers, known_bytes in self.known_values:
            resultbytes = minimalmodbus._textstring_to_bytes(
                textstring, number_of_registers
            )
            self.assertEqual(resultbytes, known_bytes)

    def testWrongInputValue(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._textstring_to_bytes, "", 1)  # TODO
        self.assertRaises(ValueError, minimalmodbus._textstring_to_bytes, "ABC", 1)
        self.assertRaises(ValueError, minimalmodbus._textstring_to_bytes, "A", -1)
        self.assertRaises(ValueError, minimalmodbus._textstring_to_bytes, "A", 124)

    def testWrongInputType(self) -> None:
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._textstring_to_bytes, value, 1)
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError, minimalmodbus._textstring_to_bytes, "AB", value
            )


class TestBytesToTextstring(ExtendedTestCase):
    known_values = TestTextstringToBytes.known_values

    def testKnownValues(self) -> None:
        for known_bytes, number_of_registers, inputbytes in self.known_values:
            resultbytes = minimalmodbus._bytes_to_textstring(
                inputbytes, number_of_registers
            )
            self.assertEqual(resultbytes.strip(), known_bytes)

    def testWrongInputValue(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._bytes_to_textstring, b"A", 1)
        self.assertRaises(ValueError, minimalmodbus._bytes_to_textstring, b"", 1)
        self.assertRaises(ValueError, minimalmodbus._bytes_to_textstring, b"", 0)
        self.assertRaises(ValueError, minimalmodbus._bytes_to_textstring, b"ABC", 1)
        self.assertRaises(ValueError, minimalmodbus._bytes_to_textstring, b"AB", 0)
        self.assertRaises(ValueError, minimalmodbus._bytes_to_textstring, b"AB", -1)
        self.assertRaises(ValueError, minimalmodbus._bytes_to_textstring, b"AB", 126)

    def testWrongInputType(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, minimalmodbus._bytes_to_textstring, value, 1)
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError, minimalmodbus._bytes_to_textstring, b"AB", value
            )


class TestSanityTextstring(ExtendedTestCase):
    known_values = TestTextstringToBytes.known_values

    def testSanity(self) -> None:
        for textstring, number_of_registers, _ in self.known_values:
            resultstring = minimalmodbus._bytes_to_textstring(
                minimalmodbus._textstring_to_bytes(textstring, number_of_registers),
                number_of_registers,
            )
            self.assertEqual(resultstring.strip(), textstring)


class TestPack(ExtendedTestCase):
    known_values = [
        (-77, ">h", b"\xff\xb3"),  # (Signed) short (2 bytes)
        (-1, ">h", b"\xff\xff"),
        (-770, ">h", b"\xfc\xfe"),
        (-32768, ">h", b"\x80\x00"),
        (32767, ">h", b"\x7f\xff"),
        (770, ">H", b"\x03\x02"),  # Unsigned short (2 bytes)
        (65535, ">H", b"\xff\xff"),
        (75000, ">l", b"\x00\x01\x24\xf8"),  # (Signed) long (4 bytes)
        (-1, ">l", b"\xff\xff\xff\xff"),
        (-2147483648, ">l", b"\x80\x00\x00\x00"),
        (-200000000, ">l", b"\xf4\x14\x3e\x00"),
        (1, ">L", b"\x00\x00\x00\x01"),  # Unsigned long (4 bytes)
        (75000, ">L", b"\x00\x01\x24\xf8"),
        (2147483648, ">L", b"\x80\x00\x00\x00"),
        (2147483647, ">L", b"\x7f\xff\xff\xff"),
        (1.0, ">f", b"\x3f\x80\x00\x00"),  # Float (4 bytes)
        (1.0e5, ">f", b"\x47\xc3\x50\x00"),
        (1.0e16, ">f", b"\x5a\x0e\x1b\xca"),
        (3.65e30, ">f", b"\x72\x38\x47\x25"),
        (-2, ">f", b"\xc0\x00\x00\x00"),
        (-3.6e30, ">f", b"\xf2\x35\xc0\xe9"),
        (1.0, ">d", b"\x3f\xf0\x00\x00\x00\x00\x00\x00"),  # Double (8 bytes)
        (2, ">d", b"\x40\x00\x00\x00\x00\x00\x00\x00"),
        (1.1e9, ">d", b"\x41\xd0\x64\x2a\xc0\x00\x00\x00"),
        (3.65e30, ">d", b"\x46\x47\x08\xe4\x9e\x2f\x4d\x62"),
        (2.42e300, ">d", b"\x7e\x4c\xe8\xa5\x67\x1f\x46\xa0"),
        (-1.1, ">d", b"\xbf\xf1\x99\x99\x99\x99\x99\x9a"),
        (-2, ">d", b"\xc0\x00\x00\x00\x00\x00\x00\x00"),
    ]

    def testKnownValues(self) -> None:
        for value, formatstring, known_bytes in self.known_values:
            resultbytes = minimalmodbus._pack_bytes(formatstring, value)
            self.assertEqual(resultbytes, known_bytes)

    def testWrongInputValue(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._pack_bytes, "ABC", 35)
        self.assertRaises(ValueError, minimalmodbus._pack_bytes, "", 35)
        self.assertRaises(ValueError, minimalmodbus._pack_bytes, ">H", -35)
        self.assertRaises(ValueError, minimalmodbus._pack_bytes, ">L", -35)

    def testWrongInputType(self) -> None:
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._pack_bytes, value, 1)
        for value in ["1", ["1"], [1], ["\x00\x2d\x00\x58"], ["A", "B", "C"], "ABC"]:
            self.assertRaises(ValueError, minimalmodbus._pack_bytes, ">h", value)


class TestUnpack(ExtendedTestCase):
    known_values = TestPack.known_values

    def testKnownValues(self) -> None:
        for known_value, formatstring, inputbytes in self.known_values:
            resultvalue = minimalmodbus._unpack_bytes(formatstring, inputbytes)
            self.assertAlmostEqualRatio(resultvalue, known_value)

    def testWrongInputValue(self) -> None:
        self.assertRaises(
            InvalidResponseError, minimalmodbus._unpack_bytes, "ABC", b"\xff\xb3"
        )
        self.assertRaises(ValueError, minimalmodbus._unpack_bytes, "", b"\xff\xb3")
        self.assertRaises(ValueError, minimalmodbus._unpack_bytes, ">h", b"")

    def testWrongInputType(self) -> None:
        for value in _NOT_STRINGS:
            self.assertRaises(
                TypeError, minimalmodbus._unpack_bytes, value, b"\xff\xb3"
            )
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, minimalmodbus._unpack_bytes, ">h", value)


class TestSwap(ExtendedTestCase):
    known_values = [
        (b"", b""),
        (b"AB", b"BA"),
        (b"ABCD", b"BADC"),
        (b"ABCDEF", b"BADCFE"),
        (b"ABCDEFGH", b"BADCFEHG"),
        (b"ABCDEFGHIJ", b"BADCFEHGJI"),
        (b"ABCDEFGHIJKL", b"BADCFEHGJILK"),
    ]

    wrongValues = [b"A", b"ABC", b"ABCDE", b"A" * 123]

    def testKnownValues(self) -> None:
        for inputvalue, known_result in self.known_values:
            result = minimalmodbus._swap(inputvalue)
            self.assertEqual(result, known_result)

    def testWrongValues(self) -> None:
        for value in self.wrongValues:
            self.assertRaises(ValueError, minimalmodbus._swap, value)


class TestSanityPackUnpack(ExtendedTestCase):
    known_values = TestPack.known_values

    def testSanity(self) -> None:
        for _, formatstring, known_bytes in self.known_values:
            resultbytes = minimalmodbus._pack_bytes(
                formatstring, minimalmodbus._unpack_bytes(formatstring, known_bytes)
            )
            self.assertEqual(resultbytes, known_bytes)


class TestHexencode(ExtendedTestCase):
    known_values = [
        (b"", False, b""),
        (b"7", False, b"37"),
        (b"J", False, b"4A"),
        (b"\x5d", False, b"5D"),
        (b"\x04", False, b"04"),
        (b"\x04\x5d", False, b"045D"),
        (b"mn", False, b"6D6E"),
        (b"Katt1", False, b"4B61747431"),
        (b"", True, b""),
        (b"7", True, b"37"),
        (b"J", True, b"4A"),
        (b"\x5d", True, b"5D"),
        (b"\x04", True, b"04"),
        (b"\x04\x5d", True, b"04 5D"),
        (b"mn", True, b"6D 6E"),
        (b"Katt1", True, b"4B 61 74 74 31"),
    ]

    def testKnownValues(self) -> None:
        for value, insert_spaces, known_bytes in self.known_values:
            resultbytes = minimalmodbus._hexencode(value, insert_spaces)
            self.assertEqual(resultbytes, known_bytes)

    def testWrongInputValue(self) -> None:
        pass

    def testWrongInputType(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, minimalmodbus._hexencode, value)


class TestHexdecode(ExtendedTestCase):
    known_values = TestHexencode.known_values

    def testKnownValues(self) -> None:
        for known_bytes, insert_spaces, value in self.known_values:
            if not insert_spaces:
                resultbytes = minimalmodbus._hexdecode(value)
                self.assertEqual(resultbytes, known_bytes)

        self.assertEqual(minimalmodbus._hexdecode(b"4A"), b"J")
        self.assertEqual(minimalmodbus._hexdecode(b"4a"), b"J")

    def testAllowLowercase(self) -> None:
        minimalmodbus._hexdecode(b"Aa")
        minimalmodbus._hexdecode(b"aa23")

    def testWrongInputValue(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._hexdecode, b"A")
        self.assertRaises(ValueError, minimalmodbus._hexdecode, b"AAA")
        self.assertRaises(TypeError, minimalmodbus._hexdecode, b"AG")

    def testWrongInputType(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, minimalmodbus._hexdecode, value)


class TestSanityHexencodeHexdecode(ExtendedTestCase):
    known_values = TestHexencode.known_values

    def testKnownValues(self) -> None:
        for value, insert_spaces, _ in self.known_values:
            if not insert_spaces:
                resultbytes = minimalmodbus._hexdecode(minimalmodbus._hexencode(value))
                self.assertEqual(resultbytes, value)

    def testKnownValuesLoop(self) -> None:
        """Loop through all bytes objects of length two."""
        RANGE_VALUE = 256
        for i in range(RANGE_VALUE):
            for j in range(RANGE_VALUE):
                inputbytes = bytes([i, j])
                resultbytes = minimalmodbus._hexdecode(
                    minimalmodbus._hexencode(inputbytes)
                )
                self.assertEqual(resultbytes, inputbytes)


class TestDescribeBytes(ExtendedTestCase):
    def testKnownValues(self) -> None:
        self.assertEqual(
            minimalmodbus._describe_bytes(b"\x01\x02\x03"), "01 02 03 (3 bytes)"
        )


############################
# Test number manipulation #
############################


class TestTwosComplement(ExtendedTestCase):
    known_values = [
        (0, 8, 0),
        (1, 8, 1),
        (127, 8, 127),
        (-128, 8, 128),
        (-127, 8, 129),
        (-1, 8, 255),
        (0, 16, 0),
        (1, 16, 1),
        (32767, 16, 32767),
        (-32768, 16, 32768),
        (-32767, 16, 32769),
        (-1, 16, 65535),
    ]

    def testKnownValues(self) -> None:
        for x, bits, known_result in self.known_values:
            result = minimalmodbus._twos_complement(x, bits)
            self.assertEqual(result, known_result)

    def testOutOfRange(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._twos_complement, 128, 8)
        self.assertRaises(ValueError, minimalmodbus._twos_complement, 1000000, 8)
        self.assertRaises(ValueError, minimalmodbus._twos_complement, -129, 8)
        self.assertRaises(ValueError, minimalmodbus._twos_complement, 32768, 16)
        self.assertRaises(ValueError, minimalmodbus._twos_complement, 1000000, 16)
        self.assertRaises(ValueError, minimalmodbus._twos_complement, -32769, 16)
        self.assertRaises(ValueError, minimalmodbus._twos_complement, 1, 0)
        self.assertRaises(ValueError, minimalmodbus._twos_complement, 1, -1)
        self.assertRaises(ValueError, minimalmodbus._twos_complement, 1, -2)
        self.assertRaises(ValueError, minimalmodbus._twos_complement, 1, -100)

    def testWrongInputType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._twos_complement, value, 8)


class TestFromTwosComplement(ExtendedTestCase):
    known_values = TestTwosComplement.known_values

    def testKnownValues(self) -> None:
        for known_result, bits, x in self.known_values:
            result = minimalmodbus._from_twos_complement(x, bits)
            self.assertEqual(result, known_result)

    def testOutOfRange(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._from_twos_complement, 256, 8)
        self.assertRaises(ValueError, minimalmodbus._from_twos_complement, 1000000, 8)
        self.assertRaises(ValueError, minimalmodbus._from_twos_complement, -1, 8)
        self.assertRaises(ValueError, minimalmodbus._from_twos_complement, 65536, 16)
        self.assertRaises(ValueError, minimalmodbus._from_twos_complement, 1000000, 16)
        self.assertRaises(ValueError, minimalmodbus._from_twos_complement, -1, 16)
        self.assertRaises(ValueError, minimalmodbus._from_twos_complement, 1, 0)
        self.assertRaises(ValueError, minimalmodbus._from_twos_complement, 1, -1)
        self.assertRaises(ValueError, minimalmodbus._from_twos_complement, 1, -2)
        self.assertRaises(ValueError, minimalmodbus._from_twos_complement, 1, -100)

    def testWrongInputType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._from_twos_complement, value, 8)
            self.assertRaises(TypeError, minimalmodbus._from_twos_complement, 1, value)


class TestSanityTwosComplement(ExtendedTestCase):
    known_values = [1, 2, 4, 8, 12, 16]

    def testSanity(self) -> None:
        for bits in self.known_values:
            for x in range(2**bits):
                resultvalue = minimalmodbus._twos_complement(
                    minimalmodbus._from_twos_complement(x, bits), bits
                )
                self.assertEqual(resultvalue, x)


#########################
# Test bit manipulation #
#########################


class TestSetBitOn(ExtendedTestCase):
    known_values = [
        (4, 0, 5),
        (4, 1, 6),
        (1, 1, 3),
    ]

    def testKnownValues(self) -> None:
        for x, bitnum, known_result in self.known_values:
            result = minimalmodbus._set_bit_on(x, bitnum)
            self.assertEqual(result, known_result)

    def testWrongInputValue(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._set_bit_on, 1, -1)
        self.assertRaises(ValueError, minimalmodbus._set_bit_on, -2, 1)

    def testWrongInputType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._set_bit_on, value, 1)
            self.assertRaises(TypeError, minimalmodbus._set_bit_on, 1, value)


class TestCheckBit(ExtendedTestCase):
    known_values = [
        (0, 0, False),
        (0, 1, False),
        (0, 2, False),
        (0, 3, False),
        (0, 4, False),
        (0, 5, False),
        (0, 6, False),
        (4, 0, False),
        (4, 1, False),
        (4, 2, True),
        (4, 3, False),
        (4, 4, False),
        (4, 5, False),
        (4, 5, False),
    ]

    def testKnownValues(self) -> None:
        for x, bitnum, known_result in self.known_values:
            result = minimalmodbus._check_bit(x, bitnum)
            self.assertEqual(result, known_result)

    def testWrongInputValue(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._check_bit, 1, -1)
        self.assertRaises(ValueError, minimalmodbus._check_bit, -2, 1)

    def testWrongInputType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._check_bit, value, 1)
            self.assertRaises(TypeError, minimalmodbus._check_bit, 1, value)


############################
# Error checking functions #
############################


class TestCalculateCrc(ExtendedTestCase):
    # Example from MODBUS over Serial Line Specification and Implementation Guide V1.02
    known_values = [
        (
            b"\x02\x07",
            b"\x41\x12",
        ),
        (b"ABCDE", b"\x0fP"),
    ]

    def testKnownValues(self) -> None:
        for inputbytes, known_result in self.known_values:
            resultbytes = minimalmodbus._calculate_crc(inputbytes)
            self.assertEqual(resultbytes, known_result)

    def testCalculationTime(self) -> None:
        all_byte_variants = [minimalmodbus._num_to_two_bytes(i) for i in range(2**16)]
        print(
            "\n\n   Measuring CRC calculation time. Running {} calculations ...".format(
                len(all_byte_variants)
            )
        )
        start_time = time.time()
        for byte_variants in all_byte_variants:
            minimalmodbus._calculate_crc(byte_variants)
        calculation_time = time.time() - start_time
        print(
            "CRC calculation time: "
            + "{} calculations took {:.3f} s ({} s per calculation)\n\n".format(
                len(all_byte_variants),
                calculation_time,
                calculation_time / float(len(all_byte_variants)),
            )
        )

    def testNotByteInput(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, minimalmodbus._calculate_crc, value)


class TestCalculateLrc(ExtendedTestCase):
    known_values = [
        (b"ABCDE", b"\xb1"),
        (
            b"\x02\x30\x30\x31\x23\x03",
            b"\x47",
        ),  # From http://en.wikipedia.org/wiki/Longitudinal_redundancy_check
    ]

    def testKnownValues(self) -> None:
        for inputbytes, known_result in self.known_values:
            resultbytes = minimalmodbus._calculate_lrc(inputbytes)
            self.assertEqual(resultbytes, known_result)

    def testNotStringInput(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, minimalmodbus._calculate_lrc, value)


class TestCheckFunctioncode(ExtendedTestCase):
    def testCorrectFunctioncode(self) -> None:
        minimalmodbus._check_functioncode(4, [4, 5])

    def testCorrectFunctioncodeNoRange(self) -> None:
        minimalmodbus._check_functioncode(4, None)
        minimalmodbus._check_functioncode(75, None)

    def testWrongFunctioncode(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._check_functioncode, 3, [4, 5])
        self.assertRaises(ValueError, minimalmodbus._check_functioncode, 3, [])

    def testWrongFunctioncodeNoRange(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._check_functioncode, 1000, None)
        self.assertRaises(ValueError, minimalmodbus._check_functioncode, -1, None)

    def testWrongFunctioncodeType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError, minimalmodbus._check_functioncode, value, [4, 5]
            )

    def testWrongFunctioncodeListValues(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._check_functioncode, -1, [-1, 5])
        self.assertRaises(ValueError, minimalmodbus._check_functioncode, 128, [4, 128])

    def testWrongListType(self) -> None:
        self.assertRaises(TypeError, minimalmodbus._check_functioncode, 4, 4)
        self.assertRaises(TypeError, minimalmodbus._check_functioncode, 4, "ABC")
        self.assertRaises(TypeError, minimalmodbus._check_functioncode, 4, (4, 5))
        self.assertRaises(ValueError, minimalmodbus._check_functioncode, 4, [4, -23])
        self.assertRaises(ValueError, minimalmodbus._check_functioncode, 4, [4, 128])
        self.assertRaises(TypeError, minimalmodbus._check_functioncode, 4, [4, "5"])
        self.assertRaises(TypeError, minimalmodbus._check_functioncode, 4, [4, None])
        self.assertRaises(TypeError, minimalmodbus._check_functioncode, 4, [4, [5]])
        self.assertRaises(TypeError, minimalmodbus._check_functioncode, 4, [4.0, 5])


class TestCheckSlaveaddress(ExtendedTestCase):
    def testKnownValues(self) -> None:
        minimalmodbus._check_slaveaddress(0)  # Broadcast
        minimalmodbus._check_slaveaddress(1)
        minimalmodbus._check_slaveaddress(10)
        minimalmodbus._check_slaveaddress(247)
        minimalmodbus._check_slaveaddress(255)  # Reserved

    def testWrongValues(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._check_slaveaddress, -1)
        self.assertRaises(ValueError, minimalmodbus._check_slaveaddress, 256)

    def testNotIntegerInput(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._check_slaveaddress, value)


class TestCheckMode(ExtendedTestCase):
    def testKnownValues(self) -> None:
        minimalmodbus._check_mode("ascii")
        minimalmodbus._check_mode("rtu")

    def testWrongValues(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._check_mode, "asc")
        self.assertRaises(ValueError, minimalmodbus._check_mode, "ASCII")
        self.assertRaises(ValueError, minimalmodbus._check_mode, "RTU")
        self.assertRaises(ValueError, minimalmodbus._check_mode, "")
        self.assertRaises(ValueError, minimalmodbus._check_mode, "ascii ")
        self.assertRaises(ValueError, minimalmodbus._check_mode, " rtu")

    def testNotIntegerInput(self) -> None:
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, minimalmodbus._check_mode, value)


class TestCheckRegisteraddress(ExtendedTestCase):
    def testKnownValues(self) -> None:
        minimalmodbus._check_registeraddress(0)
        minimalmodbus._check_registeraddress(1)
        minimalmodbus._check_registeraddress(10)
        minimalmodbus._check_registeraddress(65535)

    def testWrongValues(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._check_registeraddress, -1)
        self.assertRaises(ValueError, minimalmodbus._check_registeraddress, 65536)

    def testWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._check_registeraddress, value)


class TestCheckResponseSlaveErrorCode(ExtendedTestCase):
    def testResponsesWithoutErrors(self) -> None:
        minimalmodbus._check_response_slaveerrorcode(b"\x01\x01\x01\x00Q\x88")
        minimalmodbus._check_response_slaveerrorcode(b"\x01\x01\x05")
        minimalmodbus._check_response_slaveerrorcode(b"\x01\x81\x05")

    def testResponsesWithErrors(self) -> None:
        self.assertRaises(
            IllegalRequestError,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\x01",
        )
        self.assertRaises(
            IllegalRequestError,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\x02",
        )
        self.assertRaises(
            IllegalRequestError,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\x03",
        )
        self.assertRaises(
            SlaveReportedException,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\x04",
        )
        self.assertRaises(
            SlaveDeviceBusyError,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\x06",
        )
        self.assertRaises(
            NegativeAcknowledgeError,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\x07",
        )
        self.assertRaises(
            SlaveReportedException,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\x08",
        )
        self.assertRaises(
            SlaveReportedException,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\x09",
        )
        self.assertRaises(
            SlaveReportedException,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\x0A",
        )
        self.assertRaises(
            SlaveReportedException,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\x0B",
        )
        self.assertRaises(
            SlaveReportedException,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\x0C",
        )
        self.assertRaises(
            SlaveReportedException,
            minimalmodbus._check_response_slaveerrorcode,
            b"\x01\x81\xFF",
        )

    def testTooShortResponses(self) -> None:
        minimalmodbus._check_response_slaveerrorcode(b"")
        minimalmodbus._check_response_slaveerrorcode(b"A")
        minimalmodbus._check_response_slaveerrorcode(b"AB")


class TestCheckResponseNumberOfBytes(ExtendedTestCase):
    def testCorrectNumberOfBytes(self) -> None:
        minimalmodbus._check_response_bytecount(b"\x02\x03\x02")
        minimalmodbus._check_response_bytecount(
            b"\x0C\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C"
        )

    def testWrongNumberOfBytes(self) -> None:
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_response_bytecount,
            b"\x03\x03\x02",
        )
        self.assertRaises(
            InvalidResponseError, minimalmodbus._check_response_bytecount, b"ABC"
        )
        self.assertRaises(
            InvalidResponseError, minimalmodbus._check_response_bytecount, b""
        )

    def testNotByteInput(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, minimalmodbus._check_response_bytecount, value)


class TestCheckResponseRegisterAddress(ExtendedTestCase):
    def testCorrectResponseRegisterAddress(self) -> None:
        minimalmodbus._check_response_registeraddress(b"\x00\x2d\x00\x58", 45)
        minimalmodbus._check_response_registeraddress(b"\x00\x18\x00\x01", 24)
        minimalmodbus._check_response_registeraddress(b"\x00\x47\xff\x00", 71)
        minimalmodbus._check_response_registeraddress(b"\x00\x48\x00\x01", 72)

    def testTooShortString(self) -> None:
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_response_registeraddress,
            b"\x00",
            46,
        )

    def testNotString(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(
                TypeError, minimalmodbus._check_response_registeraddress, value, 45
            )

    def testWrongResponseRegisterAddress(self) -> None:
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_response_registeraddress,
            b"\x00\x2d\x00\x58",
            46,
        )

    def testInvalidAddress(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_response_registeraddress,
            b"\x00\x2d\x00\x58",
            -2,
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_response_registeraddress,
            b"\x00\x2d\x00\x58",
            65536,
        )

    def testAddressNotInteger(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_response_registeraddress,
                b"\x00\x2d\x00\x58",
                value,
            )


class TestCheckResponsenumber_of_registers(ExtendedTestCase):
    def testCorrectResponsenumber_of_registers(self) -> None:
        minimalmodbus._check_response_number_of_registers(b"\x00\x18\x00\x01", 1)
        minimalmodbus._check_response_number_of_registers(b"\x00#\x00\x01", 1)
        minimalmodbus._check_response_number_of_registers(b"\x00\x34\x00\x02", 2)

    def testTooShortString(self) -> None:
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_response_number_of_registers,
            b"\x00",
            1,
        )

    def testNotString(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(
                TypeError, minimalmodbus._check_response_number_of_registers, value, 1
            )

    def testWrongResponsenumber_of_registers(self) -> None:
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_response_number_of_registers,
            b"\x00#\x00\x01",
            4,
        )

    def testInvalidResponsenumber_of_registersRange(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_response_number_of_registers,
            b"\x00\x18\x00\x00",
            0,
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_response_number_of_registers,
            b"\x00\x18\x00\x01",
            -1,
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_response_number_of_registers,
            b"\x00\x18\x00\x01",
            65536,
        )

    def testnumber_of_registersNotInteger(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_response_number_of_registers,
                b"\x00\x18\x00\x01",
                value,
            )


class TestCheckResponseWriteData(ExtendedTestCase):
    def testCorrectResponseWritedata(self) -> None:
        minimalmodbus._check_response_writedata(b"\x00\x2d\x00\x58", b"\x00\x58")
        minimalmodbus._check_response_writedata(
            b"\x00\x2d\x00\x58", minimalmodbus._num_to_two_bytes(88)
        )
        minimalmodbus._check_response_writedata(b"\x00\x47\xff\x00", b"\xff\x00")
        minimalmodbus._check_response_writedata(
            b"\x00\x47\xff\x00", minimalmodbus._num_to_two_bytes(65280)
        )
        minimalmodbus._check_response_writedata(
            b"\x00\x2d\x00\x58ABCDEFGHIJKLMNOP", b"\x00\x58"
        )

    def testWrongResponseWritedata(self) -> None:
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_response_writedata,
            b"\x00\x2d\x00\x58",
            b"\x00\x59",
        )
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_response_writedata,
            b"\x00\x2d\x00\x58",
            minimalmodbus._num_to_two_bytes(89),
        )
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_response_writedata,
            b"\x00\x47\xff\x00",
            b"\xff\x01",
        )

    def testNotString(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(
                TypeError, minimalmodbus._check_response_writedata, value, b"\x00\x58"
            )
            self.assertRaises(
                TypeError,
                minimalmodbus._check_response_writedata,
                b"\x00\x2d\x00\x58",
                value,
            )

    def testTooShortPayload(self) -> None:
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_response_writedata,
            b"\x00\x58",
            b"\x00\x58",
        )
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_response_writedata,
            b"",
            b"\x00\x58",
        )

    def testInvalidReferenceData(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_response_writedata,
            b"\x00\x2d\x00\x58",
            b"\x00\x58\x00",
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_response_writedata,
            b"\x00\x2d\x00\x58",
            b"\x58",
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_response_writedata,
            b"\x00\x2d\x00\x58",
            b"",
        )


class TestCheckString(ExtendedTestCase):
    def testKnownValues(self) -> None:
        minimalmodbus._check_string("DEF", minlength=3, maxlength=3, description="ABC")
        minimalmodbus._check_string(
            "DEF", minlength=3, maxlength=3, description="ABC", force_ascii=True
        )
        minimalmodbus._check_string(
            "DEF", minlength=0, maxlength=100, description="ABC"
        )

    def testTooShort(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_string,
            "DE",
            minlength=3,
            maxlength=3,
            description="ABC",
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_string,
            "DEF",
            minlength=10,
            maxlength=3,
            description="ABC",
        )

    def testTooLong(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_string,
            "DEFG",
            minlength=1,
            maxlength=3,
            description="ABC",
        )

    def testNotAscii(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_string,
            "\u0394P",
            minlength=2,
            maxlength=2,
            description="ABC",
            force_ascii=True,
        )

    def testInconsistentLengthlimits(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_string,
            "DEFG",
            minlength=4,
            maxlength=3,
            description="ABC",
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_string,
            "DEF",
            minlength=-3,
            maxlength=3,
            description="ABC",
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_string,
            "DEF",
            minlength=3,
            maxlength=-3,
            description="ABC",
        )

    def testInputNotString(self) -> None:
        for value in _NOT_STRINGS:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_string,
                value,
                minlength=3,
                maxlength=3,
                description="ABC",
            )

    def testNotIntegerInput(self) -> None:
        for value in _NOT_INTERGERS_OR_NONE:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_string,
                "DEF",
                minlength=value,
                maxlength=3,
                description="ABC",
            )
            self.assertRaises(
                TypeError,
                minimalmodbus._check_string,
                "DEF",
                minlength=3,
                maxlength=value,
                description="ABC",
            )

    def testDescriptionNotString(self) -> None:
        for value in _NOT_STRINGS:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_string,
                "DEF",
                minlength=3,
                maxlength=3,
                description=value,
            )

    def testWrongCustomError(self) -> None:
        self.assertRaises(
            TypeError,
            minimalmodbus._check_string,
            "DEF",
            minlength=3,
            maxlength=3,
            description="ABC",
            exception_type=list,
        )
        self.assertRaises(
            TypeError,
            minimalmodbus._check_string,
            "DEF",
            minlength=3,
            maxlength=3,
            description="ABC",
            exception_type=7,
        )

    def testCustomError(self) -> None:
        for ex in [NotImplementedError, MemoryError, InvalidResponseError]:
            self.assertRaises(
                ex,
                minimalmodbus._check_string,
                "DE",
                minlength=3,
                description="ABC",
                exception_type=ex,
            )


class TestCheckBytes(ExtendedTestCase):
    def testKnownValues(self) -> None:
        minimalmodbus._check_bytes(b"DEF", minlength=3, maxlength=3, description="ABC")
        minimalmodbus._check_bytes(
            b"DEF", minlength=0, maxlength=100, description="ABC"
        )

    def testTooShort(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_bytes,
            b"DE",
            minlength=3,
            maxlength=3,
            description="ABC",
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_bytes,
            b"DEF",
            minlength=10,
            maxlength=3,
            description="ABC",
        )
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_bytes,
            b"DE",
            minlength=3,
            maxlength=3,
            description="ABC",
            exception_type=InvalidResponseError,
        )

    def testTooLong(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_bytes,
            b"DEFG",
            minlength=1,
            maxlength=3,
            description="ABC",
        )
        self.assertRaises(
            InvalidResponseError,
            minimalmodbus._check_bytes,
            b"DEFG",
            minlength=1,
            maxlength=3,
            description="ABC",
            exception_type=InvalidResponseError,
        )

    def testInconsistentLengthlimits(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_bytes,
            b"DEFG",
            minlength=4,
            maxlength=3,
            description="ABC",
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_bytes,
            b"DEF",
            minlength=-3,
            maxlength=3,
            description="ABC",
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_bytes,
            b"DEF",
            minlength=3,
            maxlength=-3,
            description="ABC",
        )

    def testInputNotBytes(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_bytes,
                value,
                minlength=3,
                maxlength=3,
                description="ABC",
            )

    def testNotIntegerInput(self) -> None:
        for value in _NOT_INTERGERS_OR_NONE:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_bytes,
                b"DEF",
                minlength=value,
                maxlength=3,
                description="ABC",
            )
            self.assertRaises(
                TypeError,
                minimalmodbus._check_bytes,
                b"DEF",
                minlength=3,
                maxlength=value,
                description="ABC",
            )

    def testDescriptionNotString(self) -> None:
        for value in _NOT_STRINGS:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_bytes,
                b"DEF",
                minlength=3,
                maxlength=3,
                description=value,
            )


class TestCheckInt(ExtendedTestCase):
    def testKnownValues(self) -> None:
        minimalmodbus._check_int(47, minvalue=None, maxvalue=None, description="ABC")
        minimalmodbus._check_int(47, minvalue=40, maxvalue=50, description="ABC")
        minimalmodbus._check_int(47, minvalue=-40, maxvalue=50, description="ABC")
        minimalmodbus._check_int(47, description="ABC", maxvalue=50, minvalue=40)
        minimalmodbus._check_int(47, minvalue=None, maxvalue=50, description="ABC")
        minimalmodbus._check_int(47, minvalue=40, maxvalue=None, description="ABC")

    def testTooLargeValue(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_int,
            47,
            minvalue=30,
            maxvalue=40,
            description="ABC",
        )
        self.assertRaises(ValueError, minimalmodbus._check_int, 47, maxvalue=46)

    def testTooSmallValue(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._check_int, 47, minvalue=48)
        self.assertRaises(
            ValueError,
            minimalmodbus._check_int,
            47,
            minvalue=48,
            maxvalue=None,
            description="ABC",
        )

    def testInconsistentLimits(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_int,
            47,
            minvalue=47,
            maxvalue=45,
            description="ABC",
        )

    def testWrongInputType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, minimalmodbus._check_int, value, minvalue=40)
        for value in _NOT_INTERGERS_OR_NONE:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_int,
                47,
                minvalue=value,
                maxvalue=50,
                description="ABC",
            )
            self.assertRaises(
                TypeError,
                minimalmodbus._check_int,
                47,
                minvalue=40,
                maxvalue=value,
                description="ABC",
            )
        for value in _NOT_STRINGS:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_int,
                47,
                minvalue=40,
                maxvalue=50,
                description=value,
            )


class TestCheckNumerical(ExtendedTestCase):
    def testKnownValues(self) -> None:
        minimalmodbus._check_numerical(
            47, minvalue=None, maxvalue=None, description="ABC"
        )
        minimalmodbus._check_numerical(47, minvalue=40, maxvalue=50, description="ABC")
        minimalmodbus._check_numerical(47, minvalue=-40, maxvalue=50, description="ABC")
        minimalmodbus._check_numerical(47, description="ABC", maxvalue=50, minvalue=40)
        minimalmodbus._check_numerical(
            47, minvalue=None, maxvalue=50, description="ABC"
        )
        minimalmodbus._check_numerical(
            47, minvalue=40, maxvalue=None, description="ABC"
        )
        minimalmodbus._check_numerical(47.0, minvalue=40)
        minimalmodbus._check_numerical(
            47, minvalue=40.0, maxvalue=50, description="ABC"
        )
        minimalmodbus._check_numerical(
            47.0, minvalue=40, maxvalue=None, description="ABC"
        )
        minimalmodbus._check_numerical(
            47.0, minvalue=40.0, maxvalue=50.0, description="ABC"
        )

    def testTooLargeValue(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_numerical,
            47.0,
            minvalue=30,
            maxvalue=40,
            description="ABC",
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_numerical,
            47.0,
            minvalue=30.0,
            maxvalue=40.0,
            description="ABC",
        )
        self.assertRaises(ValueError, minimalmodbus._check_numerical, 47, maxvalue=46.0)
        self.assertRaises(
            ValueError, minimalmodbus._check_numerical, 47.0, maxvalue=46.0
        )
        self.assertRaises(ValueError, minimalmodbus._check_numerical, 47.0, maxvalue=46)

    def testTooSmallValue(self) -> None:
        self.assertRaises(ValueError, minimalmodbus._check_numerical, 47.0, minvalue=48)
        self.assertRaises(
            ValueError, minimalmodbus._check_numerical, 47.0, minvalue=48.0
        )
        self.assertRaises(ValueError, minimalmodbus._check_numerical, 47, minvalue=48.0)
        self.assertRaises(
            ValueError,
            minimalmodbus._check_numerical,
            47,
            minvalue=48,
            maxvalue=None,
            description="ABC",
        )

    def testInconsistentLimits(self) -> None:
        self.assertRaises(
            ValueError,
            minimalmodbus._check_numerical,
            47,
            minvalue=47,
            maxvalue=45,
            description="ABC",
        )
        self.assertRaises(
            ValueError,
            minimalmodbus._check_numerical,
            47.0,
            minvalue=47.0,
            maxvalue=45.0,
            description="ABC",
        )

    def testNotNumericInput(self) -> None:
        for value in _NOT_NUMERICALS:
            self.assertRaises(
                TypeError, minimalmodbus._check_numerical, value, minvalue=40.0
            )
        for value in _NOT_NUMERICALS_OR_NONE:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_numerical,
                47.0,
                minvalue=value,
                maxvalue=50.0,
                description="ABC",
            )
            self.assertRaises(
                TypeError,
                minimalmodbus._check_numerical,
                47.0,
                minvalue=40.0,
                maxvalue=value,
                description="ABC",
            )

    def testDescriptionNotString(self) -> None:
        for value in _NOT_STRINGS:
            self.assertRaises(
                TypeError,
                minimalmodbus._check_numerical,
                47.0,
                minvalue=40,
                maxvalue=50,
                description=value,
            )


class TestCheckBool(ExtendedTestCase):
    def testKnownValues(self) -> None:
        minimalmodbus._check_bool(True, description="ABC")
        minimalmodbus._check_bool(False, description="ABC")

    def testWrongType(self) -> None:
        for value in _NOT_BOOLEANS:
            self.assertRaises(
                TypeError, minimalmodbus._check_bool, value, description="ABC"
            )
        for value in _NOT_STRINGS:
            self.assertRaises(
                TypeError, minimalmodbus._check_bool, True, description=value
            )


#####################
# Development tools #
#####################


class TestGetDiagnosticString(ExtendedTestCase):
    def testReturnsString(self) -> None:
        resultstring = minimalmodbus._get_diagnostic_string()
        self.assertTrue(len(resultstring) > 100)  # For Python 2.6 compatibility


###########################################
# Communication using a dummy serial port #
###########################################


class TestDummyCommunication(ExtendedTestCase):
    # Test fixture #

    def setUp(self) -> None:
        # Prepare a dummy serial port to have proper responses,
        # and monkey-patch minimalmodbus to use it
        # Note that mypy is unhappy about this:
        # https://github.com/python/mypy/issues/1152
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore

        self.instrument = minimalmodbus.Instrument("DUMMYPORTNAME", 1)

    # Read bit #

    def testReadBit(self) -> None:
        # Functioncode 2
        self.assertEqual(self.instrument.read_bit(61), 1)
        self.assertEqual(self.instrument.read_bit(61, functioncode=2), 1)
        self.assertEqual(self.instrument.read_bit(61, 2), 1)
        # Functioncode 1
        self.assertEqual(self.instrument.read_bit(62, functioncode=1), 0)
        self.assertEqual(self.instrument.read_bit(62, 1), 0)

    def testReadBitWrongValue(self) -> None:
        # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_bit, -1)
        self.assertRaises(ValueError, self.instrument.read_bit, 65536)
        # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_bit, 62, 0)
        self.assertRaises(ValueError, self.instrument.read_bit, 62, -1)
        self.assertRaises(ValueError, self.instrument.read_bit, 62, 128)

    def testReadBitWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_bit, value)
            self.assertRaises(TypeError, self.instrument.read_bit, 62, value)

    def testReadBitWithWrongByteCountResponse(self) -> None:
        # Functioncode 2. Slave gives wrong byte count.
        self.assertRaises(InvalidResponseError, self.instrument.read_bit, 63)

    def testReadBitWithNoResponse(self) -> None:
        # Functioncode 2. Slave gives no response.
        self.assertRaises(NoResponseError, self.instrument.read_bit, 64)

    # Write bit #

    def testWriteBit(self) -> None:
        self.instrument.write_bit(71, 0)
        self.instrument.write_bit(71, False)
        self.instrument.write_bit(71, 1)
        self.instrument.write_bit(71, True)
        self.instrument.write_bit(71, 1, 5)
        self.instrument.write_bit(71, True, 5)
        self.instrument.write_bit(71, 1, functioncode=5)
        self.instrument.write_bit(72, 1, 15)
        self.instrument.write_bit(72, 1, functioncode=15)

    def testWriteBitWrongValue(self) -> None:
        # Wrong register address
        self.assertRaises(ValueError, self.instrument.write_bit, 65536, 1)
        self.assertRaises(ValueError, self.instrument.write_bit, -1, 1)
        # Wrong bit value
        self.assertRaises(ValueError, self.instrument.write_bit, 71, 10)
        self.assertRaises(ValueError, self.instrument.write_bit, 71, -5)
        self.assertRaises(ValueError, self.instrument.write_bit, 71, 10, 5)
        # Wrong function code
        self.assertRaises(ValueError, self.instrument.write_bit, 71, 1, 6)
        self.assertRaises(ValueError, self.instrument.write_bit, 71, 1, -1)
        self.assertRaises(ValueError, self.instrument.write_bit, 71, 1, 0)
        self.assertRaises(ValueError, self.instrument.write_bit, 71, 1, 128)

    def testWriteBitWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_bit, value, 1)
            self.assertRaises(TypeError, self.instrument.write_bit, 71, value)
            self.assertRaises(TypeError, self.instrument.write_bit, 71, 1, value)

    def testWriteBitWithWrongRegisternumbersResponse(self) -> None:
        # Slave gives wrong number of registers
        self.assertRaises(
            InvalidResponseError, self.instrument.write_bit, 73, 1, functioncode=15
        )

    def testWriteBitWithWrongWritedataResponse(self) -> None:
        # Slave gives wrong write data
        self.assertRaises(InvalidResponseError, self.instrument.write_bit, 74, 1)

    # Read bits #

    def testReadBits(self) -> None:
        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        self.assertEqual(
            self.instrument.read_bits(196, 22, functioncode=2),
            [0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1],
        )

        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        self.assertEqual(
            self.instrument.read_bits(19, 19, functioncode=1),
            [1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
        )

        # Recorded on Delta DTB4824
        self.assertEqual(
            self.instrument.read_bits(0x800, 16),
            [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
        )

    def testReadBitsWrongValue(self) -> None:
        self.assertRaises(ValueError, self.instrument.read_bits, -1, 4)

    # Write bits #

    def testWriteBits(self) -> None:
        # Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
        self.instrument.write_bits(19, [1, 0, 1, 1, 0, 0, 1, 1, 1, 0])
        self.instrument.write_bits(
            19, [True, False, True, True, False, False, True, True, True, False]
        )

    def testWriteBitsWrongValue(self) -> None:
        self.assertRaises(ValueError, self.instrument.write_bits, -1, [0, 1])
        self.assertRaises(TypeError, self.instrument.write_bits, 122, 1)

    # Read register #

    def testReadRegister(self) -> None:
        # functioncode 3
        self.assertEqual(self.instrument.read_register(289), 770)
        self.assertEqual(self.instrument.read_register(5), 184)
        self.assertEqual(self.instrument.read_register(289, 0), 770)
        self.assertEqual(self.instrument.read_register(289, 0, 3), 770)
        # functioncode 4
        self.assertEqual(self.instrument.read_register(14, 0, 4), 880)
        self.assertAlmostEqual(self.instrument.read_register(289, 1), 77.0)
        self.assertAlmostEqual(self.instrument.read_register(289, 2), 7.7)
        self.assertEqual(self.instrument.read_register(101), 65531)
        self.assertEqual(self.instrument.read_register(101, signed=True), -5)

    def testReadRegisterWrongValue(self) -> None:
        # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_register, -1)
        self.assertRaises(ValueError, self.instrument.read_register, -1, 0, 3)
        self.assertRaises(ValueError, self.instrument.read_register, 65536)
        # Wrong number of decimals
        self.assertRaises(ValueError, self.instrument.read_register, 289, -1)
        self.assertRaises(ValueError, self.instrument.read_register, 289, 11)
        # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_register, 289, 0, 5)
        self.assertRaises(ValueError, self.instrument.read_register, 289, 0, -4)

    def testReadRegisterWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_register, value, 0, 3)
            self.assertRaises(TypeError, self.instrument.read_register, 289, value)
            self.assertRaises(TypeError, self.instrument.read_register, 289, 0, value)

    # Write register #

    def testWriteRegister(self) -> None:
        self.instrument.write_register(35, 20)
        self.instrument.write_register(35, 20, functioncode=16)
        self.instrument.write_register(35, 20.0)
        self.instrument.write_register(24, 50)
        self.instrument.write_register(45, 88, functioncode=6)
        self.instrument.write_register(101, 5)
        self.instrument.write_register(101, 5, signed=True)
        self.instrument.write_register(101, 5, 1)
        self.instrument.write_register(101, -5, signed=True)
        self.instrument.write_register(101, -5, 1, signed=True)

    def testWriteRegisterWithDecimals(self) -> None:
        self.instrument.write_register(35, 2.0, 1)
        self.instrument.write_register(45, 8.8, 1, functioncode=6)

    def testWriteRegisterWrongValue(self) -> None:
        # Wrong address
        self.assertRaises(ValueError, self.instrument.write_register, -1, 20)
        self.assertRaises(ValueError, self.instrument.write_register, 65536, 20)
        # Wrong register value
        self.assertRaises(ValueError, self.instrument.write_register, 35, -1)
        self.assertRaises(ValueError, self.instrument.write_register, 35, 65536)
        # Wrong number of decimals
        self.assertRaises(ValueError, self.instrument.write_register, 35, 20, -1)
        self.assertRaises(ValueError, self.instrument.write_register, 35, 20, 100)
        # Wrong function code
        self.assertRaises(
            ValueError, self.instrument.write_register, 35, 20, functioncode=12
        )
        self.assertRaises(
            ValueError, self.instrument.write_register, 35, 20, functioncode=-4
        )
        self.assertRaises(
            ValueError, self.instrument.write_register, 35, 20, functioncode=129
        )

    def testWriteRegisterWrongType(self) -> None:
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, self.instrument.write_register, value, 20)
            self.assertRaises(TypeError, self.instrument.write_register, 35, value)
            self.assertRaises(TypeError, self.instrument.write_register, 35, 20, value)
            self.assertRaises(
                TypeError, self.instrument.write_register, 35, 20, functioncode=value
            )

    def testWriteRegisterWithWrongCrcResponse(self) -> None:
        # Slave gives wrong CRC
        self.assertRaises(InvalidResponseError, self.instrument.write_register, 51, 99)

    def testWriteRegisterSuppressErrorMessageAtWrongCRC(self) -> None:
        try:
            self.instrument.write_register(51, 99)  # Slave gives wrong CRC
        except InvalidResponseError:
            print("Minimalmodbus: An error was suppressed.")

    def testWriteRegisterWithWrongSlaveaddressResponse(self) -> None:
        # Slave gives wrong slaveaddress
        self.assertRaises(InvalidResponseError, self.instrument.write_register, 54, 99)

    def testWriteRegisterWithWrongFunctioncodeResponse(self) -> None:
        # Slave gives wrong functioncode
        self.assertRaises(InvalidResponseError, self.instrument.write_register, 55, 99)
        # Slave indicates an error
        self.assertRaises(
            SlaveReportedException, self.instrument.write_register, 56, 99
        )

    def testWriteRegisterWithWrongRegisteraddressResponse(self) -> None:
        # Slave gives wrong registeraddress
        self.assertRaises(InvalidResponseError, self.instrument.write_register, 53, 99)

    def testWriteRegisterWithWrongRegisternumbersResponse(self) -> None:
        # Slave gives wrong number of registers
        self.assertRaises(InvalidResponseError, self.instrument.write_register, 52, 99)

    def testWriteRegisterWithWrongWritedataResponse(self) -> None:
        # Functioncode 6. Slave gives wrong write data.
        self.assertRaises(
            InvalidResponseError, self.instrument.write_register, 55, 99, functioncode=6
        )

    # Read Long #

    def testReadLong(self) -> None:
        self.assertEqual(self.instrument.read_long(102), 4294967295)
        self.assertEqual(self.instrument.read_long(102, signed=True), -1)
        self.assertEqual(
            self.instrument.read_long(223, byteorder=BYTEORDER_BIG), 2923517522
        )
        self.assertEqual(
            self.instrument.read_long(224, byteorder=BYTEORDER_BIG_SWAP), 2923517522
        )
        self.assertEqual(
            self.instrument.read_long(225, byteorder=BYTEORDER_LITTLE_SWAP), 2923517522
        )
        self.assertEqual(
            self.instrument.read_long(226, byteorder=BYTEORDER_LITTLE), 2923517522
        )
        self.assertEqual(
            self.instrument.read_long(108, signed=True, number_of_registers=4), -2
        )
        self.assertEqual(
            self.instrument.read_long(108, signed=False, number_of_registers=4),
            18446744073709551614,
        )

    def testReadLongWrongValue(self) -> None:
        # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_long, -1)
        self.assertRaises(ValueError, self.instrument.read_long, 65536)
        # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_long, 102, 1)
        self.assertRaises(ValueError, self.instrument.read_long, 102, -1)
        self.assertRaises(ValueError, self.instrument.read_long, 102, 256)
        # Wrong number of registers
        self.assertRaises(
            ValueError, self.instrument.read_long, 102, 3, False, BYTEORDER_BIG, 3
        )

    def testReadLongWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_long, value)
            self.assertRaises(TypeError, self.instrument.read_long, 102, value)
            self.assertRaises(
                TypeError, self.instrument.read_long, 102, 3, False, value
            )
            self.assertRaises(
                TypeError,
                self.instrument.read_long,
                102,
                3,
                False,
                BYTEORDER_BIG,
                value,
            )
        for value in _NOT_BOOLEANS:
            self.assertRaises(TypeError, self.instrument.read_long, 102, 3, value)

    # Write Long #

    def testWriteLong(self) -> None:
        self.instrument.write_long(102, 5)
        self.instrument.write_long(102, 5, signed=True)
        self.instrument.write_long(102, -5, signed=True)
        self.instrument.write_long(102, 3, False)
        self.instrument.write_long(102, -3, True)
        self.instrument.write_long(222, 2923517522)  # BYTEORDER_BIG
        self.instrument.write_long(222, 2923517522, byteorder=BYTEORDER_BIG_SWAP)
        self.instrument.write_long(222, 2923517522, byteorder=BYTEORDER_LITTLE_SWAP)
        self.instrument.write_long(222, 2923517522, byteorder=BYTEORDER_LITTLE)
        self.instrument.write_long(109, -4, signed=True, number_of_registers=4)

    def testWriteLongWrongValue(self) -> None:
        # Wrong register address
        self.assertRaises(ValueError, self.instrument.write_long, -1, 5)
        self.assertRaises(ValueError, self.instrument.write_long, 65536, 5)
        # Wrong value to write to slave
        self.assertRaises(
            ValueError, self.instrument.write_long, 102, 888888888888888888888
        )
        # Wrong value to write to slave
        self.assertRaises(ValueError, self.instrument.write_long, 102, -1, False)
        self.assertRaises(
            ValueError, self.instrument.write_long, 102, 4294967296, False
        )
        self.assertRaises(ValueError, self.instrument.write_long, 102, 2147483648, True)
        self.assertRaises(
            ValueError, self.instrument.write_long, 102, -2147483649, True
        )
        self.assertRaises(
            ValueError,
            self.instrument.write_long,
            102,
            18446744073709551616,
            False,
            BYTEORDER_BIG,
            4,
        )
        self.assertRaises(
            ValueError,
            self.instrument.write_long,
            102,
            -1,
            False,
            BYTEORDER_BIG,
            4,
        )
        self.assertRaises(
            ValueError,
            self.instrument.write_long,
            102,
            9223372036854775808,
            True,
            BYTEORDER_BIG,
            4,
        )
        self.assertRaises(
            ValueError,
            self.instrument.write_long,
            102,
            -9223372036854775809,
            True,
            BYTEORDER_BIG,
            4,
        )
        # Wrong number of registers
        self.assertRaises(
            ValueError, self.instrument.write_long, 102, 5, False, BYTEORDER_BIG, 3
        )

    def testWriteLongWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_long, value, 5)
            self.assertRaises(TypeError, self.instrument.write_long, 102, value)
            self.assertRaises(
                TypeError,
                self.instrument.write_long,
                102,
                5,
                False,
                BYTEORDER_BIG,
                value,
            )
        for value in _NOT_BOOLEANS:
            self.assertRaises(
                TypeError, self.instrument.write_long, 102, 5, signed=value
            )

    # Read Float #

    def testReadFloat(self) -> None:
        # BYTEORDER_BIG
        self.assertAlmostEqual(self.instrument.read_float(241), -4.3959787e-11)
        self.assertAlmostEqual(
            self.instrument.read_float(242, byteorder=BYTEORDER_BIG_SWAP),
            -4.3959787e-11,
        )
        self.assertAlmostEqual(
            self.instrument.read_float(243, byteorder=BYTEORDER_LITTLE_SWAP),
            -4.3959787e-11,
        )
        self.assertAlmostEqual(
            self.instrument.read_float(244, byteorder=BYTEORDER_LITTLE), -4.3959787e-11
        )
        self.assertEqual(self.instrument.read_float(103), 1.0)
        self.assertEqual(self.instrument.read_float(103, 3), 1.0)
        self.assertEqual(self.instrument.read_float(103, 3, 2), 1.0)
        self.assertEqual(self.instrument.read_float(103, 3, 4), -2.0)
        # Function code 4
        self.assertAlmostEqualRatio(self.instrument.read_float(103, 4, 2), 3.65e30)

    def testReadFloatWrongValue(self) -> None:
        # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_float, -1)
        self.assertRaises(ValueError, self.instrument.read_float, -1, 3)
        self.assertRaises(ValueError, self.instrument.read_float, -1, 3, 2)
        self.assertRaises(ValueError, self.instrument.read_float, 65536)
        # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_float, 103, 1)
        self.assertRaises(ValueError, self.instrument.read_float, 103, -1)
        self.assertRaises(ValueError, self.instrument.read_float, 103, 256)
        # Wrong number of registers
        for value in [-1, 0, 1, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, self.instrument.read_float, 103, 3, value)
        self.assertRaises(ValueError, self.instrument.read_float, 103, 3, 3)

    def testReadFloatWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_float, value, 3, 2)
            self.assertRaises(TypeError, self.instrument.read_float, 103, value, 2)
            self.assertRaises(TypeError, self.instrument.read_float, 103, 3, value)

    # Write Float #

    def testWriteFloat(self) -> None:
        self.instrument.write_float(107, 1)
        self.instrument.write_float(107, 1.0)
        self.instrument.write_float(103, 1.1)
        self.instrument.write_float(103, 1.1, 4)
        self.instrument.write_float(240, -4.3959787e-11)  # BYTEORDER_BIG
        self.instrument.write_float(240, -4.3959787e-11, byteorder=BYTEORDER_BIG_SWAP)
        self.instrument.write_float(
            240, -4.3959787e-11, byteorder=BYTEORDER_LITTLE_SWAP
        )
        self.instrument.write_float(240, -4.3959787e-11, byteorder=BYTEORDER_LITTLE)

    def testWriteFloatWrongValue(self) -> None:
        # Wrong register address
        self.assertRaises(ValueError, self.instrument.write_float, -1, 1.1)
        self.assertRaises(ValueError, self.instrument.write_float, 65536, 1.1)
        # Wrong number of registers
        for value in [-1, 0, 1, 3, 5, 6, 7, 8, 16]:
            self.assertRaises(ValueError, self.instrument.write_float, 103, 1.1, value)

    def testWriteFloatWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_float, value, 1.1)
            self.assertRaises(TypeError, self.instrument.write_float, 103, 1.1, value)
        for value in _NOT_NUMERICALS:
            self.assertRaises(TypeError, self.instrument.write_float, 103, value)

    # Read String #

    def testReadString(self) -> None:
        self.assertEqual(self.instrument.read_string(104, 1), "AB")
        self.assertEqual(self.instrument.read_string(104, 4), "ABCDEFGH")
        self.assertEqual(self.instrument.read_string(104, 4, 3), "ABCDEFGH")
        # TODO test with function code 4

    def testReadStringWrongValue(self) -> None:
        # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_string, -1)
        self.assertRaises(ValueError, self.instrument.read_string, 65536)
        # Wrong number of registers
        self.assertRaises(ValueError, self.instrument.read_string, 104, -1)
        self.assertRaises(ValueError, self.instrument.read_string, 104, 126)
        # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_string, 104, 4, 1)
        self.assertRaises(ValueError, self.instrument.read_string, 104, 4, -1)
        self.assertRaises(ValueError, self.instrument.read_string, 104, 4, 256)

    def testReadStringWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_string, value, 1)
            self.assertRaises(TypeError, self.instrument.read_string, value, 4)
            self.assertRaises(TypeError, self.instrument.read_string, 104, value)
            self.assertRaises(TypeError, self.instrument.read_string, 104, 4, value)

    # Write String #

    def testWriteString(self) -> None:
        self.instrument.write_string(104, "A", 1)
        self.instrument.write_string(104, "A", 4)
        self.instrument.write_string(104, "ABCDEFGH", 4)

    def testWriteStringWrongValue(self) -> None:
        # Wrong register address
        self.assertRaises(ValueError, self.instrument.write_string, -1, "A")
        self.assertRaises(ValueError, self.instrument.write_string, 65536, "A")
        # Too long string
        self.assertRaises(ValueError, self.instrument.write_string, 104, "AAA", 1)
        self.assertRaises(ValueError, self.instrument.write_string, 104, "ABCDEFGHI", 4)
        # Wrong number of registers
        self.assertRaises(ValueError, self.instrument.write_string, 104, "A", -1)
        self.assertRaises(ValueError, self.instrument.write_string, 104, "A", 124)
        # Non-ASCII
        self.assertRaises(ValueError, self.instrument.write_string, 104, "\u0394P", 1)

    def testWriteStringWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_string, value, "A")
            self.assertRaises(TypeError, self.instrument.write_string, 104, "A", value)
        for value in _NOT_STRINGS:
            self.assertRaises(TypeError, self.instrument.write_string, 104, value, 4)

    # Read Registers #

    def testReadRegisters(self) -> None:
        self.assertEqual(self.instrument.read_registers(105, 1), [16])
        self.assertEqual(self.instrument.read_registers(105, 3), [16, 32, 64])
        # TODO test with function code 4

    def testReadRegistersWrongValue(self) -> None:
        # Wrong register address
        self.assertRaises(ValueError, self.instrument.read_registers, -1, 1)
        self.assertRaises(ValueError, self.instrument.read_registers, 65536, 1)
        # Wrong number of registers
        self.assertRaises(ValueError, self.instrument.read_registers, 105, -1)
        self.assertRaises(ValueError, self.instrument.read_registers, 105, 126)
        # Wrong function code
        self.assertRaises(ValueError, self.instrument.read_registers, 105, 1, 1)
        self.assertRaises(ValueError, self.instrument.read_registers, 105, 1, 256)
        self.assertRaises(ValueError, self.instrument.read_registers, 105, 1, -1)

    def testReadRegistersWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.read_registers, value, 1)
            self.assertRaises(TypeError, self.instrument.read_registers, 105, value)
            self.assertRaises(TypeError, self.instrument.read_registers, 105, 1, value)

    # Write Registers #

    def testWriteRegisters(self) -> None:
        self.instrument.write_registers(105, [2])
        self.instrument.write_registers(105, [2, 4, 8])
        # Todo create suitable response
        #  self.instrument.write_registers(105, [2]*123)

    def testWriteRegistersWrongValue(self) -> None:
        # Wrong register address
        self.assertRaises(ValueError, self.instrument.write_registers, -1, [2])
        self.assertRaises(ValueError, self.instrument.write_registers, 65536, [2])
        # Wrong list value
        self.assertRaises(ValueError, self.instrument.write_registers, 105, [])
        self.assertRaises(ValueError, self.instrument.write_registers, 105, [-1])
        # Wrong number of registers
        self.assertRaises(ValueError, self.instrument.write_registers, 105, [2] * 124)

    def testWriteRegistersWrongType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(TypeError, self.instrument.write_registers, value, [2])
        for value in _NOT_INTLISTS:
            self.assertRaises(TypeError, self.instrument.write_registers, 105, value)

    # Generic command #

    def testGenericCommand(self) -> None:
        # read_bit(61)
        self.assertEqual(
            self.instrument._generic_command(
                2, 61, number_of_bits=1, payloadformat=_Payloadformat.BIT
            ),
            1,
        )

        # write_bit(71, 1)
        self.instrument._generic_command(
            5, 71, 1, number_of_bits=1, payloadformat=_Payloadformat.BIT
        )

        # read_bits(196, 22, functioncode=2)
        self.assertEqual(
            self.instrument._generic_command(
                2, 196, number_of_bits=22, payloadformat=_Payloadformat.BITS
            ),
            [0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1],
        )

        # read_bits(19, 19, functioncode=1)
        self.assertEqual(
            self.instrument._generic_command(
                1, 19, number_of_bits=19, payloadformat=_Payloadformat.BITS
            ),
            [1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
        )

        # write_bits(19, [1, 0, 1, 1, 0, 0, 1, 1, 1, 0])
        self.instrument._generic_command(
            15,
            19,
            [1, 0, 1, 1, 0, 0, 1, 1, 1, 0],
            number_of_bits=10,
            payloadformat=_Payloadformat.BITS,
        )

        # read_register(289)
        self.assertEqual(
            self.instrument._generic_command(
                3, 289, number_of_registers=1, payloadformat=_Payloadformat.REGISTER
            ),
            770,
        )

        # read_register(101, signed = True)
        self.assertEqual(
            self.instrument._generic_command(
                3,
                101,
                number_of_registers=1,
                signed=True,
                payloadformat=_Payloadformat.REGISTER,
            ),
            -5,
        )

        # read_register(289, 1)
        self.assertAlmostEqual(
            self.instrument._generic_command(
                3,
                289,
                number_of_decimals=1,
                number_of_registers=1,
                payloadformat=_Payloadformat.REGISTER,
            ),
            77.0,
        )

        # write_register(35, 20)
        self.instrument._generic_command(
            16, 35, 20, number_of_registers=1, payloadformat=_Payloadformat.REGISTER
        )

        # write_register(45, 88)
        self.instrument._generic_command(
            6, 45, 88, number_of_registers=1, payloadformat=_Payloadformat.REGISTER
        )

        # read_long(102)
        self.assertEqual(
            self.instrument._generic_command(
                3, 102, number_of_registers=2, payloadformat=_Payloadformat.LONG
            ),
            4294967295,
        )

        # write_long(102, 5)
        self.instrument._generic_command(
            16, 102, 5, number_of_registers=2, payloadformat=_Payloadformat.LONG
        )

        # read_float(103)
        self.assertAlmostEqual(
            self.instrument._generic_command(
                3, 103, number_of_registers=2, payloadformat=_Payloadformat.FLOAT
            ),
            1.0,
        )

        # write_float(103, 1.1)
        self.instrument._generic_command(
            16, 103, 1.1, number_of_registers=2, payloadformat=_Payloadformat.FLOAT
        )

        # read_string(104, 1)
        self.assertEqual(
            self.instrument._generic_command(
                3, 104, number_of_registers=1, payloadformat=_Payloadformat.STRING
            ),
            "AB",
        )

        # write_string(104, 'A', 1)
        self.instrument._generic_command(
            16, 104, "A", number_of_registers=1, payloadformat=_Payloadformat.STRING
        )

        # read_registers(105, 3)
        self.assertEqual(
            self.instrument._generic_command(
                3, 105, number_of_registers=3, payloadformat=_Payloadformat.REGISTERS
            ),
            [16, 32, 64],
        )

        # write_registers(105, [2, 4, 8])
        self.instrument._generic_command(
            16,
            105,
            [2, 4, 8],
            number_of_registers=3,
            payloadformat=_Payloadformat.REGISTERS,
        )

    def testGenericCommandWrongValue(
        self,
    ) -> None:
        # Detected without looking at parameter combinations
        for functioncode in [-1, 0, 23, 35, 128, 255, 1234567]:
            self.assertRaises(
                ValueError,
                self.instrument._generic_command,
                functioncode,
                1,
                number_of_registers=1,
                payloadformat=_Payloadformat.REGISTER,
            )
        for registeraddress in [-1, 65536]:
            self.assertRaises(
                ValueError, self.instrument._generic_command, 3, registeraddress
            )
        for number_of_decimals in [-1, 11]:
            self.assertRaises(
                ValueError,
                self.instrument._generic_command,
                3,
                289,
                number_of_decimals=number_of_decimals,
            )
        for number_of_registers in [-1, 126]:
            self.assertRaises(
                ValueError,
                self.instrument._generic_command,
                3,
                289,
                number_of_registers=number_of_registers,
            )
        for number_of_bits in [-1, 2001]:
            self.assertRaises(
                ValueError,
                self.instrument._generic_command,
                3,
                289,
                number_of_bits=number_of_bits,
            )
        self.assertRaises(
            TypeError, self.instrument._generic_command, 3, 289, payloadformat="ABC"
        )

    def testGenericCommandWrongType(
        self,
    ) -> None:
        # Detected without looking at parameter combinations
        # Note: The parameter 'value' type is dependent on the other parameters.
        # See tests above.
        for value in _NOT_INTERGERS:
            # Function code
            self.assertRaises(TypeError, self.instrument._generic_command, value, 289)
            # Register address
            self.assertRaises(TypeError, self.instrument._generic_command, 3, value)
            self.assertRaises(
                TypeError,
                self.instrument._generic_command,
                3,
                289,
                number_of_decimals=value,
            )
            self.assertRaises(
                TypeError,
                self.instrument._generic_command,
                3,
                289,
                number_of_registers=value,
            )
            self.assertRaises(
                TypeError,
                self.instrument._generic_command,
                3,
                289,
                number_of_bits=value,
            )
            self.assertRaises(
                TypeError, self.instrument._generic_command, 3, 289, byteorder=value
            )
        for value in _NOT_BOOLEANS:
            self.assertRaises(
                TypeError, self.instrument._generic_command, 3, 289, signed=value
            )
        for value in _NOT_STRINGS_OR_NONE:
            self.assertRaises(
                TypeError, self.instrument._generic_command, 3, 289, payloadformat=value
            )

    def testGenericCommandWrongValueCombinations(self) -> None:
        # Bit
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            5,
            71,
            1,
            number_of_bits=2,
            payloadformat=_Payloadformat.BIT,
        )
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            5,
            71,
            1,
            number_of_bits=1,
            payloadformat=_Payloadformat.REGISTER,
        )
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            5,
            71,
            1,
            number_of_bits=1,
            number_of_decimals=1,
            payloadformat=_Payloadformat.BIT,
        )
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            5,
            71,
            1,
            number_of_bits=1,
            number_of_registers=1,
            payloadformat=_Payloadformat.BIT,
        )
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            5,
            71,
            1,
            number_of_bits=1,
            signed=True,
            payloadformat=_Payloadformat.BIT,
        )
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            5,
            71,
            1,
            number_of_bits=1,
            byteorder=BYTEORDER_LITTLE,
            payloadformat=_Payloadformat.BIT,
        )
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            5,
            71,
            2,
            number_of_bits=1,
            payloadformat=_Payloadformat.BIT,
        )
        self.assertRaises(
            TypeError,
            self.instrument._generic_command,
            5,
            71,
            "abc",
            number_of_bits=1,
            payloadformat=_Payloadformat.BIT,
        )

        # Bits
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            2,
            71,
            number_of_bits=-1,
            payloadformat=_Payloadformat.BITS,
        )
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            2,
            71,
            number_of_bits=0,
            payloadformat=_Payloadformat.BITS,
        )
        self.assertRaises(
            TypeError,
            self.instrument._generic_command,
            15,
            71,
            1,
            number_of_bits=1,
            payloadformat=_Payloadformat.BITS,
        )
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            15,
            71,
            [1, 2],
            number_of_bits=1,
            payloadformat=_Payloadformat.BITS,
        )

        # Register
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            3,
            289,
            number_of_registers=1,
            number_of_bits=1,
            payloadformat=_Payloadformat.REGISTER,
        )

        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            3,
            289,
            number_of_registers=0,
            payloadformat=_Payloadformat.REGISTER,
        )

        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            16,
            289,
            number_of_registers=5,
            payloadformat=_Payloadformat.REGISTER,
        )

        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            16,
            289,
            number_of_registers=1,
            payloadformat=_Payloadformat.REGISTER,
        )

        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            6,
            45,
            88,
            number_of_registers=7,
            payloadformat=_Payloadformat.REGISTER,
        )

        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            3,
            289,
            88,
            number_of_registers=1,
            payloadformat=_Payloadformat.REGISTER,
        )

        self.assertRaises(
            TypeError,
            self.instrument._generic_command,
            6,
            123,
            "abc",
            number_of_registers=1,
            payloadformat=_Payloadformat.REGISTER,
        )

        # Registers
        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            1,
            105,
            number_of_registers=3,
            payloadformat=_Payloadformat.REGISTERS,
        )

        self.assertRaises(
            TypeError,
            self.instrument._generic_command,
            16,
            105,
            2,
            number_of_registers=3,
            payloadformat=_Payloadformat.REGISTERS,
        )

        self.assertRaises(
            ValueError,
            self.instrument._generic_command,
            16,
            105,
            [2, 4],
            number_of_registers=3,
            payloadformat=_Payloadformat.REGISTERS,
        )

        # String
        self.assertRaises(
            TypeError,
            self.instrument._generic_command,
            16,
            123,
            1.0,
            number_of_registers=1,
            payloadformat=_Payloadformat.STRING,
        )

    # Perform command #

    def testPerformcommandKnownResponse(self) -> None:
        # Total response length should be 8 bytes
        self.assertEqual(self.instrument._perform_command(16, b"TESTCOMMAND"), b"TRsp")
        self.assertEqual(
            self.instrument._perform_command(75, b"TESTCOMMAND2"),
            b"TESTCOMMANDRESPONSE2",
        )
        # Read bit register 61 on slave 1 using function code 2.
        self.assertEqual(
            self.instrument._perform_command(2, b"\x00\x3d\x00\x01"), b"\x01\x01"
        )

    def testPerformcommandWrongSlaveResponse(self) -> None:
        # Wrong slave address in response
        self.assertRaises(
            InvalidResponseError, self.instrument._perform_command, 1, b"TESTCOMMAND"
        )
        # Wrong function code in response
        self.assertRaises(
            InvalidResponseError, self.instrument._perform_command, 2, b"TESTCOMMAND"
        )
        # Wrong CRC in response
        self.assertRaises(
            InvalidResponseError, self.instrument._perform_command, 3, b"TESTCOMMAND"
        )
        # Too short response message from slave
        self.assertRaises(
            InvalidResponseError, self.instrument._perform_command, 4, b"TESTCOMMAND"
        )
        # Error indication from slave
        self.assertRaises(
            InvalidResponseError, self.instrument._perform_command, 5, b"TESTCOMMAND"
        )

    def testPerformcommandWrongInputValue(self) -> None:
        # Wrong function code
        self.assertRaises(
            ValueError, self.instrument._perform_command, -1, b"TESTCOMMAND"
        )
        self.assertRaises(
            ValueError, self.instrument._perform_command, 128, b"TESTCOMMAND"
        )

    def testPerformcommandWrongInputType(self) -> None:
        for value in _NOT_INTERGERS:
            self.assertRaises(
                TypeError, self.instrument._perform_command, value, b"TESTCOMMAND"
            )
        for value in _NOT_BYTES:
            self.assertRaises(TypeError, self.instrument._perform_command, 16, value)

    # Communicate #

    def testCommunicateKnownResponse(self) -> None:
        self.assertEqual(
            self.instrument._communicate(b"TESTMESSAGE", _LARGE_NUMBER_OF_BYTES),
            b"TESTRESPONSE",
        )

    def testCommunicateWrongType(self) -> None:
        for value in _NOT_BYTES:
            self.assertRaises(
                TypeError, self.instrument._communicate, value, _LARGE_NUMBER_OF_BYTES
            )

    def testCommunicateNoMessage(self) -> None:
        self.assertRaises(
            ValueError, self.instrument._communicate, b"", _LARGE_NUMBER_OF_BYTES
        )

    def testCommunicateNoSerialPort(self) -> None:
        self.instrument.serial = None
        self.assertRaises(
            minimalmodbus.ModbusException,
            self.instrument._communicate,
            b"TESTMESSAGE",
            _LARGE_NUMBER_OF_BYTES,
        )

    def testCommunicateNoResponse(self) -> None:
        self.assertRaises(
            NoResponseError,
            self.instrument._communicate,
            b"MessageForEmptyResponse",
            _LARGE_NUMBER_OF_BYTES,
        )

    def testCommunicateLocalEcho(self) -> None:
        self.instrument.handle_local_echo = True
        self.assertEqual(
            self.instrument._communicate(b"TESTMESSAGE2", _LARGE_NUMBER_OF_BYTES),
            b"TESTRESPONSE2",
        )

    def testCommunicateWrongLocalEcho(self) -> None:
        self.instrument.handle_local_echo = True
        self.assertRaises(
            IOError,
            self.instrument._communicate,
            b"TESTMESSAGE3",
            _LARGE_NUMBER_OF_BYTES,
        )  # TODO is this correct?

    def testPortWillBeOpened(self) -> None:
        assert self.instrument.serial is not None
        self.instrument.serial.close()
        self.instrument.write_bit(71, 1)

    def testMeasureRoundtriptime(self) -> None:
        self.instrument.debug = True
        self.assertIsNone(self.instrument.roundtrip_time)
        self.instrument.write_bit(71, 1)
        self.assertIsNotNone(self.instrument.roundtrip_time)
        # Measured round trip time in seconds, see dummy_serial
        self.assertGreater(self.instrument.roundtrip_time, 0.001)  # type: ignore

    # __repr__ #

    def testRepresentation(self) -> None:
        representation = repr(self.instrument)
        self.assertTrue("minimalmodbus.Instrument<id=" in representation)
        self.assertTrue(
            ", address=1, mode=rtu, close_port_after_each_call=False, "
            in representation
        )
        self.assertTrue(
            (
                ", precalculate_read_size=True, "
                + "clear_buffers_before_each_transaction=True, "
            )
            in representation
        )
        self.assertTrue(", handle_local_echo=False, debug=False, " in representation)
        self.assertTrue(", open=True>(port=" in representation)

    # Test the dummy serial port itself #

    def testReadPortClosed(self) -> None:
        assert self.instrument.serial is not None
        self.instrument.serial.close()
        # Error raised by dummy_serial
        self.assertRaises(IOError, self.instrument.serial.read, 1000)

    def testPortAlreadyOpen(self) -> None:
        assert self.instrument.serial is not None
        # Error raised by dummy_serial
        self.assertRaises(IOError, self.instrument.serial.open)

    def testPortAlreadyClosed(self) -> None:
        assert self.instrument.serial is not None
        self.instrument.serial.close()
        # Error raised by dummy_serial
        self.assertRaises(IOError, self.instrument.serial.close)

    # Tear down test fixture #

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestDummyCommunicationOmegaSlave1(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore
        self.instrument = minimalmodbus.Instrument("DUMMYPORTNAME", 1)

    def testReadBit(self) -> None:
        self.assertEqual(self.instrument.read_bit(2068), 1)

    def testWriteBit(self) -> None:
        self.instrument.write_bit(2068, 0)
        self.instrument.write_bit(2068, 1)
        self.instrument.write_bit(2068, True)
        self.instrument.write_bit(2068, False)

    def testReadRegister(self) -> None:
        self.assertAlmostEqual(self.instrument.read_register(4097, 1), 823.6)

    def testWriteRegister(self) -> None:
        self.instrument.write_register(4097, 700.0, 1)
        self.instrument.write_register(4097, 823.6, 1)

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestDummyCommunicationOmegaSlave10(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore
        self.instrument = minimalmodbus.Instrument("DUMMYPORTNAME", 10)

    def testReadBit(self) -> None:
        self.assertEqual(self.instrument.read_bit(2068), 1)

    def testWriteBit(self) -> None:
        self.instrument.write_bit(2068, 0)
        self.instrument.write_bit(2068, 1)

    def testReadRegister(self) -> None:
        self.assertAlmostEqual(self.instrument.read_register(4096, 1), 25.0)
        self.assertAlmostEqual(self.instrument.read_register(4097, 1), 325.8)

    def testWriteRegister(self) -> None:
        self.instrument.write_register(4097, 325.8, 1)
        self.instrument.write_register(4097, 20.0, 1)
        self.instrument.write_register(4097, 200.0, 1)

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestDummyCommunicationDTB4824_RTU(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore
        self.instrument = minimalmodbus.Instrument("DUMMYPORTNAME", 7)

    def testReadBit(self) -> None:
        self.assertEqual(self.instrument.read_bit(0x0800), 0)  # LED AT
        self.assertEqual(self.instrument.read_bit(0x0801), 0)  # LED Out1
        self.assertEqual(self.instrument.read_bit(0x0802), 0)  # LED Out2
        self.assertEqual(self.instrument.read_bit(0x0814), 0)  # RUN/STOP

    def testWriteBit(self) -> None:
        self.instrument.write_bit(0x0810, 1)  # "Communication write in enabled".
        self.instrument.write_bit(0x0814, 0)  # STOP
        self.instrument.write_bit(0x0814, 1)  # RUN

    def testReadBits(self) -> None:
        self.assertEqual(
            self.instrument._perform_command(2, b"\x08\x10\x00\x09"), b"\x02\x07\x00"
        )

    def testReadRegister(self) -> None:
        # Process value (PV)
        self.assertEqual(self.instrument.read_register(0x1000), 64990)
        # Setpoint (SV)
        self.assertAlmostEqual(self.instrument.read_register(0x1001, 1), 80.0)
        # Sensor type
        self.assertEqual(self.instrument.read_register(0x1004), 14)
        # Control method
        self.assertEqual(self.instrument.read_register(0x1005), 1)
        # Heating/cooling selection
        self.assertEqual(self.instrument.read_register(0x1006), 0)
        # Output 1
        self.assertAlmostEqual(self.instrument.read_register(0x1012, 1), 0.0)
        # Output 2
        self.assertAlmostEqual(self.instrument.read_register(0x1013, 1), 0.0)
        # System alarm setting
        self.assertEqual(self.instrument.read_register(0x1023), 0)
        # LED status
        self.assertEqual(self.instrument.read_register(0x102A), 0)
        # Pushbutton status
        self.assertEqual(self.instrument.read_register(0x102B), 15)
        # Firmware version
        self.assertEqual(self.instrument.read_register(0x102F), 400)

    def testReadRegisters(self) -> None:
        # Process value (PV) and setpoint (SV)
        self.assertEqual(self.instrument.read_registers(0x1000, 2), [64990, 350])

    def testWriteRegister(self) -> None:
        # Setpoint of 80.0 degrees
        self.instrument.write_register(0x1001, 0x0320, functioncode=6)
        self.instrument.write_register(0x1001, 25, 1, functioncode=6)  # Setpoint

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestDummyCommunicationDTB4824_ASCII(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = ASCII_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore
        self.instrument = minimalmodbus.Instrument(
            "DUMMYPORTNAME", 7, minimalmodbus.MODE_ASCII
        )

    def testReadBit(self) -> None:
        self.assertEqual(self.instrument.read_bit(0x0800), 0)  # LED AT
        self.assertEqual(self.instrument.read_bit(0x0801), 1)  # LED Out1
        self.assertEqual(self.instrument.read_bit(0x0802), 0)  # LED Out2
        self.assertEqual(self.instrument.read_bit(0x0814), 1)  # RUN/STOP

    def testWriteBit(self) -> None:
        self.instrument.write_bit(0x0810, 1)  # "Communication write in enabled".
        self.instrument.write_bit(0x0814, 0)  # STOP
        self.instrument.write_bit(0x0814, 1)  # RUN

    def testReadBits(self) -> None:
        self.assertEqual(
            self.instrument._perform_command(2, b"\x08\x10\x00\x09"), b"\x02\x17\x00"
        )

    def testReadRegister(self) -> None:
        # Process value (PV)
        self.assertEqual(self.instrument.read_register(0x1000), 64990)
        # Setpoint (SV)
        self.assertAlmostEqual(self.instrument.read_register(0x1001, 1), 80.0)
        # Sensor type
        self.assertEqual(self.instrument.read_register(0x1004), 14)
        # Control method
        self.assertEqual(self.instrument.read_register(0x1005), 1)
        # Heating/cooling selection
        self.assertEqual(self.instrument.read_register(0x1006), 0)
        # Output 1
        self.assertAlmostEqual(self.instrument.read_register(0x1012, 1), 100.0)
        # Output 2
        self.assertAlmostEqual(self.instrument.read_register(0x1013, 1), 0.0)
        # System alarm setting
        self.assertEqual(self.instrument.read_register(0x1023), 0)
        # LED status
        self.assertEqual(self.instrument.read_register(0x102A), 64)
        # Pushbutton status
        self.assertEqual(self.instrument.read_register(0x102B), 15)
        # Firmware version
        self.assertEqual(self.instrument.read_register(0x102F), 400)

    def testReadRegisters(self) -> None:
        # Process value (PV) and setpoint (SV)
        self.assertEqual(self.instrument.read_registers(0x1000, 2), [64990, 350])

    def testWriteRegister(self) -> None:
        # Setpoint of 80.0 degrees
        self.instrument.write_register(0x1001, 0x0320, functioncode=6)
        self.instrument.write_register(0x1001, 25, 1, functioncode=6)  # Setpoint

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestDummyCommunicationWithPortClosure(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore

        # Mimic a WindowsXP serial port
        self.instrument = minimalmodbus.Instrument(
            "DUMMYPORTNAME", 1, close_port_after_each_call=True
        )

    def testReadRegisterSeveralTimes(self) -> None:
        self.assertEqual(self.instrument.read_register(289), 770)
        self.assertEqual(self.instrument.read_register(289), 770)
        self.assertEqual(self.instrument.read_register(289), 770)

    def testPortAlreadyClosed(self) -> None:
        self.assertEqual(self.instrument.read_register(289), 770)
        assert self.instrument.serial is not None
        self.assertEqual(self.instrument.serial.is_open, False)
        self.assertRaises(IOError, self.instrument.serial.close)

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestVerboseDummyCommunicationWithPortClosure(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = True
        dummy_serial.RESPONSES = RTU_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore
        self.instrument = minimalmodbus.Instrument("DUMMYPORTNAME", 1, debug=True)
        # Mimic a WindowsXP serial port
        self.instrument.close_port_after_each_call = True

    def testReadRegister(self) -> None:
        self.assertEqual(self.instrument.read_register(289), 770)

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestVerboseDummyCommunicationNoBufferClearing(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = True
        dummy_serial.RESPONSES = RTU_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore
        self.instrument = minimalmodbus.Instrument("DUMMYPORTNAME", 1, debug=True)
        self.instrument.clear_buffers_before_each_transaction = False

    def testReadRegister(self) -> None:
        self.assertEqual(self.instrument.read_register(289), 770)

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestVerboseDummyCommunicationNoCalculateReadSize(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = True
        dummy_serial.RESPONSES = RTU_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore
        self.instrument = minimalmodbus.Instrument("DUMMYPORTNAME", 1, debug=True)
        self.instrument.precalculate_read_size = False

    def testReadRegister(self) -> None:
        self.assertEqual(self.instrument.read_register(289), 770)

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestDummyCommunicationBroadcast(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore

        # Use broadcast (slave address 0)
        self.instrument = minimalmodbus.Instrument("DUMMYPORTNAME", 0, debug=True)

    def testWriteRegister(self) -> None:
        assert self.instrument.serial is not None
        self.instrument.serial._clean_mock_data()
        start_time = time.time()
        self.instrument.write_register(24, 50)
        total_time = time.time() - start_time
        self.assertEqual(
            self.instrument.serial._last_written_data,
            b"\x00\x10\x00\x18\x00\x01\x02\x002)\xcd",
        )
        self.assertGreater(total_time, 0.1)  # seconds for broadcast delay

    def testReadingNotAllowed(self) -> None:
        self.assertRaises(ValueError, self.instrument.read_register, 289)

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestDummyCommunicationThreeInstrumentsPortClosure(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = False
        dummy_serial.RESPONSES = RTU_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore

        self.instrumentA = minimalmodbus.Instrument(
            "DUMMYPORTNAME", 1, close_port_after_each_call=True, debug=True
        )
        assert self.instrumentA.serial is not None
        self.instrumentA.serial.baudrate = 2400

        self.instrumentB = minimalmodbus.Instrument(
            "DUMMYPORTNAME", 1, close_port_after_each_call=True, debug=True
        )

        self.instrumentC = minimalmodbus.Instrument(
            "DUMMYPORTNAME", 7, close_port_after_each_call=True, debug=True
        )

    def testCommunication(self) -> None:
        self.assertEqual(self.instrumentA.read_register(289), 770)
        self.assertEqual(self.instrumentB.read_register(289), 770)
        self.assertEqual(self.instrumentC.read_bit(0x0800), 0)
        self.assertEqual(self.instrumentA.read_register(289), 770)
        self.assertEqual(self.instrumentB.read_register(289), 770)
        self.assertEqual(self.instrumentC.read_bit(0x0800), 0)

    def tearDown(self) -> None:
        if self.instrumentA.serial is not None:
            try:
                self.instrumentA.serial.close()
            except Exception:
                pass
        del self.instrumentA

        if self.instrumentB.serial is not None:
            try:
                self.instrumentB.serial.close()
            except Exception:
                pass
        del self.instrumentB

        if self.instrumentC.serial is not None:
            try:
                self.instrumentC.serial.close()
            except Exception:
                pass
        del self.instrumentC


class TestDummyCommunicationHandleLocalEcho(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = True
        dummy_serial.RESPONSES = RTU_RESPONSES
        minimalmodbus.serial.Serial = dummy_serial.Serial  # type: ignore
        self.instrument = minimalmodbus.Instrument("DUMMYPORTNAME", 20, debug=True)
        self.instrument.handle_local_echo = True

    def testReadRegister(self) -> None:
        self.assertEqual(self.instrument.read_register(289), 770)

    def testReadRegisterWrongEcho(self) -> None:
        self.assertRaises(
            minimalmodbus.LocalEchoError, self.instrument.read_register, 290
        )

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestDummyCommunicationExternalSerialPort(ExtendedTestCase):
    def setUp(self) -> None:
        dummy_serial.VERBOSE = True
        dummy_serial.RESPONSES = RTU_RESPONSES
        extserial = dummy_serial.Serial("DUMMYPORTNAME")
        self.instrument = minimalmodbus.Instrument(extserial, 1)  # type: ignore

    def testReadRegister(self) -> None:
        self.assertEqual(self.instrument.read_register(289), 770)

    def tearDown(self) -> None:
        if self.instrument.serial is not None:
            try:
                self.instrument.serial.close()
            except Exception:
                pass
        del self.instrument


class TestDummyCommunicationExternalSerialPortFailsToOpen(ExtendedTestCase):
    def testInitialise(self) -> None:
        extserial = dummy_serial.Serial("DUMMYPORTNAME", fail_to_open=True)
        self.assertRaises(
            minimalmodbus.MasterReportedException,
            minimalmodbus.Instrument,
            extserial,
            1,
        )


class TestDummyCommunicationExternalSerialPortWrongType(ExtendedTestCase):
    def testInitialiseSerialPortInteger(self) -> None:
        extserial = 123
        self.assertRaises(
            minimalmodbus.MasterReportedException,
            minimalmodbus.Instrument,
            extserial,
            1,
        )

    def testInitialiseSerialPortNone(self) -> None:
        extserial = None
        self.assertRaises(
            minimalmodbus.MasterReportedException,
            minimalmodbus.Instrument,
            extserial,
            1,
        )


RTU_RESPONSES: Dict[bytes, bytes] = {}
GOOD_RTU_RESPONSES: Dict[bytes, bytes] = {}
WRONG_RTU_RESPONSES: Dict[bytes, bytes] = {}
ASCII_RESPONSES: Dict[bytes, bytes] = {}
GOOD_ASCII_RESPONSES: Dict[bytes, bytes] = {}
WRONG_ASCII_RESPONSES: Dict[bytes, bytes] = {}
"""A dictionary of respones from a dummy instrument.

The key is the message (string) sent to the serial port, and the item is the response
(string) from the dummy serial port.
"""
# Note that the string 'AAAAAAA' might be easier to read if grouped,
# like 'AA' + 'AAAA' + 'A' for the initial part (address etc) + payload + CRC.


#                ##  READ BIT  ##

# Read bit register 61 on slave 1 using function code 2. Also for _perform_command() #
# ---------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 2. Register address 61, 1 coil. CRC.
# Response: Slave address 1, function code 2. 1 byte, value=1. CRC.
GOOD_RTU_RESPONSES[b"\x01\x02" + b"\x00\x3d\x00\x01" + b"(\x06"] = (
    b"\x01\x02" + b"\x01\x01" + b"`H"
)

# Read bit register 62 on slave 1 using function code 1 #
# ----------------------------------------------------- #
# Message:  Slave address 1, function code 1. Register address 62, 1 coil. CRC.
# Response: Slave address 1, function code 1. 1 byte, value=0. CRC.
GOOD_RTU_RESPONSES[b"\x01\x01" + b"\x00\x3e\x00\x01" + b"\x9c\x06"] = (
    b"\x01\x01" + b"\x01\x00" + b"Q\x88"
)

# Read bit register 63 on slave 1 using function code 2, slave gives wrong byte count #
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 2. Register address 63, 1 coil. CRC.
# Response: Slave address 1, function code 2. 2 bytes (wrong), value=1. CRC.
WRONG_RTU_RESPONSES[b"\x01\x02" + b"\x00\x3f\x00\x01" + b"\x89\xc6"] = (
    b"\x01\x02" + b"\x02\x01" + b"`\xb8"
)

# Read bit register 64 on slave 1 using function code 2, slave gives no response #
# ------------------------------------------------------------------------------ #
# Message:  Slave address 1, function code 2. Register address 64, 1 coil. CRC.
# Response: (empty string)
WRONG_RTU_RESPONSES[b"\x01\x02" + b"\x00\x40\x00\x01" + b"\xb8\x1e"] = b""


#                ##  WRITE BIT  ##

# Write bit=1 register 71 on slave 1 using function code 5 #
# -------------------------------------------------------- #
# Message:  Slave address 1, function code 5. Register address 71, value 1 (FF00). CRC.
# Response: Slave address 1, function code 5. Register address 71, value 1 (FF00). CRC.
GOOD_RTU_RESPONSES[b"\x01\x05" + b"\x00\x47\xff\x00" + b"</"] = (
    b"\x01\x05" + b"\x00\x47\xff\x00" + b"</"
)

# Write bit=0 register 71 on slave 1 using function code 5 #
# -------------------------------------------------------- #
# Message:  Slave address 1, function code 5. Register address 71, value 0 (0000). CRC.
# Response: Slave address 1, function code 5. Register address 71, value 0 (0000). CRC.
GOOD_RTU_RESPONSES[b"\x01\x05" + b"\x00\x47\x00\x00" + b"}\xDF"] = (
    b"\x01\x05" + b"\x00\x47\x00\x00" + b"}\xDF"
)

# Write bit register 72 on slave 1 using function code 15 #
# ------------------------------------------------------ #
# Message:  Slave address 1, function code 15. Register address 72, 1 bit, 1 byte,
#           value 1 (0100). CRC.
# Response: Slave address 1, function code 15. Register address 72, 1 bit. CRC.
GOOD_RTU_RESPONSES[b"\x01\x0f" + b"\x00\x48\x00\x01\x01\x01" + b"\x0fY"] = (
    b"\x01\x0f" + b"\x00\x48\x00\x01" + b"\x14\x1d"
)

# Write bit register 73 on slave 1 using function code 15, slave gives
# wrong number of registers #
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 15. Register address 73, 1 bit, 1 byte,
#           value 1 (0100). CRC.
# Response: Slave address 1, function code 15. Register address 73, 2 bits (wrong). CRC.
WRONG_RTU_RESPONSES[b"\x01\x0f" + b"\x00\x49\x00\x01\x01\x01" + b"2\x99"] = (
    b"\x01\x0f" + b"\x00\x49\x00\x02" + b"\x05\xdc"
)

# Write bit register 74 on slave 1 using function code 5, slave gives wrong write data #
# ------------------------------------------------------------------------------------ #
# Message:  Slave address 1, function code 5. Register address 74, value 1 (FF00). CRC.
# Response: Slave address 1, function code 5. Register address 74, value 0 (0000,
#           wrong). CRC.
WRONG_RTU_RESPONSES[b"\x01\x05" + b"\x00\x4a\xff\x00" + b"\xad\xec"] = (
    b"\x01\x05" + b"\x00\x47\x00\x00" + b"}\xdf"
)


#                ##  READ BITS  ##

# Read 19 bits starting at address 19 on slave 1 using function code 1.
# Also for testing _perform_command()
# Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 1. Register address 19, 19 coils. CRC.
# Response: Slave address 1, function code 1. 3 bytes, values. CRC.
GOOD_RTU_RESPONSES[b"\x01\x01" + b"\x00\x13\x00\x13" + b"\x8c\x02"] = (
    b"\x01\x01" + b"\x03\xCD\x6B\x05" + b"B\x82"
)

# Read 22 bits starting at address 196 on slave 1 using function code 2.
# Also for testing _perform_command()
# Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 2. Register address 196, 22 coils. CRC.
# Response: Slave address 1, function code 2. 3 bytes, values. CRC.
GOOD_RTU_RESPONSES[b"\x01\x02" + b"\x00\xC4\x00\x16" + b"\xB89"] = (
    b"\x01\x02" + b"\x03\xAC\xDB\x35" + b'"\x88'
)

# Read 16 bits starting at address 0x800 on slave 1 using function code 2.
# Recorded on Delta DTB4824
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 2. Register address 0x800, 16 coils. CRC.
# Response: Slave address 1, function code 2. 2 bytes, values. CRC.
GOOD_RTU_RESPONSES[b"\x01\x02" + b"\x08\x00\x00\x10" + b"\x7B\xA6"] = (
    b"\x01\x02" + b"\x02\x20\x0f" + b"\xE0\x7C"
)


#                ##  WRITE BITS  ##

# Write 10 bits starting at address 19 on slave 1 using function code 15.
# Also for testing _perform_command()
# Example from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 15. Address 19, 10 coils, 2 bytes,
#           values. CRC.
# Response: Slave address 1, function code 15. Address 19, 10 coils. CRC.
GOOD_RTU_RESPONSES[b"\x01\x0f" + b"\x00\x13\x00\x0A\x02\xCD\x01" + b"\x72\xCB"] = (
    b"\x01\x0f" + b"\x00\x13\x00\x0A" + b"$\t"
)


#                ##  READ REGISTER  ##

# Read register 289 on slave 1 using function code 3 #
# ---------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 289, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value=770. CRC=14709.
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x01!\x00\x01" + b"\xd5\xfc"] = (
    b"\x01\x03" + b"\x02\x03\x02" + b"\x39\x75"
)

# Read register 5 on slave 1 using function code 3 #
# ---------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 289, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value=184. CRC
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00\x05\x00\x01" + b"\x94\x0b"] = (
    b"\x01\x03" + b"\x02\x00\xb8" + b"\xb86"
)

# Read register 14 on slave 1 using function code 4 #
# --------------------------------------------------#
# Message:  Slave address 1, function code 4. Register address 14, 1 register. CRC.
# Response: Slave address 1, function code 4. 2 bytes, value=880. CRC.
GOOD_RTU_RESPONSES[b"\x01\x04" + b"\x00\x0e\x00\x01" + b"P\t"] = (
    b"\x01\x04" + b"\x02\x03\x70" + b"\xb8$"
)

# Read register 101 on slave 1 using function code 3 #
# ---------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 101, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value=-5 or 65531 (depending
#           on interpretation). CRC
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00e\x00\x01" + b"\x94\x15"] = (
    b"\x01\x03" + b"\x02\xff\xfb" + b"\xb87"
)

# Read register 201 on slave 1 using function code 3 #
# ---------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 201, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value=9. CRC
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00\xc9\x00\x01" + b"T4"] = (
    b"\x01\x03" + b"\x02\x00\x09" + b"xB"
)

# Read register 202 on slave 1 using function code 3. Too long response #
# ----------------------------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 202, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes (wrong!), value=9. CRC
WRONG_RTU_RESPONSES[b"\x01\x03" + b"\x00\xca\x00\x01" + b"\xa44"] = (
    b"\x01\x03" + b"\x02\x00\x00\x09" + b"\x84t"
)

# Read register 203 on slave 1 using function code 3. Too short response #
# ----------------------------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 203, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes (wrong!), value=9. CRC
WRONG_RTU_RESPONSES[b"\x01\x03" + b"\x00\xcb\x00\x01" + b"\xf5\xf4"] = (
    b"\x01\x03" + b"\x02\x09" + b"0\xbe"
)


#                ##  WRITE REGISTER  ##

# Write value 50 in register 24 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 24, 1 register,
#           2 bytes, value=50. CRC.
# Response: Slave address 1, function code 16. Register address 24, 1 register. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00\x18\x00\x01\x02\x002" + b"$]"] = (
    b"\x01\x10" + b"\x00\x18\x00\x01" + b"\x81\xce"
)

# Write value 20 in register 35 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 35, 1 register,
#           2 bytes, value=20. CRC.
# Response: Slave address 1, function code 16. Register address 35, 1 register. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00#\x00\x01" + b"\x02\x00\x14" + b"\xa1\x0c"] = (
    b"\x01\x10" + b"\x00#\x00\x01" + b"\xf0\x03"
)

# Write value 88 in register 45 on slave 1 using function code 6 #
# ---------------------------------------------------------------#
# Message:  Slave address 1, function code 6. Register address 45, value=88. CRC.
# Response: Slave address 1, function code 6. Register address 45, value=88. CRC.
GOOD_RTU_RESPONSES[b"\x01\x06" + b"\x00\x2d\x00\x58" + b"\x189"] = (
    b"\x01\x06" + b"\x00\x2d\x00\x58" + b"\x189"
)

# Write value 5 in register 101 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 101, 1 register,
#           2 bytes, value=5. CRC.
# Response: Slave address 1, function code 16. Register address 101, 1 register. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00e\x00\x01\x02\x00\x05" + b"o\xa6"] = (
    b"\x01\x10" + b"\x00e\x00\x01" + b"\x11\xd6"
)

# Write value 50 in register 101 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 101, 1 register,
#           2 bytes, value=5. CRC.
# Response: Slave address 1, function code 16. Register address 101, 1 register. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00e\x00\x01\x02\x002" + b".p"] = (
    b"\x01\x10" + b"\x00e\x00\x01" + b"\x11\xd6"
)

# Write value -5 in register 101 on slave 1 using function code 16 #
# ----------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 101, 1 register,
#           2 bytes, value=-5. CRC.
# Response: Slave address 1, function code 16. Register address 101, 1 register. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00e\x00\x01\x02\xff\xfb" + b"\xaf\xd6"] = (
    b"\x01\x10" + b"\x00e\x00\x01" + b"\x11\xd6"
)

# Write value -50 in register 101 on slave 1 using function code 16 #
# ----------------------------------------------------------------- #
# Message:  Slave address 1, function code 16. Register address 101, 1 register,
#           2 bytes, value=-50. CRC.
# Response: Slave address 1, function code 16. Register address 101, 1 register. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00e\x00\x01\x02\xff\xce" + b"o\xc1"] = (
    b"\x01\x10" + b"\x00e\x00\x01" + b"\x11\xd6"
)

# Write value 99 in register 51 on slave 1 using function code 16, slave gives
# wrong CRC #
# ------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 51, 1 register,
#           2 bytes, value=99. CRC.
# Response: Slave address 1, function code 16. Register address 51, 1 register.
#           Wrong CRC.
WRONG_RTU_RESPONSES[
    b"\x01\x10" + b"\x00\x33\x00\x01" + b"\x02\x00\x63" + b"\xe3\xba"
] = (b"\x01\x10" + b"\x00\x33\x00\x01" + b"AB")

# Write value 99 in register 52 on slave 1 using function code 16, slave
# gives wrong number of registers #
# ------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 52, 1 register,
#           2 bytes, value=99. CRC.
# Response: Slave address 1, function code 16. Register address 52,
#           2 registers (wrong). CRC.
WRONG_RTU_RESPONSES[b"\x01\x10" + b"\x00\x34\x00\x01" + b"\x02\x00\x63" + b"\xe2\r"] = (
    b"\x01\x10" + b"\x00\x34\x00\x02" + b"\x00\x06"
)

# Write value 99 in register 53 on slave 1 using function code 16, slave
# gives wrong register address #
# ------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 53, 1 register,
#           2 bytes, value=99. CRC.
# Response: Slave address 1, function code 16. Register address 54 (wrong), 1 register.
#           CRC.
WRONG_RTU_RESPONSES[
    b"\x01\x10" + b"\x00\x35\x00\x01" + b"\x02\x00\x63" + b"\xe3\xdc"
] = (b"\x01\x10" + b"\x00\x36\x00\x01" + b"\xe1\xc7")

# Write value 99 in register 54 on slave 1 using function code 16, slave
# gives wrong slave address #
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 16. Register address 54, 1 register,
#           2 bytes, value=99. CRC.
# Response: Slave address 2 (wrong), function code 16. Register address 54, 1 register.
#           CRC.
GOOD_RTU_RESPONSES[
    b"\x01\x10" + b"\x00\x36\x00\x01" + b"\x02\x00\x63" + b"\xe3\xef"
] = (b"\x02\x10" + b"\x00\x36\x00\x01" + b"\xe1\xf4")

# Write value 99 in register 55 on slave 1 using function code 16, slave
# gives wrong functioncode #
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 16. Register address 55, 1 register,
#           2 bytes, value=99. CRC.
# Response: Slave address 1, function code 6 (wrong). Register address 55, 1 register.
#           CRC.
WRONG_RTU_RESPONSES[b"\x01\x10" + b"\x00\x37\x00\x01" + b"\x02\x00\x63" + b"\xe2>"] = (
    b"\x01\x06" + b"\x00\x37\x00\x01" + b"\xf9\xc4"
)

# Write value 99 in register 56 on slave 1 using function code 16, slave
# gives wrong functioncode (indicates an error) #
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 16. Register address 56, 1 register,
#           2 bytes, value=99. CRC.
# Response: Slave address 1, function code 144 (wrong). Register address 56, 1 register.
#           CRC.
WRONG_RTU_RESPONSES[
    b"\x01\x10" + b"\x00\x38\x00\x01" + b"\x02\x00\x63" + b"\xe2\xc1"
] = (b"\x01\x90" + b"\x00\x38\x00\x01" + b"\x81\xda")

# Write value 99 in register 55 on slave 1 using function code 6, slave
# gives wrong write data #
# ----------------------------------------------------------------------------------- #
# Message:  Slave address 1, function code 6. Register address 55, value=99. CRC.
# Response: Slave address 1, function code 6. Register address 55, value=98 (wrong).
#           CRC.
WRONG_RTU_RESPONSES[b"\x01\x06" + b"\x00\x37\x00\x63" + b"x-"] = (
    b"\x01\x06" + b"\x00\x37\x00\x62" + b"\xb9\xed"
)

#                ##  READ LONG ##

# Read long (2 registers, starting at 102) on slave 1 using function code 3 #
# --------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 102, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, value=-1 or 4294967295
#           (depending on interpretation). CRC
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00f\x00\x02" + b"$\x14"] = (
    b"\x01\x03" + b"\x04\xff\xff\xff\xff" + b"\xfb\xa7"
)

# Read long (2 registers, starting at 223) on slave 1 using function code 3 #
# Example from https://www.simplymodbus.ca/FAQ.htm
# Byte order BYTEORDER_BIG
# ---------------------------------------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 223, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, Value 2923517522. CRC
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00\xDF\x00\x02" + b"\xF5\xF1"] = (
    b"\x01\x03" + b"\x04\xAEAVR" + b"4\x92"
)

# Read long (2 registers, starting at 224) on slave 1 using function code 3 #
# Example from https://www.simplymodbus.ca/FAQ.htm
# Byte order BYTEORDER_BIG_SWAP
# ---------------------------------------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 224, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, Value 2923517522. CRC
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00\xE0\x00\x02" + b"\xC5\xFD"] = (
    b"\x01\x03" + b"\x04A\xAERV" + b"2\xB0"
)

# Read long (2 registers, starting at 225) on slave 1 using function code 3 #
# Example from https://www.simplymodbus.ca/FAQ.htm
# Byte order BYTEORDER_LITTLE_SWAP
# --------------------------------------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 225, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, Value 2923517522. CRC
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00\xE1\x00\x02" + b"\x94="] = (
    b"\x01\x03" + b"\x04VR\xAEA" + b"\xF6:"
)

# Read long (2 registers, starting at 226) on slave 1 using function code 3 #
# Example from https://www.simplymodbus.ca/FAQ.htm
# Byte order BYTEORDER_LITTLE
# ----------------------------------------------------------------------------------#
# Message: Slave address 1, function code 3. Register address 226, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, Value 2923517522. CRC
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00\xE2\x00\x02" + b"\x64\x3D"] = (
    b"\x01\x03" + b"\x04RVA\xAE" + b"\xBBw"
)

# Read long (4 registers, starting at 108) on slave 1 using function code 3 #
# --------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 108, 4 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, value=-2 or 18446744073709551614
#           (depending on interpretation). CRC
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00\x6c\x00\x04" + b"\x84\x14"] = (
    b"\x01\x03" + b"\x08\xff\xff\xff\xff\xff\xff\xff\xfe" + b"\x15\x93"
)


#                ##  WRITE LONG ##

# Write long (2 registers, starting at 102) on slave 1 using function code 16, with
# value 5.
# -----------------------------------------------------------------------------------#
# Message: Slave address 1, function code 16. Register address 102, 2 registers,
#          4 bytes, value=5. CRC.
# Response: Slave address 1, function code 16. Register address 102, 2 registers. CRC
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00f\x00\x02\x04\x00\x00\x00\x05" + b"\xb5\xae"] = (
    b"\x01\x10" + b"\x00f\x00\x02" + b"\xa1\xd7"
)

# Write long (2 registers, starting at 102) on slave 1 using function code 16, with
# value -5.
# ------------------------------------------------------------------------------------#
# Message: Slave address 1, function code 16. Register address 102, 2 registers,
#          4 bytes, value=-5. CRC.
# Response: Slave address 1, function code 16. Register address 102, 2 registers. CRC
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00f\x00\x02\x04\xff\xff\xff\xfb" + b"u\xfa"] = (
    b"\x01\x10" + b"\x00f\x00\x02" + b"\xa1\xd7"
)

# Write long (2 registers, starting at 102) on slave 1 using function code 16, with
# value 3. #
# ------------------------------------------------------------------------------------#
# Message: Slave address 1, function code 16. Register address 102, 2 registers,
#          4 bytes, value=3. CRC.
# Response: Slave address 1, function code 16. Register address 102, 2 registers. CRC
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00f\x00\x02\x04\x00\x00\x00\x03" + b"5\xac"] = (
    b"\x01\x10" + b"\x00f\x00\x02" + b"\xa1\xd7"
)

# Write long (2 registers, starting at 102) on slave 1 using function code 16, with
# value -3. #
# ------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 102, 2 registers,
#           4 bytes, value=-3. CRC.
# Response: Slave address 1, function code 16. Register address 102, 2 registers. CRC
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00f\x00\x02\x04\xff\xff\xff\xfd" + b"\xf5\xf8"] = (
    b"\x01\x10" + b"\x00f\x00\x02" + b"\xa1\xd7"
)

# Write long (2 registers, starting at 222) on slave 1 using function code 16, with
# value 2923517522
# Example from https://www.simplymodbus.ca/FAQ.htm
# Byte order BYTEORDER_BIG
# ------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 222, 2 registers,
#           4 bytes, value. CRC.
# Response: Slave address 1, function code 16. Register address 222, 2 registers. CRC
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00\xDE\x00\x02\x04\xAEAVR" + b"\xB1\xDE"] = (
    b"\x01\x10" + b"\x00\xDE\x00\x02" + b"\x21\xF2"
)

# Write long (2 registers, starting at 222) on slave 1 using function code 16, with
# value 2923517522
# Example from https://www.simplymodbus.ca/FAQ.htm
# Byte order BYTEORDER_LITTLE
# ------------------------------------------------------------------------------------#
# Message: Slave address 1, function code 16. Register address 222, 2 registers,
#          4 bytes, value. CRC.
# Response: Slave address 1, function code 16. Register address 222, 2 registers. CRC
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00\xDE\x00\x02\x04RVA\xAE" + b"\x3E\x3B"] = (
    b"\x01\x10" + b"\x00\xDE\x00\x02" + b"\x21\xF2"
)

# Write long (2 registers, starting at 222) on slave 1 using function code 16, with
# value 2923517522
# Example from https://www.simplymodbus.ca/FAQ.htm
# Byte order BYTEORDER_BIG_SWAP
# ------------------------------------------------------------------------------------#
# Message: Slave address 1, function code 16. Register address 222, 2 registers,
#          4 bytes, value. CRC.
# Response: Slave address 1, function code 16. Register address 222, 2 registers. CRC
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00\xDE\x00\x02\x04A\xAERV" + b"\xB7\xFC"] = (
    b"\x01\x10" + b"\x00\xDE\x00\x02" + b"\x21\xF2"
)

# Write long (2 registers, starting at 222) on slave 1 using function code 16, with
# value 2923517522
# Example from https://www.simplymodbus.ca/FAQ.htm
# Byte order BYTEORDER_LITTLE_SWAP
# ------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 222, 2 registers,
#           4 bytes, value. CRC.
# Response: Slave address 1, function code 16. Register address 222, 2 registers. CRC
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00\xDE\x00\x02\x04VR\xAEA" + b"sv"] = (
    b"\x01\x10" + b"\x00\xDE\x00\x02" + b"\x21\xF2"
)

# Write long (4 registers, starting at 109) on slave 1 using function code 16, with
# value -4.
# ------------------------------------------------------------------------------------#
# Message: Slave address 1, function code 16. Register address 109, 4 registers,
#          8 bytes, value=-4. CRC.
# Response: Slave address 1, function code 16. Register address 109, 4 registers. CRC
GOOD_RTU_RESPONSES[
    b"\x01\x10" + b"\x00m\x00\x04\x08\xff\xff\xff\xff\xff\xff\xff\xfc" + b"\xda\xac"
] = (b"\x01\x10" + b"\x00m\x00\x04" + b"P\x17")


#                ##  READ FLOAT ##

# Read float from address 103 (2 registers) on slave 1 using function code 3 #
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 103, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, value=1.0. CRC.
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00g\x00\x02" + b"u\xd4"] = (
    b"\x01\x03" + b"\x04\x3f\x80\x00\x00" + b"\xf7\xcf"
)

# Read float from address 103 (2 registers) on slave 1 using function code 4 #
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 4. Register address 103, 2 registers. CRC.
# Response: Slave address 1, function code 4. 4 bytes, value=3.65e30. CRC.
GOOD_RTU_RESPONSES[b"\x01\x04" + b"\x00g\x00\x02" + b"\xc0\x14"] = (
    b"\x01\x04" + b"\x04\x72\x38\x47\x25" + b"\x93\x1a"
)

# Read float from address 103 (4 registers) on slave 1 using function code 3 #
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 103, 4 registers. CRC.
# Response: Slave address 1, function code 3. 8 bytes, value=-2.0 CRC.
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00g\x00\x04" + b"\xf5\xd6"] = (
    b"\x01\x03" + b"\x08\xc0\x00\x00\x00\x00\x00\x00\x00" + b"\x99\x87"
)

# Read float from address 241 (2 registers) on slave 1 using function code 3 #
# Example from https://www.simplymodbus.ca/FAQ.htm (truncated float on page)
# BYTEORDER_BIG
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 241, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, value=-4.3959787e-11 CRC.
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00\xF1\x00\x02" + b"\x95\xF8"] = (
    b"\x01\x03" + b"\x04\xAEAVR" + b"4\x92"
)

# Read float from address 242 (2 registers) on slave 1 using function code 3 #
# Example from https://www.simplymodbus.ca/FAQ.htm (truncated float on page,
# manually reshuffled)
# BYTEORDER_BIG_SWAP
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 242, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, value=-4.3959787e-11 CRC.
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00\xF2\x00\x02" + b"\x65\xF8"] = (
    b"\x01\x03" + b"\x04A\xAERV" + b"2\xB0"
)

# Read float from address 243 (2 registers) on slave 1 using function code 3 #
# Example from https://www.simplymodbus.ca/FAQ.htm (truncated float on page,
# manually reshuffled)
# BYTEORDER_LITTLE_SWAP
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 243, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, value=-4.3959787e-11 CRC.
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00\xF3\x00\x02" + b"\x34\x38"] = (
    b"\x01\x03" + b"\x04VR\xAEA" + b"\xf6:"
)

# Read float from address 244 (2 registers) on slave 1 using function code 3 #
# Example from https://www.simplymodbus.ca/FAQ.htm (truncated float on page,
# manually reshuffled)
# BYTEORDER_LITTLE
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 244, 2 registers. CRC.
# Response: Slave address 1, function code 3. 4 bytes, value=-4.3959787e-11 CRC.
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00\xF4\x00\x02" + b"\x85\xF9"] = (
    b"\x01\x03" + b"\x04RVA\xAE" + b"\xBBw"
)


#                ##  WRITE FLOAT ##

# Write float 1.0 to address 107 (2 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 107, 2 registers,
#           4 bytes, value=1.1 . CRC.
# Response: Slave address 1, function code 16. Register address 107, 2 registers. CRC.
GOOD_RTU_RESPONSES[
    b"\x01\x10" + b"\x00\x6b\x00\x02\x04\x3F\x80\x00\x00" + b"\xb9\xc8"
] = (b"\x01\x10" + b"\x00\x6b\x00\x02" + b"0\x14")

# Write float 1.1 to address 103 (2 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 103, 2 registers,
#           4 bytes, value=1.1 . CRC.
# Response: Slave address 1, function code 16. Register address 103, 2 registers. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00g\x00\x02\x04?\x8c\xcc\xcd" + b"\xed\x0b"] = (
    b"\x01\x10" + b"\x00g\x00\x02" + b"\xf0\x17"
)

# Write float 1.1 to address 103 (4 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 103, 4 registers,
#           8 bytes, value=1.1 . CRC.
# Response: Slave address 1, function code 16. Register address 103, 4 registers. CRC.
GOOD_RTU_RESPONSES[
    b"\x01\x10" + b"\x00g\x00\x04\x08?\xf1\x99\x99\x99\x99\x99\x9a" + b"u\xf7"
] = (b"\x01\x10" + b"\x00g\x00\x04" + b"p\x15")

# Write float 1.1 to address 103 (4 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 103, 4 registers,
#           8 bytes, value=1.1 . CRC.
# Response: Slave address 1, function code 16. Register address 103, 4 registers. CRC.
GOOD_RTU_RESPONSES[
    b"\x01\x10" + b"\x00g\x00\x04\x08?\xf1\x99\x99\x99\x99\x99\x9a" + b"u\xf7"
] = (b"\x01\x10" + b"\x00g\x00\x04" + b"p\x15")

# Write float -4.3959787e-11 to address 240 (2 registers) on slave 1 using
# function code 16 #
# Example from https://www.simplymodbus.ca/FAQ.htm (truncated float on page)
# BYTEORDER_BIG
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 240, 2 registers,
#           4 bytes, value. CRC.
# Response: Slave address 1, function code 16. Register address 240, 2 registers. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00\xF0\x00\x02\x04\xAEAVR" + b"2J"] = (
    b"\x01\x10" + b"\x00\xF0\x00\x02" + b"A\xFB"
)

# Write float -4.3959787e-11 to address 240 (2 registers) on slave 1 using
# function code 16 #
# Example from https://www.simplymodbus.ca/FAQ.htm (truncated float on page,
# manually reshuffled)
# BYTEORDER_LITTLE
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 240, 2 registers,
#           4 bytes, value. CRC.
# Response: Slave address 1, function code 16. Register address 240, 2 registers. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00\xF0\x00\x02\x04RVA\xAE" + b"\xBD\xAF"] = (
    b"\x01\x10" + b"\x00\xF0\x00\x02" + b"A\xFB"
)

# Write float -4.3959787e-11 to address 240 (2 registers) on slave 1 using
# function code 16 #
# Example from https://www.simplymodbus.ca/FAQ.htm (truncated float on page,
# manually reshuffled)
# BYTEORDER_LITTLE_SWAP
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 240, 2 registers,
#           4 bytes, value. CRC.
# Response: Slave address 1, function code 16. Register address 240, 2 registers. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00\xF0\x00\x02\x04VR\xAEA" + b"\xF0\xE2"] = (
    b"\x01\x10" + b"\x00\xF0\x00\x02" + b"A\xFB"
)

# Write float -4.3959787e-11 to address 240 (2 registers) on slave 1 using
# function code 16 #
# Example from https://www.simplymodbus.ca/FAQ.htm (truncated float on page,
# manually reshuffled)
# BYTEORDER_BIG_SWAP
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 240, 2 registers,
#           4 bytes, value. CRC.
# Response: Slave address 1, function code 16. Register address 240, 2 registers. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00\xF0\x00\x02\x04A\xAERV" + b"4h"] = (
    b"\x01\x10" + b"\x00\xF0\x00\x02" + b"A\xFB"
)


#                ##  READ STRING  ##

# Read string from address 104 (1 register) on slave 1 using function code 3 #
# ---------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 104, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value = 'AB'.  CRC.
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00h\x00\x01" + b"\x05\xd6"] = (
    b"\x01\x03" + b"\x02AB" + b"\x08%"
)

# Read string from address 104 (4 registers) on slave 1 using function code 3 #
# ----------------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 104, 4 registers. CRC.
# Response: Slave address 1, function code 3.  8 bytes, value = 'ABCDEFGH'.  CRC.
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00h\x00\x04" + b"\xc5\xd5"] = (
    b"\x01\x03" + b"\x08ABCDEFGH" + b"\x0b\xcc"
)


#                ##  WRITE STRING  ##

# Write string 'A' to address 104 (1 register) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 104, 1 register,
#           2 bytes, value='A ' . CRC.
# Response: Slave address 1, function code 16. Register address 104, 1 register. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00h\x00\x01\x02A " + b"\x9f0"] = (
    b"\x01\x10" + b"\x00h\x00\x01" + b"\x80\x15"
)

# Write string 'A' to address 104 (4 registers) on slave 1 using function code 16 #
# --------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 104, 4 registers,
#           8 bytes, value='A       ' . CRC.
# Response: Slave address 1, function code 16. Register address 104, 2 registers. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00h\x00\x04\x08A       " + b"\xa7\xae"] = (
    b"\x01\x10" + b"\x00h\x00\x04" + b"@\x16"
)

# Write string 'ABCDEFGH' to address 104 (4 registers) on slave 1 using
# function code 16
# ------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 104, 4 registers,
#           8 bytes, value='ABCDEFGH' . CRC.
# Response: Slave address 1, function code 16. Register address 104, 4 registers. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00h\x00\x04\x08ABCDEFGH" + b"I>"] = (
    b"\x01\x10" + b"\x00h\x00\x04" + b"@\x16"
)


#                ##  READ REGISTERS  ##

# Read from address 105 (1 register) on slave 1 using function code 3 #
# --------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 105, 1 register. CRC.
# Response: Slave address 1, function code 3. 2 bytes, value = 16.  CRC.
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00i\x00\x01" + b"T\x16"] = (
    b"\x01\x03" + b"\x02\x00\x10" + b"\xb9\x88"
)

# Read from address 105 (3 registers) on slave 1 using function code 3 #
# ---------------------------------------------------------------------#
# Message:  Slave address 1, function code 3. Register address 105, 3 registers. CRC.
# Response: Slave address 1, function code 3. 6 bytes, value = 16, 32, 64. CRC.
GOOD_RTU_RESPONSES[b"\x01\x03" + b"\x00i\x00\x03" + b"\xd5\xd7"] = (
    b"\x01\x03" + b"\x06\x00\x10\x00\x20\x00\x40" + b"\xe0\x8c"
)


#                ##  WRITE REGISTERS  ##

# Write value [2] to address 105 (1 register) on slave 1 using function code 16 #
# ------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 105, 1 register,
#           2 bytes, value=2 . CRC.
# Response: Slave address 1, function code 16. Register address 105, 1 register. CRC.
GOOD_RTU_RESPONSES[b"\x01\x10" + b"\x00i\x00\x01\x02\x00\x02" + b".\xa8"] = (
    b"\x01\x10" + b"\x00i\x00\x01" + b"\xd1\xd5"
)

# Write value [2, 4, 8] to address 105 (3 registers) on slave 1 using function code 16 #
# -------------------------------------------------------------------------------------#
# Message:  Slave address 1, function code 16. Register address 105, 3 register,
#           6 bytes, value=2, 4, 8. CRC.
# Response: Slave address 1, function code 16. Register address 105, 3 registers. CRC.
GOOD_RTU_RESPONSES[
    b"\x01\x10" + b"\x00i\x00\x03\x06\x00\x02\x00\x04\x00\x08" + b"\x0c\xd6"
] = (b"\x01\x10" + b"\x00i\x00\x03" + b"P\x14")


#                ##  OTHER RESPONSES  ##

# Retrieve an empty response (for testing the _communicate method) #
# ---------------------------------------------------------------- #
WRONG_RTU_RESPONSES[b"MessageForEmptyResponse"] = b""

# Retrieve an known response (for testing the _communicate method) #
# ---------------------------------------------------------------- #
WRONG_RTU_RESPONSES[b"TESTMESSAGE"] = b"TESTRESPONSE"

# Retrieve an known response with local echo (for testing the _communicate method) #
# ---------------------------------------------------------------- #
WRONG_RTU_RESPONSES[b"TESTMESSAGE2"] = b"TESTMESSAGE2TESTRESPONSE2"

# Retrieve a response with wrong local echo (for testing the _communicate method) #
# ---------------------------------------------------------------- #
WRONG_RTU_RESPONSES[b"TESTMESSAGE3"] = b"TESTMeSSAGE3TESTRESPONSE3"

# Retrieve an known response (for testing the _perform_command method) #
# ---------------------------------------------------------------- #
WRONG_RTU_RESPONSES[
    b"\x01\x10TESTCOMMAND\x08B"
] = b"\x01\x10TRspU<"  # Response should be 8 bytes
WRONG_RTU_RESPONSES[
    b"\x01\x4bTESTCOMMAND2\x18\xc8"
] = b"\x01\x4bTESTCOMMANDRESPONSE2K\x8c"
WRONG_RTU_RESPONSES[
    b"\x01\x01TESTCOMMAND4~"
] = b"\x02\x01TESTCOMMANDRESPONSEx]"  # Wrong slave address in response
WRONG_RTU_RESPONSES[
    b"\x01\x02TESTCOMMAND0z"
] = b"\x01\x03TESTCOMMANDRESPONSE2\x8c"  # Wrong function code in response
WRONG_RTU_RESPONSES[
    b"\x01\x03TESTCOMMAND\xcd\xb9"
] = b"\x01\x03TESTCOMMANDRESPONSEab"  # Wrong CRC in response
WRONG_RTU_RESPONSES[b"\x01\x04TESTCOMMAND8r"] = b"A"  # Too short response message
WRONG_RTU_RESPONSES[
    b"\x01\x05TESTCOMMAND\xc5\xb1"
] = b"\x01\x85TESTCOMMANDRESPONSE\xa54"  # Error indication from slave


# Handle local echo: Read register 289 on slave 20 using function code 3 #
# ---------------------------------------------------------------------- #
# Message:  Slave address 20, function code 3. Register address 289, 1 register. CRC.
# Response: Echo. Slave address 20, function code 3. 2 bytes, value=770. CRC.
WRONG_RTU_RESPONSES[b"\x14\x03" + b"\x01!\x00\x01" + b"\xd79"] = (
    (b"\x14\x03" + b"\x01!\x00\x01" + b"\xd79")
    + b"\x14\x03"
    + b"\x02\x03\x02"
    + b"4\xb6"
)

# Handle local echo: Read register 290 on slave 20 using function code 3. Wrong echo #
# ---------------------------------------------------------------------------------- #
# Message:  Slave address 20, function code 3. Register address 290, 1 register. CRC.
# Response: Wrong echo. Slave address 20, function code 3. 2 bytes, value=770. CRC.

WRONG_RTU_RESPONSES[b"\x14\x03" + b"\x01\x22\x00\x01" + b"\x27\x39"] = (
    (b"\x14\x03" + b"\x01\x22\x00\x02" + b"\x27\x39")
    + b"\x14\x03"
    + b"\x02\x03\x02"
    + b"4\xb6"
)


# Recorded data from OmegaCN7500 #
##################################
# (Sorted by slave address, register address)

# Slave address 1, read_bit(2068) Response value 1.
GOOD_RTU_RESPONSES[b"\x01\x02\x08\x14\x00\x01\xfb\xae"] = b"\x01\x02\x01\x01`H"

# Slave address 1, write_bit(2068, 0)
GOOD_RTU_RESPONSES[
    b"\x01\x05\x08\x14\x00\x00\x8f\xae"
] = b"\x01\x05\x08\x14\x00\x00\x8f\xae"

# Slave address 1, write_bit(2068, 1)
GOOD_RTU_RESPONSES[b"\x01\x05\x08\x14\xff\x00\xce^"] = b"\x01\x05\x08\x14\xff\x00\xce^"

# Slave address 1, read_register(4097, 1) Response value 823.6
GOOD_RTU_RESPONSES[b"\x01\x03\x10\x01\x00\x01\xd1\n"] = b"\x01\x03\x02 ,\xa0Y"

# Slave address 1, write_register(4097, 700.0, 1)
GOOD_RTU_RESPONSES[
    b"\x01\x10\x10\x01\x00\x01\x02\x1bX\xbdJ"
] = b"\x01\x10\x10\x01\x00\x01T\xc9"

# Slave address 1, write_register(4097, 823.6, 1)
GOOD_RTU_RESPONSES[
    b"\x01\x10\x10\x01\x00\x01\x02 ,\xae]"
] = b"\x01\x10\x10\x01\x00\x01T\xc9"

# Slave address 10, read_bit(2068) Response value 1
GOOD_RTU_RESPONSES[b"\n\x02\x08\x14\x00\x01\xfa\xd5"] = b"\n\x02\x01\x01bl"

# Slave address 10, write_bit(2068, 0)
GOOD_RTU_RESPONSES[
    b"\n\x05\x08\x14\x00\x00\x8e\xd5"
] = b"\n\x05\x08\x14\x00\x00\x8e\xd5"

# Slave address 10, write_bit(2068, 1)
GOOD_RTU_RESPONSES[b"\n\x05\x08\x14\xff\x00\xcf%"] = b"\n\x05\x08\x14\xff\x00\xcf%"

# Slave address 10, read_register(4096, 1) Response value 25.0
GOOD_RTU_RESPONSES[b"\n\x03\x10\x00\x00\x01\x81\xb1"] = b"\n\x03\x02\x00\xfa\x9d\xc6"

# Slave address 10, read_register(4097, 1) Response value 325.8
GOOD_RTU_RESPONSES[b"\n\x03\x10\x01\x00\x01\xd0q"] = b"\n\x03\x02\x0c\xba\x996"

# Slave address 10, write_register(4097, 325.8, 1)
GOOD_RTU_RESPONSES[
    b"\n\x10\x10\x01\x00\x01\x02\x0c\xbaA\xc3"
] = b"\n\x10\x10\x01\x00\x01U\xb2"

# Slave address 10, write_register(4097, 20.0, 1)
GOOD_RTU_RESPONSES[
    b"\n\x10\x10\x01\x00\x01\x02\x00\xc8\xc4\xe6"
] = b"\n\x10\x10\x01\x00\x01U\xb2"

# Slave address 10, write_register(4097, 200.0, 1)
GOOD_RTU_RESPONSES[
    b"\n\x10\x10\x01\x00\x01\x02\x07\xd0\xc6\xdc"
] = b"\n\x10\x10\x01\x00\x01U\xb2"


# Recorded RTU data from Delta DTB4824 #
########################################
# (Sorted by register number)

# Slave address 7, read_bit(0x0800). This is LED AT.
# Response value 0
GOOD_RTU_RESPONSES[b"\x07\x02\x08\x00\x00\x01\xbb\xcc"] = b"\x07\x02\x01\x00\xa1\x00"

# Slave address 7, read_bit(0x0801). This is LED Out1.
# Response value 0
GOOD_RTU_RESPONSES[b"\x07\x02\x08\x01\x00\x01\xea\x0c"] = b"\x07\x02\x01\x00\xa1\x00"

# Slave address 7, read_bit(0x0802). This is LED Out2.
# Response value 0
GOOD_RTU_RESPONSES[b"\x07\x02\x08\x02\x00\x01\x1a\x0c"] = b"\x07\x02\x01\x00\xa1\x00"

# Slave address 7, write_bit(0x0810, 1) This is "Communication write in enabled".
GOOD_RTU_RESPONSES[
    b"\x07\x05\x08\x10\xff\x00\x8f\xf9"
] = b"\x07\x05\x08\x10\xff\x00\x8f\xf9"

# Slave address 7, _perform_command(2, '\x08\x10\x00\x09'). This is reading 9 bits
# starting at 0x0810.
# Response value '\x02\x07\x00'
GOOD_RTU_RESPONSES[b"\x07\x02\x08\x10\x00\t\xbb\xcf"] = b"\x07\x02\x02\x07\x003\x88"

# Slave address 7, read_bit(0x0814). This is RUN/STOP setting.
# Response value 0
GOOD_RTU_RESPONSES[b"\x07\x02\x08\x14\x00\x01\xfb\xc8"] = b"\x07\x02\x01\x00\xa1\x00"

# Slave address 7, write_bit(0x0814, 0). This is STOP.
GOOD_RTU_RESPONSES[
    b"\x07\x05\x08\x14\x00\x00\x8f\xc8"
] = b"\x07\x05\x08\x14\x00\x00\x8f\xc8"

# Slave address 7, write_bit(0x0814, 1). This is RUN.
GOOD_RTU_RESPONSES[b"\x07\x05\x08\x14\xff\x00\xce8"] = b"\x07\x05\x08\x14\xff\x00\xce8"

# Slave address 7, read_registers(0x1000, 2). This is process value (PV) and
# setpoint (SV).
# Response value [64990, 350]
GOOD_RTU_RESPONSES[
    b"\x07\x03\x10\x00\x00\x02\xc0\xad"
] = b"\x07\x03\x04\xfd\xde\x01^M\xcd"

# Slave address 7, read_register(0x1000). This is process value (PV).
# Response value 64990
GOOD_RTU_RESPONSES[
    b"\x07\x03\x10\x00\x00\x01\x80\xac"
] = b"\x07\x03\x02\xfd\xde\xf0\x8c"

# Slave address 7, read_register(0x1001, 1). This is setpoint (SV).
# Response value 80.0
GOOD_RTU_RESPONSES[b"\x07\x03\x10\x01\x00\x01\xd1l"] = b"\x07\x03\x02\x03 1l"

# Slave address 7, write_register(0x1001, 25, 1, functioncode=6)
GOOD_RTU_RESPONSES[
    b"\x07\x06\x10\x01\x00\xfa\\\xef"
] = b"\x07\x06\x10\x01\x00\xfa\\\xef"

# Slave address 7, write_register(0x1001, 0x0320, functioncode=6)
# Write value 800 to register 0x1001.
# This is a setpoint of 80.0 degrees (Centigrades, dependent on setting).
GOOD_RTU_RESPONSES[b"\x07\x06\x10\x01\x03 \xdd\x84"] = b"\x07\x06\x10\x01\x03 \xdd\x84"

# Slave address 7, read_register(0x1004). This is sensor type.
# Response value 14
GOOD_RTU_RESPONSES[b"\x07\x03\x10\x04\x00\x01\xc1m"] = b"\x07\x03\x02\x00\x0e\xb1\x80"

# Slave address 7, read_register(0x1005) This is control method.
# Response value 1
GOOD_RTU_RESPONSES[
    b"\x07\x03\x10\x05\x00\x01\x90\xad"
] = b"\x07\x03\x02\x00\x01\xf1\x84"

# Slave address 7, read_register(0x1006). This is heating/cooling selection.
# Response value 0
GOOD_RTU_RESPONSES[b"\x07\x03\x10\x06\x00\x01`\xad"] = b"\x07\x03\x02\x00\x000D"

# Slave address 7, read_register(0x1012, 1). This is output 1.
# Response value 0.0
GOOD_RTU_RESPONSES[b"\x07\x03\x10\x12\x00\x01 \xa9"] = b"\x07\x03\x02\x00\x000D"

# Slave address 7, read_register(0x1013, 1). This is output 2.
# Response value 0.0
GOOD_RTU_RESPONSES[b"\x07\x03\x10\x13\x00\x01qi"] = b"\x07\x03\x02\x00\x000D"

# Slave address 7, read_register(0x1023). This is system alarm setting.
# Response value 0
GOOD_RTU_RESPONSES[b"\x07\x03\x10#\x00\x01qf"] = b"\x07\x03\x02\x00\x000D"

# Slave address 7, read_register(0x102A). This is LED status.
# Response value 0
GOOD_RTU_RESPONSES[b"\x07\x03\x10*\x00\x01\xa1d"] = b"\x07\x03\x02\x00\x000D"

# Slave address 7, read_register(0x102B). This is pushbutton status.
# Response value 15
GOOD_RTU_RESPONSES[b"\x07\x03\x10+\x00\x01\xf0\xa4"] = b"\x07\x03\x02\x00\x0fp@"

# Slave address 7, read_register(0x102F). This is firmware version.
# Response value 400
GOOD_RTU_RESPONSES[b"\x07\x03\x10/\x00\x01\xb1e"] = b"\x07\x03\x02\x01\x901\xb8"


# Recorded ASCII data from Delta DTB4824 #
##########################################
# (Sorted by register number)

# Slave address 7, read_bit(0x0800). This is LED AT.
# Response value 0
GOOD_ASCII_RESPONSES[b":070208000001EE\r\n"] = b":07020100F6\r\n"

# Slave address 7, read_bit(0x0801). This is LED Out1.
# Response value 1
GOOD_ASCII_RESPONSES[b":070208010001ED\r\n"] = b":07020101F5\r\n"

# Slave address 7, read_bit(0x0802). This is LED Out2.
# Response value 0
GOOD_ASCII_RESPONSES[b":070208020001EC\r\n"] = b":07020100F6\r\n"

# Slave address 7, _perform_command(2, '\x08\x10\x00\x09').
# This is reading 9 bits starting at 0x0810.
# Response value '\x02\x17\x00'
GOOD_ASCII_RESPONSES[b":070208100009D6\r\n"] = b":0702021700DE\r\n"

# Slave address 7, write_bit(0x0810, 1) This is "Communication write in enabled".
GOOD_ASCII_RESPONSES[b":07050810FF00DD\r\n"] = b":07050810FF00DD\r\n"

# Slave address 7, read_bit(0x0814). This is RUN/STOP setting.
# Response value 1
GOOD_ASCII_RESPONSES[b":070208140001DA\r\n"] = b":07020101F5\r\n"

# Slave address 7, write_bit(0x0814, 0). This is STOP.
GOOD_ASCII_RESPONSES[b":070508140000D8\r\n"] = b":070508140000D8\r\n"

# Slave address 7, write_bit(0x0814, 1). This is RUN.
GOOD_ASCII_RESPONSES[b":07050814FF00D9\r\n"] = b":07050814FF00D9\r\n"

# Slave address 7, read_registers(0x1000, 2).
# This is process value (PV) and setpoint (SV).
# Response value [64990, 350]
GOOD_ASCII_RESPONSES[b":070310000002E4\r\n"] = b":070304FDDE015EB8\r\n"

# Slave address 7, read_register(0x1000). This is process value (PV).
# Response value 64990
GOOD_ASCII_RESPONSES[b":070310000001E5\r\n"] = b":070302FDDE19\r\n"

# Slave address 7, read_register(0x1001, 1). This is setpoint (SV).
# Response value 80.0
GOOD_ASCII_RESPONSES[b":070310010001E4\r\n"] = b":0703020320D1\r\n"

# Slave address 7, write_register(0x1001, 25, 1, functioncode=6)
GOOD_ASCII_RESPONSES[b":0706100100FAE8\r\n"] = b":0706100100FAE8\r\n"

# Slave address 7, write_register(0x1001, 0x0320, functioncode=6)
# Write value 800 to register 0x1001.
# This is a setpoint of 80.0 degrees (Centigrades, dependent on setting).
GOOD_ASCII_RESPONSES[b":070610010320BF\r\n"] = b":070610010320BF\r\n"

# Slave address 7, read_register(0x1004). This is sensor type.
# Response value 14
GOOD_ASCII_RESPONSES[b":070310040001E1\r\n"] = b":070302000EE6\r\n"

# Slave address 7, read_register(0x1005) This is control method.
# Response value 1
GOOD_ASCII_RESPONSES[b":070310050001E0\r\n"] = b":0703020001F3\r\n"

# Slave address 7, read_register(0x1006). This is heating/cooling selection.
# Response value 0
GOOD_ASCII_RESPONSES[b":070310060001DF\r\n"] = b":0703020000F4\r\n"

# Slave address 7, read_register(0x1012, 1). This is output 1.
# Response value 100.0
GOOD_ASCII_RESPONSES[b":070310120001D3\r\n"] = b":07030203E809\r\n"

# Slave address 7, read_register(0x1013, 1). This is output 2.
# Response value 0.0
GOOD_ASCII_RESPONSES[b":070310130001D2\r\n"] = b":0703020000F4\r\n"

# Slave address 7, read_register(0x1023). This is system alarm setting.
# Response value 0
GOOD_ASCII_RESPONSES[b":070310230001C2\r\n"] = b":0703020000F4\r\n"

# Slave address 7, read_register(0x102A). This is LED status.
# Response value 64
GOOD_ASCII_RESPONSES[b":0703102A0001BB\r\n"] = b":0703020040B4\r\n"

# Slave address 7, read_register(0x102B). This is pushbutton status.
# Response value 15
GOOD_ASCII_RESPONSES[b":0703102B0001BA\r\n"] = b":070302000FE5\r\n"

# Slave address 7, read_register(0x102F). This is firmware version.
# Response value 400
GOOD_ASCII_RESPONSES[b":0703102F0001B6\r\n"] = b":070302019063\r\n"


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

if __name__ == "__main__":
    # Run all tests #

    unittest.main(verbosity=VERBOSITY)

    # Run a test class #

    # suite = unittest.TestLoader().
    # loadTestsFromTestCase(TestDummyCommunicationHandleLocalEcho)
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestCheckBytes)
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestPredictResponseSize)
    # suite = unittest.TestLoader().
    # loadTestsFromTestCase(TestDummyCommunicationBroadcast)
    # unittest.TextTestRunner(verbosity=2).run(suite)

    # Run a single test #

    # suite = unittest.TestSuite()
    # suite.addTest(("testGenericCommand"))
    # suite.addTest(TestDummyCommunication("testWriteBits"))
    # suite.addTest(TestDummyCommunication("testReadLongWrongValue"))
    # suite.addTest(TestDummyCommunication("testWriteBit"))
    # suite.addTest(TestDummyCommunication("testWriteFloat"))
    # unittest.TextTestRunner(verbosity=2).run(suite)

    # Run individual commands #

    # print(
    #     repr(
    #         minimalmodbus._calculate_crc(
    #             b"\x01\x10" + b"\x00m\x00\x04\x08\xff\xff\xff\xff\xff\xff\xff\xfc"
    #         )
    #     )
    # )
