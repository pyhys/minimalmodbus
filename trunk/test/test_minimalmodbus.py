import unittest
import minimalmodbus


print 'Testing'

class TestEmbedPayload(unittest.TestCase):

    knownValues=[
    (1, 16, 'ABC', '\x01\x10ABC<E'),
    (0, 5, 'hjl', '\x00\x05hjl\x8b\x9d'),
    (2, 2, '123', '\x02\x02123X\xc2'),
    ]

    def testKnownValues(self):
        for address, functioncode, inputstring, knownresult in self.knownValues:
            result = minimalmodbus._embedPayload(address, functioncode, inputstring)
            self.assertEqual(result, knownresult)

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
        print len(resultstring)
        ## Should be at least 100 characters



if __name__ == '__main__':
    unittest.main()
