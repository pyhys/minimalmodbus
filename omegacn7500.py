#!/usr/bin/env python
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

import minimalmodbus

__author__  = "Aaron LaLonde "
__license__ = "Apache License, Version 2.0"

__revision__  = "$Rev$"
__date__      = "$Date$"


SETPOINT_MAX = 999.9
"""Default value for maximum allowed setpoint."""
#I only allow our users to set our furnaces to 1000C, and with one decimal place on the display the maximum value is 999.9. 


TIME_MAX = 900
"""Default value for maximum allowed step time."""


CONTROL_MODES = {0: 'PID', 1: 'ON/OFF',  2: 'Manual Tuning',  3: 'Program'} 
"""Description of the control mode numerical values."""


REGISTER_START = {  'setpoint':     8192, 
                    'time':         8320,
                    'actualstep':   4160,
                    'cycles':       4176,
                    'linkpattern':  4192}
"""Register address start values for pattern related parameters."""


REGISTER_OFFSET_PER_PATTERN = { 'setpoint':     8, 
                                'time':         8,
                                'actualstep':   1,
                                'cycles':       1,
                                'linkpattern':  1}
"""Increase in register address value per pattern number (for pattern related parameters)."""                        
                      
                      
REGISTER_OFFSET_PER_STEP = {'setpoint':     1, 
                            'time':         1,
                            'actualstep':   0,
                            'cycles':       0,
                            'linkpattern':  0}                      
"""Increase in register address value per step number (for pattern related parameters)."""  


