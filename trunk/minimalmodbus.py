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

MinimalModbus: A Python driver for the Modbus RTU protocol via serial port (via RS485 or RS232).

This Python file was changed (committed) at $Date$,
which was $Revision$.

"""

__author__   = 'Jonas Berg'
__email__    = 'pyhys@users.sourceforge.net'
__url__      = 'http://minimalmodbus.sourceforge.net/'
__license__  = 'Apache License, Version 2.0'

__version__  = '0.4a2'
__status__   = 'Beta'
__revision__ = '$Rev$'
__date__     = '$Date$'

import os
import serial
import struct
import sys

# Allow long also in Python3
# http://python3porting.com/noconv.html
if sys.version > '3':
    long = int

_NUMBER_OF_BYTES_PER_REGISTER = 2

BAUDRATE = 19200
"""Default value for the baudrate in Baud (int)."""

PARITY   = serial.PARITY_NONE
"""Default value for the  parity. See the pySerial module for documentation. Defaults to serial.PARITY_NONE"""

BYTESIZE = 8
"""Default value for the bytesize (int)."""

STOPBITS = 1
"""Default value for the number of stopbits (int)."""

TIMEOUT  = 0.05
"""Default value for the timeout value in seconds (float)."""

CLOSE_PORT_AFTER_EACH_CALL = False
"""Default value for port closure setting."""

class Instrument():
    """Instrument class for talking to instruments (slaves) via the Modbus RTU protocol (via RS485 or RS232).

    Args:
        * port (str): The serial port name, for example ``/dev/ttyUSB0`` (Linux), ``/dev/tty.usbserial`` (OS X) or ``/com3`` (Windows).
        * slaveaddress (int): Slave address in the range 1 to 247 (use decimal numbers, not hex).

    """

    def __init__(self, port, slaveaddress):

        self.serial = serial.Serial(port=port, baudrate=BAUDRATE, parity=PARITY, bytesize=BYTESIZE, \
            stopbits=STOPBITS, timeout = TIMEOUT )
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

        self.debug = False
        """Set this to :const:`True` to print the communication details. Defaults to :const:`False`."""

        self.close_port_after_each_call = CLOSE_PORT_AFTER_EACH_CALL
        """If this is :const:`True`, the serial port will be closed after each call. Defaults to :data:`CLOSE_PORT_AFTER_EACH_CALL`. To change it, set the value ``minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL=True`` ."""

        if  self.close_port_after_each_call:
            self.serial.close()

    def __repr__(self):
        """String representation of the :class:`.Instrument` object."""
        return "{0}.{1}<id=0x{2:x}, address={3}, close_port_after_each_call={4}, debug={5}, serial={6}>".format(
            self.__module__,
            self.__class__.__name__,
            id(self),
            self.address,
            self.close_port_after_each_call,
            self.debug,
            self.serial,
            )


    ########################################
    ## Functions for talking to the slave ##
    ########################################

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
        _checkInt(numberOfDecimals, minvalue=0, maxvalue=10, description='number of decimals' )
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
        _checkInt(numberOfDecimals, minvalue=0, maxvalue=10, description='number of decimals' )
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
        MAX_VALUE_LONG =  4294967295 # Unsigned INT32
        MIN_VALUE_LONG = -2147483648 # INT32

        _checkInt(value, minvalue=MIN_VALUE_LONG, maxvalue=MAX_VALUE_LONG, description='input value' )
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
        _checkString(textstring, 'input string', minlength=1, maxlength=2*numberOfRegisters)
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
            raise TypeError( 'The "values parameter" must be a list. Given: {0}'.format(repr(values)))
        _checkInt(len(values), minvalue=1, description='length of input list')
        # Note: The content of the list is checked at content conversion.

        self._genericCommand(16, registeraddress, values, numberOfRegisters=len(values), payloadformat='registers')


    #####################
    ## Generic command ##
    #####################

    def _genericCommand(self, functioncode, registeraddress, value=None, \
            numberOfDecimals=0, numberOfRegisters=1, signed=False, payloadformat = None):
        """Generic command for reading and writing registers and bits.

        Args:
            * functioncode (int): Modbus function code.
            * registeraddress (int): The register address  (use decimal numbers, not hex).
            * value (numerical or string or None or list of int): The value to store in the register. Depends on payloadformat.
            * numberOfDecimals (int): The number of decimals for content conversion. Only for a single register.
            * numberOfRegisters (int): The number of registers to read/write. Only certain values allowed, depends on payloadformat.
            * signed (bool): Whether the data should be interpreted as unsigned or signed. Only for a single register or for payloadformat='long'.
            * payloadformat (None or string): None, 'long', 'float', 'string', 'register', 'registers'. Not necessary for single registers or bits.

        If a value of 77.0 is stored internally in the slave register as 770, then use ``numberOfDecimals=1``
        which will divide the received data by 10 before returning the value. Similarly ``numberOfDecimals=2`` will divide the received data by 100 before returning the value. Same functionality also
        when writing data to the slave.

        Returns:
            The register data in numerical value (int or float), or the bit value 0 or 1 (int), or ``None``.

        Raises:
            ValueError, TypeError, IOError

        """
        NUMBER_OF_BITS = 1
        NUMBER_OF_BYTES_FOR_ONE_BIT = 1
        NUMBER_OF_BYTES_BEFORE_REGISTERDATA = 1
        ALL_ALLOWED_FUNCTIONCODES = list(range(1,7)) + [15, 16] # To comply with both Python2 and Python3
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
        _checkFunctioncode(functioncode, ALL_ALLOWED_FUNCTIONCODES)
        _checkRegisteraddress(registeraddress)
        _checkInt(numberOfDecimals, minvalue=0, description='number of decimals' )
        _checkInt(numberOfRegisters, minvalue=1, maxvalue=MAX_NUMBER_OF_REGISTERS, description='number of registers' )
        _checkBool(signed, description='signed')

        if payloadformat is not None:
            if payloadformat not in ALL_PAYLOADFORMATS:
                raise ValueError('Wrong payload format variable. Given: {0}'.format( repr(payloadformat) ))

        ## Check combinations of input parameters ##
        numberOfRegisterBytes = numberOfRegisters * _NUMBER_OF_BYTES_PER_REGISTER

                    # Payload format
        if functioncode in [3, 4, 6, 16] and payloadformat is None:
            payloadformat = PAYLOADFORMAT_REGISTER

        if functioncode in [3, 4, 6, 16]:
            if payloadformat not in ALL_PAYLOADFORMATS:
                raise ValueError('The payload format is wrong. Given format: {0}.'.format( repr(payloadformat) ))

                    # Signed and numberOfDecimals
        if signed:
            if payloadformat not in [PAYLOADFORMAT_REGISTER, PAYLOADFORMAT_LONG]:
                raise ValueError('The "signed" parameter can not be used for this data format. Given format: {0}.'.format( repr(payloadformat) ))

        if numberOfDecimals>0 and payloadformat != PAYLOADFORMAT_REGISTER:
                raise ValueError('The "numberOfDecimals" parameter can not be used for this data format. Given format: {0}.'.format( repr(payloadformat) ))

                    # Number of registers
        if functioncode not in [3, 4, 16] and numberOfRegisters != 1:
            raise ValueError('The numberOfRegisters is not valid for this function code. Given {0} and {1}.'.format( \
                repr(numberOfRegisters), functioncode))

        if functioncode == 16 and payloadformat == PAYLOADFORMAT_REGISTER and numberOfRegisters != 1:
            raise ValueError('Wrong numberOfRegisters when writing to a single register. Given {0}.'.format( \
                repr(numberOfRegisters)))
            # Note: For function code 16 there is checking also in the content conversion functions.

                    # Value
        if functioncode in [5, 6, 15, 16] and value is None:
            raise ValueError('The input value is not valid for this function code. Given {0} and {1}.'.format( \
                repr(value), functioncode))

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
                raise TypeError('The value parameter must be a list. Given {0}.'.format( repr(value) ))

            if len(value) != numberOfRegisters:
                raise ValueError('The list length does not match number of registers. List: {0},  Number of registers: {1}.'.format( \
                    repr(value), repr(numberOfRegisters) ))

        ## Build payload to slave ##
        if functioncode in [1, 2]:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(NUMBER_OF_BITS)

        elif functioncode in [3, 4]:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(numberOfRegisters)

        elif functioncode == 5:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _createBitpattern(functioncode, value)

        elif functioncode == 6:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(value, numberOfDecimals, signed=signed)

        elif functioncode == 15:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
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
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(numberOfRegisters) + \
                            _numToOneByteString(numberOfRegisterBytes) + \
                            registerdata

        ## Communicate ##
        payloadFromSlave = self._performCommand(functioncode, payloadToSlave)

        ## Check the contents in the response payload ##
        if functioncode in [1, 2, 3, 4]:
            _checkResponseByteCount(payloadFromSlave)   # response byte count

        if functioncode in [5, 6, 15, 16]:
            _checkResponseRegisterAddress(payloadFromSlave, registeraddress)  # response register address

        if functioncode == 5:
            _checkResponseWriteData(payloadFromSlave, _createBitpattern(functioncode, value)) # response write data

        if functioncode == 6:
            _checkResponseWriteData(payloadFromSlave, \
                _numToTwoByteString(value, numberOfDecimals, signed=signed)) # response write data

        if functioncode == 15:
            _checkResponseNumberOfRegisters(payloadFromSlave, NUMBER_OF_BITS) # response number of bits

        if functioncode == 16:
            _checkResponseNumberOfRegisters(payloadFromSlave, numberOfRegisters) # response number of registers

        ## Calculate return value ##
        if functioncode in [1, 2]:
            registerdata = payloadFromSlave[NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]            
            if len(registerdata) != NUMBER_OF_BYTES_FOR_ONE_BIT:
                raise ValueError('The registerdata length does not match NUMBER_OF_BYTES_FOR_ONE_BIT. Given {0}.'.format( \
                    repr(len(registerdata)) ))

            return _bitResponseToValue(registerdata)

        if functioncode in [3, 4]:
            registerdata = payloadFromSlave[NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
            if len(registerdata) != numberOfRegisterBytes:
                raise ValueError('The registerdata length does not match number of register bytes. Given {0} and {1}.'.format( \
                    repr(len(registerdata)), repr(numberOfRegisterBytes) ))
            
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

            raise ValueError('Wrong payloadformat for return value generation. Given {0}'.format( \
                repr(payloadformat) ))


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

        Makes use of the :meth:`_communicate` method. The message is generated with the :func:`_embedPayload` function, and the parsing of the response is done with the :func:`_extractPayload` function.

        """
        _checkFunctioncode(functioncode, None )
        _checkString(payloadToSlave, description='payload')

        message             = _embedPayload(self.address, functioncode, payloadToSlave)
        response            = self._communicate(message)
        payloadFromSlave    = _extractPayload(response, self.address, functioncode)

        return payloadFromSlave


    def _communicate(self, message):
        """Talk to the slave via a serial port.

        Args:
            message (str): The raw message that is to be sent to the slave.

        Returns:
            The raw data (string) returned from the slave.

        Raises:
            TypeError, ValueError, IOError

        Note that the answer might have strange ASCII control signs, which
        makes it difficult to print it in the promt (messes up a bit).
        Use repr() to make the string printable (shows ascii values for control signs.)

        Will block until timeout (or reaching a large number of bytes).

        If the attribute :attr:`Instrument.debug` is :const:`True`, the communication details are printed.

        If the attribute :attr:`Instrument.close_port_after_each_call` is :const:`True` the
        serial port is closed after each call.

        .. note::
            Some implementation details:

            Modbus RTU is a serial protocol that uses binary representation of the data.

            Error checking is done using CRC (cyclic redundancy check), and the result is two bytes.

            The data is stored internally in this driver as byte strings (representing byte values).
            For example a byte with value 18 (dec) = 12 (hex) = 00010010 (bin) is stored in a string of length one.
            This can be done using the function ``chr(18)`` or typing the string ``\\x12``.

            Note that these strings can look pretty strange when printed, as values 0 to 31 (dec) are
            ASCII control signs. For example 'vertical tab' and 'line feed' are among those.

            The **raw message** to the slave has the frame format: slaveaddress byte + functioncode byte +
            data payload + CRC code (two bytes).

            The **received message** should have the format: slaveaddress byte + functioncode byte +
            data payload + CRC code (two bytes)

            For Python3, the information sent to and from pySerial should be of the type bytes.
            This is taken care of automatically.

        """
        MAX_NUMBER_OF_BYTES = 1000

        _checkString(message, minlength=1, description='message')

        if self.debug:
            _print_out( 'MinimalModbus debug mode. Writing to instrument: ' + repr(message) )

        if self.close_port_after_each_call:
            self.serial.open()

        if sys.version_info[0] > 2:
            message = bytes(message, encoding='latin1') # Convert types to make it Python3 compatible

        self.serial.write(message)
        answer =  self.serial.read(MAX_NUMBER_OF_BYTES)

        if sys.version_info[0] > 2:
            answer = str(answer, encoding='latin1') # Convert types to make it Python3 compatible

        if self.close_port_after_each_call:
            self.serial.close()

        if self.debug:
            _print_out( 'MinimalModbus debug mode. Response from instrument: ' + repr(answer) )

        if len(answer) == 0:
            raise IOError('No communication with the instrument (no answer)')

        return answer


