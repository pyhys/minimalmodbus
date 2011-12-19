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

__version__   = "0.24"
__status__    = "Alpha"
__revision__  = "$Rev$"
__date__      = "$Date$"

import os
import serial
import sys

BAUDRATE = 19200 
"""Default value for the baudrate in Baud (int)."""

PARITY   = serial.PARITY_NONE 
"""Default value for the  parity (probably int). See the pySerial module for documentation. Defaults to serial.PARITY_NONE"""

BYTESIZE = 8 
"""Default value for the bytesize (int)."""

STOPBITS = 1
"""Default value for the number of stopbits (int)."""

TIMEOUT  = 0.05 
"""Default value for the timeout value in seconds (float). Defaults to 0.05.""" 

_CLOSE_PORT_AFTER_EACH_CALL = False
"""Default value for port closure setting.""" 

class Instrument():
    """Instrument class for talking to instruments (slaves) via the Modbus RTU protocol (via RS485 or RS232).

    Args:
        * port (str): The serial port name, for example ``/dev/ttyS1`` or ``COM1``.
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
            - parity (int):    Parity. See the pySerial module for documentation. 
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

        self._debug = False
        """Set this to True to print the communication details."""
        
        self._close_port_after_each_call = _CLOSE_PORT_AFTER_EACH_CALL
        """Set this to True to close the serial port after each call."""      
        
        if  self._close_port_after_each_call:
            self.serial.close()

    ########################################
    ## Functions for talking to the slave ##
    ########################################

    def read_bit(self, registeraddress, functioncode=2):
        """Read one bit from the slave.

        Args:
            * registeraddress (int): The register address (use decimal numbers, not hex).  
            * functioncode (int): Modbus functions code. Can be 1 or 2.

        Returns:
            The bit value 0 or 1 (int).

        Raises:
            ValueError

        """
        print 'READING BIT'
        _checkFunctioncode(functioncode, [1, 2])

        return self._genericCommand(functioncode, registeraddress)


    def write_bit(self, registeraddress, value, functioncode=5):
        """Write one bit in the slave.
        
        Args:
            * registeraddress (int): The register address  (use decimal numbers, not hex).
            * value (int): 0 or 1 
            * functioncode (int): Modbus functions code. Can be 5 or 15.

        Returns:
            None

        Raises:
            ValueError

        """
        _checkFunctioncode(functioncode, [5, 15])     
        
        self._genericCommand(functioncode, registeraddress, value)
        

    def read_register(self, registeraddress, numberOfDecimals=0, functioncode=3):
        """Read one register from the slave.

        Args:
            * registeraddress (int): The register address (use decimal numbers, not hex).  
            * numberOfDecimals (int): The number of decimals for content conversion
            * functioncode (int): Modbus functions code. Can be 3 or 4.

        If a value of 77.0 is stored internally in the slave register as 770, then use numberOfDecimals=1

        Returns:
            The register data in numerical value (int or float).

        Raises:
            ValueError

        """
        _checkFunctioncode(functioncode, [3, 4])   
        
        return self._genericCommand(functioncode, registeraddress, numberOfDecimals=numberOfDecimals)


    def write_register(self, registeraddress, value, numberOfDecimals=0, functioncode=16):
        """Write to one register in the slave.
        
        Args:
            * registeraddress (int): The register address  (use decimal numbers, not hex).
            * value (float): The value to store in the register 
            * numberOfDecimals (int): The number of decimals for content conversion.
            * functioncode (int): Modbus functions code. Can be 6 or 16.

        To store for example value=77.0, use numberOfDecimals=1 if the register will hold it as 770 internally.

        Returns:
            None

        Raises:
            ValueError

        """
        _checkFunctioncode(functioncode, [6, 16])
        
        self._genericCommand(functioncode, registeraddress, value, numberOfDecimals)
    
    ##########################################
    ## Communication implementation details ##
    ##########################################
    
    def _genericCommand(self, functioncode, registeraddress, value=None, numberOfDecimals=0):
        """Generic command for reading and writing registers and bits.
        
        Args:
            * functioncode (int): Modbus functions code. 
            * registeraddress (int): The register address  (use decimal numbers, not hex).
            * value (numerical): The value to store in the register 
            * numberOfDecimals (int): The number of decimals for content conversion.
        
        
        """
        
        NUMBER_OF_REGISTERS = 1
        NUMBER_OF_BYTES_PER_REGISTER = 2
        
        numberOfRegisterBytes = NUMBER_OF_REGISTERS * NUMBER_OF_BYTES_PER_REGISTER
        
        STARTBYTENUMBER_FOR_STARTADDRESS = 0
        STARTBYTENUMBER_FOR_NUMBEROFREGISTERS = 2
                
        BYTEPOSITION_FOR_RESPONSE_NUMBEROFBYTES = 0
        NUMBER_OF_BYTES_BEFORE_REGISTERDATA = 1
        
        BITPATTERN_ON =  0x0000
        BITPATTERN_OFF = 0xFF00
                
        _checkFunctioncode(functioncode, None )
        
        ## Adjust value if writing a single bit
        if functioncode in [5, 15]:  # IS THIS CORRECT???
            if value == 0:
                writevalue = 0 #??
            elif value == 1:
                writevalue = 1 #??
            else:
                raise ValueError('Wrong')
        else:
            writevalue = value
        
        ## Build payload to slave
        if functioncode in [1, 2, 3, 4]:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(NUMBER_OF_REGISTERS)

        elif functioncode in [5, 6]:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(writevalue, numberOfDecimals)
        
        elif functioncode in [15, 16]:
            payloadToSlave =_numToTwoByteString(registeraddress) + \
                            _numToTwoByteString(NUMBER_OF_REGISTERS) + \
                            _numToOneByteString(numberOfRegisterBytes) + \
                            _numToTwoByteString(writevalue, numberOfDecimals)
                            
        ## Communicate
        payloadFromSlave = self._performCommand( functioncode, payloadToSlave)

        ## Check the contents in the response payload  
        if functioncode in [1, 2, 3, 4]:
            _checkByteCount(payloadFromSlave)   # given byte count
    
        if functioncode in [5, 6]:
            _checkResponseWriteData(payloadFromSlave, _numToTwoByteString(writevalue, numberOfDecimals)) # given write data
        
        if functioncode in [5, 6, 15, 16]:
            _checkResponseAddress(payloadFromSlave, registeraddress)    # given register address        
            
        if functioncode in [15, 16]:
            _checkResponseNumberOfRegisters(payloadFromSlave, NUMBER_OF_REGISTERS) # given number of registers    
            
        print 'PAYLOAD, len', len(payloadFromSlave), 'bytes ', repr(payloadFromSlave)    
        
        ## Extract register data
        if functioncode in [1, 2, 3, 4]:
            registerdata = payloadFromSlave[NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
            assert len(registerdata) == numberOfRegisterBytes
            
        ## Calculate response value
        if functioncode in [1, 2]:   
            return _bitResponseToValue(registerdata)  
        
        if functioncode in [3, 4]:
            return _twoByteStringToNum(registerdata, numberOfDecimals)
    
    
    def _performCommand(self, functioncode, payloadToSlave):
        """Performs the command having the *functioncode*.
        
        Args:
            * functioncode (int): The function code for the command to be performed. Can for example be 'Write register' = 16.
            * payloadToSlave (str): Data to be transmitted to the slave (will be embedded in slaveaddress, CRC etc)
    
        Returns:
            The extracted data payload from the slave (a string). It has been stripped of CRC etc.

        Makes use of the Instrument._communicate method. The message is generated with the :func:`_embedPayload` function, and the parsing of the response is done with the :func:`_extractPayload` function.

        """
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

        If the attribute ._debug is True, the communication details are printed.

        .. note::
            Some implementation details:

            Modbus RTU is a serial protocol that uses binary representation of the data.

            Error checking is done using CRC (cyclic redundancy check), and the result is two bytes.

            The data is stored internally in this driver as byte strings (representing byte values). 
            For example a byte with value 18 (dec) = 12 (hex) = 00010010 (bin) is stored in a string of length one.
            This can be done using the function chr(18) or typing the string ``BACKSLASHx12``, where ``BACKSLASH`` 
            should be replaced with the actual backslash sign. 

            Note that these strings can look pretty strange when printed, as values 0 to 31 (dec) are
            ASCII control signs. For example 'vertical tab' and 'line feed' are among those.

            The **raw message** to the slave has the frame format: slaveaddress byte + functioncode byte +
            data payload + CRC code (two bytes).

            The **received message** should have the format: slaveaddress byte + functioncode byte + 
            data payload + CRC code (two bytes)
            
        """

        MAX_NUMBER_OF_BYTES = 1000
        
        #TODO Check string type
        
        if len(message) == 0:
            raise ValueError('The message length must not be zero')
        
        if self._debug:
            _print_out( 'MinimalModbus debug mode. Writing to instrument: ' + repr(message) )           
        
        if self._close_port_after_each_call:
            self.serial.open()  
            
        self.serial.write(message)
        answer =  self.serial.read(MAX_NUMBER_OF_BYTES)
        
        if self._close_port_after_each_call:
            self.serial.close()
        
        if self._debug:
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
        * slaveaddress (int): The address of the slave
        * functioncode (int): The function code for the command to be performed. Can for example be 16 (Write register).
        * payloaddata (str): The byte integer string to be sent to the slave

    Returns:
        The built (raw) message string for sending to the slave (including CRC etc).    

    The resulting message has the format: slaveaddress byte + functioncode byte + payloaddata + CRC (which is two bytes)
    """
    
    SLAVEADDRESS_MAX = 247
    SLAVEADDRESS_MIN = 0
    
    _checkFunctioncode(functioncode, None)
    
    #TODO check types
    
    if not isinstance(payloaddata, str):
        raise TypeError( 'The input payload must be a string. Given: {0}'.format(repr(payloaddata)) )
    
    if slaveaddress < SLAVEADDRESS_MIN or slaveaddress > SLAVEADDRESS_MAX:
        raise ValueError( 'The slave address is out of range. Given value: {0} Allowed range: {1} to {2}'.format( \
            slaveaddress, SLAVEADDRESS_MIN, SLAVEADDRESS_MAX ) )
    
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
        ValueError. Raises an exception if there is any problem with the received address, the functioncode or the CRC.

    The received message should have the format: slaveaddress byte + functioncode byte + payloaddata + CRC (which is two bytes)

    """
    
    BYTEPOSITION_FOR_SLAVEADDRESS          = 0 # Zero-based counting
    BYTEPOSITION_FOR_FUNCTIONCODE          = 1
    
    NUMBER_OF_RESPONSE_STARTBYTES          = 2
    NUMBER_OF_CRC_BYTES                    = 2
    
    BITNUMBER_FUNCTIONCODE_ERRORINDICATION = 7
    
    #TODO check types
    
    if not isinstance(response, str):
        raise TypeError( 'The response must be a string. Given: {0}'.format(repr(response)) )

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

    # Check address
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
        * ValueError
        * TypeError
    """
    
    if not isinstance( inputvalue, (int, long) ):
        raise TypeError( 'The input must be an integer. Given input: {0}'.format(inputvalue) )
    
    if inputvalue > 0xFF:
        raise ValueError( 'The input value is too large. Given input: {0}'.format(inputvalue) )
    
    if inputvalue < 0:
        raise ValueError( 'The input value is negative. Given input: {0}'.format(inputvalue) )
    
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
        * ValueError
        * TypeError

    For example:
        To store for example value=77.0, use numberOfDecimals=1 if the register will hold it as 770 internally.
        The value 770 (dec) is 0302 (hex), where the most significant byte is 03 (hex) and the
        least significant byte is 02 (hex). With LsbFirst = False, the most significant byte is given first
        why the resulting string is ``BACKSLASHx03BACKSLASHx02``, which has the length 2.

    """
    
    if not isinstance( numberOfDecimals, ( int, long ) ):
        raise TypeError( 'The numberOfDecimals must be an integer. Given: {0}'.format(numberOfDecimals) )
    
    if not isinstance( LsbFirst, bool ):
        raise TypeError( 'The LsbFirst must be a boolean. Given: {0}'.format(LsbFirst) )
    
    if numberOfDecimals <0 :
        raise ValueError( 'The number of decimals must not be less than 0. Given: {0}'.format(numberOfDecimals) )

    if value < 0:
        raise ValueError( 'The input value must not be negative. Given: {0}'.format(value) )

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
        * ValueError
        * TypeError
        
    For example:
        A string ``BACKSLASHx03BACKSLASHx02`` (which has the length 2) corresponds to 0302 (hex) = 770 (dec). If
        numberOfDecimals=1, then this is converted to 77.0 (float). 

    A bug was found on 2011-05-16: The most significant byte was 
    multiplied by 255 instead of the correct value 256.
    
    """
    if not isinstance(bytestring, str):
        raise TypeError( 'The input must be a string. Given: {0}'.format(repr(bytestring)) )

    if len(bytestring) != 2:
        raise ValueError( 'The input string length is {0}. It should be 2.'.format(len(bytestring)) )

    if not isinstance( numberOfDecimals, ( int, long ) ):
        raise TypeError( 'The number of decimals must be integer. Given: {0}'.format(numberOfDecimals) )
        
    if numberOfDecimals <0 :
        raise ValueError( 'The number of decimals must not be less than 0. Given: {0}'.format(numberOfDecimals) )
        
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
        * bytestring (str): A string of leng
    """

    if not isinstance(bytestring, str):
        raise TypeError( 'The input must be a string. Given: {0}'.format(repr(bytestring)) ) 
    
    RESPONSE_ON  = '\x01'
    RESPONSE_OFF = '\x00'
    
    if bytestring == RESPONSE_ON:
                return 1
    elif bytestring == RESPONSE_OFF:
                return 0
    else:
       raise ValueError( 'Could not convert bit response to a value. Input: {0}'.format(repr(bytestring)) )


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
    if integer1 < 0 or integer2 < 0:
        raise ValueError( 'The inputs must not be less than 0. Given: {0} and {1}'.format(integer1, integer2) )
    
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
    
    if x <0 :
        raise ValueError( 'The input must not be less than 0. Given: {0}'.format(x) )
    
    if bitNum <0 :
        raise ValueError( 'The bitnumber must not be less than 0. Given: {0}'.format(bitNum) )
    
    return x | (1<<bitNum)


