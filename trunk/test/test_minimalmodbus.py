import unittest
import minimalmodbus

print 'Testing'

class TestExtractPayload(unittest.TestCase):

    knownValues=[
    (1, 16, 'ABC', '\x01\x10ABC<E'),
    (0, 5, 'hjl', '\x00\x05hjl\x8b\x9d'),
    (2, 2, '123', '\x02\x02123X\xc2'),
    ]

    def testKnownValues(self):
        for address, functioncode, knownresult, inputstring in self.knownValues:
            result = minimalmodbus._extractPayload(inputstring, address, functioncode )
            self.assertEqual(result, knownresult)
            
    def testWrongCrc(self):
        pass ##TODO        
            
    def testWrongAdress(self):
        pass ##TODO
        
    def testWrongFunctionCode(self):
        pass ##TODO

class TestEmbedPayload(unittest.TestCase):

    knownValues=TestExtractPayload.knownValues

    def testKnownValues(self):
        for address, functioncode, inputstring, knownresult in self.knownValues:
            result = minimalmodbus._embedPayload(address, functioncode, inputstring)
            self.assertEqual(result, knownresult)

    def testToLargeAdressValue(self):
        pass ##TODO
        
    def testToLargeFunctionCodeValue(self):
        pass ##TODO
    
class TestSetBitOn(unittest.TestCase):

    knownValues=[
    (4,0,5),
    (4,1,6),
    (1,1,3),
    ]

    def testKnownValues(self):
        for x, bitnum, knownresult in self.knownValues:
            result = minimalmodbus._setBitOn(x, bitnum)
            self.assertEqual(result, knownresult)
        
class TestXOR(unittest.TestCase):

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
    
class TestRightshift(unittest.TestCase):

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
    
class TestGetDiagnosticString(unittest.TestCase):

    def testReturnsString(self):
        resultstring = minimalmodbus._getDiagnosticString()
        ## Should be at least 100 characters

class TestCalculateCrcString(unittest.TestCase):

    knownValues=[
    ('\x02\x07','\x41\x12'), # Example from MODBUS over Serial Line Specification and Implementation Guide V1.02 
    ('ABCDE', '\x0fP'),
    ]

    def testKnownValues(self):
        for inputstring, knowncrc in self.knownValues:
            resultcrc = minimalmodbus._calculateCrcString(inputstring)
            self.assertEqual(resultcrc, knowncrc)       

class TestTwoByteStringToNum(unittest.TestCase):

    knownValues=[
    ('\x03\x02', 1, 77.0), 
    ('\x03\x02', 0, 770 ), 
    ]

    def testKnownValues(self):
        for inputstring, numberOfDecimals, knownvalue in self.knownValues:
            resultvalue = minimalmodbus._twoByteStringToNum(inputstring, numberOfDecimals)
            self.assertEqual(resultvalue, knownvalue)      

class TestNumToTwoByteString(unittest.TestCase):

    knownValues=[
    (77.0, 1, False, '\x03\x02' ), 
    (77.0, 1, True, '\x02\x03' ), 
    (770, 0, False, '\x03\x02' ), 
    ]

    def testKnownValues(self):
        for inputvalue, numberOfDecimals, LsbFirst, knownstring in self.knownValues:
            resultstring = minimalmodbus._numToTwoByteString(inputvalue, numberOfDecimals, LsbFirst)
            self.assertEqual(resultstring, knownstring)      

class TestSanityTwoByteString(unittest.TestCase):

    def testKnownValuesLoop(self):
        for x in range(0x10000):
            resultvalue = minimalmodbus._twoByteStringToNum( minimalmodbus._numToTwoByteString(x) )
            self.assertEqual(resultvalue, x)       

class TestNumToOneByteString(unittest.TestCase):

    knownValues=[
    (7, '\x07' ), 
    ]

    def testKnownValues(self):
        for inputvalue, knownstring in self.knownValues:
            resultstring = minimalmodbus._numToOneByteString( inputvalue )
            self.assertEqual(resultstring, knownstring)     

    def testKnownLoop(self):
        for x in range(256):
            knownstring = chr(x)
            resultstring = minimalmodbus._numToOneByteString( x )
            self.assertEqual(resultstring, knownstring)       

    def testNegativeInput(self):
        pass ##TODO 

    def testTooLargeInput(self):
        pass ##TODO

if __name__ == '__main__':
    unittest.main()
