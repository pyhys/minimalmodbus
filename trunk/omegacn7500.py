http://minimalmodbus.sourceforge.net/administrative.html#!/usr/bin/env python
#
#   Copyright 2011 Aaron LaLonde 
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

.. moduleauthor:: Aaron LaLonde 

Driver for the Omega CN7500 process controller, for communication using the Modbus RTU protocol.

This Python file was changed (committed) at 
$Date$, 
which was $Revision$.

"""
#import omegacn7500
#omega = omegacn7500.OmegaCN7500('/dev/tty.usbserial-FTF6AS6V', 10)



import minimalmodbus

__author__  = "Aaron LaLonde "
__license__ = "Apache License, Version 2.0"

__revision__  = "$Rev$"
__date__      = "$Date$"

# Here are the decimal addresses for different parameters

setpoint_addresses = range(8192,8200),range(8200,8208),range(8208,8216),range(8216,8224),range(8224,8232),range(8232,8240),range(8240,8248),range(8248,8256)
time_addresses = range(8320, 8328),range(8328,8336),range(8336,8344),range(8344,8352),range(8352,8360),range(8360,8368),range(8368,8376),range(8376,8384)
actual_step_addresses = range(4160, 4168)
additional_cycles_addresses = range(4176, 4184)
link_pattern_addresses = range(4192, 4200)

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
        return self.read_register( 4096, 1) #0x1000
   
    ## Run and stop the controller
    
    def run(self):
        """Put the process controller in run mode."""
        self.write_bit( 2068, 1)

    def stop(self):
        """Stop the process controller."""
        self.write_bit( 2068, 0)

    def is_running(self):
        """Return True if the controller is running."""
        return self.read_bit( 2068 ) == 1   

    ## Setpoint
    
    def get_setpoint(self):
        """Return the setpoint (SV)."""
        return self.read_register( 4097, 1) 
    
    def set_setpoint(self, value):
        """Set the setpoint (SV).
        
        Args:
            value (float): Setpoint [most often in degrees]
        """
        if value <= 999.9:
            self.write_register( 4097, value, 1)
        else:
            value = 999.9
            print 'Nice try rookie, how about 1000?'
            return self.write_register(4097, value, 1)

    ## Control Mode

    def get_control_mode(self):
        """Return the current operation mode"""
        mode_value = self.read_register(4101)
        if mode_value == 0:
            mode_string = 'PID'
            return mode_string
        if mode_value == 1:
            mode_string = 'ON/OFF'
            return mode_string
        if mode_value == 2:
            mode_string = 'Manual Tuning'
            return mode_string
        if mode_value == 3:
            mode_string = 'Program'
            return mode_string

    def set_control_mode(self, value):
        """Set the control method"""
        if 0 <= value <= 4:
            return self.write_register(4101, value)
        else:
            return 'Not a valid control value'

    ## Set program pattern variables

    def get_start_pattern_no(self):
        """Return the starting pattern number"""
        return self.read_register(4144, 0)

    def set_start_pattern_no(self, value):
        """Set the starting pattern number"""
        if 0 <= value <= 7:
            return self.write_register(4144, value, 0)
        else:
            return 'Not a valid pattern number, must be 0-7'
    
    def get_pattern_step_setpoint(self, pattern, step):
        """Return the value of the desired program step"""
        if 0<=pattern<=7 and 0<=step<=7:
            address = setpoint_addresses[pattern][step] 
            return self.read_register(address, 1)
        elif pattern not in range(0,8):
            return 'Not a valid pattern number, must be 0-7'
        elif step not in range(0,8):
            return 'Not a valid step number, must be 0-7'
        
    def set_pattern_step_setpoint(self, pattern, step, value):
        """Set the value of the desired program step"""
        if 0<=pattern<=7 and 0<=step<=7 and 0 <= value <= 999.9:
            address = setpoint_addresses[pattern][step]
            return self.write_register(address, value, 1)
        elif pattern not in range(0,8):
            return 'Not a valid pattern number, must be 0-7'
        elif step not in range(0,8):
            return 'Not a valid step number, must be 0-7'
        elif value > 999.9:
            return 'Nice try rookie, how about 1000?'

    def get_pattern_step_time(self, pattern, step):
        """Return the value of the desired pattern step time"""
        if 0<=pattern<=7 and 0<=step<=7:
            address = time_addresses[pattern][step]
            return self.read_register(address, 0)
        elif pattern not in range(0,8):
            return 'Not a valid pattern number, must be 0-7'
        elif step not in range(0,8):
            return 'Not a valid step number, must be 0-7'

    def set_pattern_step_time(self, pattern, step, value):
        """Set the value of the desired pattern step time"""
        if  0<=pattern<=7 and 0<=step<=7 and 0 <= value <= 900:
            address = time_addresses[pattern][step]
            return self.write_register(address, value, 0)
        elif pattern not in range(0,8):
            return 'Not a valid pattern number, must be 0-7'
        elif step not in range(0,8):
            return 'Not a valid step number, must be 0-7'
        elif value > 900: 
            return 'Time must be between 0-900'

    def get_pattern_actual_step(self, pattern):
        """Return the value of the actual step for a given pattern"""
        if 0<=pattern<=7:
            address = actual_step_addresses[pattern]
            return self.read_register(address, 0)
        else:
            return 'Not a valid pattern number, must be 0-7'

    def set_pattern_actual_step(self, pattern, value):
        """Set the actual step for a given pattern"""
        if 0<=pattern<=7 and 0 <= value <= 7:
            address = actual_step_addresses[pattern]
            return self.write_register(address, value, 0)
        elif pattern not in range(0,8):
            return 'Not a valid pattern number, must be 0-7'
        elif value not in range(0,8):
            return 'Not a valid step number, must be 0-7'

    def get_pattern_additional_cycles(self, pattern):
        """Return the value of the additional cycles for a given pattern"""
        if 0<=pattern<=7:
            address = additional_cycles_addresses[pattern]
            return self.read_register(address)
        else:
            return 'Not a valid pattern number, must be 0-7'

    def set_pattern_additional_cycles(self, pattern, value):
        """Set the number of additional cycles for a given pattern"""
        if 0 <= pattern <= 7 and 0 <= value <= 99:
            address = additional_cycles_addresses[pattern]
            return self.write_register(address, value, 0)
        elif pattern not in range(0,8):
            return 'Not a valid pattern number, must be 0-7'
        elif value > 99:
            return 'Not a valid number of additional cycles, must be 0-99'
        
    def get_pattern_link_topattern(self, pattern):
        """Get the linked pattern value for a given pattern"""
        if 0<=pattern<=7:
            address = link_pattern_addresses[pattern]
            return self.read_register(address)
        else:
            return 'Not a valid pattern number, must be 0-7'

    def set_pattern_link_topattern(self, pattern, value):
        """Set the linked pattern value for a given pattern"""
        if 0 <= pattern <= 7 and 0 <= value <= 7:
            address = link_pattern_addresses[pattern]
            return self.write_register(address, value, 0)
        elif pattern not in range(0,8):
            return 'Not a valid pattern number, must be 0-7'
        elif value not in range(0,8):
            return 'Not a valid step number, must be 0-7'

    def get_all_pattern_variables(self, pattern):
        """Get all variables for a given pattern at one time"""
        if 0<=pattern<=7:
            sp0_address = setpoint_addresses[pattern][0]
            sp1_address = setpoint_addresses[pattern][1]
            sp2_address = setpoint_addresses[pattern][2]
            sp3_address = setpoint_addresses[pattern][3]
            sp4_address = setpoint_addresses[pattern][4]
            sp5_address = setpoint_addresses[pattern][5]
            sp6_address = setpoint_addresses[pattern][6]
            sp7_address = setpoint_addresses[pattern][7]
            ti0_address = time_addresses[pattern][0]
            ti1_address = time_addresses[pattern][1]
            ti2_address = time_addresses[pattern][2]
            ti3_address = time_addresses[pattern][3]
            ti4_address = time_addresses[pattern][4]
            ti5_address = time_addresses[pattern][5]
            ti6_address = time_addresses[pattern][6]
            ti7_address = time_addresses[pattern][7]
            actual_step_address = actual_step_addresses[pattern]
            additional_cycles_address = additional_cycles_addresses[pattern]
            link_pattern_address = link_pattern_addresses[pattern]
            sp0 = self.read_register(sp0_address,1)
            sp1 = self.read_register(sp1_address,1)
            sp2 = self.read_register(sp2_address,1)
            sp3 = self.read_register(sp3_address,1)
            sp4 = self.read_register(sp4_address,1)
            sp5 = self.read_register(sp5_address,1)
            sp6 = self.read_register(sp6_address,1)
            sp7 = self.read_register(sp7_address,1)
            ti0 = self.read_register(ti0_address,0)
            ti1 = self.read_register(ti1_address,0)
            ti2 = self.read_register(ti2_address,0)
            ti3 = self.read_register(ti3_address,0)
            ti4 = self.read_register(ti4_address,0)
            ti5 = self.read_register(ti5_address,0)
            ti6 = self.read_register(ti6_address,0)
            ti7 = self.read_register(ti7_address,0)
            actual_step = self.read_register(actual_step_address,0)
            additional_cycles = self.read_register(additional_cycles_address,0)
            link_pattern = self.read_register(link_pattern_address,0)
            print "%-2s %-4d %-2s %d " % ("SP0:",sp0,"Time0:",ti0)
            print "%-2s %-4d %-2s %d" % ("SP1:",sp1,"Time1:",ti1)
            print "%-2s %-4d %-2s %d" % ("SP2:",sp2,"Time2:",ti2)
            print "%-2s %-4d %-2s %d" % ("SP3:",sp3,"Time3:",ti3)
            print "%-2s %-4d %-2s %d" % ("SP4:",sp4,"Time4:",ti4)
            print "%-2s %-4d %-2s %d" % ("SP5:",sp5,"Time5:",ti5)
            print "%-2s %-4d %-2s %d" % ("SP6:",sp6,"Time6:",ti6)
            print "%-2s %-4d %-2s %d" % ("SP7:",sp7,"Time7:",ti7)
            print "%-17s %d" % ("Actual step:",actual_step)
            print "%-17s %d" % ("Add'l cycles:",additional_cycles)
            print "%-17s %d" % ("Linked pattern:",link_pattern)
            
    def set_all_pattern_variables(self, pattern, sp0, ti0, sp1, ti1, sp2, ti2, sp3, ti3, sp4, ti4, sp5, ti5, sp6, ti6, sp7, ti7, actual_step, additional_cycles, link_pattern):
            sp0_address = setpoint_addresses[pattern][0]
            sp1_address = setpoint_addresses[pattern][1]
            sp2_address = setpoint_addresses[pattern][2]
            sp3_address = setpoint_addresses[pattern][3]
            sp4_address = setpoint_addresses[pattern][4]
            sp5_address = setpoint_addresses[pattern][5]
            sp6_address = setpoint_addresses[pattern][6]
            sp7_address = setpoint_addresses[pattern][7]
            ti0_address = time_addresses[pattern][0]
            ti1_address = time_addresses[pattern][1]
            ti2_address = time_addresses[pattern][2]
            ti3_address = time_addresses[pattern][3]
            ti4_address = time_addresses[pattern][4]
            ti5_address = time_addresses[pattern][5]
            ti6_address = time_addresses[pattern][6]
            ti7_address = time_addresses[pattern][7]
            actual_step_address = actual_step_addresses[pattern]
            additional_cycles_address = additional_cycles_addresses[pattern]
            link_pattern_address = link_pattern_addresses[pattern]
            self.write_register(sp0_address,sp0,1)
            self.write_register(sp1_address,sp1,1)
            self.write_register(sp2_address,sp2,1)
            self.write_register(sp3_address,sp3,1)
            self.write_register(sp4_address,sp4,1)
            self.write_register(sp5_address,sp5,1)
            self.write_register(sp6_address,sp6,1)
            self.write_register(sp7_address,sp7,1)
            self.write_register(ti0_address,ti0,0)
            self.write_register(ti1_address,ti1,0)
            self.write_register(ti2_address,ti2,0)
            self.write_register(ti3_address,ti3,0)
            self.write_register(ti4_address,ti4,0)
            self.write_register(ti5_address,ti5,0)
            self.write_register(ti6_address,ti6,0)
            self.write_register(ti7_address,ti7,0)
            self.write_register(actual_step_address,actual_step,0)
            self.write_register(additional_cycles_address,additional_cycles,0)
            self.write_register(link_pattern_address,link_pattern,0)
            
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

    PORTNAME = '/dev/tty.usbserial-FTF6AS6V'
    ADDRESS = 10
    
    print_out( 'Port: ' +  str(PORTNAME) + ' Address: ' + str(ADDRESS) )
    
    instr = OmegaCN7500(PORTNAME, ADDRESS)
    
    print_out( 'Control:                {0}'.format(  instr.get_operation_mode()    ))
    print_out( 'SP:                     {0}'.format(  instr.get_setpoint() ))
    print_out( 'PV:                     {0}'.format(  instr.get_pv()       ))
    print_out( 'OP1:                    {0}'.format(  instr.get_output1()  ))   
    print_out( 'Is running:             {0}'.format(  instr.is_running()   ))
    print_out( 'Start pattern:          {0}'.format(  instr.get_start_pattern_no()  ))

    print_out( 'DONE!' )

pass    