####################
# Payload handling #
####################

def _embedPayload(slaveaddress, functioncode, payloaddata):
    """Build a message from the slaveaddress, the function code and the payload data.

    Args:
        * slaveaddress (int): The address of the slave.
        * functioncode (int): The function code for the command to be performed. Can for example be 16 (Write register).
        * payloaddata (str): The byte string to be sent to the slave.

    Returns:
        The built (raw) message string for sending to the slave (including CRC etc).

    Raises:
        ValueError, TypeError.

    The resulting message has the format: slaveaddress byte + functioncode byte + payloaddata + CRC (which is two bytes).
    
    The CRC is calculated from the string made up of slaveaddress byte + functioncode byte + payloaddata.

    """
    _checkSlaveaddress(slaveaddress)
    _checkFunctioncode(functioncode, None)
    _checkString(payloaddata, description='payload')

    # Build message
    firstPart = _numToOneByteString(slaveaddress) + _numToOneByteString(functioncode) + payloaddata
    message = firstPart + _calculateCrcString(firstPart)
    return message


def _extractPayload(response, slaveaddress, functioncode):
    """Extract the payload data part from the slave's response.

    Args:
        * response (str): The raw response byte string from the slave.
        * slaveaddress (int): The adress of the slave. Used here for error checking only.
        * functioncode (int): Used here for error checking only.

    Returns:
        The payload part of the *response* string.

    Raises:
        ValueError, TypeError. Raises an exception if there is any problem with the received address, the functioncode or the CRC.

    The received message should have the format: slaveaddress byte + functioncode byte + payloaddata + CRC (which is two bytes)

    """
    BYTEPOSITION_FOR_SLAVEADDRESS          = 0 # Zero-based counting
    BYTEPOSITION_FOR_FUNCTIONCODE          = 1
    NUMBER_OF_RESPONSE_STARTBYTES          = 2
    NUMBER_OF_CRC_BYTES                    = 2
    BITNUMBER_FUNCTIONCODE_ERRORINDICATION = 7

    # Argument validity testing
    _checkString(response, description='response')
    _checkSlaveaddress(slaveaddress)
    _checkFunctioncode(functioncode, None)

    # Check CRC
    receivedCRC = response[-NUMBER_OF_CRC_BYTES:]
    responseWithoutCRC = response[0 : len(response) - NUMBER_OF_CRC_BYTES ]
    calculatedCRC = _calculateCrcString( responseWithoutCRC )

    if receivedCRC != calculatedCRC:
        raise ValueError( 'CRC error: {0} ({1}) instead of {2} ({3}). The response is: {4}'.format( \
            _twoByteStringToNum(receivedCRC),
            repr(receivedCRC),
            _twoByteStringToNum(calculatedCRC),
            repr(calculatedCRC),
            repr(response)    ))

    # Check slave address
    responseaddress = ord( response[BYTEPOSITION_FOR_SLAVEADDRESS] )

    if responseaddress != slaveaddress:
        raise ValueError( 'Wrong return slave address: {0} instead of {1}. The response is: {2}'.format( \
            responseaddress, slaveaddress, repr(response) ))

    # Check function code
    receivedFunctioncode = ord( response[BYTEPOSITION_FOR_FUNCTIONCODE ] )

    if receivedFunctioncode == _setBitOn(functioncode, BITNUMBER_FUNCTIONCODE_ERRORINDICATION):
        raise ValueError( 'The slave is indicating an error. The response is: {0}'.format( repr(response) ))

    elif receivedFunctioncode != functioncode:
        raise ValueError( 'Wrong functioncode: {0} instead of {1}. The response is: {2}'.format( \
            receivedFunctioncode, functioncode, repr(response) ))

    # Read data payload
    firstDatabyteNumber = NUMBER_OF_RESPONSE_STARTBYTES
    lastDatabyteNumber  = len(response) - NUMBER_OF_CRC_BYTES

    payload = response[ firstDatabyteNumber:lastDatabyteNumber ]
    return payload


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


