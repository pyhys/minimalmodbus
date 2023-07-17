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
"""MinimalModbus: A Python driver for Modbus RTU/ASCII via serial port."""

__author__ = "Jonas Berg"
__license__ = "Apache License, Version 2.0"
__url__ = "https://github.com/pyhys/minimalmodbus"
__version__ = "2.1.1"

import sys

if sys.version_info < (3, 8, 0):
    raise ImportError(
        "Your Python version is too old for this version of MinimalModbus"
    )

import binascii
import enum
import os
import struct
import time
from typing import Any, Dict, List, Optional, Type, Union

import serial

_NUMBER_OF_BYTES_BEFORE_REGISTERDATA = 1  # Within the payload
_NUMBER_OF_BYTES_PER_REGISTER = 2
_MAX_NUMBER_OF_REGISTERS_TO_WRITE = 123
_MAX_NUMBER_OF_REGISTERS_TO_READ = 125
_MAX_NUMBER_OF_BITS_TO_WRITE = 1968  # 0x7B0
_MAX_NUMBER_OF_BITS_TO_READ = 2000  # 0x7D0
_MAX_NUMBER_OF_DECIMALS = 10  # Some instrument might store 0.00000154 Ampere as 154 etc
_MAX_BYTEORDER_VALUE = 3
_SECONDS_TO_MILLISECONDS = 1000
_BROADCAST_DELAY: float = 0.2  # seconds
_BITS_PER_BYTE = 8
_ASCII_HEADER = b":"
_ASCII_FOOTER = b"\r\n"
_BYTEPOSITION_FOR_ASCII_HEADER = 0  # Relative to plain response
_BYTEPOSITION_FOR_SLAVEADDRESS = 0  # Relative to (stripped) response
_BYTEPOSITION_FOR_FUNCTIONCODE = 1  # Relative to (stripped) response
_BYTEPOSITION_FOR_SLAVE_ERROR_CODE = 2  # Relative to (stripped) response
_BITNUMBER_FUNCTIONCODE_ERRORINDICATION = 7
_SLAVEADDRESS_BROADCAST = 0

# Several instrument instances can share the same serialport
_serialports: Dict[str, serial.Serial] = {}  # Key: port name, value: port instance
_latest_read_times: Dict[str, float] = {}  # Key: port name, value: timestamp

# ############### #
# Named constants #
# ############### #

MODE_RTU: str = "rtu"
"""Use Modbus RTU communication."""
MODE_ASCII: str = "ascii"
"""Use Modbus ASCII communication."""

BYTEORDER_BIG: int = 0
"""Use big endian byteorder."""
BYTEORDER_LITTLE: int = 1
"""Use little endian byteorder."""
BYTEORDER_BIG_SWAP: int = 2
"""Use big endian byteorder, with swap."""
BYTEORDER_LITTLE_SWAP: int = 3
"""Use litte endian byteorder, with swap."""


@enum.unique
class _Payloadformat(enum.Enum):
    BIT = enum.auto()
    BITS = enum.auto()
    FLOAT = enum.auto()
    LONG = enum.auto()
    REGISTER = enum.auto()
    REGISTERS = enum.auto()
    STRING = enum.auto()


# ######################## #
# Modbus instrument object #
# ######################## #


