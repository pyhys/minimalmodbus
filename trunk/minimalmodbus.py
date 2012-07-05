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

MinimalModbus: A Python driver for the Modbus RTU protocol via serial port (via RS485 or RS232).

This Python file was changed (committed) at $Date$, 
which was $Revision$.

"""

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"

__version__   = "0.3.2"
__status__    = "Alpha"
__revision__  = "$Rev$"
__date__      = "$Date$"

import os
import serial
import sys

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
            * registeraddress (int): The register address (use decimal numbers, not hex).  
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
            * registeraddress (int): The register address (use decimal numbers, not hex).
            * value (int): 0 or 1 
            * functioncode (int): Modbus function code. Can be 5 or 15.

        Returns:
            None

        Raises:
            ValueError, TypeError, IOError

        """
        _checkFunctioncode(functioncode, [5, 15])     
        self._genericCommand(functioncode, registeraddress, value)
        

    def read_register(self, registeraddress, numberOfDecimals=0, functioncode=3):
        """Read an integer from one 16-bit register in the slave, possibly scaling it.
        
        The slave register can hold integer values in the range 0-65535. 

        Args:
            * registeraddress (int): The register address (use decimal numbers, not hex).  
            * numberOfDecimals (int): The number of decimals for content conversion.
            * functioncode (int): Modbus function code. Can be 3 or 4.

        If a value of 77.0 is stored internally in the slave register as 770, then use ``numberOfDecimals=1``
        which will divide the received data by 10 before returning the value.
        
        Similarly ``numberOfDecimals=2`` will divide the received data by 100 before returning the value.

        Returns:
            The register data in numerical value (int or float).

        Raises:
            ValueError, TypeError, IOError

        """
        _checkFunctioncode(functioncode, [3, 4])   
        return self._genericCommand(functioncode, registeraddress, numberOfDecimals=numberOfDecimals)


    def write_register(self, registeraddress, value, numberOfDecimals=0, functioncode=16):
        """Write an integer to one 16-bit register in the slave, possibly scaling it.
        
        The slave register can hold integer values in the range 0-65535. 
        
        Args:
            * registeraddress (int): The register address  (use decimal numbers, not hex).
            * value (int or float): The value to store in the slave (might be scaled before sending). 
            * numberOfDecimals (int): The number of decimals for content conversion.
            * functioncode (int): Modbus function code. Can be 6 or 16.

        To store for example ``value=77.0``, use ``numberOfDecimals=1`` if the register will hold it as 770 internally. 
        This will multiply ``value`` by 10 before sending it to the slave.
        
        Similarly ``numberOfDecimals=2`` will multiply ``value`` by 100 before sending it to the slave.

        Returns:
            None

        Raises:
            ValueError, TypeError, IOError

        """
        _checkFunctioncode(functioncode, [6, 16])
        self._genericCommand(functioncode, registeraddress, value, numberOfDecimals)
  
    
    def _genericCommand(self, functioncode, registeraddress, value=None, numberOfDecimals=0):
        """Generic command for reading and writing registers and bits.
        
        Args:
            * functioncode (int): Modbus function code. 
            * registeraddress (int): The register address  (use decimal numbers, not hex).
            * value (numerical): The value to store in the register 
            * numberOfDecimals (int): The number of decimals for content conversion.
        
        Returns:
            The register data in numerical value (int or float), or the bit value 0 or 1 (int), or ``None``.
        
        Raises:
            ValueError, TypeError, IOError
        
        """
                
        NUMBER_OF_REGISTERS = 1
        NUMBER_OF_BYTES_PER_REGISTER = 2
        numberOfRegisterBytes = NUMBER_OF_REGISTERS * NUMBER_OF_BYTES_PER_REGISTER
        NUMBER_OF_BITS = 1
        NUMBER_OF_BYTES_FOR_ONE_BIT = 1
        NUMBER_OF_BYTES_BEFORE_REGISTERDATA = 1
        ALL_ALLOWED_FUNCTIONCODES = list(range(1,7)) + [15, 16] # To comply with both Python2 and Python3
                        
        _checkFunctioncode(functioncode, ALL_ALLOWED_FUNCTIONCODES)
        _checkRegisteraddress(registeraddress)
        if not isinstance(value, type(None)):
            _checkNumerical(value, minvalue=0, description='input value')
        _checkInt(numberOfDecimals, minvalue=0, description='number of decimals' )
                   
        ## Build payload to slave
        
        if functioncode in [1, 2]:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(NUMBER_OF_BITS)
                            
        elif functioncode in [3, 4]:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(NUMBER_OF_REGISTERS)

        elif functioncode == 5:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _createBitpattern(functioncode, value)
        
        elif functioncode == 6:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(value, numberOfDecimals)
        
        elif functioncode == 15:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(NUMBER_OF_BITS) + \
                            _numToOneByteString(NUMBER_OF_BYTES_FOR_ONE_BIT) + \
                            _createBitpattern(functioncode, value)               
        
        elif functioncode ==16:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(NUMBER_OF_REGISTERS) + \
                            _numToOneByteString(numberOfRegisterBytes) + \
                            _numToTwoByteString(value, numberOfDecimals)
                            
        ## Communicate
        payloadFromSlave = self._performCommand(functioncode, payloadToSlave)

        ## Check the contents in the response payload  
        if functioncode in [1, 2, 3, 4]:
            _checkResponseByteCount(payloadFromSlave)   # response byte count
    
        if functioncode == 5:
            _checkResponseWriteData(payloadFromSlave, _createBitpattern(functioncode, value)) # response write data
    
        if functioncode == 6:
            _checkResponseWriteData(payloadFromSlave, _numToTwoByteString(value, numberOfDecimals)) # response write data
        
        if functioncode in [5, 6, 15, 16]:
            _checkResponseRegisterAddress(payloadFromSlave, registeraddress)  # response register address        
            
        if functioncode == 15:
            _checkResponseNumberOfRegisters(payloadFromSlave, NUMBER_OF_BITS) # response number of bits    
        
        if functioncode == 16:
            _checkResponseNumberOfRegisters(payloadFromSlave, NUMBER_OF_REGISTERS) # response number of registers    
        
        ## Calculate return value
        if functioncode in [1, 2]:   
            registerdata = payloadFromSlave[NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
            assert len(registerdata) == NUMBER_OF_BYTES_FOR_ONE_BIT
            return _bitResponseToValue(registerdata)  
        
        if functioncode in [3, 4]:
            registerdata = payloadFromSlave[NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
            assert len(registerdata) == numberOfRegisterBytes
            return _twoByteStringToNum(registerdata, numberOfDecimals)
    
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
        
    The resulting message has the format: slaveaddress byte + functioncode byte + payloaddata + CRC (which is two bytes)
    
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


def _numToTwoByteString(value, numberOfDecimals = 0, LsbFirst = False):
    """Convert a numerical value to a two-byte string.

    Args:
        * value (float or int): The numerical value to be converted.
        * numberOfDecimals (int): Number of decimals, 0 or more.
        * LsbFirst (bol): Whether the least significant byte should be first in the resulting string.

    Returns:
        A two-byte string.

    Raises:
        TypeError, ValueError

    For example:
        To store for example value=77.0, use ``numberOfDecimals = 1`` if the register will hold it as 770 internally.
        The value 770 (dec) is 0302 (hex), where the most significant byte is 03 (hex) and the
        least significant byte is 02 (hex). With ``LsbFirst = False``, the most significant byte is given first
        why the resulting string is ``\\x03\\x02``, which has the length 2.

    """
    
    _checkNumerical(value, minvalue=0, description='inputvalue')
    _checkInt(numberOfDecimals, minvalue=0, description='number of decimals' )

    if not isinstance( LsbFirst, bool ):
        raise TypeError( 'The LsbFirst must be a boolean. Given: {0}'.format(repr(LsbFirst)) )    
        
    multiplier = 10 ** numberOfDecimals
    integer = int( float(value) * multiplier )

    if integer > 0xFFFF:
        raise ValueError( 'The resulting integer is too large: {0} Given value: {1} and numberOfDecimals {2}'.format( \
            integer, value, numberOfDecimals))
    
    mostSignificantByte =  integer >> 8
    leastSignificantByte = integer & 0xFF
    if LsbFirst: 
        outstring = chr(leastSignificantByte) + chr(mostSignificantByte)
    else:
        outstring = chr(mostSignificantByte) + chr(leastSignificantByte)
        
    assert len(outstring) == 2
        
    return outstring
    
    
def _twoByteStringToNum(bytestring, numberOfDecimals = 0):
    """Convert a two-byte string to a numerical value.
    
    Args:    
        * bytestring (str): A string of length 2.
        * numberOfDecimals (int): The number of decimal. Defaults to 0.

    Returns:
        The numerical value (int or float) calculated from the ``bytestring``.        
        
    Raises:
        TypeError, ValueError
        
    For example:
        A string ``\\x03\\x02`` (which has the length 2) corresponds to 0302 (hex) = 770 (dec). If
        ``numberOfDecimals = 1``, then this is converted to 77.0 (float). 

    A bug was found on 2011-05-16: The most significant byte was 
    multiplied by 255 instead of the correct value 256.
    
    """
    _checkString(bytestring, minlength=2, maxlength=2, description='bytestring')
    _checkInt(numberOfDecimals, minvalue=0, description='number of decimals' )
        
    leastSignificantByte = ord(bytestring[1])
    mostSignificantByte  = ord(bytestring[0])
    fullregister = mostSignificantByte*0x100 + leastSignificantByte
    
    if numberOfDecimals == 0:
        return fullregister
    divisor = 10 ** numberOfDecimals
    return fullregister / float(divisor)


def _bitResponseToValue(bytestring):
    """Convert a response string to a numerical value.
    
    Args:    
        bytestring (str): A string of length 1. Can be for example ``\\x01``.
        
    Returns:
        The converted value (int).     
        
    Raises:
        TypeError
    
    """
    _checkString(bytestring, description='bytestring')
    
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

def _calculateCrcString( inputstring ):
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
    
    
def _checkRegisteraddress( registeraddress ):
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
    POSITION = 0
    NUMBER_OF_BYTES_TO_SKIP = 1
    
    _checkString(payload, minlength=1, description='payload')
 
    givenNumberOfDatabytes = ord( payload[POSITION] )
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
        * writedata (string): The data to write, should be 2 bytes.
    
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
        * inputvalue (int): The integer to be checked
        * minvalue (int): Minimum value of the integer
        * maxvalue (int): Maximum value of the integer
        * description (string): Used in error messages for the checked inputvalue
    
    Raises:
        TypeError, ValueError

    Note: Can not use the function :func:`_checkString`, as that function uses this function internally.

    """        
    
    # Type checking
    if not isinstance(description, str):
        raise TypeError( 'The description should be a string. Given: {0}'.format(repr(description)) )
    
    if not isinstance(inputvalue, int):
        raise TypeError( 'The {0} must be an integer. Given: {1}'.format(description, repr(inputvalue)) )

    if not isinstance(minvalue, (int, type(None))):
        raise TypeError( 'The minvalue must be an integer or None. Given: {0}'.format(repr(minvalue)) )

    if not isinstance(maxvalue, (int, type(None))):
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
       
    if not isinstance(inputvalue, (int, float)):
        raise TypeError( 'The {0} must be numerical. Given: {1}'.format(description, repr(inputvalue)) )
    
    if not isinstance(minvalue, (int, float, type(None))):
        raise TypeError( 'The minvalue must be numeric or None. Given: {0}'.format(repr(minvalue)) )

    if not isinstance(maxvalue, (int, float, type(None))):
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
    text += 'Python version: ' + sys.version + '\n'
    text += 'Python flags: ' + repr(sys.flags) + '\n'
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


