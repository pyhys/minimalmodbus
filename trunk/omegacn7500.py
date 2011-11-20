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

Driver for the Omega CN7500 process controller, for communication using the Modbus RTU protocol.

This Python file was changed (committed) at 
$Date$, 
which was $Revision$.

"""

import minimalmodbus

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"

__revision__  = "$Rev$"
__date__      = "$Date$"

class OmegaCN7500( minimalmodbus.Instrument ):
    """Instrument class for Omega CN7500 process controller. 
    
    Communicates via Modbus RTU protocol (via RS485), using the :mod:`minimalmodbus` Python module.    

    Args:
        * portname (str): port name
        * slaveaddress (int): slave address in the range 1 to 247 (in decimal)

    Implemented with these function codes (in decimal):
        
    ==================  ====================
    Description         Modbus function code
    ==================  ====================
    Read registers      3
    Write one register  6
    Read bits           2
    Write one bit       5
    ==================  ====================
    
    """
    
    def __init__(self, portname, slaveaddress):
        minimalmodbus.Instrument.__init__(self, portname, slaveaddress)
    
    ## Process value
    
    def get_pv(self):
        """Return the process value (PV)."""
        return self.read_register( 0x1000, 1) 
   
    ## Run and stop the controller
    
    def run(self):
        """Put the process controller in run mode."""
        self.write_bit( 0x0814, 1)

    def stop(self):
        """Stop the process controller."""
        self.write_bit( 0x0814, 0)

    def is_running(self):
        """Return True if the controller is running."""
        return self.read_bit( 0x0814 ) == 1   

    ## Setpoint
    
    def get_setpoint(self):
        """Return the setpoint (SV)."""
        return self.read_register( 0x1001, 1) 
    
    def set_setpoint(self, value):
        """Set the setpoint (SV).
        
        Args:
            value (float): Setpoint [most often in degrees]
        """
        self.write_register( 0x1001, value, 1)
    
    ## Output signal
    
    def get_output1(self):
        """Return the output value (OP) for output1 [in %]."""
        return self.read_register( 0x1012, 1)
   
########################
## Testing the module ##
########################

if __name__ == '__main__':

    import sys       
    
    def print_out( inputstring ):
        """Print the inputstring. To make it compatible with Python2 and Python3."""
        sys.stdout.write(inputstring + '\n') 

    print_out( 'TESTING OMEGA CN7500 MODBUS MODULE')

    PORTNAME = '?'
    ADDRESS = 1
    
    print_out( 'Port: ' +  str(PORTNAME) + ' Address: ' + str(ADDRESS) )
    
    instr = OmegaCN7500(PORTNAME, ADDRESS)
    
    print_out( 'SP:                     {0}'.format(  instr.get_setpoint() ))
    print_out( 'PV:                     {0}'.format(  instr.get_pv()       ))
    print_out( 'OP1:                    {0}'.format(  instr.get_output1()  ))   
    print_out( 'Is running:             {0}'.format(  instr.is_running()   ))

    print_out( 'DONE!' )

pass    