def _rightshift(inputInteger):
    """Rightshift an integer one step, and also calculate the carry bit.

    Args:
        inputInteger (int): The value to be rightshifted. Should be positive.

    Returns:
        The tuple (shifted, carrybit) where ``shifted`` is the rightshifted integer and ``carrybit`` is the
        resulting carry bit.

    For example:
        An inputInteger = 9 (dec) = 1001 (bin) will after a rightshift be 0100 (bin) = 4 and the carry bit is 1.
        The return value will then be the tuple (4, 1). 
    """
    
    if not isinstance( inputInteger, ( int, long ) ):
        raise TypeError( 'The input must be an integer. Given: {0}'.format(inputInteger) )
    
    if inputInteger <0 :
        raise ValueError( 'The input must not be less than 0. Given: {0}'.format(inputInteger) )
    
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
    
    if not isinstance(inputstring, str):
        raise TypeError( 'The input must be a string. Given: {0}'.format(repr(inputstring)) )
    
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


def _checkFunctioncode( functioncode, listOfAllowedValues ):
    """Check that the given functioncode is in the listOfAllowedValues.

    Also verifies that 0 <= function code <= 127.

    Args:
        functioncode (int): The function code
        listOfAllowedValues (list of int): Allowed values. Use None to ypass this part of
    
    Raises:
        TypeError, ValueError

    """
    FUNCTIONCODE_MIN = 0
    FUNCTIONCODE_MAX = 127
    
    if not isinstance( functioncode, ( int, long ) ):
        raise TypeError( 'The function code must be an integer. Given function code: {0}'.format(functioncode) )

    if functioncode < FUNCTIONCODE_MIN or functioncode > FUNCTIONCODE_MAX:
        raise ValueError( 'Wrong function code: {0}, allowed values are {1} to {2}'.format( \
            functioncode, FUNCTIONCODE_MIN, FUNCTIONCODE_MAX) )
    
    if listOfAllowedValues == None:
        return

    if functioncode not in listOfAllowedValues:
        raise ValueError( 'Wrong function code: {0}, allowed values are {1}'.format(functioncode, repr(listOfAllowedValues)) )


