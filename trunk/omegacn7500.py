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
$Date: 2011-10-11 14:57:10 +0200 (Tue, 11 Oct 2011) $, 
which was $Revision: 64 $.

"""

import minimalmodbus

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"

__version__   = minimalmodbus.__version__
__status__    = minimalmodbus.__status__
__revision__  = "$Rev: 64 $"
__date__      = "$Date: 2011-10-11 14:57:10 +0200 (Tue, 11 Oct 2011) $"

class OmegaCN7500( minimalmodbus.Instrument ):
    """Instrument class for Omega CN7500 process controller. 
    
    Communicates via Modbus RTU protocol (via RS485), using the :mod:`minimalmodbus` Python module.    

    Args:
        * portname (str): port name
        * slaveaddress (int): slave address in the range 1 to 247 (use decimal numbers)

    """

    # Note: To convert the hex number 0814 (often written as 0x0814), use int('0814', 16) to have the decimal number.
    
    def __init__(self, portname, slaveaddress):
        minimalmodbus.Instrument.__init__(self, portname, slaveaddress)
    
    ## Process value
    
    def get_pv(self):
        """Return the process value (PV)."""
        return self.read_register( int('1000',16), 1)
   
    ## Run and stop the controller
    
    def run(self):
        """Put the process controller in run mode."""
        self.write_bit( int('0814',16), 1)

    def stop(self):
        """Stop the process controller."""
        self.write_bit( int('0814',16), 0)

    def is_running(self):
        """Return True if the controller is running."""
        return self.read_bit( int('0814',16) ) == 1

    ## Setpoint
    
    def get_setpoint(self):
        """Return the setpoint (SV)."""
        return self.read_register( int('1001',16), 1)
    
    def set_setpoint(self, value):
        """Set the setpoint (SV).
        
        Args:
            value (float): Setpoint [most often in degrees]
        """
        self.write_register( int('1001',16), value, 1)
    
    ## Output signal
    
    def get_output1(self):
        """Return the output value (OP) for output1 [in %]."""
        return elf.read_register( int('1012',16), 1)
   
    
########################
## Testing the module ##
########################

if __name__ == '__main__':
    import sys
    def print_out( inputstring ):
        """Print the inputstring. To make it compatible with Python2 and Python3."""
        sys.stdout.write(inputstring + '\n') 

    print_out( 'TESTING EUROTHERM 3500 MODBUS MODULE')

    a = Eurotherm3500('/dev/cvdHeatercontroller', 1)
    
    print_out( 'SP1:                    {0}'.format(  a.get_sp_loop1()             ))
    print_out( 'SP1 target:             {0}'.format(  a.get_sptarget_loop1()       ))
    print_out( 'SP2:                    {0}'.format(  a.get_sp_loop2()             ))
    print_out( 'SP-rate Loop1 disabled: {0}'.format(  a.is_sprate_disabled_loop1() ))
    print_out( 'SP1 rate:               {0}'.format(  a.get_sprate_loop1()         ))
    print_out( 'OP1:                    {0}%'.format( a.get_op_loop1()             ))
    print_out( 'OP2:                    {0}%'.format( a.get_op_loop2()             ))
    print_out( 'Alarm1 threshold:       {0}'.format(  a.get_threshold_alarm1()     ))
    print_out( 'Alarm summary:          {0}'.format(  a.is_set_alarmsummary()      ))
    print_out( 'Manual mode Loop1:      {0}'.format(  a.is_manual_loop1()          ))
    print_out( 'Inhibit Loop1:          {0}'.format(  a.is_inhibited_loop1()       ))
    print_out( 'PV1:                    {0}'.format(  a.get_pv_loop1()             ))
    print_out( 'PV2:                    {0}'.format(  a.get_pv_loop2()             ))
    print_out( 'PV module 3:            {0}'.format(  a.get_pv_module3()           ))
    print_out( 'PV module 4:            {0}'.format(  a.get_pv_module4()           ))
    print_out( 'PV module 6:            {0}'.format(  a.get_pv_module6()           ))
    #a.set_sp_loop1(5)
    #a.set_sprate_loop1(20)
    #a.enable_sprate_loop1() 
    #a.disable_sprate_loop1() 
    
    print_out( 'DONE!' )

pass    
