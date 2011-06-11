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

import minimalmodbus

class eurotherm3500( minimalmodbus.Instrument ):
    """Driver for talking to Eurotherm 35xx heater controller via Modbus RTU protocol via RS485.
    """
    
    def __init__(self, port, slaveaddress):
        minimalmodbus.Instrument.__init__(self, port, slaveaddress)
    
    ## Process value
    
    def getPvLoop1(self):
        """Returns the PV for loop1."""
        return self.read_register(289, 1)
    
    def getPvLoop2(self):
        """Returns the PV for loop2."""
        return self.read_register(1313, 1)
    
    ## Auto/manual mode
    
    def isManLoop1(self):
        """Returns the True if loop1 is in man mode."""
        return self.read_register(273, 1) > 0
    
    ## Setpoint
    
    def getSpTargetLoop1(self):
        """Returns the SP target for loop1."""
        return self.read_register(2, 1)
    
    def getSpLoop1(self):
        """Returns the (working) SP for loop1."""
        return self.read_register(5, 1)
    
    def setSpLoop1(self, value):
        """Sets the SP1 for loop1.
        
        Note that this not necessarily is the working setpoint.
        """
        self.write_register(24, value, 1)
    
    def getSpLoop2(self):
        """Returns the (working) SP for loop2."""
        return self.read_register(1029, 1)
    
    ## Setpoint rate
    
    def getSpRateLoop1(self):
        """Returns the SP change rate for loop1."""
        return self.read_register(35, 1)   
    
    def setSpRateLoop1(self, value):
        """Set the SP change rate for loop1.
        
        'value' is most often in degrees/minute.
        """
        self.write_register(35, value, 1)  
    
    def isSpRateLoop1Disabled(self):
        """Returns True if Loop1 SP rate is disabled."""
        return self.read_register(78, 1) > 0

    def disableSpRateLoop1(self):
        """Disable the SP change rate for loop1. """
        VALUE = 1
        self.write_register(78, VALUE, 0) 
        
    def enableSpRateLoop1(self):
        """Set disable=false for the SP change rate for loop1.
        
        Note that also the SP rate value must be properly set for the SP rate to work.
        """
        VALUE = 0
        self.write_register(78, VALUE, 0) 
    
    ## Output signal
    
    def getOpLoop1(self):
        """Returns the OP for loop1 (in %)."""
        return self.read_register(85, 1)
   
    def isLoop1Inhibited(self):
        """Returns True if Loop1 is inhibited."""
        return self.read_register(268, 1) > 0

    def getOpLoop2(self):
        """Returns the OP for loop2 (in %)."""
        return self.read_register(1109, 1)
    
    ## Alarms

    def getAlarm1Threshold(self):
        """Returns the threshold for Alarm1."""
        return self.read_register(10241, 1)
    
    def isAlarmSummarySet(self):
        """Returns the True if there is some alarm triggered."""
        return self.read_register(10213, 1) > 0
    

########################
## Testing the module ##
########################

if __name__ == '__main__':
    print 'TESTING EUROTHERM 3500 MODBUS MODULE'

    a = eurotherm3500('/dev/cvdHeatercontroller', 1)
    
    print a.getSpLoop1(), 'SP 1'
    print a.getSpTargetLoop1(), 'SP 1 target'
    print a.getSpLoop2(), 'SP 2'
    
    print a.isSpRateLoop1Disabled(), 'SP rate Loop1 disabled'
    print a.getSpRateLoop1(), 'SP 1 rate'
    
    print a.getOpLoop1(), '% OP 1'
    print a.getOpLoop2(), '% OP 2'
    print a.getAlarm1Threshold(), 'Al 1 thr'
    print a.isAlarmSummarySet(), 'Al summ'
    print a.isManLoop1(), 'Man Loop1'
    print a.isLoop1Inhibited(), 'Inhibit Loop1'
   
    print a.getPvLoop1(), 'PV 1'
    print a.getPvLoop2(), 'PV 2'

    #a.setSpLoop1(0)
    
    #a.setSpRateLoop1(20)
    #a.enableSpRateLoop1() 
    #a.disableSpRateLoop1() 
    

pass    