def _numToTwoByteString(value, numberOfDecimals = 0, LsbFirst = False, signed=False):
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
    _checkInt(numberOfDecimals, minvalue=0, description='number of decimals' )
    _checkBool(LsbFirst, description='LsbFirst')
    _checkBool(signed, description='signed parameter')

    multiplier = 10 ** numberOfDecimals
    integer = int( float(value) * multiplier )

    if LsbFirst:
        formatcode = '<' # Little-endian
    else:
        formatcode = '>' # Big-endian
    if signed:
        formatcode += 'h' # (Signed) short (2 bytes)
    else:
        formatcode += 'H' # Unsigned short (2 bytes)

    outstring = _pack(formatcode, integer)
    assert len(outstring) == 2
    return outstring


def _twoByteStringToNum(bytestring, numberOfDecimals = 0, signed=False):
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
    _checkInt(numberOfDecimals, minvalue=0, description='number of decimals' )
    _checkBool(signed, description='signed parameter')

    formatcode = '>' # Big-endian
    if signed:
        formatcode += 'h' # (Signed) short (2 bytes)
    else:
        formatcode += 'H' # Unsigned short (2 bytes)

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
        * signed (bol): Whether large positive values should be interpreted as negative values.
        * numberOfRegisters (int): Should be 2. For error checking only.

    Returns:
        A bytestring (4 bytes).

    Raises:
        TypeError, ValueError

    """
    _checkInt(value, description='inputvalue')
    _checkBool(signed, description='signed parameter')
    _checkInt(numberOfRegisters, minvalue=2, maxvalue=2, description='number of registers' )

    formatcode = '>' # Big-endian
    if signed:
        formatcode += 'l' # (Signed) long (4 bytes)
    else:
        formatcode += 'L' # Unsigned long (4 bytes)

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
    _checkInt(numberOfRegisters, minvalue=2, maxvalue=2, description='number of registers' )

    formatcode = '>' # Big-endian
    if signed:
        formatcode += 'l' # (Signed) long (4 bytes)
    else:
        formatcode += 'L' # Unsigned long (4 bytes)

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
    _checkInt(numberOfRegisters, minvalue=2, maxvalue=4, description='number of registers' )

    formatcode = '>' # Big-endian
    if numberOfRegisters == 2:
        formatcode += 'f' # Float (4 bytes)
        lengthtarget = 4
    elif numberOfRegisters == 4:
        formatcode += 'd' # Double (8 bytes)
        lengthtarget = 8
    else:
        raise ValueError('Wrong number of registers! Given value is {0}'.format(repr(numberOfRegisters)))

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
    _checkInt(numberOfRegisters, minvalue=2, maxvalue=4, description='number of registers' )

    numberOfBytes = _NUMBER_OF_BYTES_PER_REGISTER * numberOfRegisters

    formatcode = '>' # Big-endian
    if numberOfRegisters == 2:
        formatcode += 'f' # Float (4 bytes)
    elif numberOfRegisters == 4:
        formatcode += 'd' # Double (8 bytes)
    else:
        raise ValueError('Wrong number of registers! Given value is {0}'.format(repr(numberOfRegisters)))

    if len(bytestring) != numberOfBytes:
        raise ValueError('Wrong length of the byte string! Given value is {0}, and numberOfRegisters is {1}.'.\
            format(repr(bytestring), repr(numberOfRegisters)))

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
    maxCharacters = _NUMBER_OF_BYTES_PER_REGISTER*numberOfRegisters
    _checkString(inputstring, 'input string', minlength=1, maxlength=maxCharacters)

    bytestring = inputstring.ljust(maxCharacters) # Pad with space
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
    maxCharacters = _NUMBER_OF_BYTES_PER_REGISTER*numberOfRegisters
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
        raise TypeError('The valuelist parameter must be a list. Given {0}.'.format( repr(valuelist) ))

    for value in valuelist:
        _checkInt(value, minvalue=MINVALUE, maxvalue=MAXVALUE, description='elements in the input value list' )

    _checkInt(len(valuelist), minvalue=numberOfRegisters, maxvalue=numberOfRegisters, \
        description='length of the list')

    numberOfBytes = _NUMBER_OF_BYTES_PER_REGISTER*numberOfRegisters

    bytestring =''
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
    numberOfBytes = _NUMBER_OF_BYTES_PER_REGISTER*numberOfRegisters
    _checkString(bytestring, 'byte string', minlength=numberOfBytes, maxlength=numberOfBytes)

    values = []
    for i in range(numberOfRegisters):
        offset = _NUMBER_OF_BYTES_PER_REGISTER*i
        substring = bytestring[offset : offset+_NUMBER_OF_BYTES_PER_REGISTER]
        values.append( _twoByteStringToNum(substring) )

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
        errortext += ' Value: {0} Struct format code is: {1}'
        formattedError = errortext.format(repr(value), formatstring)
        raise ValueError(formattedError)

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
        packed = bytes(packed, encoding='latin1') # Convert types to make it Python3 compatible

    try:
        value = struct.unpack(formatstring, packed)[0]
    except:
        errortext = 'The received bytestring is probably wrong  as the bytestring-to-num conversion failed.'
        errortext += ' Bytestring: {0} Struct format code is: {1}'
        formattedError = errortext.format(repr(packed), formatstring)
        raise ValueError(formattedError)

    return value


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
        raise ValueError( 'Could not convert bit response to a value. Input: {0}'.format(repr(bytestring)) )


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
    _checkInt(value, minvalue=0, maxvalue=1, description='inputvalue' )

    if functioncode == 5:
        if value == 0:
            return '\x00\x00'
        else:
            return '\xff\x00'

    elif functioncode == 15:
        if value == 0:
            return '\x00'
        else:
            return '\x01' # Is this correct??


#######################
# Number manipulation #
#######################

def _twosComplement(x, bits=16):
    """Calculate the two's complement of an integer.

    Then also negative values can be represented by an upper range of positive values.
    See http://en.wikipedia.org/wiki/Two%27s_complement

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
    upperlimit = 2**(bits - 1) - 1
    lowerlimit = -2**(bits - 1)
    if x > upperlimit or x < lowerlimit:
        raise ValueError('The input value is out of range. Given value is {0}, but allowed range is {1} to {2} when using {3} bits.' \
            .format(x, lowerlimit, upperlimit, bits) )

    # Calculate two'2 complement
    if x >= 0:
        return x
    return x + 2**bits


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
    upperlimit = 2**(bits) - 1
    lowerlimit = 0
    if x > upperlimit or x < lowerlimit:
        raise ValueError('The input value is out of range. Given value is {0}, but allowed range is {1} to {2} when using {3} bits.' \
            .format(x, lowerlimit, upperlimit, bits) )

    # Calculate inverse(?) of two'2 complement
    limit = 2**(bits - 1) - 1
    if x <= limit:
        return x
    return x - 2**bits