def _checkByteCount(payload):
    """Check that the number of bytes as given in the response is correct.
    
    The first byte in the payload indicates the length of the payload (first byte not counted).
    
    Args:
        payload (string): The payload
    
    Raises:
        * ValueError
        * TypeError
    
    """ 
    
    POSITION = 0
    NUMBER_OF_BYTES_TO_SKIP = 1
    
    if not isinstance(payload, str):
        raise TypeError( 'The input must be a string. Given: {0}'.format(repr(payload)) )
 
    givenNumberOfDatabytes = ord( payload[POSITION] )
    countedNumberOfDatabytes = len(payload) - NUMBER_OF_BYTES_TO_SKIP

    if givenNumberOfDatabytes != countedNumberOfDatabytes:
        errortemplate = 'Wrong given number of bytes in the response: {0}, but counted is {1} as data payload length is {2}.' + \
            ' The data payload is: {3}'
        errortext = errortemplate.format(givenNumberOfDatabytes, countedNumberOfDatabytes, len(payload), repr(payload))
        raise ValueError(errortext)    


def _checkResponseAddress(payload, registeraddress):
    """Check that the start adress as given in the response is correct.
    
    The first two bytes in the payload holds the address value.
    
    Args:
        payload (string): The payload
        registeraddress (int): The register address (use decimal numbers, not hex). 
    
    Raises:
        * ValueError
        * TypeError
    
    """ 
    ##TODO Check types
    if not isinstance(payload, str):
        raise TypeError( 'The input must be a string. Given: {0}'.format(repr(payload)) )
    
    ##TODO Check length
 
    BYTERANGE_FOR_STARTADDRESS = slice(0, 2)

    bytesForStartAddress = payload[BYTERANGE_FOR_STARTADDRESS]
    receivedStartAddress = _twoByteStringToNum( bytesForStartAddress )
    
    if receivedStartAddress != registeraddress:
        raise ValueError( 'Wrong given write start adress: {0}, but commanded is {1}'.format( \
            receivedStartAddress, registeraddress))        