class OmegaCN7500( minimalmodbus.Instrument ):
    """Instrument class for Omega CN7500 process controller. 
    
    Communicates via Modbus RTU protocol (via RS485), using the :mod:`minimalmodbus` Python module.

    This driver is intended to enable control of the OMEGA CN7500 controller from the command line.

    Args:
        * portname (str): port name

            * examples:
            * OS X: '/dev/tty.usbserial'
            * Linux: '/dev/ttyUSB0'
            * Windows: '/com3'
            
        * slaveaddress (int): slave address in the range 1 to 247 (in decimal)

    The controller can be used to follow predefined temperature programs, called patterns. 
    Eight patterns (numbered 0-7) are available, each having eight temperature steps (numbered 0-7).
    
    Each pattern have these parameters:
    
    * Temperature for each step (8 parameters)
    * Time for each step (8 parameters)
    * Link to another pattern
    * Number of cycles (repetitions of this pattern)
    * Actual step (which step to stop at)
    
    Attributes:
        * setpoint_max
            - Defaults to :data:`SETPOINT_MAX`.
        * time_max
            - Defaults to :data:`TIME_MAX`.
            
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
        self.setpoint_max = SETPOINT_MAX
        self.time_max = TIME_MAX
        
        
    ## Process value
    
    def get_pv(self):
        """Return the process value (PV)."""
        return self.read_register( 4096, 1) #0x1000
   
   
    ## Output signal
    
    def get_output1(self):
        """Return the output value (OP) for output1 [in %]."""
        return self.read_register( 0x1012, 1)
   
   
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
        _checkSetpointValue( value, self.setpoint_max )
        self.write_register( 4097, value, 1)

    ## Control Mode

    def get_control_mode(self):
        """Return the name of the current operation mode."""
        mode_value = self.read_register(4101)
        
        try:
            return CONTROL_MODES[mode_value]
        except KeyError:
            raise ValueError( 'Could not parse the control mode value: {0}. Allowed values are: {1}'.format(
                repr(mode_value), repr(list(CONTROL_MODES.keys()) ) )) # To comply with both Python2 and Python3

    def set_control_mode(self, value):
        """Set the control method using the corresponding integer value.
                
        Args:
            value: PID-0, ON/OFF-1, Tuning-2, Program-3
        """
        minimalmodbus._checkInt(value, minvalue=0, maxvalue=3, description='control mode') 
        self.write_register(4101, value)


    ## Set program pattern variables

    def get_start_pattern_no(self):
        """Return the starting pattern number."""
        return self.read_register(4144, 0)


    def set_start_pattern_no(self, value):
        """Set the starting pattern number.

        Args:
            value (integer): From 0-7
        """
        _checkPatternNumber( value )
        self.write_register(4144, value, 0)
    
    
    def get_pattern_step_setpoint(self, pattern, step):
        """Return the setpoint value of the desired pattern step.

        Args:
            * pattern (integer): From 0-7
            * step (integer): From 0-7
        """
        _checkPatternNumber( pattern )
        _checkStepNumber( step )
   
        address = _calculateRegisterAddress('setpoint', pattern, step)
        return self.read_register(address, 1)
        
        
    def set_pattern_step_setpoint(self, pattern, step, value):
        """Set the value of the desired pattern step

        Args:
            * pattern (integer): From 0-7
            * step (integer): From 0-7
            * value (float): Setpoint value
        """
        _checkPatternNumber( pattern )
        _checkStepNumber( step )
        _checkSetpointValue( value, self.setpoint_max  )
        
        address = _calculateRegisterAddress('setpoint', pattern, step)
        self.write_register(address, value, 1)
            
            
    def get_pattern_step_time(self, pattern, step):
        """Return the step time value of the desired pattern.

        Args:
            * pattern (integer): From 0-7
            * step (integer): From 0-7
        """
        _checkPatternNumber( pattern )
        _checkStepNumber( step )
        
        address = _calculateRegisterAddress('time', pattern, step)
        return self.read_register(address, 0)


    def set_pattern_step_time(self, pattern, step, value):
        """Set the value of the desired pattern step time.

        Args:
            * pattern (integer): From 0-7
            * step (integer): From 0-7
            * value (integer): From 0-900
        """
        _checkPatternNumber( pattern )
        _checkStepNumber( step )
        _checkTimeValue( value, self.time_max )
        
        address = _calculateRegisterAddress('time', pattern, step)
        self.write_register(address, value, 0)
        
        
    def get_pattern_actual_step(self, pattern):
        """Return the value of the actual step parameter for a given pattern.

        Args:
            pattern (integer): From 0-7
        """
        _checkPatternNumber( pattern )
        
        address = _calculateRegisterAddress('actualstep', pattern)
        return self.read_register(address, 0)


    def set_pattern_actual_step(self, pattern, value):
        """Set the actual step parameter for a given pattern.

        Args:
            * pattern (integer): From 0-7
            * value (integer): From 0-7
        """
        _checkPatternNumber( pattern )
        _checkStepNumber( value )
        
        address = _calculateRegisterAddress('actualstep', pattern)
        self.write_register(address, value, 0)


    def get_pattern_additional_cycles(self, pattern):
        """Return the value of the additional cycles for a given pattern.

        Args:
            pattern (integer): From 0-7
        """
        _checkPatternNumber( pattern )

        address = _calculateRegisterAddress('cycles', pattern)
        return self.read_register(address)


    def set_pattern_additional_cycles(self, pattern, value):
        """Set the number of additional cycles for a given pattern.

        Args:
            * pattern (integer): From 0-7
            * value (integer): From 0-99
        """
        _checkPatternNumber( pattern )
        minimalmodbus._checkInt(value, minvalue=0, maxvalue=99, description='number of additional cycles') 
            
        address = _calculateRegisterAddress('cycles', pattern)
        self.write_register(address, value, 0)

        
    def get_pattern_link_topattern(self, pattern):
        """Get the linked pattern value for a given pattern.

        Args:
            pattern (integer): From 0-7
        """
        _checkPatternNumber( pattern )

        address = _calculateRegisterAddress('linkpattern', pattern)
        return self.read_register(address)


    def set_pattern_link_topattern(self, pattern, value):
        """Set the linked pattern value for a given pattern.

        Args:
            * pattern (integer): From 0-7
            * value (integer): From 0-7, value=8 sets the link parameter to OFF
        """
        _checkPatternNumber( pattern )
        minimalmodbus._checkInt(value, minvalue=0, maxvalue=8, description='linked pattern value') 
        
        address = _calculateRegisterAddress('linkpattern', pattern)
        self.write_register(address, value, 0)
               
               
    def get_all_pattern_variables(self, pattern):
        """Get all variables for a given pattern at one time.

        Args:
            pattern (integer): From 0-7
            
        Returns:
            A descriptive multiline string.    
            
        """
        _checkPatternNumber( pattern )
        
        outputstring = ''
        for stepnumber in range(8):
            outputstring += 'SP{0}: {1}  Time{0}: {2}\n'.format(stepnumber, \
                self.get_pattern_step_setpoint( pattern, stepnumber), \
                self.get_pattern_step_time(     pattern, stepnumber)   )
        
        outputstring += 'Actual step:        {0}\n'.format(self.get_pattern_actual_step(        pattern) )
        outputstring += 'Additional cycles:  {0}\n'.format(self.get_pattern_additional_cycles(  pattern) )
        outputstring += 'Linked pattern:     {0}\n'.format(self.get_pattern_link_topattern(     pattern) ) 
            
        return outputstring
        

    def set_all_pattern_variables(self, pattern, \
        sp0, ti0, sp1, ti1, sp2, ti2, sp3, ti3, sp4, ti4, sp5, ti5, sp6, ti6, sp7, ti7, \
        actual_step, additional_cycles, link_pattern):
        """Set all variables for a given pattern at one time.

        Args:
            * pattern (integer): From 0-7
            * sp[n] (float): setpoint value for *n* pattern
            * ti[n] (integer): time value for *n* pattern, 0-900
            * actual_step ?
            * additional_cycles ?
            * link_pattern ?
            
        Raises:
            TypeError, ValueError    
            
        """
        _checkPatternNumber( pattern )
        
        self.set_pattern_step_setpoint( pattern, 0, sp0)
        self.set_pattern_step_setpoint( pattern, 1, sp1)
        self.set_pattern_step_setpoint( pattern, 2, sp2)
        self.set_pattern_step_setpoint( pattern, 3, sp3)
        self.set_pattern_step_setpoint( pattern, 4, sp4)
        self.set_pattern_step_setpoint( pattern, 5, sp5)
        self.set_pattern_step_setpoint( pattern, 6, sp6)
        self.set_pattern_step_setpoint( pattern, 7, sp7)
        self.set_pattern_step_time(     pattern, 0, ti0)
        self.set_pattern_step_time(     pattern, 1, ti1)
        self.set_pattern_step_time(     pattern, 2, ti2)
        self.set_pattern_step_time(     pattern, 3, ti3)
        self.set_pattern_step_time(     pattern, 4, ti4)
        self.set_pattern_step_time(     pattern, 5, ti5)
        self.set_pattern_step_time(     pattern, 6, ti6)
        self.set_pattern_step_time(     pattern, 7, ti7)
        self.set_pattern_additional_cycles( pattern, additional_cycles)
        self.set_pattern_link_topattern(    pattern, link_pattern)
        self.set_pattern_actual_step(       pattern, actual_step)


def _checkPatternNumber( patternnumber ):
    """Check that the given patternnumber is valid.
    
    Args:
        * patternnumber (int): The patternnumber to be checked.
        
    Raises:
        TypeError, ValueError
    
    """
    minimalmodbus._checkInt(patternnumber, minvalue=0, maxvalue=7, description='pattern number') 


def _checkStepNumber( stepnumber ):
    """Check that the given  stepumber is valid.
    
    Args:
        * stepnumber (int): The stepnumber to be checked.
        
    Raises:
        TypeError, ValueError
    
    """
    minimalmodbus._checkInt(stepnumber, minvalue=0, maxvalue=7, description='step number') 


def _checkSetpointValue( setpointvalue, maxvalue ):   
    """Check that the given setpointvalue is valid.
    
    Args:
        * setpointvalue (numerical): The setpoint value to be checked. Must be positive.
        * maxvalue (numerical): Upper limit for setpoint value. Must be positive.
        
    Raises:
        TypeError, ValueError
    
    """
    if maxvalue is None:
        raise TypeError('The maxvalue (for the setpoint) must not be None!')
    minimalmodbus._checkNumerical(setpointvalue, minvalue=0, maxvalue=maxvalue, description='setpoint value')   


def _checkTimeValue( timevalue, maxvalue ):   
    """Check that the given timevalue is valid.
    
    Args:
        * timevalue (numerical): The time value to be checked. Must be positive.
        * maxvalue (numerical): Upper limit for time value. Must be positive.
        
    Raises:
        TypeError, ValueError
    
    """
    if maxvalue is None:
        raise TypeError('The maxvalue (for the time value) must not be None!')
    minimalmodbus._checkNumerical(timevalue, minvalue=0, maxvalue=maxvalue, description='time value')     
    
    
def _calculateRegisterAddress( registertype, patternnumber, stepnumber = None):
    """Calculate the register address for pattern related parameters.
    
    Args:
        * registertype (string): The type of parameter, for example 'cycles'. 
          Allowed are the keys from :data:`REGISTER_START`.
        * patternnumber (int): The pattern number.
        * stepnumber (int): The step number. Use None if it not should affect the calculation.
    
    Returns:
        The register address (int).
    
    Raises:
        TypeError, ValueError
    
    """
    if stepnumber is None:
        stepnumber = 0
    
    # Argument checking
    _checkPatternNumber( patternnumber )
    _checkStepNumber( stepnumber )
    
    if not registertype in list(REGISTER_START.keys()): # To comply with both Python2 and Python3
        raise ValueError('Wrong register type: {0}. Allowed values: {1}'.format( 
            repr(registertype), repr( list(REGISTER_START.keys()) )))

    # Calculate register address
    address = REGISTER_START[registertype] + \
                patternnumber * REGISTER_OFFSET_PER_PATTERN[registertype] + \
                stepnumber * REGISTER_OFFSET_PER_STEP[registertype]
        
    return address
    
    
########################
## Testing the module ##
########################

if __name__ == '__main__':

    minimalmodbus._print_out('TESTING OMEGA CN7500 MODBUS MODULE')

    PORTNAME = '/dev/tty.usbserial-FTFO1057'
    ADDRESS = 10
    
    minimalmodbus._print_out( 'Port: ' +  str(PORTNAME) + ', Address: ' + str(ADDRESS) )
    
    instr = OmegaCN7500(PORTNAME, ADDRESS)
    
    minimalmodbus._print_out( 'Control:                {0}'.format(  instr.get_control_mode()    ))
    minimalmodbus._print_out( 'SP:                     {0}'.format(  instr.get_setpoint() ))
    minimalmodbus._print_out( 'PV:                     {0}'.format(  instr.get_pv()       ))
    minimalmodbus._print_out( 'OP1:                    {0}'.format(  instr.get_output1()  ))   
    minimalmodbus._print_out( 'Is running:             {0}'.format(  instr.is_running()   ))
    minimalmodbus._print_out( 'Start pattern:          {0}'.format(  instr.get_start_pattern_no()  ))

    minimalmodbus._print_out('DONE!')

pass    