####################
# Bit manipulation #
####################

def _XOR(integer1, integer2):
    """An alias for the bitwise XOR command.

    Args:
        * integer1 (int): Input integer
        * integer2 (int): Input integer

    Returns:
        The XOR:ed value of the two input integers. This is an integer.
    """
    _checkInt(integer1, minvalue=0, description='integer1' )
    _checkInt(integer2, minvalue=0, description='integer2' )

    return integer1 ^ integer2


def _setBitOn( x, bitNum ):
    """Set bit 'bitNum' to True.

    Args:
        * x (int): The value before.
        * bitNum (int): The bit number that should be set to True.

    Returns:
        The value after setting the bit. This is an integer.

    For example:
        For x = 4 (dec) = 0100 (bin), setting bit number 0 results in 0101 (bin) = 5 (dec).

    """
    _checkInt(x, minvalue=0, description='input value' )
    _checkInt(bitNum, minvalue=0, description='bitnumber' )

    return x | (1<<bitNum)


def _rightshift(inputInteger):
    """Rightshift an integer one step, and also calculate the carry bit.

    Args:
        inputInteger (int): The value to be rightshifted. Should be positive.

    Returns:
        The tuple (*shifted*, *carrybit*) where *shifted* is the rightshifted integer and *carrybit* is the
        resulting carry bit.

    For example:
        An *inputInteger* = 9 (dec) = 1001 (bin) will after a rightshift be 0100 (bin) = 4 and the carry bit is 1.
        The return value will then be the tuple (4, 1).

    """
    _checkInt(inputInteger, minvalue=0)

    shifted = inputInteger >> 1
    carrybit = inputInteger & 1
    return shifted, carrybit