def _checkResponseNumberOfRegisters(payload, numberOfRegisters):
    """Check that the number of written registers as given in the response is correct.
    
    The bytes 2 and 3 (zero based counting) in the payload holds the value.
    
    Args:
        payload (string): The payload
        numberOfRegisters (int): Number of registers that have been written
    
    Raises:
        * ValueError
        * TypeError
    
    """ 
    
    ##TODO Check types
    if not isinstance(payload, str):
        raise TypeError( 'The input must be a string. Given: {0}'.format(repr(payload)) )
    
    ##TODO Check length
    
    BYTERANGE_FOR_NUMBER_OF_REGISTERS = slice(2, 4)
    
    bytesForNumberOfRegisters = payload[BYTERANGE_FOR_NUMBER_OF_REGISTERS]
    receivedNumberOfWrittenReisters = _twoByteStringToNum( bytesForNumberOfRegisters )
    
    if receivedNumberOfWrittenReisters != numberOfRegisters:
        raise ValueError( 'Wrong number of registers to write in the response: {0}, but commanded is {1}'.format( \
            receivedNumberOfWrittenReisters, numberOfRegisters) )


def _checkResponseWriteData(payload, writedata):
    """Check that the write data as given in the response is correct.
    
    The bytes 2 and 3 (zero based counting) in the payload holds the write data.
    
    Args:
        payload (string): The payload
        writedata (string): The data to write
    
    Raises:
        * ValueError
        * TypeError
    
    """ 
        
    ##TODO Check types
    if not isinstance(payload, str):
        raise TypeError( 'The input must be a string. Given: {0}'.format(repr(payload)) )
    
    ##TODO Check length
    
    BYTERANGE_FOR_WRITEDATA = slice(2, 4)
    
    receivedWritedata = payload[BYTERANGE_FOR_WRITEDATA]
    
    if receivedWritedata != writedata:
        raise ValueError( 'Wrong write data in the response: {0}, but commanded is {1}'.format( \
            receivedWritedata, writedata) )


