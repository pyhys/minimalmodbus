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

__version__   = "0.21"
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

class Instrument():
    """Instrument class for talking to instruments (slaves) via the Modbus RTU protocol (via RS485 or RS232).

    Args:
        * port (str): The serial port name, for example ``/dev/ttyS1`` or ``COM1``.
        * slaveaddress (int): Slave address in the range 1 to 247.

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

    ########################################
    ## Functions for talking to the slave ##
    ########################################
    
    def read_register(self, registeraddress, numberOfDecimals=0):
        """Read one register from the slave. Implemented with Modbus functioncode 3.

        Args:
            * registeraddress (int): The register address   
            * numberOfDecimals (int): The number of decimals for content conversion

        If a value of 77.0 is stored internally in the slave register as 770, then use numberOfDecimals=1

        Returns:
            The register data in numerical value (int or float).

        Raises:
            ValueError

        .. note::
            Some implementation details for 'Read register' functioncode (3):

            The payload to the slave is: Register startaddress, number of registers

            The payload from the slave is: Number of bytes, registerdata

        """

        FUNCTIONCODE_READ_REGISTERS = 3
        NUMBER_OF_REGISTERS_TO_READ = 1
        
        # Build data for reading one register
        payloadToSlave =  _numToTwoByteString(registeraddress) + _numToTwoByteString(NUMBER_OF_REGISTERS_TO_READ)
        
        # Communicate
        payloadFromSlave= self._performCommand( FUNCTIONCODE_READ_REGISTERS, payloadToSlave)
        
        # Check number of bytes
        # These constants are for dealing with the frame payload data
        BYTEPOSITION_FOR_NUMBEROFBYTES = 0
        NUMBER_OF_BYTES_BEFORE_REGISTERDATA = 1
        givenNumberOfDatabytes = ord( payloadFromSlave[BYTEPOSITION_FOR_NUMBEROFBYTES ] )
        countedNumberOfDatabytes = len(payloadFromSlave) - NUMBER_OF_BYTES_BEFORE_REGISTERDATA
        if givenNumberOfDatabytes != countedNumberOfDatabytes:
            raise ValueError( 'Wrong given number of bytes: {0}, but counted is {1} as data payload length is {2}'.format( \
                givenNumberOfDatabytes, countedNumberOfDatabytes, len(payloadFromSlave)) )
 
        # Extract register data
        registerdata = payloadFromSlave[NUMBER_OF_BYTES_BEFORE_REGISTERDATA:]
        
        # Calculate value 
        # (Up to here the code is pretty general, but from here we assume that only one register is read)
        assert len(registerdata) == 2
        registervalue = _twoByteStringToNum(registerdata, numberOfDecimals)
        return registervalue
        
    def write_register(self, registeraddress, value, numberOfDecimals=0):
        """Write to one register in the slave. Implemented with Modbus functioncode 16.
        
        Args:
            * registeraddress (int): The register address 
            * value (float): The value to store in the register 
            * numberOfDecimals (int): The number of decimals for content conversion.

        To store for example `value`=77.0, use `numberOfDecimals`=1 if the register will hold it as 770 internally.

        Returns:
            None

        Raises:
            ValueError
        
        .. note::
            Some implementation details for 'Write register' functioncode (16):

            The payload to the slave is: Register startaddress, number of registers, number of bytes, registerdata
            
            The payload from the slave is: Register startaddress, number of registers.

        """
        FUNCTIONCODE_WRITE_REGISTERS = 16
        NUMBER_OF_REGISTERS_TO_WRITE = 1
        NUMBER_OF_BYTES_PER_REGISTER = 2
        STARTBYTENUMBER_FOR_STARTADDRESS = 0
        STARTBYTENUMBER_FOR_NUMBEROFREGISTERS = 2
        
        ## Build data for writing one register
        numberOfRegisterBytes = NUMBER_OF_REGISTERS_TO_WRITE * NUMBER_OF_BYTES_PER_REGISTER
        
        payloadToSlave =  _numToTwoByteString(registeraddress) + _numToTwoByteString(NUMBER_OF_REGISTERS_TO_WRITE) + \
                        _numToOneByteString(numberOfRegisterBytes) + _numToTwoByteString(value, numberOfDecimals)
        
        # Communicate
        payloadFromSlave = self._performCommand( FUNCTIONCODE_WRITE_REGISTERS, payloadToSlave)
        assert len(payloadFromSlave) == 4
        
        ## Check start write register        
        bytesForStartAddress = payloadFromSlave[STARTBYTENUMBER_FOR_STARTADDRESS : STARTBYTENUMBER_FOR_STARTADDRESS+NUMBER_OF_BYTES_PER_REGISTER]
        receivedStartAddress =  _twoByteStringToNum( bytesForStartAddress )
        if receivedStartAddress != registeraddress:
            raise ValueError( 'Wrong given write start adress: {0}, but commanded is {1}'.format( receivedStartAddress, registeraddress) )
        
        ## Check number of registers written
        bytesForNumberOfRegisters = payloadFromSlave[STARTBYTENUMBER_FOR_NUMBEROFREGISTERS : STARTBYTENUMBER_FOR_NUMBEROFREGISTERS+NUMBER_OF_BYTES_PER_REGISTER]
        receivedNumberOfWrittenReisters =  _twoByteStringToNum( bytesForNumberOfRegisters )
        if receivedNumberOfWrittenReisters != NUMBER_OF_REGISTERS_TO_WRITE:
            raise ValueError( 'Wrong given number of registers to write: {0}, but commanded is {1}'.format( \
                receivedNumberOfWrittenReisters, NUMBER_OF_REGISTERS_TO_WRITE) )
    
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
            ValueError

        Note that the answer might have strange ASCII control signs, which
        makes it difficult to print it in the promt (messes up a bit).
        
        Will block until timeout (or reaching a large number of bytes).

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
        
        if len(message) == 0:
            raise ValueError('The message length must not be zero')
            
        self.serial.write(message)
        answer =  self.serial.read(MAX_NUMBER_OF_BYTES)
        
        if len(answer) == 0:
            raise ValueError('No communication with the instrument (no answer)')
        
        return answer

######################
## Helper functions ##
######################

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
    
    # Constants
    BYTEPOSITION_FOR_ADDRESS               = 0 # Zero-based counting
    BYTEPOSITION_FOR_FUNCTIONCODE          = 1
    NUMBER_OF_RESPONSE_STARTBYTES          = 2
    NUMBER_OF_CRC_BYTES                    = 2
    BITNUMBER_FUNCTIONCODE_ERRORINDICATION = 7

    # Check CRC
    receivedCRC = response[-NUMBER_OF_CRC_BYTES:]
    responseWithoutCRC = response[0 : len(response) - NUMBER_OF_CRC_BYTES ]
    calculatedCRC = _calculateCrcString( responseWithoutCRC )
    if receivedCRC != calculatedCRC:
        raise ValueError( 'CRC error: {0} instead of {1}'.format( _twoByteStringToNum(receivedCRC), _twoByteStringToNum(calculatedCRC)) )

    # Check Address
    responseaddress = ord( response[BYTEPOSITION_FOR_ADDRESS] )
    if responseaddress != slaveaddress:
        raise ValueError( 'Wrong return address: {0} instead of {1}'.format(responseaddress, slaveaddress) )
    
    # Check function code
    receivedFunctioncode = ord( response[BYTEPOSITION_FOR_FUNCTIONCODE ] )
    if receivedFunctioncode == _setBitOn(functioncode, BITNUMBER_FUNCTIONCODE_ERRORINDICATION):
        raise ValueError( 'The slave is indicating an error.' )
    elif receivedFunctioncode != functioncode:
        raise ValueError( 'Wrong functioncode: {0} instead of {1}'.format(receivedFunctioncode, functioncode) )
     
    # Read data payload
    firstDatabyteNumber = NUMBER_OF_RESPONSE_STARTBYTES
    lastDatabyteNumber  = len(response) - NUMBER_OF_CRC_BYTES
    payload = response[ firstDatabyteNumber:lastDatabyteNumber ]
    
    return payload

def _twoByteStringToNum(bytestring, numberOfDecimals = 0):
    """Convert a two-byte string to a numerical value.
    
    Args:    
        * bytestring (str): A string of length 2.
        * numberOfDecimals (int): The number of decimal. Defaults to 0.

    Returns:
        The numerical value (int or float) calculated from the ``bytestring``.        
        
    Raises:
        ValueError. Raises an exception if the bytestring has wrong length or the numberOfDecimals is wrong.

    For example:
        A string ``BACKSLASHx03BACKSLASHx02`` (which has the length 2) corresponds to 0302 (hex) = 770 (dec). If
        numberOfDecimals=1, then this is converted to 77.0 (float). 

    A bug was found on 2011-05-16: The most significant byte was 
    multiplied by 255 instead of the correct value 256.
    
    """
    if len(bytestring) != 2:
        raise ValueError( 'The input string length is {0}. It should be 2.'.format(len(bytestring)) )
        
    if numberOfDecimals <0 :
        raise ValueError( 'The number of decimals must not be less than 0.' )
        
    leastSignificantByte = ord(bytestring[1])
    mostSignificantByte  = ord(bytestring[0])
    fullregister = mostSignificantByte*0x100 + leastSignificantByte
    
    if numberOfDecimals == 0:
        return fullregister
    divisor = 10 ** numberOfDecimals
    return fullregister / float(divisor)
   
def _numToOneByteString(integer):
    """Convert a numerical value to a one-byte string.

    Args:
        integer (int): The value to be converted. Should be >=0 and <=255.

    Returns:
        A one-byte string created by chr(integer).

    Raises:
        ValueError. Raises an exception if the integer is out of range.
    """
    if integer > 0xFF:
        raise ValueError( 'The input value is too large.')
    if integer < 0:
        raise ValueError( 'The input value is negative.')
    return chr(integer)

def _numToTwoByteString(value, numberOfDecimals = 0, LsbFirst = False):
    """Convert a numerical value to a two-byte string.

    Args:
        * value (float or int): The numerical value to be converted
        * numberOfDecimals (int): Number of decimals, 0 or more
        * LsbFirst (bol): Whether the least significant byte should be first in the resulting string.

    Returns:
        A two-byte string.

    Raises:
        ValueError Raises an exception if the numberOfDecimals or the value is out of range.

    For example:
        To store for example value=77.0, use numberOfDecimals=1 if the register will hold it as 770 internally.
        The value 770 (dec) is 0302 (hex), where the most significant byte is 03 (hex) and the
        least significant byte is 02 (hex). With LsbFirst = False, the most significant byte is given first
        why the resulting string is ``BACKSLASHx03BACKSLASHx02``, which has the length 2.

    """
    if numberOfDecimals <0 :
        raise ValueError( 'The number of decimals must not be less than 0.' )

    multiplier = 10 ** numberOfDecimals
    integer = int( float(value) * multiplier )

    if integer > 0xFFFF:
        raise ValueError( 'The input value is too large.')
    if integer < 0:
        raise ValueError( 'The input value is negative.')
    
    mostSignificantByte =  integer >> 8
    leastSignificantByte = integer & 0xFF
    if LsbFirst: 
        outstring = chr(leastSignificantByte) + chr(mostSignificantByte)
    else:
        outstring = chr(mostSignificantByte) + chr(leastSignificantByte)
    return outstring

def _calculateCrcString( inputstring ):
    """Calculate CRC-16 for Modbus.
    
    Args:
        inputstring (str): An arbitrary-length message (without the CRC).

    Returns:
        A two-byte CRC string, where the least significant byte is first.
    
    Algorithm from the document 'MODBUS over serial line specification and implementation guide V1.02'.
    """
    
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

def _XOR(integer1, integer2):
    """An alias for the bitwise XOR command.

    Args:
        * integer1 (int): Input integer
        * integer2 (int): Input integer

    Returns:
        The XOR:ed value of the two input integers. This is an integer.
