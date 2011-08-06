#!/usr/bin/python
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

Text describing the minimalmodbus module.


"""
$Date$
$Revision$


__version__ = "$Revision$"
# $Source$

import serial

class Instrument():
    """Driver for talking to instruments (slaves) via the Modbus RTU protocol (via RS485 or RS232).

    Args:
        * port (str): The serial port name, for example '???' or '???'
        * slaveaddress (int): in the range 0-???. Note that slaveaddress=0 is used for ??

    """
    
    def __init__(self, port, slaveaddress):
        self.port     = port
        self.baudrate = 19200    # Baud
        self.timeout  = 0.05     # seconds
        self.parity   = serial.PARITY_NONE
        self.bytesize = 8
        self.stopbits = 1
        self.serial   = serial.Serial(self.port, self.baudrate, parity=self.parity, bytesize=self.bytesize, \
                        stopbits=self.stopbits, timeout = self.timeout )
        
        self.address = slaveaddress
    
    ########################################
    ## Functions for talking to the slave ##
    ########################################
    
    def read_register(self, registeraddress, numberOfDecimals=0):
        """Read one register from the slave.

        Args:
            * registeraddress (int): The register address   
            * numberOfDecimals (int): The number of decimals for content conversion

        If a value of 77.0 is stored internally in the slave register as 770, then use numberOfDecimals=1

        Returns:
            The register data in numerical value.

        Raises:
            ValueError

        .. note::
            Some implementation details for 'Read register' functioncode:

            The payload to the slave is: Startaddress, number of registers

            The payload from the slave is: ?????

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
        """Write to one register in the slave.
        
        Args:
            * registeraddress (int): The register address 
            * value (float): The value to store in the register 
            * numberOfDecimals (int): The number of decimals for content conversion.

        To store for example value=77.0, use numberOfDecimals=1 if the register will hold it as 770 internally.

        Returns:
            None

        Raises:
            ValueError
        
        .. note::
            Some implementation details for 'Write register' functioncode:

            The payload to the slave is: Startaddress, number of registers, number of bytes, registerdata
            
            The payload from the slave is: Startaddress, number of registers.

        """
        FUNCTIONCODE_WRITE_REGISTERS = 16
        NUMBER_OF_REGISTERS_TO_WRITE = 1
        NUMBER_OF_BYTES_PER_REGISTER = 2
        
        ## Build data for reading one register
        numberOfRegisterBytes = NUMBER_OF_REGISTERS_TO_WRITE * NUMBER_OF_BYTES_PER_REGISTER
        
        payloadToSlave =  _numToTwoByteString(registeraddress) + _numToTwoByteString(NUMBER_OF_REGISTERS_TO_WRITE) + \
                        _numToOneByteString(numberOfRegisterBytes) + _numToTwoByteString(value, numberOfDecimals)
        
        # Communicate
        payloadFromSlave = self._performCommand( FUNCTIONCODE_WRITE_REGISTERS, payloadToSlave)
        assert len(payloadFromSlave) == 4
        
        ## Check start write register
        STARTBYTENUMBER_FOR_STARTADDRESS = 0
        bytesForStartAddress = payloadFromSlave[STARTBYTENUMBER_FOR_STARTADDRESS : STARTBYTENUMBER_FOR_STARTADDRESS+NUMBER_OF_BYTES_PER_REGISTER]
        receivedStartAddress =  _twoByteStringToNum( bytesForStartAddress )
        if receivedStartAddress != registeraddress:
            raise ValueError( 'Wrong given write start adress: {0}, but commanded is {1}'.format( receivedStartAddress, registeraddress) )
        
        ## Check number of registers written
        STARTBYTENUMBER_FOR_NUMBEROFREGISTERS = 2
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
            * functioncode (int): The function code for the command to be performed. Can for example be 'Write register'.
            * payloadToSlave (str): Data to be transmitted to the slave (will be embedded in address, crc etc)
    
        Returns:
            The extracted data payload from the slave (a string). It is stripped of CRC etc.

        Makes use of the Instrument._communicate method.

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

            The data is stored as hex strings internally. For example a byte 

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
        * functioncode (int): 
        * payloaddata (str): The hex integer string to be sent to the slave

    Returns:
        The built (raw) message string for sending to the slave.    

    The resulting message has the format: slaveaddress byte + functioncode byte + payloaddata + crc (which is two bytes)
    """
    firstPart = _numToOneByteString(slaveaddress) + _numToOneByteString(functioncode) + payloaddata
    message = firstPart + _calculateCrcString(firstPart)       
    return message

def _extractPayload(response, slaveaddress, functioncode):
    """Extract the payload data part from the slave's response.
    
    Args:
        * response (str): The raw response hex string from the slave.
        * slaveaddress (int): The adress of the slave. Used here for error checking only.
        * functioncode (int): Used here for error checking only.
    
    Returns:
        The payload part of the *response* string.

    Raises:
        ValueError. Raises an exception if there is any problem with the received address, the functioncode or the crc.

    The received message should have the format: address byte + functioncode byte + payloaddata + crc (which is two bytes)

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
        ValueError
    """
    if integer > 0xFF:
        raise ValueError( 'The input value is too large.')
    if integer < 0:
        raise ValueError( 'The input value is negative.')
    return chr(integer)

def _numToTwoByteString(value, numberOfDecimals = 0, LsbFirst = False):
    """Convert a numerical value to a two-byte string.

    Args:
        value (float or int): The numerical value to be converted
        numberOfDecimals (int): Number of decimals, 0 or more
        LsbFirst (bol): 

    Returns:
        A two-byte string.

    Raises:
        ValueError

    Example ???????????

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
        A two-byte CRC string.
    
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
    """An alias for the bitwise XOR command."""
    return integer1 ^ integer2

def _setBitOn( x, bitNum ):
    """Set bit 'bitNum' to True.
 
    Args:
        * x (int): The value before.
        * bitNum (int): The bit number that should be set to True.

    Returns:
        The value after setting the bit. This is an integer.
    """
    return x | (1<<bitNum)

def _rightshift(inputInteger):
    """Rightshift an integer one step, and also calculate the carry bit."""
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
    With an input string of '\x12\x02\x74ABC', it will return the string:
    'String length: 6 bytes. Values: 18, 2, 116, 65, 66, 67'

    ``\``x12``\``x02``\``x7    

    'BACKSLASHx12'
4
    """
    
    firstpart = 'String length: {0} bytes. Values: '.format( len(inputstring) )

    valuestrings = []
    for character in inputstring:
        valuestrings.append( str(ord(character)) )
    valuepart = ', '.join( valuestrings )

    return firstpart + valuepart

########################
## Testing the module ##
########################

if __name__ == '__main__':
    print 'TESTING MODBUS MODULE'
    
    a = Instrument('/dev/cvdHeatercontroller', 1)
    
    print a.read_register(1, 1)
    #print a.read_register(273, 1)
    #print a.read_register(289, 10)
    #print a.read_register(1313, 10)
    print a.read_register(10241, 1)
 
    print 'DONE!'
    
pass    
