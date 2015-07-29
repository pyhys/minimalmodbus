#!/usr/bin/env python
#
#   Copyright 2015 Jonas Berg
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

MinimalModbus: A Python driver for the Modbus RTU and Modbus ASCII protocols via serial port (via RS485 or RS232).
"""

__author__   = 'Jonas Berg'
__email__    = 'pyhys@users.sourceforge.net'
__url__      = 'https://github.com/pyhys/minimalmodbus'
__license__  = 'Apache License, Version 2.0'

__version__  = '0.7'
__status__   = 'Beta'


import os
import serial
import struct
import sys
import time

if sys.version > '3':
    import binascii

# Allow long also in Python3
# http://python3porting.com/noconv.html
if sys.version > '3':
    long = int

_NUMBER_OF_BYTES_PER_REGISTER = 2
_SECONDS_TO_MILLISECONDS = 1000
_ASCII_HEADER = ':'
_ASCII_FOOTER = '\r\n'

# Several instrument instances can share the same serialport
_SERIALPORTS = {}
_LATEST_READ_TIMES = {}

####################
## Default values ##
####################

BAUDRATE = 19200
"""Default value for the baudrate in Baud (int)."""

PARITY   = serial.PARITY_NONE
"""Default value for the parity. See the pySerial module for documentation. Defaults to serial.PARITY_NONE"""

BYTESIZE = 8
"""Default value for the bytesize (int)."""

STOPBITS = 1
"""Default value for the number of stopbits (int)."""

TIMEOUT  = 0.05
"""Default value for the timeout value in seconds (float)."""

CLOSE_PORT_AFTER_EACH_CALL = False
"""Default value for port closure setting."""

#####################
## Named constants ##
#####################

MODE_RTU   = 'rtu'
MODE_ASCII = 'ascii'

##############################
## Modbus instrument object ##
##############################


class Instrument():
    """Instrument class for talking to instruments (slaves) via the Modbus RTU or ASCII protocols (via RS485 or RS232).

    Args:
        * port (str): The serial port name, for example ``/dev/ttyUSB0`` (Linux), ``/dev/tty.usbserial`` (OS X) or ``COM4`` (Windows).
        * slaveaddress (int): Slave address in the range 1 to 247 (use decimal numbers, not hex).
        * mode (str): Mode selection. Can be MODE_RTU or MODE_ASCII.

    """

    def __init__(self, port, slaveaddress, mode=MODE_RTU):
        if port not in _SERIALPORTS or not _SERIALPORTS[port]:
            self.serial = _SERIALPORTS[port] = serial.Serial(port=port, baudrate=BAUDRATE, parity=PARITY, bytesize=BYTESIZE, stopbits=STOPBITS, timeout=TIMEOUT)
        else:
            self.serial = _SERIALPORTS[port]
            if self.serial.port is None:
                self.serial.open()
        """The serial port object as defined by the pySerial module. Created by the constructor.

        Attributes:
            - port (str):      Serial port name.
                - Most often set by the constructor (see the class documentation).
            - baudrate (int):  Baudrate in Baud.
                - Defaults to :data:`BAUDRATE`.
            - parity (probably int): Parity. See the pySerial module for documentation.
                - Defaults to :data:`PARITY`.
            - bytesize (int):  Bytesize in bits.
                - Defaults to :data:`BYTESIZE`.
            - stopbits (int):  The number of stopbits.
                - Defaults to :data:`STOPBITS`.
            - timeout (float): Timeout value in seconds.
                - Defaults to :data:`TIMEOUT`.
        """

        self.address = slaveaddress
        """Slave address (int). Most often set by the constructor (see the class documentation). """

        self.mode = mode
        """Slave mode (str), can be MODE_RTU or MODE_ASCII.  Most often set by the constructor (see the class documentation).

        New in version 0.6.
        """

        self.debug = False
        """Set this to :const:`True` to print the communication details. Defaults to :const:`False`."""

        self.close_port_after_each_call = CLOSE_PORT_AFTER_EACH_CALL
        """If this is :const:`True`, the serial port will be closed after each call. Defaults to :data:`CLOSE_PORT_AFTER_EACH_CALL`. To change it, set the value ``minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL=True`` ."""

        self.precalculate_read_size = True
        """If this is :const:`False`, the serial port reads until timeout
        instead of just reading a specific number of bytes. Defaults to :const:`True`.

        New in version 0.5.
        """
        
        self.handle_local_echo = False
        """Set to to :const:`True` if your RS-485 adaptor has local echo enabled. 
        Then the transmitted message will immeadiately appear at the receive line of the RS-485 adaptor.
        MinimalModbus will then read and discard this data, before reading the data from the slave.
        Defaults to :const:`False`.

        New in version 0.7.
        """

        if  self.close_port_after_each_call:
            self.serial.close()

    def __repr__(self):
        """String representation of the :class:`.Instrument` object."""
        return "{}.{}<id=0x{:x}, address={}, mode={}, close_port_after_each_call={}, precalculate_read_size={}, debug={}, serial={}>".format(
            self.__module__,
            self.__class__.__name__,
            id(self),
            self.address,
            self.mode,
            self.close_port_after_each_call,
            self.precalculate_read_size,
            self.debug,
            self.serial,
            )

    ######################################
    ## Methods for talking to the slave ##
    ######################################


    def read_bit(self, registeraddress, functioncode=2):
        """Read one bit from the slave.

        Args:
            * registeraddress (int): The slave register address (use decimal numbers, not hex).
            * functioncode (int): Modbus function code. Can be 1 or 2.

        Returns:
            The bit value 0 or 1 (int).

        Raises:
            ValueError, TypeError, IOError

        """
        _checkFunctioncode(functioncode, [1, 2])
        return self._genericCommand(functioncode, registeraddress)


    def write_bit(self, registeraddress, value, functioncode=5):
        """Write one bit to the slave.

        Args:
            * registeraddress (int): The slave register address (use decimal numbers, not hex).
            * value (int): 0 or 1
            * functioncode (int): Modbus function code. Can be 5 or 15.

        Returns:
            None

        Raises:
            ValueError, TypeError, IOError

        """
        _checkFunctioncode(functioncode, [5, 15])
        _checkInt(value, minvalue=0, maxvalue=1, description='input value')
        self._genericCommand(functioncode, registeraddress, value)


    def read_register(self, registeraddress, numberOfDecimals=0, functioncode=3, signed=False):
        """Read an integer from one 16-bit register in the slave, possibly scaling it.

        The slave register can hold integer values in the range 0 to 65535 ("Unsigned INT16").

        Args:
            * registeraddress (int): The slave register address (use decimal numbers, not hex).
            * numberOfDecimals (int): The number of decimals for content conversion.
            * functioncode (int): Modbus function code. Can be 3 or 4.
            * signed (bool): Whether the data should be interpreted as unsigned or signed.

        If a value of 77.0 is stored internally in the slave register as 770, then use ``numberOfDecimals=1``
        which will divide the received data by 10 before returning the value.

        Similarly ``numberOfDecimals=2`` will divide the received data by 100 before returning the value.

        Some manufacturers allow negative values for some registers. Instead of
        an allowed integer range 0 to 65535, a range -32768 to 32767 is allowed. This is
        implemented as any received value in the upper range (32768 to 65535) is
        interpreted as negative value (in the range -32768 to -1).

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
            ValueError, TypeError, IOError

        """
        _checkFunctioncode(functioncode, [3, 4])
        _checkInt(numberOfDecimals, minvalue=0, maxvalue=10, description='number of decimals')
        _checkBool(signed, description='signed')
        return self._genericCommand(functioncode, registeraddress, numberOfDecimals=numberOfDecimals, signed=signed)


    def write_register(self, registeraddress, value, numberOfDecimals=0, functioncode=16, signed=False):
        """Write an integer to one 16-bit register in the slave, possibly scaling it.

        The slave register can hold integer values in the range 0 to 65535 ("Unsigned INT16").

        Args:
            * registeraddress (int): The slave register address  (use decimal numbers, not hex).
            * value (int or float): The value to store in the slave register (might be scaled before sending).
            * numberOfDecimals (int): The number of decimals for content conversion.
            * functioncode (int): Modbus function code. Can be 6 or 16.
            * signed (bool): Whether the data should be interpreted as unsigned or signed.

        To store for example ``value=77.0``, use ``numberOfDecimals=1`` if the slave register will hold it as 770 internally.
        This will multiply ``value`` by 10 before sending it to the slave register.

        Similarly ``numberOfDecimals=2`` will multiply ``value`` by 100 before sending it to the slave register.

        For discussion on negative values, the range and on alternative names, see :meth:`.read_register`.

        Use the parameter ``signed=True`` if writing to a register that can hold
        negative values. Then negative input will be automatically converted into
        upper range data (two's complement).

        Returns:
            None

        Raises:
            ValueError, TypeError, IOError

        """
        _checkFunctioncode(functioncode, [6, 16])
        _checkInt(numberOfDecimals, minvalue=0, maxvalue=10, description='number of decimals')
        _checkBool(signed, description='signed')
        _checkNumerical(value, description='input value')

        self._genericCommand(functioncode, registeraddress, value, numberOfDecimals, signed=signed)


    def read_long(self, registeraddress, functioncode=3, signed=False):
        """Read a long integer (32 bits) from the slave.

        Long integers (32 bits = 4 bytes) are stored in two consecutive 16-bit registers in the slave.

        Args:
            * registeraddress (int): The slave register start address (use decimal numbers, not hex).
            * functioncode (int): Modbus function code. Can be 3 or 4.
            * signed (bool): Whether the data should be interpreted as unsigned or signed.

        ============== ================== ================ ==========================
        ``signed``     Data type in slave Alternative name Range
        ============== ================== ================ ==========================
        :const:`False` Unsigned INT32     Unsigned long    0 to 4294967295
        :const:`True`  INT32              Long             -2147483648 to 2147483647
        ============== ================== ================ ==========================

        Returns:
            The numerical value (int).

        Raises:
            ValueError, TypeError, IOError

        """
        _checkFunctioncode(functioncode, [3, 4])
        _checkBool(signed, description='signed')
        return self._genericCommand(functioncode, registeraddress, numberOfRegisters=2, signed=signed, payloadformat='long')


    def write_long(self, registeraddress, value, signed=False):
        """Write a long integer (32 bits) to the slave.

        Long integers (32 bits = 4 bytes) are stored in two consecutive 16-bit registers in the slave.

        Uses Modbus function code 16.

        For discussion on number of bits, number of registers, the range
        and on alternative names, see :meth:`.read_long`.

        Args:
            * registeraddress (int): The slave register start address  (use decimal numbers, not hex).
            * value (int or long): The value to store in the slave.
            * signed (bool): Whether the data should be interpreted as unsigned or signed.

        Returns:
            None

        Raises:
            ValueError, TypeError, IOError

        """
        MAX_VALUE_LONG =  4294967295  # Unsigned INT32
        MIN_VALUE_LONG = -2147483648  # INT32

        _checkInt(value, minvalue=MIN_VALUE_LONG, maxvalue=MAX_VALUE_LONG, description='input value')
        _checkBool(signed, description='signed')
        self._genericCommand(16, registeraddress, value, numberOfRegisters=2, signed=signed, payloadformat='long')


    def read_float(self, registeraddress, functioncode=3, numberOfRegisters=2):
        """Read a floating point number from the slave.

        Floats are stored in two or more consecutive 16-bit registers in the slave. The
        encoding is according to the standard IEEE 754.

        There are differences in the byte order used by different manufacturers. A floating
        point value of 1.0 is encoded (in single precision) as 3f800000 (hex). In this
        implementation the data will be sent as ``'\\x3f\\x80'`` and ``'\\x00\\x00'``
        to two consecutetive registers . Make sure to test that it makes sense for your instrument.
        It is pretty straight-forward to change this code if some other byte order is
        required by anyone (see support section).

        Args:
            * registeraddress (int): The slave register start address (use decimal numbers, not hex).
            * functioncode (int): Modbus function code. Can be 3 or 4.
            * numberOfRegisters (int): The number of registers allocated for the float. Can be 2 or 4.

        ====================================== ================= =========== =================
        Type of floating point number in slave Size              Registers   Range
        ====================================== ================= =========== =================
        Single precision (binary32)            32 bits (4 bytes) 2 registers 1.4E-45 to 3.4E38
        Double precision (binary64)            64 bits (8 bytes) 4 registers 5E-324 to 1.8E308
        ====================================== ================= =========== =================

        Returns:
            The numerical value (float).

        Raises:
            ValueError, TypeError, IOError

        """
        _checkFunctioncode(functioncode, [3, 4])
        _checkInt(numberOfRegisters, minvalue=2, maxvalue=4, description='number of registers')
        return self._genericCommand(functioncode, registeraddress, numberOfRegisters=numberOfRegisters, payloadformat='float')


    def write_float(self, registeraddress, value, numberOfRegisters=2):
        """Write a floating point number to the slave.

        Floats are stored in two or more consecutive 16-bit registers in the slave.

        Uses Modbus function code 16.

        For discussion on precision, number of registers and on byte order, see :meth:`.read_float`.

        Args:
            * registeraddress (int): The slave register start address (use decimal numbers, not hex).
            * value (float or int): The value to store in the slave
            * numberOfRegisters (int): The number of registers allocated for the float. Can be 2 or 4.

        Returns:
            None

        Raises:
            ValueError, TypeError, IOError

        """
        _checkNumerical(value, description='input value')
        _checkInt(numberOfRegisters, minvalue=2, maxvalue=4, description='number of registers')
        self._genericCommand(16, registeraddress, value, \
            numberOfRegisters=numberOfRegisters, payloadformat='float')


    def read_string(self, registeraddress, numberOfRegisters=16, functioncode=3):
        """Read a string from the slave.

        Each 16-bit register in the slave are interpreted as two characters (1 byte = 8 bits).
        For example 16 consecutive registers can hold 32 characters (32 bytes).

        Args:
            * registeraddress (int): The slave register start address (use decimal numbers, not hex).
            * numberOfRegisters (int): The number of registers allocated for the string.
            * functioncode (int): Modbus function code. Can be 3 or 4.

        Returns:
            The string (str).

        Raises:
            ValueError, TypeError, IOError

        """
        _checkFunctioncode(functioncode, [3, 4])
        _checkInt(numberOfRegisters, minvalue=1, description='number of registers for read string')
        return self._genericCommand(functioncode, registeraddress, \
            numberOfRegisters=numberOfRegisters, payloadformat='string')


    def write_string(self, registeraddress, textstring, numberOfRegisters=16):
        """Write a string to the slave.

        Each 16-bit register in the slave are interpreted as two characters (1 byte = 8 bits).
        For example 16 consecutive registers can hold 32 characters (32 bytes).

        Uses Modbus function code 16.

        Args:
            * registeraddress (int): The slave register start address  (use decimal numbers, not hex).
            * textstring (str): The string to store in the slave
            * numberOfRegisters (int): The number of registers allocated for the string.

        If the textstring is longer than the 2*numberOfRegisters, an error is raised.
        Shorter strings are padded with spaces.

        Returns:
            None

        Raises:
            ValueError, TypeError, IOError

        """
        _checkInt(numberOfRegisters, minvalue=1, description='number of registers for write string')
        _checkString(textstring, 'input string', minlength=1, maxlength=2 * numberOfRegisters)
        self._genericCommand(16, registeraddress, textstring, \
            numberOfRegisters=numberOfRegisters, payloadformat='string')


    def read_registers(self, registeraddress, numberOfRegisters, functioncode=3):
        """Read integers from 16-bit registers in the slave.

        The slave registers can hold integer values in the range 0 to 65535 ("Unsigned INT16").

        Args:
            * registeraddress (int): The slave register start address (use decimal numbers, not hex).
            * numberOfRegisters (int): The number of registers to read.
            * functioncode (int): Modbus function code. Can be 3 or 4.

        Any scaling of the register data, or converting it to negative number (two's complement)
        must be done manually.

        Returns:
            The register data (a list of int).

        Raises:
            ValueError, TypeError, IOError

        """
        _checkFunctioncode(functioncode, [3, 4])
        _checkInt(numberOfRegisters, minvalue=1, description='number of registers')
        return self._genericCommand(functioncode, registeraddress, \
            numberOfRegisters=numberOfRegisters, payloadformat='registers')


    def write_registers(self, registeraddress, values):
        """Write integers to 16-bit registers in the slave.

        The slave register can hold integer values in the range 0 to 65535 ("Unsigned INT16").

        Uses Modbus function code 16.

        The number of registers that will be written is defined by the length of the ``values`` list.

        Args:
            * registeraddress (int): The slave register start address (use decimal numbers, not hex).
            * values (list of int): The values to store in the slave registers.

        Any scaling of the register data, or converting it to negative number (two's complement)
        must be done manually.

        Returns:
            None

        Raises:
            ValueError, TypeError, IOError

        """
        if not isinstance(values, list):
            raise TypeError('The "values parameter" must be a list. Given: {0!r}'.format(values))
        _checkInt(len(values), minvalue=1, description='length of input list')
        # Note: The content of the list is checked at content conversion.

        self._genericCommand(16, registeraddress, values, numberOfRegisters=len(values), payloadformat='registers')

    #####################
    ## Generic command ##
    #####################


    def _genericCommand(self, functioncode, registeraddress, value=None, \
            numberOfDecimals=0, numberOfRegisters=1, signed=False, payloadformat=None):
        """Generic command for reading and writing registers and bits.

        Args:
            * functioncode (int): Modbus function code.
            * registeraddress (int): The register address  (use decimal numbers, not hex).
            * value (numerical or string or None or list of int): The value to store in the register. Depends on payloadformat.
            * numberOfDecimals (int): The number of decimals for content conversion. Only for a single register.
            * numberOfRegisters (int): The number of registers to read/write. Only certain values allowed, depends on payloadformat.
            * signed (bool): Whether the data should be interpreted as unsigned or signed. Only for a single register or for payloadformat='long'.
            * payloadformat (None or string): None, 'long', 'float', 'string', 'register', 'registers'. Not necessary for single registers or bits.

        If a value of 77.0 is stored internally in the slave register as 770,
        then use ``numberOfDecimals=1`` which will divide the received data from the slave by 10
        before returning the value. Similarly ``numberOfDecimals=2`` will divide
        the received data by 100 before returning the value. Same functionality is also used
        when writing data to the slave.

        Returns:
            The register data in numerical value (int or float), or the bit value 0 or 1 (int), or ``None``.

        Raises:
            ValueError, TypeError, IOError

        """
        NUMBER_OF_BITS = 1
        NUMBER_OF_BYTES_FOR_ONE_BIT = 1
        NUMBER_OF_BYTES_BEFORE_REGISTERDATA = 1
        ALL_ALLOWED_FUNCTIONCODES = list(range(1, 7)) + [15, 16]  # To comply with both Python2 and Python3
        MAX_NUMBER_OF_REGISTERS = 255

        # Payload format constants, so datatypes can be told apart.
        # Note that bit datatype not is included, because it uses other functioncodes.
        PAYLOADFORMAT_LONG      = 'long'
        PAYLOADFORMAT_FLOAT     = 'float'
        PAYLOADFORMAT_STRING    = 'string'
        PAYLOADFORMAT_REGISTER  = 'register'
        PAYLOADFORMAT_REGISTERS = 'registers'

        ALL_PAYLOADFORMATS = [PAYLOADFORMAT_LONG, PAYLOADFORMAT_FLOAT, \
            PAYLOADFORMAT_STRING, PAYLOADFORMAT_REGISTER, PAYLOADFORMAT_REGISTERS]

        ## Check input values ##
        _checkFunctioncode(functioncode, ALL_ALLOWED_FUNCTIONCODES)  # Note: The calling facade functions should validate this
        _checkRegisteraddress(registeraddress)
        _checkInt(numberOfDecimals, minvalue=0, description='number of decimals')
        _checkInt(numberOfRegisters, minvalue=1, maxvalue=MAX_NUMBER_OF_REGISTERS, description='number of registers')
        _checkBool(signed, description='signed')

        if payloadformat is not None:
            if payloadformat not in ALL_PAYLOADFORMATS:
                raise ValueError('Wrong payload format variable. Given: {0!r}'.format(payloadformat))

        ## Check combinations of input parameters ##
        numberOfRegisterBytes = numberOfRegisters * _NUMBER_OF_BYTES_PER_REGISTER

                    # Payload format
        if functioncode in [3, 4, 6, 16] and payloadformat is None:
            payloadformat = PAYLOADFORMAT_REGISTER

        if functioncode in [3, 4, 6, 16]:
            if payloadformat not in ALL_PAYLOADFORMATS:
                raise ValueError('The payload format is unknown. Given format: {0!r}, functioncode: {1!r}.'.\
                    format(payloadformat, functioncode))
        else:
            if payloadformat is not None:
                raise ValueError('The payload format given is not allowed for this function code. ' + \
                    'Given format: {0!r}, functioncode: {1!r}.'.format(payloadformat, functioncode))

                    # Signed and numberOfDecimals
        if signed:
            if payloadformat not in [PAYLOADFORMAT_REGISTER, PAYLOADFORMAT_LONG]:
                raise ValueError('The "signed" parameter can not be used for this data format. ' + \
                    'Given format: {0!r}.'.format(payloadformat))

        if numberOfDecimals > 0 and payloadformat != PAYLOADFORMAT_REGISTER:
            raise ValueError('The "numberOfDecimals" parameter can not be used for this data format. ' + \
                'Given format: {0!r}.'.format(payloadformat))

                    # Number of registers
        if functioncode not in [3, 4, 16] and numberOfRegisters != 1:
            raise ValueError('The numberOfRegisters is not valid for this function code. ' + \
                'NumberOfRegisters: {0!r}, functioncode {1}.'.format(numberOfRegisters, functioncode))

        if functioncode == 16 and payloadformat == PAYLOADFORMAT_REGISTER and numberOfRegisters != 1:
            raise ValueError('Wrong numberOfRegisters when writing to a ' + \
                'single register. Given {0!r}.'.format(numberOfRegisters))
            # Note: For function code 16 there is checking also in the content conversion functions.

                    # Value
        if functioncode in [5, 6, 15, 16] and value is None:
            raise ValueError('The input value is not valid for this function code. ' + \
                'Given {0!r} and {1}.'.format(value, functioncode))

        if functioncode == 16 and payloadformat in [PAYLOADFORMAT_REGISTER, PAYLOADFORMAT_FLOAT, PAYLOADFORMAT_LONG]:
            _checkNumerical(value, description='input value')

        if functioncode == 6 and payloadformat == PAYLOADFORMAT_REGISTER:
            _checkNumerical(value, description='input value')

                    # Value for string
        if functioncode == 16 and payloadformat == PAYLOADFORMAT_STRING:
            _checkString(value, 'input string', minlength=1, maxlength=numberOfRegisterBytes)
            # Note: The string might be padded later, so the length might be shorter than numberOfRegisterBytes.

                    # Value for registers
        if functioncode == 16 and payloadformat == PAYLOADFORMAT_REGISTERS:
            if not isinstance(value, list):
                raise TypeError('The value parameter must be a list. Given {0!r}.'.format(value))

            if len(value) != numberOfRegisters:
                raise ValueError('The list length does not match number of registers. ' + \
                    'List: {0!r},  Number of registers: {1!r}.'.format(value, numberOfRegisters))

        ## Build payload to slave ##
        if functioncode in [1, 2]:
            payloadToSlave = _numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(NUMBER_OF_BITS)

        elif functioncode in [3, 4]:
            payloadToSlave = _numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(numberOfRegisters)

        elif functioncode == 5:
            payloadToSlave = _numToTwoByteString(registeraddress) + \
                            _createBitpattern(functioncode, value)

        elif functioncode == 6:
            payloadToSlave = _numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(value, numberOfDecimals, signed=signed)

        elif functioncode == 15:
            payloadToSlave = _numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(NUMBER_OF_BITS) + \
                            _numToOneByteString(NUMBER_OF_BYTES_FOR_ONE_BIT) + \
                            _createBitpattern(functioncode, value)

        elif functioncode == 16:
            if payloadformat == PAYLOADFORMAT_REGISTER:
                registerdata = _numToTwoByteString(value, numberOfDecimals, signed=signed)

            elif payloadformat == PAYLOADFORMAT_STRING:
                registerdata = _textstringToBytestring(value, numberOfRegisters)

            elif payloadformat == PAYLOADFORMAT_LONG:
                registerdata = _longToBytestring(value, signed, numberOfRegisters)

            elif payloadformat == PAYLOADFORMAT_FLOAT:
                registerdata = _floatToBytestring(value, numberOfRegisters)

            elif payloadformat == PAYLOADFORMAT_REGISTERS:
                registerdata = _valuelistToBytestring(value, numberOfRegisters)

            assert len(registerdata) == numberOfRegisterBytes
            payloadToSlave = _numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(numberOfRegisters) + \
                            _numToOneByteString(numberOfRegisterBytes) + \
                            registerdata

        ## Communicate ##
        payloadFromSlave = self._performCommand(functioncode, payloadToSlave)

        ## Check the contents in the response payload ##
        if functioncode in [1, 2, 3, 4]:
            _checkResponseByteCount(payloadFromSlave)  # response byte count

        if functioncode in [5, 6, 15, 16]:
            _checkResponseRegisterAddress(payloadFromSlave, registeraddress)  # response register address

        if functioncode == 5:
            _checkResponseWriteData(payloadFromSlave, _createBitpattern(functioncode, value))  # response write data

        if functioncode == 6:
            _checkResponseWriteData(payloadFromSlave, \
                _numToTwoByteString(value, numberOfDecimals, signed=signed))  # response write data

        if functioncode == 15:
            _checkResponseNumberOfRegisters(payloadFromSlave, NUMBER_OF_BITS)  # response number of bits

        if functioncode == 16:
            _checkResponseNumberOfRegisters(payloadFromSlave, numberOfRegisters)  # response number of registers

        ## Calculate return value ##
        if functioncode in [1, 2]:
            registerdata = payloadFromSlave[NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
            if len(registerdata) != NUMBER_OF_BYTES_FOR_ONE_BIT:
                raise ValueError('The registerdata length does not match NUMBER_OF_BYTES_FOR_ONE_BIT. ' + \
                    'Given {0}.'.format(len(registerdata)))

            return _bitResponseToValue(registerdata)

        if functioncode in [3, 4]:
            registerdata = payloadFromSlave[NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
            if len(registerdata) != numberOfRegisterBytes:
                raise ValueError('The registerdata length does not match number of register bytes. ' + \
                    'Given {0!r} and {1!r}.'.format(len(registerdata), numberOfRegisterBytes))

            if payloadformat == PAYLOADFORMAT_STRING:
                return _bytestringToTextstring(registerdata, numberOfRegisters)

            elif payloadformat == PAYLOADFORMAT_LONG:
                return _bytestringToLong(registerdata, signed, numberOfRegisters)

            elif payloadformat == PAYLOADFORMAT_FLOAT:
                return _bytestringToFloat(registerdata, numberOfRegisters)

            elif payloadformat == PAYLOADFORMAT_REGISTERS:
                return _bytestringToValuelist(registerdata, numberOfRegisters)

            elif payloadformat == PAYLOADFORMAT_REGISTER:
                return _twoByteStringToNum(registerdata, numberOfDecimals, signed=signed)

            raise ValueError('Wrong payloadformat for return value generation. ' + \
                'Given {0}'.format(payloadformat))

    ##########################################
    ## Communication implementation details ##
    ##########################################


    def _performCommand(self, functioncode, payloadToSlave):
        """Performs the command having the *functioncode*.

        Args:
            * functioncode (int): The function code for the command to be performed. Can for example be 'Write register' = 16.
            * payloadToSlave (str): Data to be transmitted to the slave (will be embedded in slaveaddress, CRC etc)

        Returns:
            The extracted data payload from the slave (a string). It has been stripped of CRC etc.

        Raises:
            ValueError, TypeError.

        Makes use of the :meth:`_communicate` method. The request is generated
        with the :func:`_embedPayload` function, and the parsing of the
        response is done with the :func:`_extractPayload` function.

        """
        DEFAULT_NUMBER_OF_BYTES_TO_READ = 1000

        _checkFunctioncode(functioncode, None)
        _checkString(payloadToSlave, description='payload')

        # Build request
        request = _embedPayload(self.address, self.mode, functioncode, payloadToSlave)

        # Calculate number of bytes to read
        number_of_bytes_to_read = DEFAULT_NUMBER_OF_BYTES_TO_READ
        if self.precalculate_read_size:
            try:
                number_of_bytes_to_read = _predictResponseSize(self.mode, functioncode, payloadToSlave)
            except:
                if self.debug:
                    template = 'MinimalModbus debug mode. Could not precalculate response size for Modbus {} mode. ' + \
                        'Will read {} bytes. request: {!r}'
                    _print_out(template.format(self.mode, number_of_bytes_to_read, request))

        # Communicate
        response = self._communicate(request, number_of_bytes_to_read)

        # Extract payload
        payloadFromSlave = _extractPayload(response, self.address, self.mode, functioncode)
        return payloadFromSlave


    def _communicate(self, request, number_of_bytes_to_read):
        """Talk to the slave via a serial port.

        Args:
            request (str): The raw request that is to be sent to the slave.
            number_of_bytes_to_read (int): number of bytes to read

        Returns:
            The raw data (string) returned from the slave.

        Raises:
            TypeError, ValueError, IOError

        Note that the answer might have strange ASCII control signs, which
        makes it difficult to print it in the promt (messes up a bit).
        Use repr() to make the string printable (shows ASCII values for control signs.)

        Will block until reaching *number_of_bytes_to_read* or timeout.

        If the attribute :attr:`Instrument.debug` is :const:`True`, the communication details are printed.

        If the attribute :attr:`Instrument.close_port_after_each_call` is :const:`True` the
        serial port is closed after each call.

        Timing::

                                                  Request from master (Master is writing)
                                                  |
                                                  |       Response from slave (Master is reading)
                                                  |       |
            ----W----R----------------------------W-------R----------------------------------------
                     |                            |       |
                     |<----- Silent period ------>|       |
                                                  |       |
                             Roundtrip time  ---->|-------|<--

        The resolution for Python's time.time() is lower on Windows than on Linux.
        It is about 16 ms on Windows according to
        http://stackoverflow.com/questions/157359/accurate-timestamping-in-python

        For Python3, the information sent to and from pySerial should be of the type bytes.
        This is taken care of automatically by MinimalModbus.
        
        

        """

        _checkString(request, minlength=1, description='request')
        _checkInt(number_of_bytes_to_read)

        if self.debug:
            _print_out('\nMinimalModbus debug mode. Writing to instrument (expecting {} bytes back): {!r} ({})'. \
                format(number_of_bytes_to_read, request, _hexlify(request)))

        if self.close_port_after_each_call:
            self.serial.open()

        #self.serial.flushInput() TODO

        if sys.version_info[0] > 2:
            request = bytes(request, encoding='latin1')  # Convert types to make it Python3 compatible

        # Sleep to make sure 3.5 character times have passed
        minimum_silent_period   = _calculate_minimum_silent_period(self.serial.baudrate)
        time_since_read         = time.time() - _LATEST_READ_TIMES.get(self.serial.port, 0)

        if time_since_read < minimum_silent_period:
            sleep_time = minimum_silent_period - time_since_read

            if self.debug:
                template = 'MinimalModbus debug mode. Sleeping for {:.1f} ms. ' + \
                        'Minimum silent period: {:.1f} ms, time since read: {:.1f} ms.'
                text = template.format(
                    sleep_time * _SECONDS_TO_MILLISECONDS,
                    minimum_silent_period * _SECONDS_TO_MILLISECONDS,
                    time_since_read * _SECONDS_TO_MILLISECONDS)
                _print_out(text)

            time.sleep(sleep_time)

        elif self.debug:
            template = 'MinimalModbus debug mode. No sleep required before write. ' + \
                'Time since previous read: {:.1f} ms, minimum silent period: {:.2f} ms.'
            text = template.format(
                time_since_read * _SECONDS_TO_MILLISECONDS,
                minimum_silent_period * _SECONDS_TO_MILLISECONDS)
            _print_out(text)

        # Write request
        latest_write_time = time.time()
        
        self.serial.write(request)

        # Read and discard local echo
        if self.handle_local_echo:
            localEchoToDiscard = self.serial.read(len(request))
            if self.debug:
                template = 'MinimalModbus debug mode. Discarding this local echo: {!r} ({} bytes).' 
                text = template.format(localEchoToDiscard, len(localEchoToDiscard))
                _print_out(text)
            if localEchoToDiscard != request:
                template = 'Local echo handling is enabled, but the local echo does not match the sent request. ' + \
                    'Request: {!r} ({} bytes), local echo: {!r} ({} bytes).' 
                text = template.format(request, len(request), localEchoToDiscard, len(localEchoToDiscard))
                raise IOError(text)

        # Read response
        answer = self.serial.read(number_of_bytes_to_read)
        _LATEST_READ_TIMES[self.serial.port] = time.time()

        if self.close_port_after_each_call:
            self.serial.close()

        if sys.version_info[0] > 2:
            answer = str(answer, encoding='latin1')  # Convert types to make it Python3 compatible

        if self.debug:
            template = 'MinimalModbus debug mode. Response from instrument: {!r} ({}) ({} bytes), ' + \
                'roundtrip time: {:.1f} ms. Timeout setting: {:.1f} ms.\n'
            text = template.format(
                answer,
                _hexlify(answer),
                len(answer),
                (_LATEST_READ_TIMES.get(self.serial.port, 0) - latest_write_time) * _SECONDS_TO_MILLISECONDS,
                self.serial.timeout * _SECONDS_TO_MILLISECONDS)
            _print_out(text)

        if len(answer) == 0:
            raise IOError('No communication with the instrument (no answer)')

        return answer

####################
# Payload handling #
####################


def _embedPayload(slaveaddress, mode, functioncode, payloaddata):
    """Build a request from the slaveaddress, the function code and the payload data.

    Args:
        * slaveaddress (int): The address of the slave.
        * mode (str): The modbus protcol mode (MODE_RTU or MODE_ASCII)
        * functioncode (int): The function code for the command to be performed. Can for example be 16 (Write register).
        * payloaddata (str): The byte string to be sent to the slave.

    Returns:
        The built (raw) request string for sending to the slave (including CRC etc).

    Raises:
        ValueError, TypeError.

    The resulting request has the format:
     * RTU Mode: slaveaddress byte + functioncode byte + payloaddata + CRC (which is two bytes).
     * ASCII Mode: header (:) + slaveaddress (2 characters) + functioncode (2 characters) + payloaddata + LRC (which is two characters) + footer (CRLF)

    The LRC or CRC is calculated from the byte string made up of slaveaddress + functioncode + payloaddata.
    The header, LRC/CRC, and footer are excluded from the calculation.

    """
    _checkSlaveaddress(slaveaddress)
    _checkMode(mode)
    _checkFunctioncode(functioncode, None)
    _checkString(payloaddata, description='payload')

    firstPart = _numToOneByteString(slaveaddress) + _numToOneByteString(functioncode) + payloaddata

    if mode == MODE_ASCII:
        request = _ASCII_HEADER + \
                _hexencode(firstPart) + \
                _hexencode(_calculateLrcString(firstPart)) + \
                _ASCII_FOOTER
    else:
        request = firstPart + _calculateCrcString(firstPart)

    return request


def _extractPayload(response, slaveaddress, mode, functioncode):
    """Extract the payload data part from the slave's response.

    Args:
        * response (str): The raw response byte string from the slave.
        * slaveaddress (int): The adress of the slave. Used here for error checking only.
        * mode (str): The modbus protcol mode (MODE_RTU or MODE_ASCII)
        * functioncode (int): Used here for error checking only.

    Returns:
        The payload part of the *response* string.

    Raises:
        ValueError, TypeError. Raises an exception if there is any problem with the received address, the functioncode or the CRC.

    The received response should have the format:
    * RTU Mode: slaveaddress byte + functioncode byte + payloaddata + CRC (which is two bytes)
    * ASCII Mode: header (:) + slaveaddress byte + functioncode byte + payloaddata + LRC (which is two characters) + footer (CRLF)

    For development purposes, this function can also be used to extract the payload from the request sent TO the slave.

    """
    BYTEPOSITION_FOR_ASCII_HEADER          = 0  # Relative to plain response

    BYTEPOSITION_FOR_SLAVEADDRESS          = 0  # Relative to (stripped) response
    BYTEPOSITION_FOR_FUNCTIONCODE          = 1

    NUMBER_OF_RESPONSE_STARTBYTES          = 2  # Number of bytes before the response payload (in stripped response)
    NUMBER_OF_CRC_BYTES                    = 2
    NUMBER_OF_LRC_BYTES                    = 1
    BITNUMBER_FUNCTIONCODE_ERRORINDICATION = 7

    MINIMAL_RESPONSE_LENGTH_RTU            = NUMBER_OF_RESPONSE_STARTBYTES + NUMBER_OF_CRC_BYTES
    MINIMAL_RESPONSE_LENGTH_ASCII          = 9

    # Argument validity testing
    _checkString(response, description='response')
    _checkSlaveaddress(slaveaddress)
    _checkMode(mode)
    _checkFunctioncode(functioncode, None)

    plainresponse = response

    # Validate response length
    if mode == MODE_ASCII:
        if len(response) < MINIMAL_RESPONSE_LENGTH_ASCII:
            raise ValueError('Too short Modbus ASCII response (minimum length {} bytes). Response: {!r}'.format( \
                MINIMAL_RESPONSE_LENGTH_ASCII,
                response))
    elif len(response) < MINIMAL_RESPONSE_LENGTH_RTU:
            raise ValueError('Too short Modbus RTU response (minimum length {} bytes). Response: {!r}'.format( \
                MINIMAL_RESPONSE_LENGTH_RTU,
                response))

    # Validate the ASCII header and footer.
    if mode == MODE_ASCII:
        if response[BYTEPOSITION_FOR_ASCII_HEADER] != _ASCII_HEADER:
            raise ValueError('Did not find header ({!r}) as start of ASCII response. The plain response is: {!r}'.format( \
                _ASCII_HEADER,
                response))
        elif response[-len(_ASCII_FOOTER):] != _ASCII_FOOTER:
            raise ValueError('Did not find footer ({!r}) as end of ASCII response. The plain response is: {!r}'.format( \
                _ASCII_FOOTER,
                response))

        # Strip ASCII header and footer
        response = response[1:-2]

        if len(response) % 2 != 0:
            template = 'Stripped ASCII frames should have an even number of bytes, but is {} bytes. ' + \
                    'The stripped response is: {!r} (plain response: {!r})'
            raise ValueError(template.format(len(response), response, plainresponse))

        # Convert the ASCII (stripped) response string to RTU-like response string
        response = _hexdecode(response)

    # Validate response checksum
    if mode == MODE_ASCII:
        calculateChecksum = _calculateLrcString
        numberOfChecksumBytes = NUMBER_OF_LRC_BYTES
    else:
        calculateChecksum = _calculateCrcString
        numberOfChecksumBytes = NUMBER_OF_CRC_BYTES

    receivedChecksum = response[-numberOfChecksumBytes:]
    responseWithoutChecksum = response[0 : len(response) - numberOfChecksumBytes]
    calculatedChecksum = calculateChecksum(responseWithoutChecksum)

    if receivedChecksum != calculatedChecksum:
        template = 'Checksum error in {} mode: {!r} instead of {!r} . The response is: {!r} (plain response: {!r})'
        text = template.format(
                mode,
                receivedChecksum,
                calculatedChecksum,
                response, plainresponse)
        raise ValueError(text)

    # Check slave address
    responseaddress = ord(response[BYTEPOSITION_FOR_SLAVEADDRESS])

    if responseaddress != slaveaddress:
        raise ValueError('Wrong return slave address: {} instead of {}. The response is: {!r}'.format( \
            responseaddress, slaveaddress, response))

    # Check function code
    receivedFunctioncode = ord(response[BYTEPOSITION_FOR_FUNCTIONCODE])

    if receivedFunctioncode == _setBitOn(functioncode, BITNUMBER_FUNCTIONCODE_ERRORINDICATION):
        raise ValueError('The slave is indicating an error. The response is: {!r}'.format(response))

    elif receivedFunctioncode != functioncode:
        raise ValueError('Wrong functioncode: {} instead of {}. The response is: {!r}'.format( \
            receivedFunctioncode, functioncode, response))

    # Read data payload
    firstDatabyteNumber = NUMBER_OF_RESPONSE_STARTBYTES

    if mode == MODE_ASCII:
        lastDatabyteNumber = len(response) - NUMBER_OF_LRC_BYTES
    else:
        lastDatabyteNumber = len(response) - NUMBER_OF_CRC_BYTES

    payload = response[firstDatabyteNumber:lastDatabyteNumber]
    return payload

############################################
## Serial communication utility functions ##
############################################


def _predictResponseSize(mode, functioncode, payloadToSlave):
    """Calculate the number of bytes that should be received from the slave.

    Args:
     * mode (str): The modbus protcol mode (MODE_RTU or MODE_ASCII)
     * functioncode (int): Modbus function code.
     * payloadToSlave (str): The raw request that is to be sent to the slave (not hex encoded string)

    Returns:
        The preducted number of bytes (int) in the response.

    Raises:
        ValueError, TypeError.

    """
    MIN_PAYLOAD_LENGTH = 4  # For implemented functioncodes here
    BYTERANGE_FOR_GIVEN_SIZE = slice(2, 4)  # Within the payload

    NUMBER_OF_PAYLOAD_BYTES_IN_WRITE_CONFIRMATION = 4
    NUMBER_OF_PAYLOAD_BYTES_FOR_BYTECOUNTFIELD = 1

    RTU_TO_ASCII_PAYLOAD_FACTOR = 2

    NUMBER_OF_RTU_RESPONSE_STARTBYTES   = 2
    NUMBER_OF_RTU_RESPONSE_ENDBYTES     = 2
    NUMBER_OF_ASCII_RESPONSE_STARTBYTES = 5
    NUMBER_OF_ASCII_RESPONSE_ENDBYTES   = 4

    # Argument validity testing
    _checkMode(mode)
    _checkFunctioncode(functioncode, None)
    _checkString(payloadToSlave, description='payload', minlength=MIN_PAYLOAD_LENGTH)

    # Calculate payload size
    if functioncode in [5, 6, 15, 16]:
        response_payload_size = NUMBER_OF_PAYLOAD_BYTES_IN_WRITE_CONFIRMATION

    elif functioncode in [1, 2, 3, 4]:
        given_size = _twoByteStringToNum(payloadToSlave[BYTERANGE_FOR_GIVEN_SIZE])
        if functioncode == 1 or functioncode == 2:
            # Algorithm from MODBUS APPLICATION PROTOCOL SPECIFICATION V1.1b
            number_of_inputs = given_size
            response_payload_size = NUMBER_OF_PAYLOAD_BYTES_FOR_BYTECOUNTFIELD + \
                                    number_of_inputs // 8 + (1 if number_of_inputs % 8 else 0)

        elif functioncode == 3 or functioncode == 4:
            number_of_registers = given_size
            response_payload_size = NUMBER_OF_PAYLOAD_BYTES_FOR_BYTECOUNTFIELD + \
                                    number_of_registers * _NUMBER_OF_BYTES_PER_REGISTER

    else:
        raise ValueError('Wrong functioncode: {}. The payload is: {!r}'.format( \
            functioncode, payloadToSlave))

    # Calculate number of bytes to read
    if mode == MODE_ASCII:
        return NUMBER_OF_ASCII_RESPONSE_STARTBYTES + \
            response_payload_size * RTU_TO_ASCII_PAYLOAD_FACTOR + \
            NUMBER_OF_ASCII_RESPONSE_ENDBYTES
    else:
        return NUMBER_OF_RTU_RESPONSE_STARTBYTES + \
            response_payload_size + \
            NUMBER_OF_RTU_RESPONSE_ENDBYTES


def _calculate_minimum_silent_period(baudrate):
    """Calculate the silent period length to comply with the 3.5 character silence between messages.

    Args:
        baudrate (numerical): The baudrate for the serial port

    Returns:
        The number of seconds (float) that should pass between each message on the bus.

    Raises:
        ValueError, TypeError.

    """
    _checkNumerical(baudrate, minvalue=1, description='baudrate')  # Avoid division by zero

    BITTIMES_PER_CHARACTERTIME = 11
    MINIMUM_SILENT_CHARACTERTIMES = 3.5

    bittime = 1 / float(baudrate)
    return bittime * BITTIMES_PER_CHARACTERTIME * MINIMUM_SILENT_CHARACTERTIMES

##############################
# String and num conversions #
##############################


def _numToOneByteString(inputvalue):
    """Convert a numerical value to a one-byte string.

    Args:
        inputvalue (int): The value to be converted. Should be >=0 and <=255.

    Returns:
        A one-byte string created by chr(inputvalue).

    Raises:
        TypeError, ValueError

    """
    _checkInt(inputvalue, minvalue=0, maxvalue=0xFF)

    return chr(inputvalue)


def _numToTwoByteString(value, numberOfDecimals=0, LsbFirst=False, signed=False):
    """Convert a numerical value to a two-byte string, possibly scaling it.

    Args:
        * value (float or int): The numerical value to be converted.
        * numberOfDecimals (int): Number of decimals, 0 or more, for scaling.
        * LsbFirst (bol): Whether the least significant byte should be first in the resulting string.
        * signed (bol): Whether negative values should be accepted.

    Returns:
        A two-byte string.

    Raises:
        TypeError, ValueError. Gives DeprecationWarning instead of ValueError
        for some values in Python 2.6.

    Use ``numberOfDecimals=1`` to multiply ``value`` by 10 before sending it to the slave register.
    Similarly ``numberOfDecimals=2`` will multiply ``value`` by 100 before sending it to the slave register.

    Use the parameter ``signed=True`` if making a bytestring that can hold
    negative values. Then negative input will be automatically converted into
    upper range data (two's complement).

    The byte order is controlled by the ``LsbFirst`` parameter, as seen here:

    ====================== ============= ====================================
    ``LsbFirst`` parameter Endianness    Description
    ====================== ============= ====================================
    False (default)        Big-endian    Most significant byte is sent first
    True                   Little-endian Least significant byte is sent first
    ====================== ============= ====================================

    For example:
        To store for example value=77.0, use ``numberOfDecimals = 1`` if the register will hold it as 770 internally.
        The value 770 (dec) is 0302 (hex), where the most significant byte is 03 (hex) and the
        least significant byte is 02 (hex). With ``LsbFirst = False``, the most significant byte is given first
        why the resulting string is ``\\x03\\x02``, which has the length 2.

    """
    _checkNumerical(value, description='inputvalue')
    _checkInt(numberOfDecimals, minvalue=0, description='number of decimals')
    _checkBool(LsbFirst, description='LsbFirst')
    _checkBool(signed, description='signed parameter')

    multiplier = 10 ** numberOfDecimals
    integer = int(float(value) * multiplier)

    if LsbFirst:
        formatcode = '<'  # Little-endian
    else:
        formatcode = '>'  # Big-endian
    if signed:
        formatcode += 'h'  # (Signed) short (2 bytes)
    else:
        formatcode += 'H'  # Unsigned short (2 bytes)

    outstring = _pack(formatcode, integer)
    assert len(outstring) == 2
    return outstring


def _twoByteStringToNum(bytestring, numberOfDecimals=0, signed=False):
    """Convert a two-byte string to a numerical value, possibly scaling it.

    Args:
        * bytestring (str): A string of length 2.
        * numberOfDecimals (int): The number of decimals. Defaults to 0.
        * signed (bol): Whether large positive values should be interpreted as negative values.

    Returns:
        The numerical value (int or float) calculated from the ``bytestring``.

    Raises:
        TypeError, ValueError

    Use the parameter ``signed=True`` if converting a bytestring that can hold
    negative values. Then upper range data will be automatically converted into
    negative return values (two's complement).

    Use ``numberOfDecimals=1`` to divide the received data by 10 before returning the value.
    Similarly ``numberOfDecimals=2`` will divide the received data by 100 before returning the value.

    The byte order is big-endian, meaning that the most significant byte is sent first.

    For example:
        A string ``\\x03\\x02`` (which has the length 2) corresponds to 0302 (hex) = 770 (dec). If
        ``numberOfDecimals = 1``, then this is converted to 77.0 (float).

    """
    _checkString(bytestring, minlength=2, maxlength=2, description='bytestring')
    _checkInt(numberOfDecimals, minvalue=0, description='number of decimals')
    _checkBool(signed, description='signed parameter')

    formatcode = '>'  # Big-endian
    if signed:
        formatcode += 'h'  # (Signed) short (2 bytes)
    else:
        formatcode += 'H'  # Unsigned short (2 bytes)

    fullregister = _unpack(formatcode, bytestring)

    if numberOfDecimals == 0:
        return fullregister
    divisor = 10 ** numberOfDecimals
    return fullregister / float(divisor)


def _longToBytestring(value, signed=False, numberOfRegisters=2):
    """Convert a long integer to a bytestring.

    Long integers (32 bits = 4 bytes) are stored in two consecutive 16-bit registers in the slave.

    Args:
        * value (int): The numerical value to be converted.
        * signed (bool): Whether large positive values should be interpreted as negative values.
        * numberOfRegisters (int): Should be 2. For error checking only.

    Returns:
        A bytestring (4 bytes).

    Raises:
        TypeError, ValueError

    """
    _checkInt(value, description='inputvalue')
    _checkBool(signed, description='signed parameter')
    _checkInt(numberOfRegisters, minvalue=2, maxvalue=2, description='number of registers')

    formatcode = '>'  # Big-endian
    if signed:
        formatcode += 'l'  # (Signed) long (4 bytes)
    else:
        formatcode += 'L'  # Unsigned long (4 bytes)

    outstring = _pack(formatcode, value)
    assert len(outstring) == 4
    return outstring


def _bytestringToLong(bytestring, signed=False, numberOfRegisters=2):
    """Convert a bytestring to a long integer.

    Long integers (32 bits = 4 bytes) are stored in two consecutive 16-bit registers in the slave.

    Args:
        * bytestring (str): A string of length 4.
        * signed (bol): Whether large positive values should be interpreted as negative values.
        * numberOfRegisters (int): Should be 2. For error checking only.

    Returns:
        The numerical value (int).

    Raises:
        ValueError, TypeError

    """
    _checkString(bytestring, 'byte string', minlength=4, maxlength=4)
    _checkBool(signed, description='signed parameter')
    _checkInt(numberOfRegisters, minvalue=2, maxvalue=2, description='number of registers')

    formatcode = '>'  # Big-endian
    if signed:
        formatcode += 'l'  # (Signed) long (4 bytes)
    else:
        formatcode += 'L'  # Unsigned long (4 bytes)

    return _unpack(formatcode, bytestring)


def _floatToBytestring(value, numberOfRegisters=2):
    """Convert a numerical value to a bytestring.

    Floats are stored in two or more consecutive 16-bit registers in the slave. The
    encoding is according to the standard IEEE 754.

    ====================================== ================= =========== =================
    Type of floating point number in slave Size              Registers   Range
    ====================================== ================= =========== =================
    Single precision (binary32)            32 bits (4 bytes) 2 registers 1.4E-45 to 3.4E38
    Double precision (binary64)            64 bits (8 bytes) 4 registers 5E-324 to 1.8E308
    ====================================== ================= =========== =================

    A floating  point value of 1.0 is encoded (in single precision) as 3f800000 (hex).
    This will give a byte string ``'\\x3f\\x80\\x00\\x00'`` (big endian).

    Args:
        * value (float or int): The numerical value to be converted.
        * numberOfRegisters (int): Can be 2 or 4.

    Returns:
        A bytestring (4 or 8 bytes).

    Raises:
        TypeError, ValueError

    """
    _checkNumerical(value, description='inputvalue')
    _checkInt(numberOfRegisters, minvalue=2, maxvalue=4, description='number of registers')

    formatcode = '>'  # Big-endian
    if numberOfRegisters == 2:
        formatcode += 'f'  # Float (4 bytes)
        lengthtarget = 4
    elif numberOfRegisters == 4:
        formatcode += 'd'  # Double (8 bytes)
        lengthtarget = 8
    else:
        raise ValueError('Wrong number of registers! Given value is {0!r}'.format(numberOfRegisters))

    outstring = _pack(formatcode, value)
    assert len(outstring) == lengthtarget
    return outstring


def _bytestringToFloat(bytestring, numberOfRegisters=2):
    """Convert a four-byte string to a float.

    Floats are stored in two or more consecutive 16-bit registers in the slave.

    For discussion on precision, number of bits, number of registers, the range, byte order
    and on alternative names, see :func:`minimalmodbus._floatToBytestring`.

    Args:
        * bytestring (str): A string of length 4 or 8.
        * numberOfRegisters (int): Can be 2 or 4.

    Returns:
        A float.

    Raises:
        TypeError, ValueError

    """
    _checkString(bytestring, minlength=4, maxlength=8, description='bytestring')
    _checkInt(numberOfRegisters, minvalue=2, maxvalue=4, description='number of registers')

    numberOfBytes = _NUMBER_OF_BYTES_PER_REGISTER * numberOfRegisters

    formatcode = '>'  # Big-endian
    if numberOfRegisters == 2:
        formatcode += 'f'  # Float (4 bytes)
    elif numberOfRegisters == 4:
        formatcode += 'd'  # Double (8 bytes)
    else:
        raise ValueError('Wrong number of registers! Given value is {0!r}'.format(numberOfRegisters))

    if len(bytestring) != numberOfBytes:
        raise ValueError('Wrong length of the byte string! Given value is {0!r}, and numberOfRegisters is {1!r}.'.\
            format(bytestring, numberOfRegisters))

    return _unpack(formatcode, bytestring)


def _textstringToBytestring(inputstring, numberOfRegisters=16):
    """Convert a text string to a bytestring.

    Each 16-bit register in the slave are interpreted as two characters (1 byte = 8 bits).
    For example 16 consecutive registers can hold 32 characters (32 bytes).

    Not much of conversion is done, mostly error checking and string padding.
    If the inputstring is shorter that the allocated space, it is padded with spaces in the end.

    Args:
        * inputstring (str): The string to be stored in the slave. Max 2*numberOfRegisters characters.
        * numberOfRegisters (int): The number of registers allocated for the string.

    Returns:
        A bytestring (str).

    Raises:
        TypeError, ValueError

    """
    _checkInt(numberOfRegisters, minvalue=1, description='number of registers')
    maxCharacters = _NUMBER_OF_BYTES_PER_REGISTER * numberOfRegisters
    _checkString(inputstring, 'input string', minlength=1, maxlength=maxCharacters)

    bytestring = inputstring.ljust(maxCharacters)  # Pad with space
    assert len(bytestring) == maxCharacters
    return bytestring


def _bytestringToTextstring(bytestring, numberOfRegisters=16):
    """Convert a bytestring to a text string.

    Each 16-bit register in the slave are interpreted as two characters (1 byte = 8 bits).
    For example 16 consecutive registers can hold 32 characters (32 bytes).

    Not much of conversion is done, mostly error checking.

    Args:
        * bytestring (str): The string from the slave. Length = 2*numberOfRegisters
        * numberOfRegisters (int): The number of registers allocated for the string.

    Returns:
        A the text string (str).

    Raises:
        TypeError, ValueError

    """
    _checkInt(numberOfRegisters, minvalue=1, description='number of registers')
    maxCharacters = _NUMBER_OF_BYTES_PER_REGISTER * numberOfRegisters
    _checkString(bytestring, 'byte string', minlength=maxCharacters, maxlength=maxCharacters)

    textstring = bytestring
    return textstring


def _valuelistToBytestring(valuelist, numberOfRegisters):
    """Convert a list of numerical values to a bytestring.

    Each element is 'unsigned INT16'.

    Args:
        * valuelist (list of int): The input list. The elements should be in the range 0 to 65535.
        * numberOfRegisters (int): The number of registers. For error checking.

    Returns:
        A bytestring (str). Length = 2*numberOfRegisters

    Raises:
        TypeError, ValueError

    """
    MINVALUE = 0
    MAXVALUE = 65535

    _checkInt(numberOfRegisters, minvalue=1, description='number of registers')

    if not isinstance(valuelist, list):
        raise TypeError('The valuelist parameter must be a list. Given {0!r}.'.format(valuelist))

    for value in valuelist:
        _checkInt(value, minvalue=MINVALUE, maxvalue=MAXVALUE, description='elements in the input value list')

    _checkInt(len(valuelist), minvalue=numberOfRegisters, maxvalue=numberOfRegisters, \
        description='length of the list')

    numberOfBytes = _NUMBER_OF_BYTES_PER_REGISTER * numberOfRegisters

    bytestring = ''
    for value in valuelist:
        bytestring += _numToTwoByteString(value, signed=False)

    assert len(bytestring) == numberOfBytes
    return bytestring


def _bytestringToValuelist(bytestring, numberOfRegisters):
    """Convert a bytestring to a list of numerical values.

    The bytestring is interpreted as 'unsigned INT16'.

    Args:
        * bytestring (str): The string from the slave. Length = 2*numberOfRegisters
        * numberOfRegisters (int): The number of registers. For error checking.

    Returns:
        A list of integers.

    Raises:
        TypeError, ValueError

    """
    _checkInt(numberOfRegisters, minvalue=1, description='number of registers')
    numberOfBytes = _NUMBER_OF_BYTES_PER_REGISTER * numberOfRegisters
    _checkString(bytestring, 'byte string', minlength=numberOfBytes, maxlength=numberOfBytes)

    values = []
    for i in range(numberOfRegisters):
        offset = _NUMBER_OF_BYTES_PER_REGISTER * i
        substring = bytestring[offset : offset + _NUMBER_OF_BYTES_PER_REGISTER]
        values.append(_twoByteStringToNum(substring))

    return values


def _pack(formatstring, value):
    """Pack a value into a bytestring.

    Uses the built-in :mod:`struct` Python module.

    Args:
        * formatstring (str): String for the packing. See the :mod:`struct` module for details.
        * value (depends on formatstring): The value to be packed

    Returns:
        A bytestring (str).

    Raises:
        ValueError

    Note that the :mod:`struct` module produces byte buffers for Python3,
    but bytestrings for Python2. This is compensated for automatically.

    """
    _checkString(formatstring, description='formatstring', minlength=1)

    try:
        result = struct.pack(formatstring, value)
    except:
        errortext = 'The value to send is probably out of range, as the num-to-bytestring conversion failed.'
        errortext += ' Value: {0!r} Struct format code is: {1}'
        raise ValueError(errortext.format(value, formatstring))

    if sys.version_info[0] > 2:
        return str(result, encoding='latin1')  # Convert types to make it Python3 compatible
    return result


def _unpack(formatstring, packed):
    """Unpack a bytestring into a value.

    Uses the built-in :mod:`struct` Python module.

    Args:
        * formatstring (str): String for the packing. See the :mod:`struct` module for details.
        * packed (str): The bytestring to be unpacked.

    Returns:
        A value. The type depends on the formatstring.

    Raises:
        ValueError

    Note that the :mod:`struct` module wants byte buffers for Python3,
    but bytestrings for Python2. This is compensated for automatically.

    """
    _checkString(formatstring, description='formatstring', minlength=1)
    _checkString(packed, description='packed string', minlength=1)

    if sys.version_info[0] > 2:
        packed = bytes(packed, encoding='latin1')  # Convert types to make it Python3 compatible

    try:
        value = struct.unpack(formatstring, packed)[0]
    except:
        errortext = 'The received bytestring is probably wrong, as the bytestring-to-num conversion failed.'
        errortext += ' Bytestring: {0!r} Struct format code is: {1}'
        raise ValueError(errortext.format(packed, formatstring))

    return value


def _hexencode(bytestring, insert_spaces = False):
    """Convert a byte string to a hex encoded string.

    For example 'J' will return '4A', and ``'\\x04'`` will return '04'.

    Args:
        bytestring (str): Can be for example ``'A\\x01B\\x45'``.
        insert_spaces (bool): Insert space characters between pair of characters to increase readability.

    Returns:
        A string of twice the length, with characters in the range '0' to '9' and 'A' to 'F'.
        The string will be longer if spaces are inserted.

    Raises:
        TypeError, ValueError

    """
    _checkString(bytestring, description='byte string')

    separator = '' if not insert_spaces else ' '
    
    # Use plain string formatting instead of binhex.hexlify,
    # in order to have it Python 2.x and 3.x compatible

    byte_representions = []
    for c in bytestring:
        byte_representions.append( '{0:02X}'.format(ord(c)) )
    return separator.join(byte_representions).strip()


def _hexdecode(hexstring):
    """Convert a hex encoded string to a byte string.

    For example '4A' will return 'J', and '04' will return ``'\\x04'`` (which has length 1).

    Args:
        hexstring (str): Can be for example 'A3' or 'A3B4'. Must be of even length.
        Allowed characters are '0' to '9', 'a' to 'f' and 'A' to 'F' (not space).

    Returns:
        A string of half the length, with characters corresponding to all 0-255 values for each byte.

    Raises:
        TypeError, ValueError

    """
    # Note: For Python3 the appropriate would be: raise TypeError(new_error_message) from err
    # but the Python2 interpreter will indicate SyntaxError.
    # Thus we need to live with this warning in Python3:
    # 'During handling of the above exception, another exception occurred'

    _checkString(hexstring, description='hexstring')

    if len(hexstring) % 2 != 0:
        raise ValueError('The input hexstring must be of even length. Given: {!r}'.format(hexstring))

    if sys.version_info[0] > 2:
        by = bytes(hexstring, 'latin1')
        try:
            return str(binascii.unhexlify(by), encoding='latin1')
        except binascii.Error as err:
            new_error_message = 'Hexdecode reported an error: {!s}. Input hexstring: {}'.format(err.args[0], hexstring)
            raise TypeError(new_error_message)

    else:
        try:
            return hexstring.decode('hex')
        except TypeError as err:
            raise TypeError('Hexdecode reported an error: {}. Input hexstring: {}'.format(err.message, hexstring))


def _hexlify(bytestring):
    """Convert a byte string to a hex encoded string, with spaces for easier reading.
    
    This is just a facade for _hexencode() with insert_spaces = True.
    
    See _hexencode() for details.

    """
    return _hexencode(bytestring, insert_spaces = True)


def _bitResponseToValue(bytestring):
    """Convert a response string to a numerical value.

    Args:
        bytestring (str): A string of length 1. Can be for example ``\\x01``.

    Returns:
        The converted value (int).

    Raises:
        TypeError, ValueError

    """
    _checkString(bytestring, description='bytestring', minlength=1, maxlength=1)

    RESPONSE_ON  = '\x01'
    RESPONSE_OFF = '\x00'

    if bytestring == RESPONSE_ON:
        return 1
    elif bytestring == RESPONSE_OFF:
        return 0
    else:
        raise ValueError('Could not convert bit response to a value. Input: {0!r}'.format(bytestring))


def _createBitpattern(functioncode, value):
    """Create the bit pattern that is used for writing single bits.

    This is basically a storage of numerical constants.

    Args:
        * functioncode (int): can be 5 or 15
        * value (int): can be 0 or 1

    Returns:
        The bit pattern (string).

    Raises:
        TypeError, ValueError

    """
    _checkFunctioncode(functioncode, [5, 15])
    _checkInt(value, minvalue=0, maxvalue=1, description='inputvalue')

    if functioncode == 5:
        if value == 0:
            return '\x00\x00'
        else:
            return '\xff\x00'

    elif functioncode == 15:
        if value == 0:
            return '\x00'
        else:
            return '\x01'  # Is this correct??

#######################
# Number manipulation #
#######################


def _twosComplement(x, bits=16):
    """Calculate the two's complement of an integer.

    Then also negative values can be represented by an upper range of positive values.
    See https://en.wikipedia.org/wiki/Two%27s_complement

    Args:
        * x (int): input integer.
        * bits (int): number of bits, must be > 0.

    Returns:
        An int, that represents the two's complement of the input.

    Example for bits=8:

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
    _checkInt(bits, minvalue=0, description='number of bits')
    _checkInt(x, description='input')
    upperlimit = 2 ** (bits - 1) - 1
    lowerlimit = -2 ** (bits - 1)
    if x > upperlimit or x < lowerlimit:
        raise ValueError('The input value is out of range. Given value is {0}, but allowed range is {1} to {2} when using {3} bits.' \
            .format(x, lowerlimit, upperlimit, bits))

    # Calculate two'2 complement
    if x >= 0:
        return x
    return x + 2 ** bits


def _fromTwosComplement(x, bits=16):
    """Calculate the inverse(?) of a two's complement of an integer.

    Args:
        * x (int): input integer.
        * bits (int): number of bits, must be > 0.

    Returns:
        An int, that represents the inverse(?) of two's complement of the input.

    Example for bits=8:

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
    _checkInt(bits, minvalue=0, description='number of bits')

    _checkInt(x, description='input')
    upperlimit = 2 ** (bits) - 1
    lowerlimit = 0
    if x > upperlimit or x < lowerlimit:
        raise ValueError('The input value is out of range. Given value is {0}, but allowed range is {1} to {2} when using {3} bits.' \
            .format(x, lowerlimit, upperlimit, bits))

    # Calculate inverse(?) of two'2 complement
    limit = 2 ** (bits - 1) - 1
    if x <= limit:
        return x
    return x - 2 ** bits

####################
# Bit manipulation #
####################

def _setBitOn(x, bitNum):
    """Set bit 'bitNum' to True.

    Args:
        * x (int): The value before.
        * bitNum (int): The bit number that should be set to True.

    Returns:
        The value after setting the bit. This is an integer.

    For example:
        For x = 4 (dec) = 0100 (bin), setting bit number 0 results in 0101 (bin) = 5 (dec).

    """
    _checkInt(x, minvalue=0, description='input value')
    _checkInt(bitNum, minvalue=0, description='bitnumber')

    return x | (1 << bitNum)

############################
# Error checking functions #
############################

_CRC16TABLE = (
        0, 49345, 49537,   320, 49921,   960,   640, 49729, 50689,  1728,  1920, 
    51009,  1280, 50625, 50305,  1088, 52225,  3264,  3456, 52545,  3840, 53185, 
    52865,  3648,  2560, 51905, 52097,  2880, 51457,  2496,  2176, 51265, 55297, 
     6336,  6528, 55617,  6912, 56257, 55937,  6720,  7680, 57025, 57217,  8000, 
    56577,  7616,  7296, 56385,  5120, 54465, 54657,  5440, 55041,  6080,  5760, 
    54849, 53761,  4800,  4992, 54081,  4352, 53697, 53377,  4160, 61441, 12480, 
    12672, 61761, 13056, 62401, 62081, 12864, 13824, 63169, 63361, 14144, 62721, 
    13760, 13440, 62529, 15360, 64705, 64897, 15680, 65281, 16320, 16000, 65089, 
    64001, 15040, 15232, 64321, 14592, 63937, 63617, 14400, 10240, 59585, 59777, 
    10560, 60161, 11200, 10880, 59969, 60929, 11968, 12160, 61249, 11520, 60865, 
    60545, 11328, 58369,  9408,  9600, 58689,  9984, 59329, 59009,  9792,  8704, 
    58049, 58241,  9024, 57601,  8640,  8320, 57409, 40961, 24768, 24960, 41281, 
    25344, 41921, 41601, 25152, 26112, 42689, 42881, 26432, 42241, 26048, 25728, 
    42049, 27648, 44225, 44417, 27968, 44801, 28608, 28288, 44609, 43521, 27328, 
    27520, 43841, 26880, 43457, 43137, 26688, 30720, 47297, 47489, 31040, 47873, 
    31680, 31360, 47681, 48641, 32448, 32640, 48961, 32000, 48577, 48257, 31808, 
    46081, 29888, 30080, 46401, 30464, 47041, 46721, 30272, 29184, 45761, 45953, 
    29504, 45313, 29120, 28800, 45121, 20480, 37057, 37249, 20800, 37633, 21440, 
    21120, 37441, 38401, 22208, 22400, 38721, 21760, 38337, 38017, 21568, 39937, 
    23744, 23936, 40257, 24320, 40897, 40577, 24128, 23040, 39617, 39809, 23360, 
    39169, 22976, 22656, 38977, 34817, 18624, 18816, 35137, 19200, 35777, 35457, 
    19008, 19968, 36545, 36737, 20288, 36097, 19904, 19584, 35905, 17408, 33985, 
    34177, 17728, 34561, 18368, 18048, 34369, 33281, 17088, 17280, 33601, 16640, 
    33217, 32897, 16448)
"""CRC-16 lookup table with 256 elements.
    Built with this code:    
    
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


def _calculateCrcString(inputstring):
    """Calculate CRC-16 for Modbus.

    Args:
        inputstring (str): An arbitrary-length message (without the CRC).

    Returns:
        A two-byte CRC string, where the least significant byte is first.

    """
    _checkString(inputstring, description='input CRC string')
 
    # Preload a 16-bit register with ones
    register = 0xFFFF

    for char in inputstring:
        register = (register >> 8) ^ _CRC16TABLE[(register ^ ord(char)) & 0xFF]
 
    return _numToTwoByteString(register, LsbFirst=True)


def _calculateLrcString(inputstring):
    """Calculate LRC for Modbus.

    Args:
        inputstring (str): An arbitrary-length message (without the beginning
        colon and terminating CRLF). It should already be decoded from hex-string.

    Returns:
        A one-byte LRC bytestring (not encoded to hex-string)

    Algorithm from the document 'MODBUS over serial line specification and implementation guide V1.02'.

    The LRC is calculated as 8 bits (one byte).

    For example a LRC 0110 0001 (bin) = 61 (hex) = 97 (dec) = 'a'. This function will
    then return 'a'.

    In Modbus ASCII mode, this should be transmitted using two characters. This
    example should be transmitted '61', which is a string of length two. This function
    does not handle that conversion for transmission.
    """
    _checkString(inputstring, description='input LRC string')

    register = 0
    for character in inputstring:
        register += ord(character)

    lrc = ((register ^ 0xFF) + 1) & 0xFF

    lrcString = _numToOneByteString(lrc)
    return lrcString


def _checkMode(mode):
    """Check that the Modbus mode is valie.

    Args:
        mode (string): The Modbus mode (MODE_RTU or MODE_ASCII)

    Raises:
        TypeError, ValueError

    """

    if not isinstance(mode, str):
        raise TypeError('The {0} should be a string. Given: {1!r}'.format("mode", mode))

    if mode not in [MODE_RTU, MODE_ASCII]:
        raise ValueError("Unreconized Modbus mode given. Must be 'rtu' or 'ascii' but {0!r} was given.".format(mode))


def _checkFunctioncode(functioncode, listOfAllowedValues=[]):
    """Check that the given functioncode is in the listOfAllowedValues.

    Also verifies that 1 <= function code <= 127.

    Args:
        * functioncode (int): The function code
        * listOfAllowedValues (list of int): Allowed values. Use *None* to bypass this part of the checking.

    Raises:
        TypeError, ValueError

    """
    FUNCTIONCODE_MIN = 1
    FUNCTIONCODE_MAX = 127

    _checkInt(functioncode, FUNCTIONCODE_MIN, FUNCTIONCODE_MAX, description='functioncode')

    if listOfAllowedValues is None:
        return

    if not isinstance(listOfAllowedValues, list):
        raise TypeError('The listOfAllowedValues should be a list. Given: {0!r}'.format(listOfAllowedValues))

    for value in listOfAllowedValues:
        _checkInt(value, FUNCTIONCODE_MIN, FUNCTIONCODE_MAX, description='functioncode inside listOfAllowedValues')

    if functioncode not in listOfAllowedValues:
        raise ValueError('Wrong function code: {0}, allowed values are {1!r}'.format(functioncode, listOfAllowedValues))


def _checkSlaveaddress(slaveaddress):
    """Check that the given slaveaddress is valid.

    Args:
        slaveaddress (int): The slave address

    Raises:
        TypeError, ValueError

    """
    SLAVEADDRESS_MAX = 247
    SLAVEADDRESS_MIN = 0

    _checkInt(slaveaddress, SLAVEADDRESS_MIN, SLAVEADDRESS_MAX, description='slaveaddress')


def _checkRegisteraddress(registeraddress):
    """Check that the given registeraddress is valid.

    Args:
        registeraddress (int): The register address

    Raises:
        TypeError, ValueError

    """
    REGISTERADDRESS_MAX = 0xFFFF
    REGISTERADDRESS_MIN = 0

    _checkInt(registeraddress, REGISTERADDRESS_MIN, REGISTERADDRESS_MAX, description='registeraddress')


def _checkResponseByteCount(payload):
    """Check that the number of bytes as given in the response is correct.

    The first byte in the payload indicates the length of the payload (first byte not counted).

    Args:
        payload (string): The payload

    Raises:
        TypeError, ValueError

    """
    POSITION_FOR_GIVEN_NUMBER = 0
    NUMBER_OF_BYTES_TO_SKIP = 1

    _checkString(payload, minlength=1, description='payload')

    givenNumberOfDatabytes = ord(payload[POSITION_FOR_GIVEN_NUMBER])
    countedNumberOfDatabytes = len(payload) - NUMBER_OF_BYTES_TO_SKIP

    if givenNumberOfDatabytes != countedNumberOfDatabytes:
        errortemplate = 'Wrong given number of bytes in the response: {0}, but counted is {1} as data payload length is {2}.' + \
            ' The data payload is: {3!r}'
        errortext = errortemplate.format(givenNumberOfDatabytes, countedNumberOfDatabytes, len(payload), payload)
        raise ValueError(errortext)


def _checkResponseRegisterAddress(payload, registeraddress):
    """Check that the start adress as given in the response is correct.

    The first two bytes in the payload holds the address value.

    Args:
        * payload (string): The payload
        * registeraddress (int): The register address (use decimal numbers, not hex).

    Raises:
        TypeError, ValueError

    """
    _checkString(payload, minlength=2, description='payload')
    _checkRegisteraddress(registeraddress)

    BYTERANGE_FOR_STARTADDRESS = slice(0, 2)

    bytesForStartAddress = payload[BYTERANGE_FOR_STARTADDRESS]
    receivedStartAddress = _twoByteStringToNum(bytesForStartAddress)

    if receivedStartAddress != registeraddress:
        raise ValueError('Wrong given write start adress: {0}, but commanded is {1}. The data payload is: {2!r}'.format( \
            receivedStartAddress, registeraddress, payload))


def _checkResponseNumberOfRegisters(payload, numberOfRegisters):
    """Check that the number of written registers as given in the response is correct.

    The bytes 2 and 3 (zero based counting) in the payload holds the value.

    Args:
        * payload (string): The payload
        * numberOfRegisters (int): Number of registers that have been written

    Raises:
        TypeError, ValueError

    """
    _checkString(payload, minlength=4, description='payload')
    _checkInt(numberOfRegisters, minvalue=1, maxvalue=0xFFFF, description='numberOfRegisters')

    BYTERANGE_FOR_NUMBER_OF_REGISTERS = slice(2, 4)

    bytesForNumberOfRegisters = payload[BYTERANGE_FOR_NUMBER_OF_REGISTERS]
    receivedNumberOfWrittenReisters = _twoByteStringToNum(bytesForNumberOfRegisters)

    if receivedNumberOfWrittenReisters != numberOfRegisters:
        raise ValueError('Wrong number of registers to write in the response: {0}, but commanded is {1}. The data payload is: {2!r}'.format( \
            receivedNumberOfWrittenReisters, numberOfRegisters, payload))


def _checkResponseWriteData(payload, writedata):
    """Check that the write data as given in the response is correct.

    The bytes 2 and 3 (zero based counting) in the payload holds the write data.

    Args:
        * payload (string): The payload
        * writedata (string): The data to write, length should be 2 bytes.

    Raises:
        TypeError, ValueError

    """
    _checkString(payload, minlength=4, description='payload')
    _checkString(writedata, minlength=2, maxlength=2, description='writedata')

    BYTERANGE_FOR_WRITEDATA = slice(2, 4)

    receivedWritedata = payload[BYTERANGE_FOR_WRITEDATA]

    if receivedWritedata != writedata:
        raise ValueError('Wrong write data in the response: {0!r}, but commanded is {1!r}. The data payload is: {2!r}'.format( \
            receivedWritedata, writedata, payload))


def _checkString(inputstring, description, minlength=0, maxlength=None):
    """Check that the given string is valid.

    Args:
        * inputstring (string): The string to be checked
        * description (string): Used in error messages for the checked inputstring
        * minlength (int): Minimum length of the string
        * maxlength (int or None): Maximum length of the string

    Raises:
        TypeError, ValueError

    Uses the function :func:`_checkInt` internally.

    """
    # Type checking
    if not isinstance(description, str):
        raise TypeError('The description should be a string. Given: {0!r}'.format(description))

    if not isinstance(inputstring, str):
        raise TypeError('The {0} should be a string. Given: {1!r}'.format(description, inputstring))

    if not isinstance(maxlength, (int, type(None))):
        raise TypeError('The maxlength must be an integer or None. Given: {0!r}'.format(maxlength))

    # Check values
    _checkInt(minlength, minvalue=0, maxvalue=None, description='minlength')

    if len(inputstring) < minlength:
        raise ValueError('The {0} is too short: {1}, but minimum value is {2}. Given: {3!r}'.format( \
            description, len(inputstring), minlength, inputstring))

    if not maxlength is None:
        if maxlength < 0:
            raise ValueError('The maxlength must be positive. Given: {0}'.format(maxlength))

        if maxlength < minlength:
            raise ValueError('The maxlength must not be smaller than minlength. Given: {0} and {1}'.format( \
                maxlength, minlength))

        if len(inputstring) > maxlength:
            raise ValueError('The {0} is too long: {1}, but maximum value is {2}. Given: {3!r}'.format( \
                description, len(inputstring), maxlength, inputstring))


def _checkInt(inputvalue, minvalue=None, maxvalue=None, description='inputvalue'):
    """Check that the given integer is valid.

    Args:
        * inputvalue (int or long): The integer to be checked
        * minvalue (int or long, or None): Minimum value of the integer
        * maxvalue (int or long, or None): Maximum value of the integer
        * description (string): Used in error messages for the checked inputvalue

    Raises:
        TypeError, ValueError

    Note: Can not use the function :func:`_checkString`, as that function uses this function internally.

    """
    if not isinstance(description, str):
        raise TypeError('The description should be a string. Given: {0!r}'.format(description))

    if not isinstance(inputvalue, (int, long)):
        raise TypeError('The {0} must be an integer. Given: {1!r}'.format(description, inputvalue))

    if not isinstance(minvalue, (int, long, type(None))):
        raise TypeError('The minvalue must be an integer or None. Given: {0!r}'.format(minvalue))

    if not isinstance(maxvalue, (int, long, type(None))):
        raise TypeError('The maxvalue must be an integer or None. Given: {0!r}'.format(maxvalue))

    _checkNumerical(inputvalue, minvalue, maxvalue, description)


def _checkNumerical(inputvalue, minvalue=None, maxvalue=None, description='inputvalue'):
    """Check that the given numerical value is valid.

    Args:
        * inputvalue (numerical): The value to be checked.
        * minvalue (numerical): Minimum value  Use None to skip this part of the test.
        * maxvalue (numerical): Maximum value. Use None to skip this part of the test.
        * description (string): Used in error messages for the checked inputvalue

    Raises:
        TypeError, ValueError

    Note: Can not use the function :func:`_checkString`, as it uses this function internally.

    """
    # Type checking
    if not isinstance(description, str):
        raise TypeError('The description should be a string. Given: {0!r}'.format(description))

    if not isinstance(inputvalue, (int, long, float)):
        raise TypeError('The {0} must be numerical. Given: {1!r}'.format(description, inputvalue))

    if not isinstance(minvalue, (int, float, long, type(None))):
        raise TypeError('The minvalue must be numeric or None. Given: {0!r}'.format(minvalue))

    if not isinstance(maxvalue, (int, float, long, type(None))):
        raise TypeError('The maxvalue must be numeric or None. Given: {0!r}'.format(maxvalue))

    # Consistency checking
    if (not minvalue is None) and (not maxvalue is None):
        if maxvalue < minvalue:
            raise ValueError('The maxvalue must not be smaller than minvalue. Given: {0} and {1}, respectively.'.format( \
                maxvalue, minvalue))

    # Value checking
    if not minvalue is None:
        if inputvalue < minvalue:
            raise ValueError('The {0} is too small: {1}, but minimum value is {2}.'.format( \
                description, inputvalue, minvalue))

    if not maxvalue is None:
        if inputvalue > maxvalue:
            raise ValueError('The {0} is too large: {1}, but maximum value is {2}.'.format( \
                description, inputvalue, maxvalue))


def _checkBool(inputvalue, description='inputvalue'):
    """Check that the given inputvalue is a boolean.

    Args:
        * inputvalue (boolean): The value to be checked.
        * description (string): Used in error messages for the checked inputvalue.

    Raises:
        TypeError, ValueError

    """
    _checkString(description, minlength=1, description='description string')
    if not isinstance(inputvalue, bool):
        raise TypeError('The {0} must be boolean. Given: {1!r}'.format(description, inputvalue))

#####################
# Development tools #
#####################


def _print_out(inputstring):
    """Print the inputstring. To make it compatible with Python2 and Python3.

    Args:
        inputstring (str): The string that should be printed.

    Raises:
        TypeError

    """
    _checkString(inputstring, description='string to print')

    sys.stdout.write(inputstring + '\n')


def _interpretRawMessage(inputstr):
    r"""Generate a human readable description of a Modbus bytestring.
    
    Args:
        inputstr (str): The bytestring that should be interpreted.

    Returns:
        A descriptive string.

    For example, the string ``'\n\x03\x10\x01\x00\x01\xd0q'`` should give something like::
        
        TODO: update
    
        Modbus bytestring decoder
        Input string (length 8 characters): '\n\x03\x10\x01\x00\x01\xd0q'
        Probably modbus RTU mode.
        Slave address: 10 (dec). Function code: 3 (dec).
        Valid message. Extracted payload: '\x10\x01\x00\x01'

        Pos   Character Hex  Dec  Probable interpretation 
        -------------------------------------------------
          0:  '\n'      0A    10  Slave address 
          1:  '\x03'    03     3  Function code 
          2:  '\x10'    10    16  Payload    
          3:  '\x01'    01     1  Payload    
          4:  '\x00'    00     0  Payload    
          5:  '\x01'    01     1  Payload    
          6:  '\xd0'    D0   208  Checksum, CRC LSB 
          7:  'q'       71   113  Checksum, CRC MSB 

    """
    raise NotImplementedError()
    output = ''
    output += 'Modbus bytestring decoder\n'
    output += 'Input string (length {} characters): {!r} \n'.format(len(inputstr), inputstr)

    # Detect modbus type
    if inputstr.startswith(_ASCII_HEADER) and inputstr.endswith(_ASCII_FOOTER):
        mode = MODE_ASCII
    else:
        mode = MODE_RTU
    output += 'Probably Modbus {} mode.\n'.format(mode.upper())

    # Extract slave address and function code
    try:
        if mode == MODE_ASCII:
            slaveaddress = int(inputstr[1:3])
            functioncode = int(inputstr[3:5])
        else:
            slaveaddress = ord(inputstr[0])
            functioncode = ord(inputstr[1])
        output += 'Slave address: {} (dec). Function code: {} (dec).\n'.format(slaveaddress, functioncode)
    except:
        output += '\nCould not extract slave address and function code. \n\n'

    # Check message validity
    try:
        extractedpayload = _extractPayload(inputstr, slaveaddress, mode, functioncode)
        output += 'Valid message. Extracted payload: {!r}\n'.format(extractedpayload)
    except (ValueError, TypeError) as err:
        output += '\nThe message does not seem to be valid Modbus {}. Error message: \n{}. \n\n'.format(mode.upper(), err.message)
    except NameError as err:
        output += '\nNo message validity checking. \n\n' # Slave address or function code not available

    # Generate table describing the message
    if mode == MODE_RTU:
        output += '\nPos   Character Hex  Dec  Probable interpretation \n'
        output += '------------------------------------------------- \n'
        for i, character in enumerate(inputstr):
            if i==0:
                description = 'Slave address'
            elif i==1:
                description = 'Function code'
            elif i==len(inputstr)-2:
                description = 'Checksum, CRC LSB'
            elif i==len(inputstr)-1:
                description = 'Checksum, CRC MSB'
            else:
                description = 'Payload'
            output += '{0:3.0f}:  {1!r:<8}  {2:02X}  {2: 4.0f}  {3:<10} \n'.format(i, character, ord(character), description)
        
    elif mode == MODE_ASCII:
        output += '\nPos   Character(s) Converted  Hex  Dec  Probable interpretation \n'
        output += '--------------------------------------------------------------- \n'
        
        i = 0
        while i < len(inputstr):
            
            if inputstr[i] in [':', '\r', '\n']:
                if inputstr[i] == ':': 
                    description = 'Start character'
                else:
                    description = 'Stop character'
                    
                output += '{0:3.0f}:  {1!r:<8}                          {2} \n'.format(i, inputstr[i], description)
                i += 1
                
            else:
                if i == 1:
                    description = 'Slave address'
                elif i == 3:
                    description = 'Function code'
                elif i == len(inputstr)-4:
                    description = 'Checksum (LRC)'
                else:
                    description = 'Payload'
                
                try:
                    hexvalue = _hexdecode(inputstr[i:i+2])
                    output +=  '{0:3.0f}:  {1!r:<8}     {2!r}     {3:02X}  {3: 4.0f}  {4} \n'.format(i, inputstr[i:i+2], hexvalue, ord(hexvalue), description)
                except:
                    output +=  '{0:3.0f}:  {1!r:<8}     ?           ?     ?  {2} \n'.format(i, inputstr[i:i+2], description)
                i += 2
        
    # Generate description for the payload
    output += '\n\n'
    try:
        output += _interpretPayload(functioncode, extractedpayload)
    except:
        output += '\nCould not interpret the payload. \n\n' # Payload or function code not available
    
    return output
    

def _interpretPayload(functioncode, payload):
    r"""Generate a human readable description of a Modbus payload.
    
    Args:
      * functioncode (int): Function code
      * payload (str): The payload that should be interpreted. It should be a byte string.

    Returns:
        A descriptive string.

    For example, the payload ``'\x10\x01\x00\x01'`` for functioncode 3 should give something like::
    
        TODO: Update
    

    """
    raise NotImplementedError()
    output = ''
    output += 'Modbus payload decoder\n'
    output += 'Input payload (length {} characters): {!r} \n'.format(len(payload), payload)
    output += 'Function code: {} (dec).\n'.format(functioncode)
    
    if len(payload) == 4:
        FourbyteMessageFirstHalfValue = _twoByteStringToNum(payload[0:2])
        FourbyteMessageSecondHalfValue = _twoByteStringToNum(payload[2:4])


    return output

def _getDiagnosticString():
    """Generate a diagnostic string, showing the module version, the platform, current directory etc.

    Returns:
        A descriptive string.

    """
    text = '\n## Diagnostic output from minimalmodbus ## \n\n'
    text += 'Minimalmodbus version: ' + __version__ + '\n'
    text += 'Minimalmodbus status: ' + __status__ + '\n'
    text += 'File name (with relative path): ' + __file__ + '\n'
    text += 'Full file path: ' + os.path.abspath(__file__) + '\n\n'
    text += 'pySerial version: ' + serial.VERSION + '\n'
    text += 'pySerial full file path: ' + os.path.abspath(serial.__file__) + '\n\n'
    text += 'Platform: ' + sys.platform + '\n'
    text += 'Filesystem encoding: ' + repr(sys.getfilesystemencoding()) + '\n'
    text += 'Byteorder: ' + sys.byteorder + '\n'
    text += 'Python version: ' + sys.version + '\n'
    text += 'Python version info: ' + repr(sys.version_info) + '\n'
    text += 'Python flags: ' + repr(sys.flags) + '\n'
    text += 'Python argv: ' + repr(sys.argv) + '\n'
    text += 'Python prefix: ' + repr(sys.prefix) + '\n'
    text += 'Python exec prefix: ' + repr(sys.exec_prefix) + '\n'
    text += 'Python executable: ' + repr(sys.executable) + '\n'
    try:
        text += 'Long info: ' + repr(sys.long_info) + '\n'
    except:
        text += 'Long info: (none)\n'  # For Python3 compatibility
    try:
        text += 'Float repr style: ' + repr(sys.float_repr_style) + '\n\n'
    except:
        text += 'Float repr style: (none) \n\n'  # For Python 2.6 compatibility
    text += 'Variable __name__: ' + __name__ + '\n'
    text += 'Current directory: ' + os.getcwd() + '\n\n'
    text += 'Python path: \n'
    text += '\n'.join(sys.path) + '\n'
    text += '\n## End of diagnostic output ## \n'
    return text