"""
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
    return x | (1<<bitNum)

def _rightshift(inputInteger):
    """Rightshift an integer one step, and also calculate the carry bit.

    Args:
        inputInteger (int): The value to be rightshifted

    Returns:
        The tuple (shifted, carrybit) where ``shifted`` is the rightshifted integer and ``carrybit`` is the
        resulting carry bit.

    For example:
        An inputInteger = 9 (dec) = 1001 (bin) will after a rightshift be 0100 (bin) = 4 and the carry bit is 1.
        The return value will then be the tuple (4, 1). 
    """
    shifted = inputInteger >> 1
    carrybit = inputInteger & 1
    return shifted, carrybit

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
    text += 'Current directory: ' + os.getcwd() + '\n'
    text += 'Python version: ' + sys.version + '\n'
    text += 'Variable __name__: ' + __name__ + '\n'
    text += 'Current directory: ' + os.getcwd() + '\n'
    text += 'Python path: \n' 
    text += '\n'.join( sys.path ) + '\n'
    return text

########################
## Testing the module ##
########################

if __name__ == '__main__':

    def print_out( inputstring ):
        """Print the inputstring. To make it compatible with Python2 and Python3."""
        sys.stdout.write(inputstring + '\n')     

    #import a_module

    #
    #print __file__ 
    #print os.path.dirname( __file__ )

    print_out( 'TESTING MODBUS MODULE' )

    #print dir(serial)

    #print serial.VERSION

    #quit()
    print _getDiagnosticString()

    quit()
    #instrument = Instrument('/dev/cvdHeatercontroller', 1)

    print_out(str(  instrument.read_register(1, 1)     ))
    print_out(str(  instrument.read_register(273, 1)   ))
    print_out(str(  instrument.read_register(289, 10)  ))
    print_out(str(  instrument.read_register(1313, 10) ))
    print_out(str(  instrument.read_register(10241, 1) ))
 
    print_out( 'DONE!' )
    
pass    