class Instrument:
    """Instrument class for talking to instruments (slaves).

    Uses the Modbus RTU or ASCII protocols (via RS485 or RS232).

    Args:
        * port: The serial port name, for example ``/dev/ttyUSB0`` (Linux),
          ``/dev/tty.usbserial`` (OS X) or ``COM4`` (Windows).
          It is also possible to pass in an already opened ``serial.Serial``
          object (new in version 2.1).
        * slaveaddress: Slave address in the range 0 to 247.
          Address 0 is for broadcast, and 248-255 are reserved.
        * mode: Mode selection. Can be :data:`minimalmodbus.MODE_RTU` or
          :data:`minimalmodbus.MODE_ASCII`.
        * close_port_after_each_call: If the serial port should be closed after
          each call to the instrument.
        * debug: Set this to :const:`True` to print the communication details
    """

    def __init__(
        self,
        port: Union[str, serial.Serial],
        slaveaddress: int,
        mode: str = MODE_RTU,
        close_port_after_each_call: bool = False,
        debug: bool = False,
    ) -> None:
        """Initialize instrument and open corresponding serial port."""
        self.address = slaveaddress
        """Slave address (int). Most often set by the constructor (see the class
        documentation).

        Slave address 0 is for broadcasting to all slaves (no responses are sent). It is
        only possible to write infomation (not read) via broadcast. A long delay is
        added after each transmission to allow the slowest slaves to digest the
        information.

        New in version 2.0: Support for broadcast
        """

        self.mode = mode
        """Slave mode (str), can be :data:`minimalmodbus.MODE_RTU` or
        :data:`minimalmodbus.MODE_ASCII`. Most often set by the constructor (see the
        class documentation). Defaults to RTU.

        Changing this will not affect how other instruments use the same serial port.

        New in version 0.6.
        """

        self.precalculate_read_size = True
        """If this is :const:`False`, the serial port reads until timeout instead of
        just reading a specific number of bytes. Defaults to :const:`True`.

        Changing this will not affect how other instruments use the same serial port.

        New in version 0.5.
        """

        self.debug = debug
        """Set this to :const:`True` to print the communication details. Defaults to
        :const:`False`.

        Most often set by the constructor (see the class documentation).

        Changing this will not affect how other instruments use the same serial port.
        """

        self.clear_buffers_before_each_transaction = True
        """If this is :const:`True`, the serial port read and write buffers are cleared
        before each request to the instrument, to avoid cumulative byte sync errors
        across multiple messages. Defaults to :const:`True`.

        Changing this will not affect how other instruments use the same serial port.

        New in version 1.0.
        """

        self.close_port_after_each_call = close_port_after_each_call
        """If this is :const:`True`, the serial port will be closed after each call.
        Defaults to :const:`False`.

        Changing this will not affect how other instruments use the same serial port.

        Most often set by the constructor (see the class documentation).
        """

        self.handle_local_echo = False
        """Set to to :const:`True` if your RS-485 adaptor has local echo enabled. Then
        the transmitted message will immeadiately appear at the receive line of the
        RS-485 adaptor. MinimalModbus will then read and discard this data, before
        reading the data from the slave. Defaults to :const:`False`.

        Changing this will not affect how other instruments use the same serial port.

        New in version 0.7.
        """

        self.serial: Optional[serial.Serial] = None
        """The serial port object as defined by the pySerial module. Created by the
        constructor.

        Attributes that could be changed after initialisation:

            - port (str):      Serial port name.
                - Most often set by the constructor (see the class documentation).
            - baudrate (int):  Baudrate in Baud.
                - Defaults to 19200.
            - parity (use PARITY_xxx constants): Parity. See the pySerial module.
                - Defaults to :const:`serial.PARITY_NONE`.
            - bytesize (int):  Bytesize in bits.
                - Defaults to 8.
            - stopbits (use STOPBITS_xxx constants):  Number of stopbits. See pySerial.
                - Defaults to :const:`serial.STOPBITS_ONE`.
            - timeout (float): Read timeout value in seconds.
                - Defaults to 0.05 s.
            - write_timeout (float): Write timeout value in seconds.
                - Defaults to 2.0 s.
        """

        if _is_serial_object(port):
            self.serial = port  # type: ignore
        elif isinstance(port, str) and (
            port not in _serialports or not _serialports[port]
        ):
            self._print_debug("Create serial port {}".format(port))
            self.serial = _serialports[port] = serial.Serial(
                port=port,
                baudrate=19200,
                parity=serial.PARITY_NONE,
                bytesize=8,
                stopbits=1,
                timeout=0.05,
                write_timeout=2.0,
            )
        elif isinstance(port, str):
            self._print_debug("Serial port {} already exists".format(port))
            self.serial = _serialports[port]
            if (self.serial.port is None) or (not self.serial.is_open):
                self._print_debug("Serial port {} is closed. Opening.".format(port))
                self.serial.open()

        if self.serial is None or not _is_serial_object(self.serial):
            raise MasterReportedException("Failed to initialise serial port")

        if not self.serial.is_open:
            raise MasterReportedException("Failed to open serial port")

        if self.close_port_after_each_call:
            self._print_debug("Closing serial port {}".format(port))
            self.serial.close()

        self._latest_roundtrip_time: Optional[float] = None

    def __repr__(self) -> str:
        """Give string representation of the :class:`.Instrument` object."""
        template = (
            "{}.{}<id=0x{:x}, address={}, mode={}, close_port_after_each_call={}, "
            + "precalculate_read_size={}, clear_buffers_before_each_transaction={}, "
            + "handle_local_echo={}, debug={}, serial={}>"
        )
        return template.format(
            self.__module__,
            self.__class__.__name__,
            id(self),
            self.address,
            self.mode,
            self.close_port_after_each_call,
            self.precalculate_read_size,
            self.clear_buffers_before_each_transaction,
            self.handle_local_echo,
            self.debug,
            self.serial,
        )

    @property
    def roundtrip_time(self) -> Optional[float]:
        """Latest measured round-trip time, in seconds. Read only.

        Note that the value is ``None`` if no data is available.

        The round-trip time is the time from minimalmodbus sends request data,
        to the time it receives response data from the instrument.
        It is basically the time spent waiting on external communication.

        Note that mimimalmodbus also sleeps (not included in the round trip time),
        for example to fulfill the inter-message time interval or to give
        slaves time to process broadcasted information.

        New in version 2.0
        """
        return self._latest_roundtrip_time

    def _print_debug(self, text: str) -> None:
        if self.debug:
            print("MinimalModbus debug mode. " + text)

    # ################################# #
    #  Methods for talking to the slave #
    # ################################# #

    def read_bit(self, registeraddress: int, functioncode: int = 2) -> int:
        """Read one bit from the slave (instrument).

        This is for a bit that has its individual address in the instrument.

        Args:
            * registeraddress: The slave register address.
            * functioncode Modbus function code. Can be 1 or 2.

        Returns:
            The bit value 0 or 1.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        _check_functioncode(functioncode, [1, 2])
        return int(
            self._generic_command(
                functioncode,
                registeraddress,
                number_of_bits=1,
                payloadformat=_Payloadformat.BIT,
            )
        )

    def write_bit(
        self, registeraddress: int, value: int, functioncode: int = 5
    ) -> None:
        """Write one bit to the slave (instrument).

        This is for a bit that has its individual address in the instrument.

        Args:
            * registeraddress: The slave register address.
            * value: 0 or 1, or True or False
            * functioncode: Modbus function code. Can be 5 or 15.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        _check_functioncode(functioncode, [5, 15])
        _check_int(value, minvalue=0, maxvalue=1, description="input value")
        self._generic_command(
            functioncode,
            registeraddress,
            value,
            number_of_bits=1,
            payloadformat=_Payloadformat.BIT,
        )

    def read_bits(
        self, registeraddress: int, number_of_bits: int, functioncode: int = 2
    ) -> List[int]:
        """Read multiple bits from the slave (instrument).

        This is for bits that have individual addresses in the instrument.

        Args:
            * registeraddress: The slave register start address.
            * number_of_bits: Number of bits to read
            * functioncode: Modbus function code. Can be 1 or 2.

        Returns:
            A list of bit values 0 or 1. The first value in the list is for
            the bit at the given address.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        _check_functioncode(functioncode, [1, 2])
        _check_int(
            number_of_bits,
            minvalue=1,
            maxvalue=_MAX_NUMBER_OF_BITS_TO_READ,
            description="number of bits",
        )
        returnvalue = self._generic_command(
            functioncode,
            registeraddress,
            number_of_bits=number_of_bits,
            payloadformat=_Payloadformat.BITS,
        )
        # Make sure that we really return a list of integers
        assert isinstance(returnvalue, list)
        return [int(x) for x in returnvalue]

    def write_bits(self, registeraddress: int, values: List[int]) -> None:
        """Write multiple bits to the slave (instrument).

        This is for bits that have individual addresses in the instrument.

        Uses Modbus functioncode 15.

        Args:
            * registeraddress: The slave register start address.
            * values: List of 0 or 1, or True or False. The first
              value in the list is for the bit at the given address.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        if not isinstance(values, list):
            raise TypeError(
                'The "values parameter" must be a list. Given: {0!r}'.format(values)
            )
        # Note: The content of the list is checked at content conversion.
        _check_int(
            len(values),
            minvalue=1,
            maxvalue=_MAX_NUMBER_OF_BITS_TO_WRITE,
            description="length of input list",
        )

        self._generic_command(
            15,
            registeraddress,
            values,
            number_of_bits=len(values),
            payloadformat=_Payloadformat.BITS,
        )

    def read_register(
        self,
        registeraddress: int,
        number_of_decimals: int = 0,
        functioncode: int = 3,
        signed: bool = False,
    ) -> Union[int, float]:
        """Read an integer from one 16-bit register in the slave, possibly scaling it.

        The slave register can hold integer values in the range 0 to 65535
        ("Unsigned INT16").

        Args:
            * registeraddress: The slave register address.
            * number_of_decimals: The number of decimals for content conversion.
            * functioncode: Modbus function code. Can be 3 or 4.
            * signed: Whether the data should be interpreted as unsigned or signed.

        .. note:: The parameter number_of_decimals was named numberOfDecimals
                  before MinimalModbus 1.0

        If a value of 77.0 is stored internally in the slave register as 770,
        then use ``number_of_decimals=1`` which will divide the received data by 10
        before returning the value.

        Similarly ``number_of_decimals=2`` will divide the received data by 100 before
        returning the value.

        Some manufacturers allow negative values for some registers. Instead of
        an allowed integer range 0 to 65535, a range -32768 to 32767 is allowed.
        This is implemented as any received value in the upper range (32768 to
        65535) is interpreted as negative value (in the range -32768 to -1).

        Use the parameter ``signed=True`` if reading from a register that can hold
        negative values. Then upper range data will be automatically converted into
        negative return values (two's complement).

        ============== ================== ================ ===============
        ``signed``     Data type in slave Alternative name Range
        ============== ================== ================ ===============
        :const:`False` Unsigned INT16     Unsigned short   0 to 65535
        :const:`True`  INT16              Short            -32768 to 32767
        ============== ================== ================ ===============

        Returns:
            The register data in numerical value (int or float).

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        _check_functioncode(functioncode, [3, 4])
        _check_int(
            number_of_decimals,
            minvalue=0,
            maxvalue=_MAX_NUMBER_OF_DECIMALS,
            description="number of decimals",
        )
        _check_bool(signed, description="signed")
        returnvalue = self._generic_command(
            functioncode,
            registeraddress,
            number_of_decimals=number_of_decimals,
            number_of_registers=1,
            signed=signed,
            payloadformat=_Payloadformat.REGISTER,
        )
        if int(returnvalue) == returnvalue:
            return int(returnvalue)
        return float(returnvalue)

    def write_register(
        self,
        registeraddress: int,
        value: Union[int, float],
        number_of_decimals: int = 0,
        functioncode: int = 16,
        signed: bool = False,
    ) -> None:
        """Write an integer to one 16-bit register in the slave, possibly scaling it.

        The slave register can hold integer values in the range 0 to
        65535 ("Unsigned INT16").

        Args:
            * registeraddress: The slave register address.
            * value (int or float): The value to store in the slave register (might be
              scaled before sending).
            * number_of_decimals: The number of decimals for content conversion.
            * functioncode: Modbus function code. Can be 6 or 16.
            * signed: Whether the data should be interpreted as unsigned or signed.

        .. note:: The parameter number_of_decimals was named numberOfDecimals
                  before MinimalModbus 1.0

        To store for example ``value=77.0``, use ``number_of_decimals=1`` if the
        slave register will hold it as 770 internally. This will multiply ``value`` by
        10 before sending it to the slave register.

        Similarly ``number_of_decimals=2`` will multiply ``value`` by 100 before sending
        it to the slave register.

        As the largest number that can be written to a register is 0xFFFF = 65535,
        the ``value`` and ``number_of_decimals`` should max be 65535 when combined.
        So when using ``number_of_decimals=3`` the maximum ``value`` is 65.535.

        For discussion on negative values, the range and on alternative names,
        see :meth:`.read_register`.

        Use the parameter ``signed=True`` if writing to a register that can hold
        negative values. Then negative input will be automatically converted into
        upper range data (two's complement).

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        _check_functioncode(functioncode, [6, 16])
        _check_int(
            number_of_decimals,
            minvalue=0,
            maxvalue=_MAX_NUMBER_OF_DECIMALS,
            description="number of decimals",
        )
        _check_bool(signed, description="signed")
        _check_numerical(value, description="input value")

        self._generic_command(
            functioncode,
            registeraddress,
            value,
            number_of_decimals=number_of_decimals,
            number_of_registers=1,
            signed=signed,
            payloadformat=_Payloadformat.REGISTER,
        )

    def read_long(
        self,
        registeraddress: int,
        functioncode: int = 3,
        signed: bool = False,
        byteorder: int = BYTEORDER_BIG,
        number_of_registers: int = 2,
    ) -> int:
        """Read a long integer (32 or 64 bits) from the slave.

        Long integers (32 bits = 4 bytes or 64 bits = 8 bytes) are stored in
        two or four consecutive 16-bit registers in the slave respectively.

        Args:
            * registeraddress: The slave register start address.
            * functioncode: Modbus function code. Can be 3 or 4.
            * signed: Whether the data should be interpreted as unsigned or signed.
            * byteorder: How multi-register data should be interpreted.
              Use the BYTEORDER_xxx constants. Defaults to
              :data:`minimalmodbus.BYTEORDER_BIG`.
            * number_of_registers: The number of registers allocated for the long.
              Can be 2 or 4. (New in version 2.1)


        ======================= ============== =============== =====================
        ``number_of_registers`` ``signed``     Slave data type Range
        ======================= ============== =============== =====================
        2                       :const:`False` Unsigned INT32  0 to 4294967295
        2                       :const:`True`  INT32           -2147483648 to 2147483647
        4                       :const:`False` Unsigned INT64  0 to approx 1.8E19
        4                       :const:`True`  INT64           Approx -9.2E18 to 9.2E18
        ======================= ============== =============== =====================

        Returns:
            The numerical value.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        _check_functioncode(functioncode, [3, 4])
        _check_bool(signed, description="signed")
        _check_int(
            number_of_registers,
            minvalue=2,
            maxvalue=4,
            description="number of registers",
        )
        return int(
            self._generic_command(
                functioncode,
                registeraddress,
                number_of_registers=number_of_registers,
                signed=signed,
                byteorder=byteorder,
                payloadformat=_Payloadformat.LONG,
            )
        )

    def write_long(
        self,
        registeraddress: int,
        value: int,
        signed: bool = False,
        byteorder: int = BYTEORDER_BIG,
        number_of_registers: int = 2,
    ) -> None:
        """Write a long integer (32 or 64 bits) to the slave.

        Long integers (32 bits = 4 bytes or 64 bits = 8 bytes) are stored in
        two or four consecutive 16-bit registers in the slave respectively.

        Uses Modbus function code 16.

        For discussion on number of bits, number of registers and the range,
        see :meth:`.read_long`.

        Args:
            * registeraddress: The slave register start address.
            * value: The value to store in the slave.
            * signed: Whether the data should be interpreted as unsigned or signed.
            * byteorder: How multi-register data should be interpreted.
              Use the BYTEORDER_xxx constants. Defaults to
              :data:`minimalmodbus.BYTEORDER_BIG`.
            * number_of_registers: The number of registers allocated for the long.
              Can be 2 or 4. (New in version 2.1)

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        MAX_VALUE_LONG = 4294967295  # Unsigned INT32
        MIN_VALUE_LONG = -2147483648  # INT32
        MAX_VALUE_LONG_LONG = 18446744073709551615  # Unsigned INT64
        MIN_VALUE_LONG_LONG = -9223372036854775808  # INT64

        _check_int(
            number_of_registers,
            minvalue=2,
            maxvalue=4,
            description="number of registers",
        )
        if number_of_registers == 2:
            _check_int(
                value,
                minvalue=MIN_VALUE_LONG,
                maxvalue=MAX_VALUE_LONG,
                description="input value",
            )
        elif number_of_registers == 4:
            _check_int(
                value,
                minvalue=MIN_VALUE_LONG_LONG,
                maxvalue=MAX_VALUE_LONG_LONG,
                description="input value",
            )
        _check_bool(signed, description="signed")
        self._generic_command(
            16,
            registeraddress,
            value,
            number_of_registers=number_of_registers,
            signed=signed,
            byteorder=byteorder,
            payloadformat=_Payloadformat.LONG,
        )

    def read_float(
        self,
        registeraddress: int,
        functioncode: int = 3,
        number_of_registers: int = 2,
        byteorder: int = BYTEORDER_BIG,
    ) -> float:
        r"""Read a floating point number from the slave.

        Floats are stored in two or more consecutive 16-bit registers in the slave.
        The encoding is according to the standard IEEE 754.

        There are differences in the byte order used by different manufacturers.
        A floating point value of 1.0 is encoded (in single precision) as 3f800000
        (hex). In this implementation the data will be sent as ``'\x3f\x80'``
        and ``'\x00\x00'`` to two consecutetive registers by default. Make sure to
        test that it makes sense for your instrument. If not, change the
        ``byteorder`` argument.

        Args:
            * registeraddress : The slave register start address.
            * functioncode: Modbus function code. Can be 3 or 4.
            * number_of_registers: The number of registers allocated for the float.
              Can be 2 or 4.
            * byteorder: How multi-register data should be interpreted.
              Use the BYTEORDER_xxx constants. Defaults to
              :data:`minimalmodbus.BYTEORDER_BIG`.

        .. note:: The parameter number_of_registers was named numberOfRegisters
                  before MinimalModbus 1.0

        =============================== ================= =========== =================
        Type of floating point in slave Size              Registers   Range
        =============================== ================= =========== =================
        Single precision (binary32)     32 bits (4 bytes) 2 registers 1.4E-45 to 3.4E38
        Double precision (binary64)     64 bits (8 bytes) 4 registers 5E-324 to 1.8E308
        =============================== ================= =========== =================

        Returns:
            The numerical value.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        _check_functioncode(functioncode, [3, 4])
        _check_int(
            number_of_registers,
            minvalue=2,
            maxvalue=4,
            description="number of registers",
        )
        return float(
            self._generic_command(
                functioncode,
                registeraddress,
                number_of_registers=number_of_registers,
                byteorder=byteorder,
                payloadformat=_Payloadformat.FLOAT,
            )
        )

    def write_float(
        self,
        registeraddress: int,
        value: Union[int, float],
        number_of_registers: int = 2,
        byteorder: int = BYTEORDER_BIG,
    ) -> None:
        """Write a floating point number to the slave.

        Floats are stored in two or more consecutive 16-bit registers in the slave.

        Uses Modbus function code 16.

        For discussion on precision, number of registers and on byte order,
        see :meth:`.read_float`.

        Args:
            * registeraddress: The slave register start address.
            * value (float or int): The value to store in the slave
            * number_of_registers: The number of registers allocated for the float.
              Can be 2 or 4.
            * byteorder: How multi-register data should be interpreted.
              Use the BYTEORDER_xxx constants. Defaults to
              :data:`minimalmodbus.BYTEORDER_BIG`.

        .. note:: The parameter number_of_registers was named numberOfRegisters
                  before MinimalModbus 1.0

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        _check_numerical(value, description="input value")
        _check_int(
            number_of_registers,
            minvalue=2,
            maxvalue=4,
            description="number of registers",
        )
        self._generic_command(
            16,
            registeraddress,
            value,
            number_of_registers=number_of_registers,
            byteorder=byteorder,
            payloadformat=_Payloadformat.FLOAT,
        )

    def read_string(
        self, registeraddress: int, number_of_registers: int = 16, functioncode: int = 3
    ) -> str:
        """Read an ASCII string from the slave.

        Each 16-bit register in the slave are interpreted as two characters
        (each 1 byte = 8 bits). For example 16 consecutive registers can hold 32
        characters (32 bytes).

        International characters (Unicode/UTF-8) are not supported.

        Args:
            * registeraddress: The slave register start address.
            * number_of_registers: The number of registers allocated for the string.
            * functioncode: Modbus function code. Can be 3 or 4.

        .. note:: The parameter number_of_registers was named numberOfRegisters
                  before MinimalModbus 1.0

        Returns:
            The string.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        _check_functioncode(functioncode, [3, 4])
        _check_int(
            number_of_registers,
            minvalue=1,
            maxvalue=_MAX_NUMBER_OF_REGISTERS_TO_READ,
            description="number of registers for read string",
        )
        return str(
            self._generic_command(
                functioncode,
                registeraddress,
                number_of_registers=number_of_registers,
                payloadformat=_Payloadformat.STRING,
            )
        )

    def write_string(
        self, registeraddress: int, textstring: str, number_of_registers: int = 16
    ) -> None:
        """Write an ASCII string to the slave.

        Each 16-bit register in the slave are interpreted as two characters
        (each 1 byte = 8 bits). For example 16 consecutive registers can hold 32
        characters (32 bytes).

        Uses Modbus function code 16.

        International characters (Unicode/UTF-8) are not supported.

        Args:
            * registeraddress: The slave register start address.
            * textstring: The string to store in the slave, must be ASCII.
            * number_of_registers: The number of registers allocated for the string.

        .. note:: The parameter number_of_registers was named numberOfRegisters
                  before MinimalModbus 1.0

        If the ``textstring`` is longer than the ``2*number_of_registers``, an
        error is raised. Shorter strings are padded with spaces.

        Returns:
            None

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        _check_int(
            number_of_registers,
            minvalue=1,
            maxvalue=_MAX_NUMBER_OF_REGISTERS_TO_WRITE,
            description="number of registers for write string",
        )
        _check_string(
            textstring,
            "input string",
            minlength=1,
            maxlength=2 * number_of_registers,
            force_ascii=True,
        )
        self._generic_command(
            16,
            registeraddress,
            textstring,
            number_of_registers=number_of_registers,
            payloadformat=_Payloadformat.STRING,
        )

    def read_registers(
        self, registeraddress: int, number_of_registers: int, functioncode: int = 3
    ) -> List[int]:
        """Read integers from 16-bit registers in the slave.

        The slave registers can hold integer values in the range 0 to
        65535 ("Unsigned INT16").

        Args:
            * registeraddress: The slave register start address.
            * number_of_registers: The number of registers to read, max 125 registers.
            * functioncode: Modbus function code. Can be 3 or 4.

        .. note:: The parameter number_of_registers was named numberOfRegisters
                  before MinimalModbus 1.0

        Any scaling of the register data, or converting it to negative number
        (two's complement) must be done manually.

        Returns:
            The register data. The first value in the list is for
            the register at the given address.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        _check_functioncode(functioncode, [3, 4])
        _check_int(
            number_of_registers,
            minvalue=1,
            maxvalue=_MAX_NUMBER_OF_REGISTERS_TO_READ,
            description="number of registers",
        )
        returnvalue = self._generic_command(
            functioncode,
            registeraddress,
            number_of_registers=number_of_registers,
            payloadformat=_Payloadformat.REGISTERS,
        )
        # Make sure that we really return a list of integers
        assert isinstance(returnvalue, list)
        return [int(x) for x in returnvalue]

    def write_registers(self, registeraddress: int, values: List[int]) -> None:
        """Write integers to 16-bit registers in the slave.

        The slave register can hold integer values in the range 0 to
        65535 ("Unsigned INT16").

        Uses Modbus function code 16.

        The number of registers that will be written is defined by the length of
        the ``values`` list.

        Args:
            * registeraddress: The slave register start address.
            * values: The values to store in the slave registers,
              max 123 values. The first value in the list is for the register
              at the given address.

        .. note:: The parameter number_of_registers was named numberOfRegisters
                  before MinimalModbus 1.0

        Any scaling of the register data, or converting it to negative number
        (two's complement) must be done manually.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        if not isinstance(values, list):
            raise TypeError(
                'The "values parameter" must be a list. Given: {0!r}'.format(values)
            )
        _check_int(
            len(values),
            minvalue=1,
            maxvalue=_MAX_NUMBER_OF_REGISTERS_TO_WRITE,
            description="length of input list",
        )
        # Note: The content of the list is checked at content conversion.

        self._generic_command(
            16,
            registeraddress,
            values,
            number_of_registers=len(values),
            payloadformat=_Payloadformat.REGISTERS,
        )

    # ############### #
    # Generic command #
    # ############### #

    def _generic_command(
        self,
        functioncode: int,
        registeraddress: int,
        value: Union[None, str, int, float, List[int]] = None,
        number_of_decimals: int = 0,
        number_of_registers: int = 0,
        number_of_bits: int = 0,
        signed: bool = False,
        byteorder: int = BYTEORDER_BIG,
        payloadformat: _Payloadformat = _Payloadformat.REGISTER,
    ) -> Any:
        """Perform generic command for reading and writing registers and bits.

        Args:
            * functioncode: Modbus function code.
            * registeraddress: The register address.
            * value (numerical or string or None or list of int): The value to store
              in the register. Depends on payloadformat.
            * number_of_decimals: The number of decimals for content conversion.
              Only for a single register.
            * number_of_registers: The number of registers to read/write.
              Only certain values allowed, depends on payloadformat.
            * number_of_bits: The number of bits to read/write.
            * signed: Whether the data should be interpreted as unsigned or signed.
              Only for a single register or for payloadformat='long'.
            * byteorder: How multi-register data should be interpreted.
            * payloadformat: An _Payloadformat enum

        If a value of 77.0 is stored internally in the slave register as 770,
        then use ``number_of_decimals=1`` which will divide the received data
        from the slave by 10 before returning the value. Similarly
        ``number_of_decimals=2`` will divide the received data by 100 before returning
        the value. Same functionality is also used when writing data to the slave.

        Returns:
            The register data in numerical value (int or float), or the bit value 0 or
            1 (int), or a list of int, or ``None``.

            Returns ``None`` for all write function codes.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)
        """
        ALL_ALLOWED_FUNCTIONCODES = [1, 2, 3, 4, 5, 6, 15, 16]
        ALLOWED_FUNCTIONCODES_BROADCAST = [5, 6, 15, 16]
        ALLOWED_FUNCTIONCODES = {}
        ALLOWED_FUNCTIONCODES[_Payloadformat.BIT] = [1, 2, 5, 15]
        ALLOWED_FUNCTIONCODES[_Payloadformat.BITS] = [1, 2, 15]
        ALLOWED_FUNCTIONCODES[_Payloadformat.REGISTER] = [3, 4, 6, 16]
        ALLOWED_FUNCTIONCODES[_Payloadformat.FLOAT] = [3, 4, 16]
        ALLOWED_FUNCTIONCODES[_Payloadformat.STRING] = [3, 4, 16]
        ALLOWED_FUNCTIONCODES[_Payloadformat.LONG] = [3, 4, 16]
        ALLOWED_FUNCTIONCODES[_Payloadformat.REGISTERS] = [3, 4, 16]

        # Check input values
        _check_functioncode(functioncode, ALL_ALLOWED_FUNCTIONCODES)
        _check_registeraddress(registeraddress)
        _check_int(
            number_of_decimals,
            minvalue=0,
            maxvalue=_MAX_NUMBER_OF_DECIMALS,
            description="number of decimals",
        )
        _check_int(
            number_of_registers,
            minvalue=0,
            maxvalue=max(
                _MAX_NUMBER_OF_REGISTERS_TO_READ, _MAX_NUMBER_OF_REGISTERS_TO_WRITE
            ),
            description="number of registers",
        )
        _check_int(
            number_of_bits,
            minvalue=0,
            maxvalue=max(_MAX_NUMBER_OF_BITS_TO_READ, _MAX_NUMBER_OF_BITS_TO_WRITE),
            description="number of bits",
        )
        _check_bool(signed, description="signed")
        _check_int(
            byteorder,
            minvalue=0,
            maxvalue=_MAX_BYTEORDER_VALUE,
            description="byteorder",
        )

        if not isinstance(payloadformat, _Payloadformat):
            raise TypeError(
                "The payload format should be an enum of type _Payloadformat. "
                + "Given: {!r}".format(payloadformat)
            )

        number_of_register_bytes = number_of_registers * _NUMBER_OF_BYTES_PER_REGISTER

        # Check combinations: Payload format and functioncode
        if functioncode not in ALLOWED_FUNCTIONCODES[payloadformat]:
            raise ValueError(
                "Wrong functioncode for payloadformat "
                + "{!r}. Given: {!r}.".format(payloadformat, functioncode)
            )

        # Check combinations: Broadcast and functioncode
        if (
            self.address == _SLAVEADDRESS_BROADCAST
            and functioncode not in ALLOWED_FUNCTIONCODES_BROADCAST
        ):
            raise ValueError(
                f"Wrong functioncode for broadcast. Given: {functioncode!r}"
            )

        # Check combinations: signed
        if signed:
            if payloadformat not in [_Payloadformat.REGISTER, _Payloadformat.LONG]:
                raise ValueError(
                    'The "signed" parameter can not be used for this payload format. '
                    + "Given format: {!r}.".format(payloadformat)
                )

        # Check combinations: number_of_decimals
        if number_of_decimals > 0:
            if payloadformat != _Payloadformat.REGISTER:
                raise ValueError(
                    'The "number_of_decimals" parameter can not be used for this '
                    + "payload format. Given format: {0!r}.".format(payloadformat)
                )

        # Check combinations: byteorder
        if byteorder:
            if payloadformat not in [_Payloadformat.FLOAT, _Payloadformat.LONG]:
                raise ValueError(
                    'The "byteorder" parameter can not be used for this payload'
                    + " format. Given format: {0!r}.".format(payloadformat)
                )

        # Check combinations: number of bits
        if payloadformat == _Payloadformat.BIT:
            if number_of_bits != 1:
                raise ValueError(
                    "For BIT payload format the number of bits should be 1. "
                    + "Given: {0!r}.".format(number_of_bits)
                )
        elif payloadformat == _Payloadformat.BITS:
            if number_of_bits < 1:
                raise ValueError(
                    "For BITS payload format the number of bits should be at least 1. "
                    + "Given: {0!r}.".format(number_of_bits)
                )
        elif number_of_bits:
            raise ValueError(
                "The number_of_bits parameter is wrong for payload format "
                + "{0!r}. Given: {1!r}.".format(payloadformat, number_of_bits)
            )

        # Check combinations: Number of registers
        if functioncode in [1, 2, 5, 15] and number_of_registers:
            raise ValueError(
                "The number_of_registers is not valid for this function code. "
                + "number_of_registers: {0!r}, functioncode {1}.".format(
                    number_of_registers, functioncode
                )
            )
        if functioncode in [3, 4, 16] and not number_of_registers:
            raise ValueError(
                "The number_of_registers must be > 0 for functioncode "
                + "{}.".format(functioncode)
            )
        if functioncode == 6 and number_of_registers != 1:
            raise ValueError(
                "The number_of_registers must be 1 for functioncode 6. "
                + "Given: {}.".format(number_of_registers)
            )
        if (
            functioncode == 16
            and payloadformat == _Payloadformat.REGISTER
            and number_of_registers != 1
        ):
            raise ValueError(
                "Wrong number_of_registers when writing to a "
                + "single register. Given {0!r}.".format(number_of_registers)
            )
            # Note: For function code 16 there is checking also in the content
            # conversion functions.

        # Number of registers for float and long
        if payloadformat == _Payloadformat.FLOAT and number_of_registers not in [2, 4]:
            raise ValueError(
                "The number of registers for float must be 2 or 4. "
                + "Given {0!r}".format(number_of_registers)
            )
        if payloadformat == _Payloadformat.LONG and number_of_registers not in [2, 4]:
            raise ValueError(
                "The number of registers for long must be 2 or 4. "
                + "Given {0!r}".format(number_of_registers)
            )

        # Check combinations: Value
        if functioncode in [5, 6, 15, 16] and value is None:
            raise ValueError(
                "The input value must be given for this function code. "
                + "Given {0!r} and {1}.".format(value, functioncode)
            )
        if functioncode in [1, 2, 3, 4] and value is not None:
            raise ValueError(
                "The input value should not be given for this function code. "
                + "Given {0!r} and {1}.".format(value, functioncode)
            )

        # Check combinations: Value for numerical
        if (
            functioncode == 16
            and payloadformat
            in [
                _Payloadformat.REGISTER,
                _Payloadformat.FLOAT,
                _Payloadformat.LONG,
            ]
        ) or (functioncode == 6 and payloadformat == _Payloadformat.REGISTER):
            if not isinstance(value, (int, float)):
                raise TypeError(f"The input value must be numerical. Given: {value!r}")

        # Check combinations: Value for string
        if functioncode == 16 and payloadformat == _Payloadformat.STRING:
            if not isinstance(value, str):
                raise TypeError(f"The input should be a string. Given: {value!r}")
            _check_string(
                value, "input string", minlength=1, maxlength=number_of_register_bytes
            )
            # Note: The string might be padded later, so the length might be shorter
            # than number_of_register_bytes.

        # Check combinations: Value for registers
        if functioncode == 16 and payloadformat == _Payloadformat.REGISTERS:
            if not isinstance(value, list):
                raise TypeError(
                    "The value parameter for payloadformat REGISTERS must be a list. "
                    + "Given {0!r}.".format(value)
                )

            if len(value) != number_of_registers:
                raise ValueError(
                    "The list length does not match number of registers. "
                    + "List: {0!r},  Number of registers: {1!r}.".format(
                        value, number_of_registers
                    )
                )

        # Check combinations: Value for bit
        if functioncode in [5, 15] and payloadformat == _Payloadformat.BIT:
            if not isinstance(value, int):
                raise TypeError(f"The input should be an integer. Given: {value!r}")
            _check_int(
                value,
                minvalue=0,
                maxvalue=1,
                description="input value for payload format BIT",
            )

        # Check combinations: Value for bits
        if functioncode == 15 and payloadformat == _Payloadformat.BITS:
            if not isinstance(value, list):
                raise TypeError(
                    "The value parameter for payloadformat BITS must be a list. "
                    + "Given {0!r}.".format(value)
                )

            if len(value) != number_of_bits:
                raise ValueError(
                    "The list length does not match number of bits. "
                    + "List: {0!r},  Number of registers: {1!r}.".format(
                        value, number_of_registers
                    )
                )

        # Create payload
        payload_to_slave = _create_payload(
            functioncode,
            registeraddress,
            value,
            number_of_decimals,
            number_of_registers,
            number_of_bits,
            signed,
            byteorder,
            payloadformat,
        )

        # Communicate with instrument
        payload_from_slave = self._perform_command(functioncode, payload_to_slave)

        # There is no response for broadcasts
        if self.address == _SLAVEADDRESS_BROADCAST:
            return None

        # Parse response payload
        return _parse_payload(
            payload_from_slave,
            functioncode,
            registeraddress,
            value,
            number_of_decimals,
            number_of_registers,
            number_of_bits,
            signed,
            byteorder,
            payloadformat,
        )

    # #################################### #
    # Communication implementation details #
    # #################################### #

    def _perform_command(self, functioncode: int, payload_to_slave: bytes) -> bytes:
        """Perform the command having the *functioncode*.

        Args:
            * functioncode: The function code for the command to be performed.
              Can for example be 'Write register' = 16.
            * payload_to_slave: Data to be transmitted to the slave (will be
              embedded in slaveaddress, CRC etc)

        Returns:
            The extracted data payload from the slave. It has been
            stripped of CRC etc.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)

        Makes use of the :meth:`_communicate` method. The request is generated
        with the :func:`_embed_payload` function, and the parsing of the
        response is done with the :func:`_extract_payload` function.
        """
        DEFAULT_NUMBER_OF_BYTES_TO_READ = 1000

        _check_functioncode(functioncode, None)
        _check_bytes(payload_to_slave, description="payload")

        # Build request
        request_bytes = _embed_payload(
            self.address, self.mode, functioncode, payload_to_slave
        )

        # Calculate number of bytes to read
        number_of_bytes_to_read = DEFAULT_NUMBER_OF_BYTES_TO_READ
        if self.address == _SLAVEADDRESS_BROADCAST:
            number_of_bytes_to_read = 0
        elif self.precalculate_read_size:
            try:
                number_of_bytes_to_read = _predict_response_size(
                    self.mode, functioncode, payload_to_slave
                )
            except Exception:
                if self.debug:
                    template = (
                        "Could not precalculate response size for Modbus {} mode. "
                        + "Will read {} bytes. Request: {!r}"
                    )
                    self._print_debug(
                        template.format(
                            self.mode, number_of_bytes_to_read, request_bytes
                        )
                    )

        # Communicate
        response_bytes = self._communicate(request_bytes, number_of_bytes_to_read)

        if number_of_bytes_to_read == 0:
            return b""

        # Extract payload
        payload_from_slave = _extract_payload(
            response_bytes, self.address, self.mode, functioncode
        )
        return payload_from_slave

    def _communicate(self, request: bytes, number_of_bytes_to_read: int) -> bytes:
        """Talk to the slave via a serial port.

        Args:
            * request: The raw request that is to be sent to the slave.
            * number_of_bytes_to_read: Number of bytes to read

        Returns:
            The raw data returned from the slave.

        Raises:
            TypeError, ValueError, ModbusException,
            serial.SerialException (inherited from IOError)

        Sleeps if the previous message arrived less than the "silent period" ago.

        Will block until reaching *number_of_bytes_to_read* or timeout.

        Additional delay will be used after broadcast transmissions (slave address 0).

        If the attribute :attr:`Instrument.debug` is :const:`True`, the communication
        details are printed.

        If the attribute :attr:`Instrument.close_port_after_each_call` is :const:`True`
        the serial port is closed after each call.

        Timing::

                            Request from master (Master is writing)
                            |
                            |                             Response from slave
                            |                             (Master is reading)
                            |                             |
            --------R-------W-----------------------------R-------W--------------------
                     |     |                               |
                     |     |<------- Roundtrip time ------>|
                     |     |
                  -->|-----|<----- Silent period

        The resolution for Python's :py:func:`time.time()` is lower on Windows than
        on Linux.
        It is about 16 ms on Windows according to
        stackoverflow.com/questions/157359/accurate-timestamping-in-python-logging
        """
        _check_bytes(request, minlength=1, description="request")
        _check_int(number_of_bytes_to_read)

        self._print_debug(
            "Will write to instrument (expecting {} bytes back): {}".format(
                number_of_bytes_to_read, _describe_bytes(request)
            )
        )

        if self.serial is None:
            raise ModbusException("The serial port instance is None")

        if not self.serial.is_open:
            self._print_debug("Opening port {}".format(self.serial.port))
            self.serial.open()

        portname: str = ""
        if self.serial.port is not None:
            portname = self.serial.port

        if self.clear_buffers_before_each_transaction:
            self._print_debug("Clearing serial buffers for port {}".format(portname))
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()

        # Sleep to make sure 3.5 character times have passed
        minimum_silent_period = _calculate_minimum_silent_period(self.serial.baudrate)
        time_since_read = time.monotonic() - _latest_read_times.get(portname, 0)

        if time_since_read < minimum_silent_period:
            sleep_time = minimum_silent_period - time_since_read

            if self.debug:
                template = (
                    "Sleeping {:.2f} ms before sending. "
                    + "Minimum silent period: {:.2f} ms, time since read: {:.2f} ms."
                )
                text = template.format(
                    sleep_time * _SECONDS_TO_MILLISECONDS,
                    minimum_silent_period * _SECONDS_TO_MILLISECONDS,
                    time_since_read * _SECONDS_TO_MILLISECONDS,
                )
                self._print_debug(text)

            time.sleep(sleep_time)

        elif self.debug:
            template = (
                "No sleep required before write. Time since "
                + "previous read: {:.2f} ms, minimum silent period: {:.2f} ms."
            )
            text = template.format(
                time_since_read * _SECONDS_TO_MILLISECONDS,
                minimum_silent_period * _SECONDS_TO_MILLISECONDS,
            )
            self._print_debug(text)

        # Write request
        write_time = time.monotonic()
        self.serial.write(request)

        # Read and discard local echo
        if self.handle_local_echo:
            local_echo_to_discard = self.serial.read(len(request))
            if self.debug:
                text = "Discarding this local echo: {}".format(
                    _describe_bytes(local_echo_to_discard),
                )
                self._print_debug(text)
            if local_echo_to_discard != request:
                template = (
                    "Local echo handling is enabled, but the local echo does "
                    + "not match the sent request. "
                    + "Request: {}, local echo: {}."
                )
                text = template.format(
                    _describe_bytes(request),
                    _describe_bytes(local_echo_to_discard),
                )
                raise LocalEchoError(text)

        # Read response
        if number_of_bytes_to_read > 0:
            answer = self.serial.read(number_of_bytes_to_read)
        else:
            answer = b""
            self.serial.flush()

        read_time = time.monotonic()
        _latest_read_times[portname] = read_time
        roundtrip_time = read_time - write_time
        self._latest_roundtrip_time = roundtrip_time

        if self.close_port_after_each_call:
            self._print_debug("Closing port {}".format(portname))
            self.serial.close()

        if self.debug:
            if isinstance(self.serial.timeout, float):
                timeout_time = self.serial.timeout * _SECONDS_TO_MILLISECONDS
            else:
                timeout_time = 0
            text = (
                "Response from instrument: {}, roundtrip time: {:.1f} ms."
                " Timeout for reading: {:.1f} ms.\n"
            ).format(
                _describe_bytes(answer),
                roundtrip_time,
                timeout_time,
            )
            self._print_debug(text)

        if not answer and number_of_bytes_to_read > 0:
            raise NoResponseError("No communication with the instrument (no answer)")

        if number_of_bytes_to_read == 0:
            self._print_debug(
                "Broadcast delay: Sleeping for {} s".format(_BROADCAST_DELAY)
            )
            time.sleep(_BROADCAST_DELAY)

        return answer


# ########## #
# Exceptions #
# ########## #


class ModbusException(IOError):
    """Base class for Modbus communication exceptions.

    Inherits from IOError, which is an alias for OSError in Python3.
    """


class SlaveReportedException(ModbusException):
    """Base class for exceptions that the slave (instrument) reports."""


class SlaveDeviceBusyError(SlaveReportedException):
    """The slave is busy processing some command."""


class NegativeAcknowledgeError(SlaveReportedException):
    """The slave can not fulfil the programming request.

    This typically happens when using function code 13 or 14 decimal.
    """


class IllegalRequestError(SlaveReportedException):
    """The slave has received an illegal request."""


class MasterReportedException(ModbusException):
    """Base class for exceptions that the master (computer) detects."""


class NoResponseError(MasterReportedException):
    """No response from the slave."""


class LocalEchoError(MasterReportedException):
    """There is some problem with the local echo."""


class InvalidResponseError(MasterReportedException):
    """The response does not fulfill the Modbus standad, for example wrong checksum."""


# ################ #
# Payload handling #
# ################ #


def _create_payload(
    functioncode: int,
    registeraddress: int,
    value: Union[None, str, int, float, List[int]],
    number_of_decimals: int,
    number_of_registers: int,
    number_of_bits: int,
    signed: bool,
    byteorder: int,
    payloadformat: _Payloadformat,
) -> bytes:
    """Create the payload.

    Error checking should have been done before calling this function.

    For argument descriptions, see the :py:meth:`_generic_command` method.
    """
    if functioncode in [1, 2]:
        return _num_to_two_bytes(registeraddress) + _num_to_two_bytes(number_of_bits)
    if functioncode in [3, 4]:
        return _num_to_two_bytes(registeraddress) + _num_to_two_bytes(
            number_of_registers
        )
    if functioncode == 5:
        assert isinstance(value, int)
        return _num_to_two_bytes(registeraddress) + _bit_to_bytes(value)
    if functioncode == 6:
        assert isinstance(value, (int, float))
        return _num_to_two_bytes(registeraddress) + _num_to_two_bytes(
            value, number_of_decimals, signed=signed
        )
    if functioncode == 15:
        if payloadformat == _Payloadformat.BIT and isinstance(value, int):
            bitlist = [value]
        elif payloadformat == _Payloadformat.BITS and isinstance(value, list):
            bitlist = value
        else:
            raise ValueError(
                f"Wrong payloadformat {payloadformat} or type "
                + "for the value for function code 15"
            )
        number_of_bytes_for_bits = _calculate_number_of_bytes_for_bits(number_of_bits)
        return (
            _num_to_two_bytes(registeraddress)
            + _num_to_two_bytes(number_of_bits)
            + number_of_bytes_for_bits.to_bytes(1, "big")
            + _bits_to_bytes(bitlist)
        )
    if functioncode == 16:
        if payloadformat == _Payloadformat.REGISTER:
            assert isinstance(value, (int, float))
            registerdata = _num_to_two_bytes(value, number_of_decimals, signed=signed)
        elif payloadformat == _Payloadformat.STRING:
            assert isinstance(value, str)
            registerdata = _textstring_to_bytes(value, number_of_registers)
        elif payloadformat == _Payloadformat.LONG:
            assert isinstance(value, int)
            registerdata = _long_to_bytes(value, signed, number_of_registers, byteorder)
        elif payloadformat == _Payloadformat.FLOAT:
            assert isinstance(value, float) or isinstance(value, int)
            registerdata = _float_to_bytes(value, number_of_registers, byteorder)
        elif payloadformat == _Payloadformat.REGISTERS:
            assert isinstance(value, list)
            registerdata = _valuelist_to_bytes(value, number_of_registers)
        else:
            raise ValueError(
                f"Wrong payloadformat '{payloadformat}' for function code 16"
            )
        assert len(registerdata) == number_of_registers * _NUMBER_OF_BYTES_PER_REGISTER

        registerdata_bytecount = len(registerdata)
        return (
            _num_to_two_bytes(registeraddress)
            + _num_to_two_bytes(number_of_registers)
            + registerdata_bytecount.to_bytes(1, "big")
            + registerdata
        )
    raise ValueError("Wrong function code: " + str(functioncode))


def _parse_payload(
    payload: bytes,
    functioncode: int,
    registeraddress: int,
    value: Any,
    number_of_decimals: int,
    number_of_registers: int,
    number_of_bits: int,
    signed: bool,
    byteorder: int,
    payloadformat: _Payloadformat,
) -> Union[None, str, int, float, List[int], List[float]]:
    """Extract the payload data from a response.

    Args:
        * payload:              Payload to be parsed
        * functioncode:         Function code
        * registeraddress:      Register address for error checking
        * value:                Value in request, for error checking
        * number_of_decimals:   Number of decimals
        * number_of_registers:  Number of registers
        * number_of_bits:       Number of bits
        * signed:               Signed
        * byteorder:            Byte order
        * payloadformat:        Payload format

    Returns:
        The parsed payload.
    """
    _check_response_payload(
        payload,
        functioncode,
        registeraddress,
        value,
        number_of_decimals,
        number_of_registers,
        number_of_bits,
        signed,
        byteorder,
        payloadformat,
    )

    if functioncode in [1, 2]:
        registerdata = payload[_NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
        if payloadformat == _Payloadformat.BIT:
            return _bytes_to_bits(registerdata, number_of_bits)[0]
        if payloadformat == _Payloadformat.BITS:
            return _bytes_to_bits(registerdata, number_of_bits)

    if functioncode in [3, 4]:
        registerdata = payload[_NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
        if payloadformat == _Payloadformat.STRING:
            return _bytes_to_textstring(registerdata, number_of_registers)

        if payloadformat == _Payloadformat.LONG:
            return _bytes_to_long(registerdata, signed, number_of_registers, byteorder)

        if payloadformat == _Payloadformat.FLOAT:
            return _bytes_to_float(registerdata, number_of_registers, byteorder)

        if payloadformat == _Payloadformat.REGISTERS:
            return _bytes_to_valuelist(registerdata, number_of_registers)

        if payloadformat == _Payloadformat.REGISTER:
            return _two_bytes_to_num(registerdata, number_of_decimals, signed=signed)

    if functioncode in [5, 6, 15, 16]:
        # Response to write
        return None

    raise ValueError(
        f"Wrong function code {functioncode} and payloadformat {payloadformat!r}"
        + " combination"
    )


def _embed_payload(
    slaveaddress: int, mode: str, functioncode: int, payloaddata: bytes
) -> bytes:
    """Build a request from the slaveaddress, the function code and the payload data.

    Args:
        * slaveaddress: The address of the slave.
        * mode: The modbus protcol mode (MODE_RTU or MODE_ASCII)
        * functioncode: The function code for the command to be performed.
          Can for example be 16 (Write register).
        * payloaddata: The bytes to be sent to the slave.

    Returns:
        The built (raw) request for sending to the slave (including CRC etc).

    Raises:
        ValueError, TypeError.

    The resulting request has the format:
     * RTU Mode: slaveaddress byte + functioncode byte + payloaddata + CRC (two bytes).
     * ASCII Mode: header (``:``) + slaveaddress (2 characters) + functioncode
       (2 characters) + payloaddata + LRC (which is two characters) + footer (CR+LF)

    The LRC or CRC is calculated from the bytes made up of slaveaddress +
    functioncode + payloaddata.
    The header, LRC/CRC, and footer are excluded from the calculation.
    """
    _check_slaveaddress(slaveaddress)
    _check_mode(mode)
    _check_functioncode(functioncode, None)
    _check_bytes(payloaddata, description="payload")

    first_part = (
        _num_to_one_byte(slaveaddress) + _num_to_one_byte(functioncode) + payloaddata
    )

    if mode == MODE_ASCII:
        request = (
            _ASCII_HEADER
            + _hexencode(first_part)
            + _hexencode(_calculate_lrc(first_part))
            + _ASCII_FOOTER
        )
    else:
        request = first_part + _calculate_crc(first_part)

    return request


def _extract_payload(
    response: bytes, slaveaddress: int, mode: str, functioncode: int
) -> bytes:
    """Extract the payload data part from the slave's response.

    Args:
        * response: The raw response bytes from the slave.
          This is different for RTU and ASCII.
        * slaveaddress: The adress of the slave. Used here for error checking only.
        * mode: The modbus protocol mode (MODE_RTU or MODE_ASCII)
        * functioncode: Used here for error checking only.

    Returns:
        The payload part of the *response*. Conversion from Modbus ASCII
        has been done if applicable.

    Raises:
        ValueError, TypeError, ModbusException (or subclasses).

    Raises an exception if there is any problem with the received address,
    the functioncode or the CRC.

    The received response should have the format:

    * RTU Mode: slaveaddress byte + functioncode byte + payloaddata + CRC (two bytes)
    * ASCII Mode: header (``:``) + slaveaddress byte + functioncode byte +
      payloaddata + LRC (which is two characters) + footer (CR+LF)

    For development purposes, this function can also be used to extract the payload
    from the request sent **to** the slave.
    """
    # Number of bytes before the response payload (in stripped response)
    NUMBER_OF_RESPONSE_STARTBYTES = 2

    NUMBER_OF_CRC_BYTES = 2
    NUMBER_OF_LRC_BYTES = 1
    MINIMAL_RESPONSE_LENGTH_RTU = NUMBER_OF_RESPONSE_STARTBYTES + NUMBER_OF_CRC_BYTES
    MINIMAL_RESPONSE_LENGTH_ASCII = 9

    # Argument validity testing (ValueError/TypeError at lib programming error)
    _check_bytes(response, description="response")
    _check_slaveaddress(slaveaddress)
    _check_mode(mode)
    _check_functioncode(functioncode, None)

    plainresponse = response

    # Validate response length
    if mode == MODE_ASCII:
        if len(response) < MINIMAL_RESPONSE_LENGTH_ASCII:
            raise InvalidResponseError(
                "Too short Modbus ASCII response (minimum "
                + "length {} bytes). Response: {!r}".format(
                    MINIMAL_RESPONSE_LENGTH_ASCII, response
                )
            )
    elif len(response) < MINIMAL_RESPONSE_LENGTH_RTU:
        raise InvalidResponseError(
            "Too short Modbus RTU response (minimum "
            + "length {} bytes). Response: {!r}".format(
                MINIMAL_RESPONSE_LENGTH_RTU, response
            )
        )

    if mode == MODE_ASCII:
        # Validate the ASCII header and footer.
        if response[_BYTEPOSITION_FOR_ASCII_HEADER].to_bytes(1, "big") != _ASCII_HEADER:
            raise InvalidResponseError(
                "Did not find header ({!r}) as start ".format(_ASCII_HEADER)
                + "of ASCII response. The plain response is: {!r}".format(response)
            )
        if response[-len(_ASCII_FOOTER) :] != _ASCII_FOOTER:
            raise InvalidResponseError(
                "Did not find footer "
                + "({!r}) as end of ASCII response. The plain response is: {!r}".format(
                    _ASCII_FOOTER, response
                )
            )

        # Strip ASCII header and footer
        response = response[1:-2]

        if len(response) % 2 != 0:
            template = (
                "Stripped ASCII frames should have an even "
                + "number of bytes, but is {} bytes. "
                + "The stripped response is: {!r} (plain response: {!r})"
            )
            raise InvalidResponseError(
                template.format(len(response), response, plainresponse)
            )

        # Convert the ASCII (stripped) response string to RTU-like response string
        response = _hexdecode(response)

    # Validate response checksum
    if mode == MODE_ASCII:
        calculate_checksum = _calculate_lrc
        number_of_checksum_bytes = NUMBER_OF_LRC_BYTES
    else:
        calculate_checksum = _calculate_crc
        number_of_checksum_bytes = NUMBER_OF_CRC_BYTES

    received_checksum = response[-number_of_checksum_bytes:]
    response_without_checksum = response[0 : (len(response) - number_of_checksum_bytes)]
    calculated_checksum = calculate_checksum(response_without_checksum)

    if received_checksum != calculated_checksum:
        template = (
            "Checksum error in {} mode: {!r} instead of {!r} . The response "
            + "is: {!r} (plain response: {!r})"
        )
        text = template.format(
            mode, received_checksum, calculated_checksum, response, plainresponse
        )
        raise InvalidResponseError(text)

    # Check slave address
    responseaddress = response[_BYTEPOSITION_FOR_SLAVEADDRESS]

    if responseaddress != slaveaddress:
        raise InvalidResponseError(
            "Wrong return slave "
            + "address: {} instead of {}. The response is: {!r}".format(
                responseaddress, slaveaddress, response
            )
        )

    # Check if slave indicates error
    _check_response_slaveerrorcode(response)

    # Check function code
    received_functioncode = response[_BYTEPOSITION_FOR_FUNCTIONCODE]
    if received_functioncode != functioncode:
        raise InvalidResponseError(
            "Wrong functioncode: {} instead of {}. The response is: {!r}".format(
                received_functioncode, functioncode, response
            )
        )

    # Read data payload
    first_databyte_number = NUMBER_OF_RESPONSE_STARTBYTES

    if mode == MODE_ASCII:
        last_databyte_number = len(response) - NUMBER_OF_LRC_BYTES
    else:
        last_databyte_number = len(response) - NUMBER_OF_CRC_BYTES

    payload = response[first_databyte_number:last_databyte_number]
    return payload


# ###################################### #
# Serial communication utility functions #
# ###################################### #


def _predict_response_size(
    mode: str, functioncode: int, payload_to_slave: bytes
) -> int:
    """Calculate the number of bytes that should be received from the slave.

    Args:
     * mode: The modbus protcol mode (MODE_RTU or MODE_ASCII)
     * functioncode: Modbus function code.
     * payload_to_slave: The raw request that is to be sent to the slave
       (not hex encoded)

    Returns:
        The predicted number of bytes in the response.

    Raises:
        ValueError, TypeError.
    """
    MIN_PAYLOAD_LENGTH = 4  # For the functioncodes implemented here
    BYTERANGE_FOR_GIVEN_SIZE = slice(2, 4)  # Within the payload

    NUMBER_OF_PAYLOAD_BYTES_IN_WRITE_CONFIRMATION = 4
    NUMBER_OF_PAYLOAD_BYTES_FOR_BYTECOUNTFIELD = 1

    RTU_TO_ASCII_PAYLOAD_FACTOR = 2

    NUMBER_OF_RTU_RESPONSE_STARTBYTES = 2
    NUMBER_OF_RTU_RESPONSE_ENDBYTES = 2
    NUMBER_OF_ASCII_RESPONSE_STARTBYTES = 5
    NUMBER_OF_ASCII_RESPONSE_ENDBYTES = 4

    # Argument validity testing
    _check_mode(mode)
    _check_functioncode(functioncode, None)
    _check_bytes(payload_to_slave, description="payload", minlength=MIN_PAYLOAD_LENGTH)

    # Calculate payload size
    if functioncode in [5, 6, 15, 16]:
        response_payload_size = NUMBER_OF_PAYLOAD_BYTES_IN_WRITE_CONFIRMATION

    elif functioncode in [1, 2, 3, 4]:
        given_size = int(_two_bytes_to_num(payload_to_slave[BYTERANGE_FOR_GIVEN_SIZE]))
        if functioncode in [1, 2]:
            # Algorithm from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
            number_of_inputs = given_size
            response_payload_size = (
                NUMBER_OF_PAYLOAD_BYTES_FOR_BYTECOUNTFIELD
                + number_of_inputs // 8
                + (1 if number_of_inputs % 8 else 0)
            )

        else:
            number_of_registers = given_size
            response_payload_size = (
                NUMBER_OF_PAYLOAD_BYTES_FOR_BYTECOUNTFIELD
                + number_of_registers * _NUMBER_OF_BYTES_PER_REGISTER
            )

    else:
        raise ValueError(
            "Wrong functioncode: {}. The payload is: {!r}".format(
                functioncode, payload_to_slave
            )
        )

    # Calculate number of bytes to read
    if mode == MODE_ASCII:
        return (
            NUMBER_OF_ASCII_RESPONSE_STARTBYTES
            + response_payload_size * RTU_TO_ASCII_PAYLOAD_FACTOR
            + NUMBER_OF_ASCII_RESPONSE_ENDBYTES
        )
    return (
        NUMBER_OF_RTU_RESPONSE_STARTBYTES
        + response_payload_size
        + NUMBER_OF_RTU_RESPONSE_ENDBYTES
    )


def _calculate_minimum_silent_period(baudrate: Union[int, float]) -> float:
    """Calculate the silent period length between messages.

    It should correspond to the time to send 3.5 characters.

    Args:
        baudrate: The baudrate for the serial port

    Returns:
        The number of seconds that should pass between each message on the bus.

    Raises:
        ValueError, TypeError.
    """
    # Avoid division by zero
    _check_numerical(baudrate, minvalue=1, description="baudrate")

    BITTIMES_PER_CHARACTERTIME = 11
    MINIMUM_SILENT_CHARACTERTIMES = 3.5
    MINIMUM_SILENT_TIME_SECONDS = 0.00175  # See Modbus standard

    bittime = 1 / float(baudrate)
    return max(
        bittime * BITTIMES_PER_CHARACTERTIME * MINIMUM_SILENT_CHARACTERTIMES,
        MINIMUM_SILENT_TIME_SECONDS,
    )


# ########################## #
# String and num conversions #
# ########################## #


def _num_to_one_byte(inputvalue: int) -> bytes:
    """Convert a numerical value to one byte.

    Args:
        inputvalue: The value to be converted. Should be >=0 and <=255.

    Returns:
        One byte representing the inputvalue.

    Raises:
        TypeError, ValueError
    """
    _check_int(inputvalue, minvalue=0, maxvalue=0xFF)

    return inputvalue.to_bytes(1, "big")


def _num_to_two_bytes(
    value: Union[int, float],
    number_of_decimals: int = 0,
    lsb_first: bool = False,
    signed: bool = False,
) -> bytes:
    r"""Convert a numerical value to two bytes, possibly scaling it.

    Args:
        * value: The numerical value to be converted.
        * number_of_decimals: Number of decimals, 0 or more, for scaling.
        * lsb_first: Whether the least significant byte should be first in
          the resulting string.
        * signed: Whether negative values should be accepted.

    Returns:
        Two bytes representing the inputvalue.

    Raises:
        TypeError, ValueError.

    Use ``number_of_decimals=1`` to multiply ``value`` by 10 before sending it to
    the slave register. Similarly ``number_of_decimals=2`` will multiply ``value``
    by 100 before sending it to the slave register.

    Use the parameter ``signed=True`` if making a bytes object that can hold
    negative values. Then negative input will be automatically converted into
    upper range data (two's complement).

    The byte order is controlled by the ``lsb_first`` parameter, as seen here:

    ======================= ============= ====================================
    ``lsb_first`` parameter Endianness    Description
    ======================= ============= ====================================
    False (default)         Big-endian    Most significant byte is sent first
    True                    Little-endian Least significant byte is sent first
    ======================= ============= ====================================

    For example:
        To store for example value=77.0, use ``number_of_decimals = 1`` if the
        register will hold it as 770 internally. The value 770 (dec) is 0302 (hex),
        where the most significant byte is 03 (hex) and the least significant byte
        is 02 (hex). With ``lsb_first = False``, the most significant byte is
        given first why the resulting bytes are ``\x03\x02``, which has the length 2.
    """
    _check_numerical(value, description="inputvalue")
    _check_int(
        number_of_decimals,
        minvalue=0,
        maxvalue=_MAX_NUMBER_OF_DECIMALS,
        description="number of decimals",
    )
    _check_bool(lsb_first, description="lsb_first")
    _check_bool(signed, description="signed parameter")

    multiplier = 10**number_of_decimals
    integer = int(float(value) * multiplier)

    if lsb_first:
        formatcode = "<"  # Little-endian
    else:
        formatcode = ">"  # Big-endian
    if signed:
        formatcode += "h"  # (Signed) short (2 bytes)
    else:
        formatcode += "H"  # Unsigned short (2 bytes)

    outbytes = _pack_bytes(formatcode, integer)
    assert len(outbytes) == 2
    return outbytes


def _two_bytes_to_num(
    inputbytes: bytes, number_of_decimals: int = 0, signed: bool = False
) -> Union[int, float]:
    r"""Convert two bytes to a numerical value, possibly scaling it.

    Args:
        * inputbytes: Bytes of length 2.
        * number_of_decimals: The number of decimals. Defaults to 0.
        * signed: Whether large positive values should be interpreted as
          negative values.

    Returns:
        The numerical value (int or float) calculated from the ``inputbytes``.

    Raises:
        TypeError, ValueError

    Use the parameter ``signed=True`` if converting bytes that can hold
    negative values. Then upper range data will be automatically converted into
    negative return values (two's complement).

    Use ``number_of_decimals=1`` to divide the received data by 10 before returning
    the value. Similarly ``number_of_decimals=2`` will divide the received data by
    100 before returning the value.

    The byte order is big-endian, meaning that the most significant byte is sent first.

    For example:
        The bytes ``\x03\x02`` (which has the length 2) corresponds to 0302 (hex) =
        770 (dec). If ``number_of_decimals = 1``, then this is converted
        to 77.0 (float).
    """
    _check_bytes(inputbytes, minlength=2, maxlength=2, description="inputbytes")
    _check_int(
        number_of_decimals,
        minvalue=0,
        maxvalue=_MAX_NUMBER_OF_DECIMALS,
        description="number of decimals",
    )
    _check_bool(signed, description="signed parameter")

    formatcode = ">"  # Big-endian
    if signed:
        formatcode += "h"  # (Signed) short (2 bytes)
    else:
        formatcode += "H"  # Unsigned short (2 bytes)

    fullregister: int = _unpack_bytes(formatcode, inputbytes)

    if number_of_decimals == 0:
        return fullregister
    divisor = 10**number_of_decimals
    return fullregister / float(divisor)


def _long_to_bytes(
    value: int,
    signed: bool = False,
    number_of_registers: int = 2,
    byteorder: int = BYTEORDER_BIG,
) -> bytes:
    """Convert a long integer to bytes.

    Long integers (32 bits = 4 bytes or 64 bite = 8 bytes) are stored in two
    or four consecutive 16-bit registers in the slave respectively.

    Args:
        * value: The numerical value to be converted.
        * signed: Whether large positive values should be interpreted as
          negative values.
        * number_of_registers: Should be 2 or 4.
        * byteorder: How multi-register data should be interpreted.

    Returns:
        Four or eight bytes.

    Raises:
        TypeError, ValueError
    """
    _check_int(value, description="inputvalue")
    _check_bool(signed, description="signed parameter")
    _check_int(
        number_of_registers, minvalue=2, maxvalue=4, description="number of registers"
    )
    _check_int(
        byteorder, minvalue=0, maxvalue=_MAX_BYTEORDER_VALUE, description="byteorder"
    )

    if byteorder in [BYTEORDER_BIG, BYTEORDER_BIG_SWAP]:
        formatcode = ">"
    else:
        formatcode = "<"
    if number_of_registers == 2 and signed:
        formatcode += "l"  # (Signed) long (4 bytes)
        lengthtarget = 4
    elif number_of_registers == 2:
        formatcode += "L"  # Unsigned long (4 bytes)
        lengthtarget = 4
    elif number_of_registers == 4 and signed:
        formatcode += "q"  # (Signed) long long (8 bytes)
        lengthtarget = 8
    elif number_of_registers == 4:
        formatcode += "Q"  # Unsigned long long (8 bytes)
        lengthtarget = 8
    else:
        raise ValueError(
            "Wrong number of registers! Given value is {0!r}".format(
                number_of_registers
            )
        )
    outputbytes = _pack_bytes(formatcode, value)
    if byteorder in [BYTEORDER_BIG_SWAP, BYTEORDER_LITTLE_SWAP]:
        outputbytes = _swap(outputbytes)

    assert len(outputbytes) == lengthtarget
    return outputbytes


def _bytes_to_long(
    inputbytes: bytes,
    signed: bool = False,
    number_of_registers: int = 2,
    byteorder: int = BYTEORDER_BIG,
) -> int:
    """Convert bytes to a long integer.

    Long integers (32 bits = 4 bytes or 64 bite = 8 bytes) are stored in two
    or four consecutive 16-bit registers in the slave respectively.

    Args:
        * inputbytes: Length 4 or 8 bytes.
        * signed: Whether large positive values should be interpreted as
          negative values.
        * number_of_registers: Should be 2 or 4.
        * byteorder: How multi-register data should be interpreted.

    Returns:
        The numerical value.

    Raises:
        ValueError, TypeError
    """
    _check_bool(signed, description="signed parameter")
    _check_int(
        number_of_registers, minvalue=2, maxvalue=4, description="number of registers"
    )
    _check_int(
        byteorder, minvalue=0, maxvalue=_MAX_BYTEORDER_VALUE, description="byteorder"
    )

    if byteorder in [BYTEORDER_BIG, BYTEORDER_BIG_SWAP]:
        formatcode = ">"
    else:
        formatcode = "<"
    if number_of_registers == 2 and signed:
        formatcode += "l"  # (Signed) long (4 bytes)
        lengthtarget = 4
    elif number_of_registers == 2:
        formatcode += "L"  # Unsigned long (4 bytes)
        lengthtarget = 4
    elif number_of_registers == 4 and signed:
        formatcode += "q"  # (Signed) long long (8 bytes)
        lengthtarget = 8
    elif number_of_registers == 4:
        formatcode += "Q"  # Unsigned long long (8 bytes)
        lengthtarget = 8
    else:
        raise ValueError(
            "Wrong number of registers! Given value is {0!r}".format(
                number_of_registers
            )
        )
    _check_bytes(
        inputbytes, "input bytes", minlength=lengthtarget, maxlength=lengthtarget
    )

    if byteorder in [BYTEORDER_BIG_SWAP, BYTEORDER_LITTLE_SWAP]:
        inputbytes = _swap(inputbytes)

    return int(_unpack_bytes(formatcode, inputbytes))


def _float_to_bytes(
    value: Union[int, float],
    number_of_registers: int = 2,
    byteorder: int = BYTEORDER_BIG,
) -> bytes:
    r"""Convert a numerical value to bytes.

    Floats are stored in two or more consecutive 16-bit registers in the slave. The
    encoding is according to the standard IEEE 754.

    =============================== ================= =========== =================
    Type of floating point in slave Size              Registers   Range
    =============================== ================= =========== =================
    Single precision (binary32)     32 bits (4 bytes) 2 registers 1.4E-45 to 3.4E38
    Double precision (binary64)     64 bits (8 bytes) 4 registers 5E-324 to 1.8E308
    =============================== ================= =========== =================

    A floating  point value of 1.0 is encoded (in single precision) as 3f800000 (hex).
    This will give the bytes ``'\x3f\x80\x00\x00'`` (big endian).

    Args:
        * value (float or int): The numerical value to be converted.
        * number_of_registers: Can be 2 or 4.
        * byteorder: How multi-register data should be interpreted.

    Returns:
        4 or 8 bytes.

    Raises:
        TypeError, ValueError
    """
    _check_numerical(value, description="inputvalue")
    _check_int(
        number_of_registers, minvalue=2, maxvalue=4, description="number of registers"
    )
    _check_int(
        byteorder, minvalue=0, maxvalue=_MAX_BYTEORDER_VALUE, description="byteorder"
    )

    if byteorder in [BYTEORDER_BIG, BYTEORDER_BIG_SWAP]:
        formatcode = ">"
    else:
        formatcode = "<"
    if number_of_registers == 2:
        formatcode += "f"  # Float (4 bytes)
        lengthtarget = 4
    elif number_of_registers == 4:
        formatcode += "d"  # Double (8 bytes)
        lengthtarget = 8
    else:
        raise ValueError(
            "Wrong number of registers! Given value is {0!r}".format(
                number_of_registers
            )
        )

    outputbytes = _pack_bytes(formatcode, value)
    if byteorder in [BYTEORDER_BIG_SWAP, BYTEORDER_LITTLE_SWAP]:
        outputbytes = _swap(outputbytes)
    assert len(outputbytes) == lengthtarget
    return outputbytes


def _bytes_to_float(
    inputbytes: bytes, number_of_registers: int = 2, byteorder: int = BYTEORDER_BIG
) -> float:
    """Convert four bytes to a float.

    Floats are stored in two or more consecutive 16-bit registers in the slave.

    For discussion on precision, number of bits, number of registers, the range,
    byte order and on alternative names, see :func:`minimalmodbus._float_to_bytes`.

    Args:
        * inputbytes: Four or eight bytes
        * number_of_registers: Can be 2 or 4.
        * byteorder: How multi-register data should be interpreted.

    Returns:
        A float.

    Raises:
        TypeError, ValueError
    """
    _check_bytes(inputbytes, minlength=4, maxlength=8, description="input bytes")
    _check_int(
        number_of_registers, minvalue=2, maxvalue=4, description="number of registers"
    )
    _check_int(
        byteorder, minvalue=0, maxvalue=_MAX_BYTEORDER_VALUE, description="byteorder"
    )
    number_of_bytes = _NUMBER_OF_BYTES_PER_REGISTER * number_of_registers

    if byteorder in [BYTEORDER_BIG, BYTEORDER_BIG_SWAP]:
        formatcode = ">"
    else:
        formatcode = "<"
    if number_of_registers == 2:
        formatcode += "f"  # Float (4 bytes)
    elif number_of_registers == 4:
        formatcode += "d"  # Double (8 bytes)
    else:
        raise ValueError(
            "Wrong number of registers! Given value is {0!r}".format(
                number_of_registers
            )
        )

    if len(inputbytes) != number_of_bytes:
        raise ValueError(
            "Wrong length of the input bytes! Given value is "
            + "{0!r}, and number_of_registers is {1!r}.".format(
                inputbytes, number_of_registers
            )
        )

    if byteorder in [BYTEORDER_BIG_SWAP, BYTEORDER_LITTLE_SWAP]:
        inputbytes = _swap(inputbytes)
    return float(_unpack_bytes(formatcode, inputbytes))


def _textstring_to_bytes(inputstring: str, number_of_registers: int = 16) -> bytes:
    """Convert a text string to bytes.

    Each 16-bit register in the slave are interpreted as two characters (1 byte =
    8 bits). For example 16 consecutive registers can hold 32 characters (32 bytes).

    Not much of conversion is done, mostly error checking and string padding.
    If the *inputstring* is shorter that the allocated space, it is padded with
    spaces in the end.

    Args:
        * inputstring: The string to be stored in the slave.
          Max 2 * *number_of_registers* characters.
        * number_of_registers: The number of registers allocated for the string.

    Returns:
        Bytes.

    Raises:
        TypeError, ValueError
    """
    _check_int(
        number_of_registers,
        minvalue=1,
        maxvalue=_MAX_NUMBER_OF_REGISTERS_TO_WRITE,
        description="number of registers",
    )
    max_characters = _NUMBER_OF_BYTES_PER_REGISTER * number_of_registers
    _check_string(inputstring, "input string", minlength=1, maxlength=max_characters)

    padded = inputstring.ljust(max_characters)  # Pad with space
    outputbytes = bytes(padded, encoding="ascii")
    assert len(outputbytes) == max_characters
    return outputbytes


def _bytes_to_textstring(inputbytes: bytes, number_of_registers: int = 16) -> str:
    """Convert bytes to a text string.

    Each 16-bit register in the slave are interpreted as two characters (1 byte =
    8 bits). For example 16 consecutive registers can hold 32 characters (32 bytes).

    Not much of conversion is done, mostly error checking.

    Args:
        * inputbytes: The bytes from the slave. Length = 2 * *number_of_registers*
        * number_of_registers (int): The number of registers allocated for the string.
          Should be >0.

    Returns:
        A the text string.

    Raises:
        TypeError, ValueError
    """
    _check_int(
        number_of_registers,
        minvalue=1,
        maxvalue=_MAX_NUMBER_OF_REGISTERS_TO_READ,
        description="number of registers",
    )
    max_characters = _NUMBER_OF_BYTES_PER_REGISTER * number_of_registers
    _check_bytes(
        inputbytes, "input bytes", minlength=max_characters, maxlength=max_characters
    )

    return inputbytes.decode(encoding="ascii")


def _valuelist_to_bytes(valuelist: List[int], number_of_registers: int) -> bytes:
    """Convert a list of numerical values to bytes.

    Each element is 'unsigned INT16'.

    Args:
        * valuelist: The input list. The elements should be in the
          range 0 to 65535.
        * number_of_registers: The number of registers. For error checking.
          Should equal the number of elements in *valuelist*.

    Returns:
        Bytes Length = 2 * *number_of_registers*

    Raises:
        TypeError, ValueError
    """
    MINVALUE = 0
    MAXVALUE = 0xFFFF

    _check_int(number_of_registers, minvalue=1, description="number of registers")

    if not isinstance(valuelist, list):
        raise TypeError(
            "The valuelist parameter must be a list. Given {0!r}.".format(valuelist)
        )

    for value in valuelist:
        _check_int(
            value,
            minvalue=MINVALUE,
            maxvalue=MAXVALUE,
            description="elements in the input value list",
        )

    _check_int(
        len(valuelist),
        minvalue=number_of_registers,
        maxvalue=number_of_registers,
        description="length of the list",
    )

    number_of_bytes = _NUMBER_OF_BYTES_PER_REGISTER * number_of_registers

    outputbytes = b""
    for value in valuelist:
        outputbytes += _num_to_two_bytes(value, signed=False)

    assert len(outputbytes) == number_of_bytes
    return outputbytes


def _bytes_to_valuelist(inputbytes: bytes, number_of_registers: int) -> List[int]:
    """Convert bytes to a list of numerical values.

    The bytes are interpreted as 'unsigned INT16'.

    Args:
        * inputbytes: The bytes from the slave. Length = 2 * *number_of_registers*
        * number_of_registers: The number of registers. For error checking.

    Returns:
        A list of integers.

    Raises:
        TypeError, ValueError
    """
    _check_int(number_of_registers, minvalue=1, description="number of registers")
    number_of_bytes = _NUMBER_OF_BYTES_PER_REGISTER * number_of_registers
    _check_bytes(
        inputbytes, "input bytes", minlength=number_of_bytes, maxlength=number_of_bytes
    )

    values = []
    for i in range(number_of_registers):
        offset = _NUMBER_OF_BYTES_PER_REGISTER * i
        sub_bytes = inputbytes[offset : (offset + _NUMBER_OF_BYTES_PER_REGISTER)]
        values.append(int(_two_bytes_to_num(sub_bytes)))

    return values


def _pack_bytes(formatstring: str, value: Any) -> bytes:
    """Pack a value into bytes.

    Uses the built-in :mod:`struct` Python module, and adds relevant error messages.

    Args:
        * formatstring: String for the packing. See the :mod:`struct` module
          for details.
        * value (depends on formatstring): The value to be packed

    Returns:
        The packed bytes

    Raises:
        ValueError
    """
    _check_string(formatstring, description="formatstring", minlength=1)

    try:
        result = struct.pack(formatstring, value)
    except Exception as exc:
        errortext = "The value to send is probably out of range, as the num-to-bytes "
        errortext += "conversion failed. Value: {0!r} Struct format code is: {1}"
        raise ValueError(errortext.format(value, formatstring)) from exc

    return result


def _unpack_bytes(formatstring: str, packed_bytes: bytes) -> Any:
    """Unpack bytes into a value.

    Uses the built-in :mod:`struct` Python module, and adds relevant error messages.

    Args:
        * formatstring: String for the packing. See the :mod:`struct` module
          for details.
        * packed_bytes: The bytes to be unpacked.

    Returns:
        A value. The type depends on the formatstring.

    Raises:
        ValueError
    """
    _check_string(formatstring, description="formatstring", minlength=1)
    _check_bytes(packed_bytes, description="packed bytes", minlength=1)

    try:
        value = struct.unpack(formatstring, packed_bytes)[0]
    except Exception:
        errortext = "The received bytes is probably wrong, as the bytes-to-num "
        errortext += "conversion failed. Bytes: {0!r} Struct format code is: {1}"
        raise InvalidResponseError(errortext.format(packed_bytes, formatstring))

    return value


def _swap(inputbytes: bytes) -> bytes:
    """Swap bytes pairwise.

    This corresponds to a "byte swap".

    Args:
        * inputbytes: input. The length should be an even number.

    Return the bytes swapped.
    """
    length = len(inputbytes)
    if length % 2:
        raise ValueError(
            "The length of the inputbytes should be even. Given {!r}.".format(
                inputbytes
            )
        )
    templist = list(inputbytes)
    templist[1:length:2], templist[:length:2] = (
        templist[:length:2],
        templist[1:length:2],
    )
    return bytes(templist)


def _hexencode(inputbytes: bytes, insert_spaces: bool = False) -> bytes:
    r"""Convert bytes to a hex encoded bytes.

    For example ``b'J'`` will return ``b'4A'``, and ``b'\x04'`` will return ``b'04'``.

    Args:
        * inputbytes: Can be for example ``b'A\x01B\x45'``.
        * insert_spaces: Insert space characters between pair of characters
          to increase readability.

    Returns:
        Bytes of twice the length, with characters in the range '0' to '9' and
        'A' to 'F'. It will be longer if spaces are inserted.

    Raises:
        TypeError, ValueError
    """
    _check_bytes(inputbytes, description="input bytes")

    if insert_spaces:
        return binascii.hexlify(inputbytes, sep=" ").upper()
    return binascii.hexlify(inputbytes).upper()


def _hexdecode(hexbytes: bytes) -> bytes:
    r"""Convert hex encoded bytes to bytes.

    For example ``b'4A'`` will return ``b'J'``, and ``b'04'`` will
    return ``b'\x04'`` (which has length 1).

    Args:
        * hexbytes: Can be for example ``b'A3'`` or ``b'A3B4'``. Must be of even length.
          Allowed bytes are ``b'0'`` to ``b'9'``, ``b'a'`` to ``b'f'``
          and ``b'A'`` to ``b'F'`` (not space).

    Returns:
        Bytes of half the length, with bytes corresponding to all 0-255 values.

    Raises:
        TypeError, ValueError
    """
    # TODO Note: For Python3 the appropriate would be:
    #   raise TypeError(new_error_message) from err
    # but the Python2 interpreter will indicate SyntaxError.
    # Thus we need to live with this warning in Python3:
    # 'During handling of the above exception, another exception occurred'

    _check_bytes(hexbytes, description="hex bytes")

    if len(hexbytes) % 2 != 0:
        raise ValueError(
            "The input hex bytes must be of even length. Given: {!r}".format(hexbytes)
        )

    try:
        return binascii.unhexlify(hexbytes)
    except binascii.Error as err:
        new_error_message = (
            "Hexdecode reported an error: {!s}. Input hexstring: {!r}".format(
                err.args[0], hexbytes
            )
        )
        raise TypeError(new_error_message)


def _describe_bytes(inputbytes: bytes) -> str:
    r"""Describe bytes in a human friendly way.

    Args:
        * inputbytes: Bytes to describe

    Returns a space separated descriptive string.
    For example ``b'\x01\x02\x03'`` gives: ``01 02 03 (3 bytes)``
    """
    return " ".join([f"{x:02X}" for x in inputbytes]) + " ({} bytes)".format(
        len(inputbytes)
    )


def _calculate_number_of_bytes_for_bits(number_of_bits: int) -> int:
    """Calculate number of full bytes required to house a number of bits.

    Args:
        * number_of_bits: Number of bits

    Error checking should have been done before.

    For example 9 bits requires 2 bytes.

    Algorithm from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
    """
    result = number_of_bits // _BITS_PER_BYTE  # Integer division in Python2 and 3
    if number_of_bits % _BITS_PER_BYTE:
        result += 1
    return result


def _bit_to_bytes(value: int) -> bytes:
    """Create the bit pattern that is used for writing single bits.

    Used for functioncode 5. The same value is sent back in the response
    from the slave.

    This is basically a storage of numerical constants.

    Args:
        * value: Can be 0 or 1

    Returns:
        The bit pattern.

    Raises:
        TypeError, ValueError
    """
    _check_int(value, minvalue=0, maxvalue=1, description="inputvalue")

    if value == 0:
        return b"\x00\x00"
    return b"\xff\x00"


def _bits_to_bytes(valuelist: List[int]) -> bytes:
    """Build bytes from a list of bits.

    This is used for functioncode 15.

    Args:
        * valuelist: List of int (0 or 1)

    Returns bytes.
    """
    if not isinstance(valuelist, list):
        raise TypeError(
            "The input should be a list. " + "Given: {!r}".format(valuelist)
        )
    for value in valuelist:
        if value not in [0, 1, False, True]:
            raise ValueError(
                "Wrong value in list of bits. " + "Given: {!r}".format(value)
            )

    list_position = 0
    outputbytes = b""
    while list_position < len(valuelist):
        sublist = valuelist[list_position : (list_position + _BITS_PER_BYTE)]

        bytevalue = 0
        for bitposition, value in enumerate(sublist):
            bytevalue |= value << bitposition
        outputbytes += bytevalue.to_bytes(1, "big")

        list_position += _BITS_PER_BYTE
    return outputbytes


def _bytes_to_bits(inputbytes: bytes, number_of_bits: int) -> List[int]:
    """Parse bits from bytes.

    This is used for parsing the bits in response messages for functioncode 1 and 2.

    The first byte in the *inputbytes* contains info on the addressed bit
    (in LSB in that byte). Second bit from right contains info on the bit
    on the next address.

    Next byte in the *inputbytes* contains data on next 8 bits. Might be padded with
    zeros toward MSB.

    Args:
        * inputbytes: Input bytes
        * number_of_bits: Number of bits to extract

    Returns a list of values (0 or 1). The length of the list is equal to
    *number_of_bits*.
    """
    expected_length = _calculate_number_of_bytes_for_bits(number_of_bits)
    if len(inputbytes) != expected_length:
        raise ValueError(
            "Wrong length of input bytes. Expected is "
            + "{} bytes (for {} bits), actual is {} bytes.".format(
                expected_length, number_of_bits, len(inputbytes)
            )
        )
    total_list = []
    for bytevalue in inputbytes:  # Gives individual bytes as int
        for bitposition in range(_BITS_PER_BYTE):
            bitvalue = (bytevalue & (1 << bitposition)) > 0
            total_list.append(int(bitvalue))
    return total_list[:number_of_bits]


# ################### #
# Number manipulation #
# ################### #


def _twos_complement(x: int, bits: int = 16) -> int:
    """Calculate the two's complement of an integer.

    Then also negative values can be represented by an upper range of positive values.
    See https://en.wikipedia.org/wiki/Two%27s_complement

    Args:
        * x: Input integer.
        * bits: Number of bits, must be > 0.

    Returns:
        The two's complement of the input.

    Example for *bits* = 8:

    ==== =======
    x    returns
    ==== =======
    0    0
    1    1
    127  127
    -128 128
    -127 129
    -1   255
    ==== =======
    """
    _check_int(bits, minvalue=0, description="number of bits")
    _check_int(x, description="input")
    upperlimit: int = 2 ** (bits - 1) - 1
    lowerlimit: int = -(2 ** (bits - 1))
    if x > upperlimit or x < lowerlimit:
        raise ValueError(
            "The input value is out of range. Given value is "
            + "{0}, but allowed range is {1} to {2} when using {3} bits.".format(
                x, lowerlimit, upperlimit, bits
            )
        )

    # Calculate two'2 complement
    if x >= 0:
        return x
    return int(x + 2**bits)


def _from_twos_complement(x: int, bits: int = 16) -> int:
    """Calculate the inverse(?) of a two's complement of an integer.

    Args:
        * x: Input integer.
        * bits: Number of bits, must be > 0.

    Returns:
        The inverse(?) of two's complement of the input.

     Example for *bits* = 8:

    === =======
    x   returns
    === =======
    0   0
    1   1
    127 127
    128 -128
    129 -127
    255 -1
    === =======
    """
    _check_int(bits, minvalue=0, description="number of bits")

    _check_int(x, description="input")
    upperlimit = 2 ** (bits) - 1
    lowerlimit = 0
    if x > upperlimit or x < lowerlimit:
        raise ValueError(
            "The input value is out of range. Given value is "
            + "{0}, but allowed range is {1} to {2} when using {3} bits.".format(
                x, lowerlimit, upperlimit, bits
            )
        )

    # Calculate inverse(?) of two'2 complement
    limit = 2 ** (bits - 1) - 1
    if x <= limit:
        return x
    return int(x - 2**bits)


# ################ #
# Bit manipulation #
# ################ #


def _set_bit_on(x: int, bit_num: int) -> int:
    """Set bit *bit_num* to True.

    Args:
        * x: The value before.
        * bit_num: The bit number that should be set to True.

    Returns:
        The value after setting the bit.

    For example:
        For x = 4 (dec) = 0100 (bin), setting bit number 0 results
        in 0101 (bin) = 5 (dec).
    """
    _check_int(x, minvalue=0, description="input value")
    _check_int(bit_num, minvalue=0, description="bitnumber")

    return x | (1 << bit_num)


def _check_bit(x: int, bit_num: int) -> bool:
    """Check if bit *bit_num* is set the input integer.

    Args:
        * x: The input value.
        * bit_num: The bit number to be checked

    Returns:
        True or False

    For example:
        For x = 4 (dec) = 0100 (bin), checking bit number 2 results in True, and
        checking bit number 3 results in False.
    """
    _check_int(x, minvalue=0, description="input value")
    _check_int(bit_num, minvalue=0, description="bitnumber")

    return (x & (1 << bit_num)) > 0


# ######################## #
# Error checking functions #
# ######################## #


_CRC16TABLE = (
    0,
    49345,
    49537,
    320,
    49921,
    960,
    640,
    49729,
    50689,
    1728,
    1920,
    51009,
    1280,
    50625,
    50305,
    1088,
    52225,
    3264,
    3456,
    52545,
    3840,
    53185,
    52865,
    3648,
    2560,
    51905,
    52097,
    2880,
    51457,
    2496,
    2176,
    51265,
    55297,
    6336,
    6528,
    55617,
    6912,
    56257,
    55937,
    6720,
    7680,
    57025,
    57217,
    8000,
    56577,
    7616,
    7296,
    56385,
    5120,
    54465,
    54657,
    5440,
    55041,
    6080,
    5760,
    54849,
    53761,
    4800,
    4992,
    54081,
    4352,
    53697,
    53377,
    4160,
    61441,
    12480,
    12672,
    61761,
    13056,
    62401,
    62081,
    12864,
    13824,
    63169,
    63361,
    14144,
    62721,
    13760,
    13440,
    62529,
    15360,
    64705,
    64897,
    15680,
    65281,
    16320,
    16000,
    65089,
    64001,
    15040,
    15232,
    64321,
    14592,
    63937,
    63617,
    14400,
    10240,
    59585,
    59777,
    10560,
    60161,
    11200,
    10880,
    59969,
    60929,
    11968,
    12160,
    61249,
    11520,
    60865,
    60545,
    11328,
    58369,
    9408,
    9600,
    58689,
    9984,
    59329,
    59009,
    9792,
    8704,
    58049,
    58241,
    9024,
    57601,
    8640,
    8320,
    57409,
    40961,
    24768,
    24960,
    41281,
    25344,
    41921,
    41601,
    25152,
    26112,
    42689,
    42881,
    26432,
    42241,
    26048,
    25728,
    42049,
    27648,
    44225,
    44417,
    27968,
    44801,
    28608,
    28288,
    44609,
    43521,
    27328,
    27520,
    43841,
    26880,
    43457,
    43137,
    26688,
    30720,
    47297,
    47489,
    31040,
    47873,
    31680,
    31360,
    47681,
    48641,
    32448,
    32640,
    48961,
    32000,
    48577,
    48257,
    31808,
    46081,
    29888,
    30080,
    46401,
    30464,
    47041,
    46721,
    30272,
    29184,
    45761,
    45953,
    29504,
    45313,
    29120,
    28800,
    45121,
    20480,
    37057,
    37249,
    20800,
    37633,
    21440,
    21120,
    37441,
    38401,
    22208,
    22400,
    38721,
    21760,
    38337,
    38017,
    21568,
    39937,
    23744,
    23936,
    40257,
    24320,
    40897,
    40577,
    24128,
    23040,
    39617,
    39809,
    23360,
    39169,
    22976,
    22656,
    38977,
    34817,
    18624,
    18816,
    35137,
    19200,
    35777,
    35457,
    19008,
    19968,
    36545,
    36737,
    20288,
    36097,
    19904,
    19584,
    35905,
    17408,
    33985,
    34177,
    17728,
    34561,
    18368,
    18048,
    34369,
    33281,
    17088,
    17280,
    33601,
    16640,
    33217,
    32897,
    16448,
)
r"""CRC-16 lookup table with 256 elements.

Built with this code::

    poly=0xA001
    table = []
    for index in range(256):
        data = index << 1
        crc = 0
        for _ in range(8, 0, -1):
            data >>= 1
            if (data ^ crc) & 0x0001:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
        table.append(crc)
    output = ''
    for i, m in enumerate(table):
        if not i%11:
            output += "\n"
        output += "{:5.0f}, ".format(m)
    print output
"""


def _is_serial_object(obj: Any) -> bool:
    """Check if an object is serialport-like."""
    KNOWN_ATTRIBUTES = ["open", "close", "read", "write", "is_open"]

    for attribute_name in KNOWN_ATTRIBUTES:
        if not hasattr(obj, attribute_name):
            return False
    return True


def _calculate_crc(inputbytes: bytes) -> bytes:
    """Calculate CRC-16 for Modbus RTU.

    Args:
        inputbytes: An arbitrary-length message (without the CRC).

    Returns:
        A two-byte CRC, where the least significant byte is first.
    """
    _check_bytes(inputbytes, description="CRC input bytes")

    # Preload a 16-bit register with ones
    register = 0xFFFF

    for current_byte in inputbytes:
        register = (register >> 8) ^ _CRC16TABLE[(register ^ current_byte) & 0xFF]

    return _num_to_two_bytes(register, lsb_first=True)


def _calculate_lrc(inputbytes: bytes) -> bytes:
    """Calculate LRC for Modbus ASCII.

    Args:
        inputbytes: An arbitrary-length message (without the beginning
        colon and terminating CRLF). It should already be decoded from hex-string.

    Returns:
        A one-byte LRC (not encoded to hex-string)

    Algorithm from the document 'MODBUS over serial line specification and
    implementation guide V1.02'.

    The LRC is calculated as 8 bits (one byte).

    For example a resulting LRC 0110 0001 (bin) = 61 (hex) = 97 (dec) = ``b'a'``.
    This function will then return ``b'a'``.

    In Modbus ASCII mode, this should be transmitted using two characters. This
    example should be transmitted as ``b'61'``, which is a bytes object of length two.
    This function does not handle that conversion for transmission.
    """
    _check_bytes(inputbytes, description="LRC input bytes")

    register = 0
    for bytevalue in inputbytes:
        register += bytevalue

    lrc = ((register ^ 0xFF) + 1) & 0xFF

    return _num_to_one_byte(lrc)


def _check_mode(mode: str) -> None:
    """Check that the Modbus mode is valid.

    Args:
        mode: The Modbus mode (MODE_RTU or MODE_ASCII)

    Raises:
        TypeError, ValueError
    """
    if not isinstance(mode, str):
        raise TypeError("The {0} should be a string. Given: {1!r}".format("mode", mode))

    if mode not in [MODE_RTU, MODE_ASCII]:
        raise ValueError(
            "Unreconized Modbus mode given. Must "
            + "be 'rtu' or 'ascii' but {0!r} was given.".format(mode)
        )


def _check_functioncode(
    functioncode: int, list_of_allowed_values: Optional[List[int]] = None
) -> None:
    """Check that the given functioncode is in the *list_of_allowed_values*.

    Also verifies that 1 <= function code <= 127.

    Args:
        * functioncode: The function code
        * list_of_allowed_values: Allowed values. Use *None* to bypass
          this part of the checking.

    Raises:
        TypeError, ValueError
    """
    FUNCTIONCODE_MIN = 1
    FUNCTIONCODE_MAX = 127

    _check_int(
        functioncode, FUNCTIONCODE_MIN, FUNCTIONCODE_MAX, description="functioncode"
    )

    if list_of_allowed_values is None:
        return

    if not isinstance(list_of_allowed_values, list):
        raise TypeError(
            "The list_of_allowed_values should be a list. Given: {0!r}".format(
                list_of_allowed_values
            )
        )

    for value in list_of_allowed_values:
        _check_int(
            value,
            FUNCTIONCODE_MIN,
            FUNCTIONCODE_MAX,
            description="functioncode inside list_of_allowed_values",
        )

    if functioncode not in list_of_allowed_values:
        raise ValueError(
            "Wrong function code: {0}, allowed values are {1!r}".format(
                functioncode, list_of_allowed_values
            )
        )


def _check_slaveaddress(slaveaddress: int) -> None:
    """Check that the given *slaveaddress* is valid.

    Args:
        slaveaddress: The slave address

    Raises:
        TypeError, ValueError
    """
    SLAVEADDRESS_MAX = 255  # Allows usage also of reserved addresses
    SLAVEADDRESS_MIN = 0

    _check_int(
        slaveaddress, SLAVEADDRESS_MIN, SLAVEADDRESS_MAX, description="slaveaddress"
    )


def _check_registeraddress(registeraddress: int) -> None:
    """Check that the given *registeraddress* is valid.

    Args:
        registeraddress: The register address

    Raises:
        TypeError, ValueError
    """
    REGISTERADDRESS_MAX = 0xFFFF
    REGISTERADDRESS_MIN = 0

    _check_int(
        registeraddress,
        REGISTERADDRESS_MIN,
        REGISTERADDRESS_MAX,
        description="registeraddress",
    )


def _check_response_payload(
    payload: bytes,
    functioncode: int,
    registeraddress: int,
    value: Any,
    number_of_decimals: int,
    number_of_registers: int,
    number_of_bits: int,
    signed: bool,
    byteorder: int,  # Not used. For same signature as _parse_payload()
    payloadformat: _Payloadformat,  # Not used. For same signature as _parse_payload()
) -> None:
    """Check the response payload.

    Args:
        * payload:              Payload to be checked
        * functioncode:         Function code
        * registeraddress:      Register address
        * value:                Value in request
        * number_of_decimals:   Number of decimals
        * number_of_registers:  Number of registers
        * number_of_bits:       Number of bits
        * signed:               Signed
        * byteorder:            Byte order
        * payloadformat:        Payload format

    Raises:
        ValueError, TypeError
    """
    if functioncode in [1, 2, 3, 4]:
        _check_response_bytecount(payload)

    if functioncode in [5, 6, 15, 16]:
        _check_response_registeraddress(payload, registeraddress)

    if functioncode == 5:
        _check_response_writedata(payload, _bit_to_bytes(value))
    elif functioncode == 6:
        _check_response_writedata(
            payload, _num_to_two_bytes(value, number_of_decimals, signed=signed)
        )
    elif functioncode == 15:
        # response number of bits
        _check_response_number_of_registers(payload, number_of_bits)

    elif functioncode == 16:
        _check_response_number_of_registers(payload, number_of_registers)

    # Response for read bits
    if functioncode in [1, 2]:
        registerdata = payload[_NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
        expected_number_of_bytes = _calculate_number_of_bytes_for_bits(number_of_bits)
        if len(registerdata) != expected_number_of_bytes:
            raise InvalidResponseError(
                "The data length is wrong for payloadformat BIT/BITS."
                + " Expected: {} Actual: {}.".format(
                    expected_number_of_bytes, len(registerdata)
                )
            )

    # Response for read registers
    if functioncode in [3, 4]:
        registerdata = payload[_NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
        number_of_register_bytes = number_of_registers * _NUMBER_OF_BYTES_PER_REGISTER
        if len(registerdata) != number_of_register_bytes:
            raise InvalidResponseError(
                "The register data length is wrong. "
                + "Registerdata: {!r} bytes. Expected: {!r}.".format(
                    len(registerdata), number_of_register_bytes
                )
            )


def _check_response_slaveerrorcode(response: bytes) -> None:
    """Check if the slave indicates an error.

    Args:
        * response: Response from the slave

    The response is in RTU format, but the checksum might be one or two bytes
    depending on whether it was sent in RTU or ASCII mode.

    Checking of type and length of the response should be done before calling
    this functions.

    Raises:
        SlaveReportedException or subclass
    """
    NON_ERRORS = [5]
    SLAVE_ERRORS = {
        1: IllegalRequestError("Slave reported illegal function"),
        2: IllegalRequestError("Slave reported illegal data address"),
        3: IllegalRequestError("Slave reported illegal data value"),
        4: SlaveReportedException("Slave reported device failure"),
        6: SlaveDeviceBusyError("Slave reported device busy"),
        7: NegativeAcknowledgeError("Slave reported negative acknowledge"),
        8: SlaveReportedException("Slave reported memory parity error"),
        10: SlaveReportedException("Slave reported gateway path unavailable"),
        11: SlaveReportedException(
            "Slave reported gateway target device failed to respond"
        ),
    }

    if len(response) < _BYTEPOSITION_FOR_SLAVE_ERROR_CODE + 1:
        return  # This check is also done before calling, do not raise exception here.

    received_functioncode = response[_BYTEPOSITION_FOR_FUNCTIONCODE]

    if _check_bit(received_functioncode, _BITNUMBER_FUNCTIONCODE_ERRORINDICATION):
        slave_error_code = response[_BYTEPOSITION_FOR_SLAVE_ERROR_CODE]

        if slave_error_code in NON_ERRORS:
            return

        error = SLAVE_ERRORS.get(
            slave_error_code,
            SlaveReportedException(
                "Slave reported error code " + str(slave_error_code)
            ),
        )
        raise error


def _check_response_bytecount(payload: bytes) -> None:
    """Check that the number of bytes as given in the response is correct.

    The first byte in the payload indicates the length of the payload (first
    byte not counted).

    Args:
        payload: The payload

    Raises:
        TypeError, ValueError, InvalidResponseError
    """
    POSITION_FOR_GIVEN_NUMBER = 0
    NUMBER_OF_BYTES_TO_SKIP = 1

    _check_bytes(
        payload, minlength=1, description="payload", exception_type=InvalidResponseError
    )

    given_number_of_databytes = payload[POSITION_FOR_GIVEN_NUMBER]
    counted_number_of_databytes = len(payload) - NUMBER_OF_BYTES_TO_SKIP

    if given_number_of_databytes != counted_number_of_databytes:
        errortemplate = (
            "Wrong given number of bytes in the response: "
            + "{0}, but counted is {1} as data payload length is {2}."
            + " The data payload is: {3!r}"
        )
        errortext = errortemplate.format(
            given_number_of_databytes,
            counted_number_of_databytes,
            len(payload),
            payload,
        )
        raise InvalidResponseError(errortext)


def _check_response_registeraddress(payload: bytes, registeraddress: int) -> None:
    """Check that the start adress as given in the response is correct.

    The first two bytes in the payload holds the address value.

    Args:
        * payload: The payload
        * registeraddress: What the register address actually shoud be.

    Raises:
        TypeError, ValueError, InvalidResponseError
    """
    _check_bytes(
        payload, minlength=2, description="payload", exception_type=InvalidResponseError
    )
    _check_registeraddress(registeraddress)

    BYTERANGE_FOR_STARTADDRESS = slice(0, 2)

    bytes_for_startaddress = payload[BYTERANGE_FOR_STARTADDRESS]
    received_startaddress = _two_bytes_to_num(bytes_for_startaddress)

    if received_startaddress != registeraddress:
        raise InvalidResponseError(
            "Wrong given write start adress: "
            + "{0}, but commanded is {1}. The data payload is: {2!r}".format(
                received_startaddress, registeraddress, payload
            )
        )


def _check_response_number_of_registers(
    payload: bytes, number_of_registers: int
) -> None:
    """Check that the number of written registers as given in the response is correct.

    The bytes 2 and 3 (zero based counting) in the payload holds the value.

    Args:
        * payload: The payload
        * number_of_registers: Number of registers that have been written

    Raises:
        TypeError, ValueError, InvalidResponseError
    """
    _check_bytes(
        payload, minlength=4, description="payload", exception_type=InvalidResponseError
    )
    _check_int(
        number_of_registers,
        minvalue=1,
        maxvalue=max(
            _MAX_NUMBER_OF_REGISTERS_TO_READ, _MAX_NUMBER_OF_REGISTERS_TO_WRITE
        ),
        description="number of registers",
    )

    BYTERANGE_FOR_NUMBER_OF_REGISTERS = slice(2, 4)

    bytes_for_mumber_of_registers = payload[BYTERANGE_FOR_NUMBER_OF_REGISTERS]
    received_number_of_written_registers = _two_bytes_to_num(
        bytes_for_mumber_of_registers
    )

    if received_number_of_written_registers != number_of_registers:
        raise InvalidResponseError(
            "Wrong number of registers to write in the response: "
            + "{0}, but commanded is {1}. The data payload is: {2!r}".format(
                received_number_of_written_registers, number_of_registers, payload
            )
        )


def _check_response_writedata(payload: bytes, writedata: bytes) -> None:
    """Check that the write data as given in the response is correct.

    The bytes 2 and 3 (zero based counting) in the payload holds the write data.

    Args:
        * payload: The payload
        * writedata: The data that should have been written.
          Length should be 2 bytes.

    Raises:
        TypeError, ValueError, InvalidResponseError
    """
    _check_bytes(
        payload, minlength=4, description="payload", exception_type=InvalidResponseError
    )
    _check_bytes(writedata, minlength=2, maxlength=2, description="writedata")

    BYTERANGE_FOR_WRITEDATA = slice(2, 4)

    received_writedata = payload[BYTERANGE_FOR_WRITEDATA]

    if received_writedata != writedata:
        raise InvalidResponseError(
            "Wrong write data in the response: "
            + "{0!r}, but commanded is {1!r}. The data payload is: {2!r}".format(
                received_writedata, writedata, payload
            )
        )


def _check_bytes(
    inputbytes: bytes,
    description: str,
    minlength: int = 0,
    maxlength: Optional[int] = None,
    exception_type: Type[Exception] = ValueError,
) -> None:
    """Check that the bytes are valid.

    Args:
        * inputbytes: The bytes to be checked
        * description: Used in error messages for the checked inputbytes
        * minlength: Minimum length of the inputbytes
        * maxlength: Maximum length of the inputbytes
        * exception_type: The type of exception to raise for length errors
    """
    # Type checking
    if not isinstance(description, str):
        raise TypeError(
            "The description should be a string. Given: {0!r}".format(description)
        )

    if not isinstance(inputbytes, bytes):
        raise TypeError(
            "The {0} should be bytes. Given: {1!r}".format(description, inputbytes)
        )

    if not isinstance(maxlength, (int, type(None))):
        raise TypeError(
            "The maxlength must be an integer or None. Given: {0!r}".format(maxlength)
        )

    # Check values
    _check_int(minlength, minvalue=0, maxvalue=None, description="minlength")

    if len(inputbytes) < minlength:
        raise exception_type(
            "The {0} is too short: {1}, but minimum value is {2}. Given: {3!r}".format(
                description, len(inputbytes), minlength, inputbytes
            )
        )

    if maxlength is not None:
        if maxlength < 0:
            raise ValueError(
                "The maxlength must be positive. Given: {0}".format(maxlength)
            )

        if maxlength < minlength:
            raise ValueError(
                "The maxlength must not be smaller than "
                + "minlength. Given: {0} and {1}".format(maxlength, minlength)
            )

        if len(inputbytes) > maxlength:
            raise exception_type(
                "The "
                + "{0} is too long: {1}, but maximum value is {2}. Given: {3!r}".format(
                    description, len(inputbytes), maxlength, inputbytes
                )
            )


def _check_string(
    inputstring: str,
    description: str,
    minlength: int = 0,
    maxlength: Optional[int] = None,
    force_ascii: bool = False,
    exception_type: Type[Exception] = ValueError,
) -> None:
    """Check that the given string is valid.

    Args:
        * inputstring: The string to be checked
        * description: Used in error messages for the checked *inputstring*
        * minlength: Minimum length of the string
        * maxlength: Maximum length of the string
        * force_ascii: Enforce that the string is ASCII
        * exception_type: The type of exception to raise for length errors

    Raises:
        TypeError, ValueError or the one given by exception_type

    Uses the function :func:`_check_int` internally.
    """
    # Type checking
    if not isinstance(description, str):
        raise TypeError(
            "The description should be a string. Given: {0!r}".format(description)
        )

    if not isinstance(inputstring, str):
        raise TypeError(
            "The {0} should be a string. Given: {1!r}".format(description, inputstring)
        )

    if not isinstance(maxlength, (int, type(None))):
        raise TypeError(
            "The maxlength must be an integer or None. Given: {0!r}".format(maxlength)
        )
    try:
        issubclass(exception_type, Exception)
    except TypeError:
        raise TypeError(
            "The exception_type must be an exception class. "
            + "It not even a class. Given: {0!r}".format(type(exception_type))
        )
    if not issubclass(exception_type, Exception):
        raise TypeError(
            "The exception_type must be an exception class. Given: {0!r}".format(
                type(exception_type)
            )
        )

    # Check values
    _check_int(minlength, minvalue=0, maxvalue=None, description="minlength")

    if len(inputstring) < minlength:
        raise exception_type(
            "The {0} is too short: {1}, but minimum value is {2}. Given: {3!r}".format(
                description, len(inputstring), minlength, inputstring
            )
        )

    if maxlength is not None:
        if maxlength < 0:
            raise ValueError(
                "The maxlength must be positive. Given: {0}".format(maxlength)
            )

        if maxlength < minlength:
            raise ValueError(
                "The maxlength must "
                + "not be smaller than minlength. Given: {0} and {1}".format(
                    maxlength, minlength
                )
            )

        if len(inputstring) > maxlength:
            raise exception_type(
                "The "
                + "{0} is too long: {1}, but maximum value is {2}. Given: {3!r}".format(
                    description, len(inputstring), maxlength, inputstring
                )
            )

    if force_ascii and sys.version > "3":
        try:
            inputstring.encode("ascii")
        except UnicodeEncodeError:
            raise ValueError(
                "The {0} must be ASCII. Given: {1!r}".format(description, inputstring)
            )


def _check_int(
    inputvalue: int,
    minvalue: Optional[int] = None,
    maxvalue: Optional[int] = None,
    description: str = "inputvalue",
) -> None:
    """Check that the given integer is valid.

    Args:
        * inputvalue: The integer to be checked
        * minvalue: Minimum value of the integer
        * maxvalue: Maximum value of the integer
        * description: Used in error messages for the checked inputvalue

    Raises:
        TypeError, ValueError

    Note: Can not use the function :func:`_check_string`, as that function uses this
    function internally.
    """
    if not isinstance(description, str):
        raise TypeError(
            "The description should be a string. Given: {0!r}".format(description)
        )

    if not isinstance(inputvalue, (int)):
        raise TypeError(
            "The {0} must be an integer. Given: {1!r}".format(description, inputvalue)
        )

    if not isinstance(minvalue, (int, type(None))):
        raise TypeError(
            "The minvalue must be an integer or None. Given: {0!r}".format(minvalue)
        )

    if not isinstance(maxvalue, (int, type(None))):
        raise TypeError(
            "The maxvalue must be an integer or None. Given: {0!r}".format(maxvalue)
        )

    _check_numerical(inputvalue, minvalue, maxvalue, description)


def _check_numerical(
    inputvalue: Union[int, float],
    minvalue: Union[None, int, float] = None,
    maxvalue: Union[None, int, float] = None,
    description: str = "inputvalue",
) -> None:
    """Check that the given numerical value is valid.

    Args:
        * inputvalue: The value to be checked.
        * minvalue: Minimum value. Use None to skip this part of the test.
        * maxvalue: Maximum value. Use None to skip this part of the test.
        * description: Used in error messages for the checked inputvalue

    Raises:
        TypeError, ValueError

    Note: Can not use the function :func:`_check_string`, as it uses this function
    internally.
    """
    # Type checking
    if not isinstance(description, str):
        raise TypeError(
            "The description should be a string. Given: {0!r}".format(description)
        )

    if not isinstance(inputvalue, (int, float)):
        raise TypeError(
            "The {0} must be numerical. Given: {1!r}".format(description, inputvalue)
        )

    if not isinstance(minvalue, (int, float, type(None))):
        raise TypeError(
            "The minvalue must be numeric or None. Given: {0!r}".format(minvalue)
        )

    if not isinstance(maxvalue, (int, float, type(None))):
        raise TypeError(
            "The maxvalue must be numeric or None. Given: {0!r}".format(maxvalue)
        )

    # Consistency checking
    if (minvalue is not None) and (maxvalue is not None):
        if maxvalue < minvalue:
            raise ValueError(
                "The maxvalue must not be smaller than minvalue. "
                + "Given: {0} and {1}, respectively.".format(maxvalue, minvalue)
            )

    # Value checking
    if minvalue is not None:
        if inputvalue < minvalue:
            raise ValueError(
                "The {0} is too small: {1}, but minimum value is {2}.".format(
                    description, inputvalue, minvalue
                )
            )

    if maxvalue is not None:
        if inputvalue > maxvalue:
            raise ValueError(
                "The {0} is too large: {1}, but maximum value is {2}.".format(
                    description, inputvalue, maxvalue
                )
            )


def _check_bool(inputvalue: bool, description: str = "inputvalue") -> None:
    """Check that the given *inputvalue* is a boolean.

    Args:
        * inputvalue: The value to be checked.
        * description: Used in error messages for the checked inputvalue.

    Raises:
        TypeError, ValueError
    """
    _check_string(description, minlength=1, description="description string")
    if not isinstance(inputvalue, bool):
        raise TypeError(
            "The {0} must be boolean. Given: {1!r}".format(description, inputvalue)
        )


#####################
# Development tools #
#####################


def _get_diagnostic_string() -> str:
    """Generate a diagnostic string, showing the module version, the platform etc.

    Returns:
        A descriptive string.
    """
    text = "\n## Diagnostic output from minimalmodbus ## \n\n"
    text += "Minimalmodbus version: " + __version__ + "\n"
    text += "File name (with relative path): " + __file__ + "\n"
    text += "Full file path: " + os.path.abspath(__file__) + "\n\n"
    text += "pySerial version: " + serial.VERSION + "\n"
    text += "pySerial full file path: " + os.path.abspath(serial.__file__) + "\n\n"
    text += "Platform: " + sys.platform + "\n"
    text += "Filesystem encoding: " + repr(sys.getfilesystemencoding()) + "\n"
    text += "Byteorder: " + sys.byteorder + "\n"
    text += "Python version: " + sys.version + "\n"
    text += "Python version info: " + repr(sys.version_info) + "\n"
    text += "Python flags: " + repr(sys.flags) + "\n"
    text += "Python argv: " + repr(sys.argv) + "\n"
    text += "Python prefix: " + repr(sys.prefix) + "\n"
    text += "Python exec prefix: " + repr(sys.exec_prefix) + "\n"
    text += "Python executable: " + repr(sys.executable) + "\n"
    text += "Float repr style: " + repr(sys.float_repr_style) + "\n\n"
    text += "Variable __name__: " + __name__ + "\n"
    text += "Current directory: " + os.getcwd() + "\n\n"
    text += "Python path: \n"
    text += "\n".join(sys.path) + "\n"
    text += "\n## End of diagnostic output ## \n"
    return text


# For backward compatibility
_getDiagnosticString = _get_diagnostic_string