############################
# Error checking functions #
############################

def _calculateCrcString(inputstring):
    """Calculate CRC-16 for Modbus.

    Args:
        inputstring (str): An arbitrary-length message (without the CRC).

    Returns:
        A two-byte CRC string, where the least significant byte is first.

    Algorithm from the document 'MODBUS over serial line specification and implementation guide V1.02'.

    """
    _checkString(inputstring, description='input CRC string')

    # Constant for MODBUS CRC-16
    POLY = 0xA001

    # Preload a 16-bit register with ones
    register = 0xFFFF

    for character in inputstring:

        # XOR with each character
        register = _XOR(register, ord(character))

        # Rightshift 8 times, and XOR with polynom if carry overflows
        for i in range(8):
            register, carrybit = _rightshift(register)
            if carrybit == 1:
                register = _XOR(register, POLY)

    return _numToTwoByteString(register, LsbFirst = True)


def _checkFunctioncode(functioncode, listOfAllowedValues = []):
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

    _checkInt(functioncode, FUNCTIONCODE_MIN, FUNCTIONCODE_MAX, description='functioncode' )

    if listOfAllowedValues is None:
        return

    if not isinstance(listOfAllowedValues, list):
        raise TypeError( 'The listOfAllowedValues should be a list. Given: {0}'.format(repr(listOfAllowedValues)) )

    for value in listOfAllowedValues:
        _checkInt(value, FUNCTIONCODE_MIN, FUNCTIONCODE_MAX, description='functioncode inside listOfAllowedValues')

    if functioncode not in listOfAllowedValues:
        raise ValueError( 'Wrong function code: {0}, allowed values are {1}'.format(functioncode, repr(listOfAllowedValues)) )


