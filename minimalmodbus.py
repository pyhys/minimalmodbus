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

import serial

class Instrument():
    """Driver for talking to instruments via Modbus protocol (via RS485 or RS232).

    port is the serial port name, for example '???' or '???'
    slaveaddress is an integer in the range 0-???. 

    Note that slaveaddress=0 is used for ??

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
        """Read one register.
        
        Converts the data to a numerical value?
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
        """Write to one register.
        
        To store for example value=77.0, use numberOfDecimals=1 if the register will hold it as 770 internally.
        
        The payload to the slave is: Startaddress, number of registers, number of bytes, registerdata
        The payload from the slave is: Startaddress, number of registers.
        
        No return value.
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
        
        ## Check start wright register
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
        """Performs the command having the 'functioncode'.
        
        'payloadToSlave' is transmitted (embedded in address, crc etc)
        The return value is the extracted data payload from the slave.
        """
        message             = _embedPayload(self.address, functioncode, payloadToSlave)
        response            = self._communicate(message)
        payloadFromSlave    = _extractPayload(response, self.address, functioncode)

        return payloadFromSlave
        
    def _communicate(self, message):
        """Talk to the slave.
        
        Note that the answer might have strange ASCII control signs, which
        makes it difficult to print it in the promt (messes up a bit).
        
        Will block until timeout (or reaching a large number of bytes).
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
    
    'slaveaddress' is an integer.
    'functioncode' is an integer.
    'payloaddata' is a string of hex integers
    The resulting message has the format: slaveaddress byte + functioncode + payloaddata + crc
    """
    firstPart = _numToOneByteString(slaveaddress) + _numToOneByteString(functioncode) + payloaddata
    message = firstPart + _calculateCrcString(firstPart)       
    return message

def _extractPayload(response, slaveaddress, functioncode):
    """Extract the payload data from the slave's response.
    
    'response' is a hex string.
    'slaveaddress' is an integer. It is for error checking only.
    'functioncode' is an integer. It is for error checking only.
    
    The received message should have the format: address byte + functioncode + payloaddata + crc
    Raises an exception if there is any problem with the received address, the functioncode or the crc.
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
    if integer > 0xFF:
        raise ValueError( 'The input value is too large.')
    if integer < 0:
        raise ValueError( 'The input value is negative.')
    return chr(integer)

def _numToTwoByteString(value, numberOfDecimals = 0, LsbFirst = False):
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
    
    Inputstring is the message (without the CRC).
    Returns a two-byte CRC string.
    
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
    """Set bit 'bitNum' to True."""
    return x | (1<<bitNum)

def _rightshift(inputInteger):
    """Rightshift an integer one step, and also calculate the carry bit."""
    shifted = inputInteger >> 1
    carrybit = inputInteger & 1
    return shifted, carrybit

def _toPrintableString( inputstring ):
    """Make a descriptive string, showing the ord() numbers for the characters in the inputstring.
    
    Use it for diagnostic printing of strings representing byte values (might have non-printing characters).
    With an input string of '\x12\x02\x74ABC', it will return the string:
    'String length: 6 bytes. Values: 18, 2, 116, 65, 66, 67'
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