#####################
# Development tools #
#####################
        
def _print_out( inputstring ):
    """Print the inputstring. To make it compatible with Python2 and Python3."""
    sys.stdout.write(inputstring + '\n')           
        
def _toPrintableString( inputstring ):
    """Make a descriptive string, showing the ord() numbers (in decimal) for the characters in the inputstring.
    
    Args:
        inputstring (str): The string that should be converted to something printable.

    Returns:
        A descriptive string.

    Use it for diagnostic printing of strings representing byte values (might have non-printing characters).
    With an input string of ``BACKSLASHx12BACKSLASHx02BACKSLASHx74ABC`` (which is length 6), it will return the string:: 

        'String length: 6 bytes. Values: 18, 2, 116, 65, 66, 67'
    
    """
    
    firstpart = 'String length: {0} bytes. Values: '.format( len(inputstring) )

    valuestrings = []
    for character in inputstring:
        valuestrings.append( str(ord(character)) )
    valuepart = ', '.join( valuestrings )

    return firstpart + valuepart

def _getDiagnosticString():
    """Generate a diagnostic string, showing the module version, the platform, current directory etc.

    Returns:
        A descriptive string.
    
    """
    text = '\n## Diagnostic output from minimalmodbus ## \n\n'
    text += 'Minimalmodbus version: ' + __version__ + '\n'
    text += 'Revision: ' + __revision__ + '\n'
    text += 'Release date: ' + __date__ + '\n'
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

    _CLOSE_PORT_AFTER_EACH_CALL = False
    instrument = Instrument('/dev/cvdHeatercontroller', 1)
    instrument._debug = True
    
    
    _print_out( str(instrument.read_register(273, 1)) )

    _print_out( 'DONE!' )
    
pass    