def _checkSlaveaddress(slaveaddress):
    """Check that the given slaveaddress is valid.

    Args:
        slaveaddress (int): The slave address

    Raises:
        TypeError, ValueError

    """
    SLAVEADDRESS_MAX = 247
    SLAVEADDRESS_MIN = 0

    _checkInt(slaveaddress, SLAVEADDRESS_MIN, SLAVEADDRESS_MAX, description='slaveaddress' )


def _checkRegisteraddress(registeraddress):
    """Check that the given registeraddress is valid.

    Args:
        registeraddress (int): The register address

    Raises:
        TypeError, ValueError

    """
    REGISTERADDRESS_MAX = 0xFFFF
    REGISTERADDRESS_MIN = 0

    _checkInt(registeraddress, REGISTERADDRESS_MIN, REGISTERADDRESS_MAX, description='registeraddress' )


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

    givenNumberOfDatabytes = ord( payload[POSITION_FOR_GIVEN_NUMBER] )
    countedNumberOfDatabytes = len(payload) - NUMBER_OF_BYTES_TO_SKIP

    if givenNumberOfDatabytes != countedNumberOfDatabytes:
        errortemplate = 'Wrong given number of bytes in the response: {0}, but counted is {1} as data payload length is {2}.' + \
            ' The data payload is: {3}'
        errortext = errortemplate.format(givenNumberOfDatabytes, countedNumberOfDatabytes, len(payload), repr(payload))
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
    receivedStartAddress = _twoByteStringToNum( bytesForStartAddress )

    if receivedStartAddress != registeraddress:
        raise ValueError( 'Wrong given write start adress: {0}, but commanded is {1}. The data payload is: {2}'.format( \
            receivedStartAddress, registeraddress, repr(payload)))


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
    _checkInt(numberOfRegisters, minvalue=1, maxvalue=0xFFFF, description='numberOfRegisters' )

    BYTERANGE_FOR_NUMBER_OF_REGISTERS = slice(2, 4)

    bytesForNumberOfRegisters = payload[BYTERANGE_FOR_NUMBER_OF_REGISTERS]
    receivedNumberOfWrittenReisters = _twoByteStringToNum( bytesForNumberOfRegisters )

    if receivedNumberOfWrittenReisters != numberOfRegisters:
        raise ValueError( 'Wrong number of registers to write in the response: {0}, but commanded is {1}. The data payload is: {2}'.format( \
            receivedNumberOfWrittenReisters, numberOfRegisters, repr(payload)) )


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
        raise ValueError( 'Wrong write data in the response: {0}, but commanded is {1}. The data payload is: {2}'.format( \
            repr(receivedWritedata), repr(writedata), repr(payload)) )


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
        raise TypeError( 'The description should be a string. Given: {0}'.format(repr(description)) )

    if not isinstance(inputstring, str):
        raise TypeError( 'The {0} should be a string. Given: {1}'.format(description, repr(inputstring)) )

    if not isinstance(maxlength, (int, type(None))):
        raise TypeError( 'The maxlength must be an integer or None. Given: {0}'.format(repr(maxlength)) )

    # Check values
    _checkInt(minlength, minvalue=0, maxvalue=None, description='minlength')

    if len(inputstring) < minlength:
        raise ValueError( 'The {0} is too short: {1}, but minimum value is {2}. Given: {3}'.format( \
            description, len(inputstring), minlength, repr(inputstring)))

    if not maxlength is None:
        if maxlength < 0:
            raise ValueError( 'The maxlength must be positive. Given: {0}'.format(maxlength) )

        if maxlength < minlength:
            raise ValueError( 'The maxlength must not be smaller than minlength. Given: {0} and {1}'.format( \
                maxlength, minlength) )

        if len(inputstring) > maxlength:
            raise ValueError( 'The {0} is too long: {1}, but maximum value is {2}. Given: {3}'.format( \
                description, len(inputstring), maxlength, repr(inputstring)))


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
        raise TypeError( 'The description should be a string. Given: {0}'.format(repr(description)) )

    if not isinstance(inputvalue, (int, long)):
        raise TypeError( 'The {0} must be an integer. Given: {1}'.format(description, repr(inputvalue)) )

    if not isinstance(minvalue, (int, long, type(None))):
        raise TypeError( 'The minvalue must be an integer or None. Given: {0}'.format(repr(minvalue)) )

    if not isinstance(maxvalue, (int, long, type(None))):
        raise TypeError( 'The maxvalue must be an integer or None. Given: {0}'.format(repr(maxvalue)) )

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
        raise TypeError( 'The description should be a string. Given: {0}'.format(repr(description)) )

    if not isinstance(inputvalue, (int, long, float)):
        raise TypeError( 'The {0} must be numerical. Given: {1}'.format(description, repr(inputvalue)) )

    if not isinstance(minvalue, (int, float, long, type(None))):
        raise TypeError( 'The minvalue must be numeric or None. Given: {0}'.format(repr(minvalue)) )

    if not isinstance(maxvalue, (int, float, long, type(None))):
        raise TypeError( 'The maxvalue must be numeric or None. Given: {0}'.format(repr(maxvalue)) )

    # Consistency checking
    if (not minvalue is None) and (not maxvalue is None):
        if maxvalue < minvalue:
            raise ValueError( 'The maxvalue must not be smaller than minvalue. Given: {0} and {1}, respectively.'.format( \
                maxvalue, minvalue) )

    # Value checking
    if not minvalue is None:
        if inputvalue < minvalue:
            raise ValueError( 'The {0} is too small: {1}, but minimum value is {2}.'.format( \
                description, inputvalue, minvalue))

    if not maxvalue is None:
        if inputvalue > maxvalue:
            raise ValueError( 'The {0} is too large: {1}, but maximum value is {2}.'.format( \
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
        raise TypeError( 'The {0} must be boolean. Given: {1}'.format(description, repr(inputvalue)) )


#####################
# Development tools #
#####################

def _print_out( inputstring ):
    """Print the inputstring. To make it compatible with Python2 and Python3.

     Args:
        inputstring (str): The string that should be printed.

    Raises:
        TypeError

    """
    _checkString(inputstring, description='string to print')

    sys.stdout.write(inputstring + '\n')


def _getDiagnosticString():
    """Generate a diagnostic string, showing the module version, the platform, current directory etc.

    Returns:
        A descriptive string.

    """
    text = '\n## Diagnostic output from minimalmodbus ## \n\n'
    text += 'Minimalmodbus version: ' + __version__ + '\n'
    text += 'Minimalmodbus status: ' + __status__ + '\n'
    text += 'Revision: ' + __revision__ + '\n'
    text += 'Revision date: ' + __date__ + '\n'
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
        text += 'Long info: (none)\n' # For Python3 compatibility
    try:
        text += 'Float repr style: ' + repr(sys.float_repr_style) + '\n\n'
    except:
        text += 'Float repr style: (none) \n\n'  # For Python 2.6 compatibility
    text += 'Variable __name__: ' + __name__ + '\n'
    text += 'Current directory: ' + os.getcwd() + '\n\n'
    text += 'Python path: \n'
    text += '\n'.join( sys.path ) + '\n'
    text += '\n## End of diagnostic output ## \n'
    return text


########################
## Testing the module ##
########################

if __name__ == '__main__':

    _print_out( 'TESTING MODBUS MODULE' )
    #instrument = Instrument('/dev/cvdHeatercontroller', 1)
    #instrument.debug = True
    #_print_out( str(instrument.read_register(273, 1)) )
    _print_out( 'DONE!' )

pass


