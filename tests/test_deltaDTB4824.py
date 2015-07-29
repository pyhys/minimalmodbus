"""
Hardware testing of MinimalModbus using the Delta DTB temperature controller.

For use with Delta DTB4824VR. 

Usage
-------------

::

    python scriptname [-rtu] [-ascii] [-b38400] [-D/dev/ttyUSB0]

Arguments:
 * -b : baud rate
 * -D : port name
 
NOTE: There should be no space between the option switch and its argument.

Defaults to RTU mode.


Recommended test sequence
---------------------------
Make sure that RUN_VERIFY_EXAMPLES and similar flags are all 'True'.

 * Run the tests under Linux and Windows
 * Use 2400 bps and 38400 bps
 * Use Modbus ASCII and Modbus RTU
 * Use Python 2.7 and Python 3.x 
 
 
 Sequence (for each use Python 2.7 and 3.x):
  * 38400 bps RTU
  * 38400 bps ASCII
  * 2400 bps ASCII
  * 2400 bps RTU


Settings in the temperature controller
------------------------------------------
To change the settings on the temperature controller panel,
hold the SET button for more than 3 seconds. Use the 'loop arrow' button for 
moving to next parameter. Change the value with the up and down arrows, and 
confirm using the SET button. Press SET again to exit setting mode.

Use these setting values in the temperature controller:
 * SP   1    (Decimal point position)
 * CoSH on   (ON: communication write-in enabled)
 * C-SL rtu  (use RTU or ASCII)
 * C-no 1    (Slave number)
 * BPS       (see the DEFAULT_BAUDRATE setting below, or the command line argument)
 * LEN  8
 * PRTY None
 * Stop 1
 
When running, the setpoint is seen on the rightmost part of the display.


USB-to-RS485 converter
----------------------------
BOB-09822 USB to RS-485 Converter:
 * https://www.sparkfun.com/products/9822
 * SP3485 RS-485 transceiver
 * FT232RL USB UART IC
 * FT232RL pin2: RE^
 * FT232RL pin3: DE

================ ================== ====================
DTB4824 terminal USB-RS485 terminal Description
================ ================== ====================
DATA+            A                  Positive at idle
DATA-            B                  Negative at idle
================ ================== ====================

Sometimes after changing the baud rate, there is no communication with
the temperature controller. Reset the FTDI chip by unplugging and
replugging the USB-to-RS485 converter.


Function codes for DTB4824
-------------------------------
From "DTB Series Temperature Controller Instruction Sheet":
 * 02H to read the bits data (Max. 16 bits).
 * 03H to read the contents of register (Max. 8 words).
 * 05H to write 1 (one) bit into register.
 * 06H to write 1 (one) word into register.


Manual testing in interactive mode (at the Python prompt)
----------------------------------------------------------
Use a setting of 19200 bps, RTU mode and slave addess 1 for the DTB4824. 
Run these commands::

    import minimalmodbus
    instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1)  # Adjust if necessary.
    instrument.debug = True
    instrument.read_register(4143)  # Read firmware version (address in hex is 0x102F)


"""
import os
import sys
import time

import minimalmodbus

SECONDS_TO_MILLISECONDS = 1000

##############
## Settings ##
##############

DEFAULT_PORT_NAME   = '/dev/ttyUSB0'
SLAVE_ADDRESS       = 1
DEFAULT_BAUDRATE    = 38400 # baud (pretty much bits/s). Use 2400 or 38400 bits/s.
TIMEOUT             = 0.2 # seconds. At least 0.2 seconds required for 2400 bits/s.


###############################
## Select which tests to run ##
###############################

RUN_VERIFY_EXAMPLES             = True
RUN_READOUT_PRESENT_SETTINGS    = True
RUN_START_AND_STOP_REGULATOR    = True
RUN_MEASURE_ROUNDTRIP_TIME      = True
RUN_VERIFY_TWO_INSTRUMENTS      = True


def main():
    #################################
    ## Read command line arguments ##
    #################################

    # Do manual parsing of command line,
    # as none of the modules in the standard library handles python 2.6 to 3.x

    MODE        = minimalmodbus.MODE_RTU
    BAUDRATE    = DEFAULT_BAUDRATE
    PORT_NAME   = DEFAULT_PORT_NAME

    for arg in sys.argv:
        if arg.startswith('-ascii'):
            MODE = minimalmodbus.MODE_ASCII
            
        elif arg.startswith('-rtu'): 
            MODE = minimalmodbus.MODE_RTU
        
        elif arg.startswith('-b'):
            if len(arg) < 3:
                minimalmodbus._print_out('Wrong usage of the -b option. Use -b9600')
                sys.exit()
            BAUDRATE = int(arg[2:])
            
        elif arg.startswith('-D'):
            if len(arg) < 3:
                minimalmodbus._print_out('Wrong usage of the -D option. Use -D/dev/ttyUSB0 or -DCOM4')
                sys.exit()
            PORT_NAME = arg[2:]
    
    ################################
    ## Create instrument instance ##
    ################################
    instrument = minimalmodbus.Instrument(PORT_NAME, SLAVE_ADDRESS, MODE)
    instrument.serial.baudrate = BAUDRATE
    instrument.serial.timeout = TIMEOUT
    instrument.debug = False
    instrument.precalculate_read_size = True


    text = '\n'
    text += '###############################################################\n'
    text += '## Hardware test with Delta DTB4824                          ##\n'
    text += '## Minimalmodbus version: {:8}                           ##\n'.format(minimalmodbus.__version__)
    text += '##                                                           ##\n'
    text += '## Modbus mode:    {:15}                           ##\n'.format(instrument.mode)
    text += '## Python version: {}.{}.{}                                     ##\n'.format(sys.version_info[0], sys.version_info[1], sys.version_info[2])
    text += '## Baudrate (-b):  {:>5} bits/s                              ##\n'.format(instrument.serial.baudrate)
    text += '## Platform:       {:15}                           ##\n'.format(sys.platform)
    text += '##                                                           ##\n'
    text += '## Port name (-D): {:15}                           ##\n'.format(instrument.serial.port)
    text += '## Slave address:  {:<15}                           ##\n'.format(instrument.address)
    text += '## Timeout:        {:0.3f} s                                   ##\n'.format(instrument.serial.timeout)
    text += '## Full file path: ' + os.path.abspath(__file__) + '\n'
    text += '###############################################################\n'
    minimalmodbus._print_out(text)

    minimalmodbus._print_out(repr(instrument))


    if RUN_VERIFY_EXAMPLES:
        #########################################################################################
        ## Examples from page 11 in the "DTB Series Temperature Controller Instruction Sheet", ##
        ## version 2010-04-20                                                                  ##
        #########################################################################################
        instrument.debug = False

        # Read two registers starting at 0x1000. This is process value (PV) and setpoint (SV).
        # Should send '\x01\x03\x10\x00\x00\x02\xc0\xcb' OK!
        minimalmodbus._print_out('\nReading register 0x1000 and 0x1001:')
        minimalmodbus._print_out(repr(instrument.read_registers(0x1000, 2)))

        # Read 9 bits starting at 0x0810.
        # Should send '\x01\x02\x08\x10\x00\x09\xbb\xa9' OK!
        minimalmodbus._print_out('\nReading 9 bits starting at 0x0810:')
        minimalmodbus._print_out(repr(instrument._performCommand(2, '\x08\x10\x00\x09')))

        # Write value 800 to register 0x1001. This is a setpoint of 80.0 degrees (Centigrades, dependent on setting).
        # Should send '\x01\x06\x10\x01\x03\x20\xdd\xe2' OK!
        instrument.write_register(0x1001, 0x0320, functioncode=6)
        # Response from instrument: '\x01\x06\x10\x01\x03 \xdd\xe2' OK!
        # Note that the slave will indicate an error if the CoSH parameter in the controller
        # does not allow writing.
        # ASCII mode: Request  ':010610010320C5\r\n' 
        #             Response ':010610010320C5\r\n'

        # Write 1 to one bit at 0x0810. This is "Communication write in enabled".
        # Should send '\x01\x05\x08\x10\xff\x00\x8f\x9f' OK!
        instrument.write_bit(0x0810, 1)
        # Response from instrument: '\x01\x05\x08\x10\xff\x00\x8f\x9f' OK!
        
        
        #instrument.read_register(0x1001)
        # ASCII mode: Request  ':010310010001EA\r\n'
        #             Response ':0103020320D7\r\n'
        

    if RUN_READOUT_PRESENT_SETTINGS:
        ###############################
        ## Read out present settings ##
        ###############################
        instrument.debug = False
        
        minimalmodbus._print_out('\nPV: '                        + str(instrument.read_register(0x1000)))
        minimalmodbus._print_out('Setpoint: '                    + str(instrument.read_register(0x1001, 1)))
        minimalmodbus._print_out('Sensor type: '                 + str(instrument.read_register(0x1004)))
        minimalmodbus._print_out('Control method: '              + str(instrument.read_register(0x1005)))
        minimalmodbus._print_out('Heating/cooling selection: '   + str(instrument.read_register(0x1006)))
        minimalmodbus._print_out('Output 1 value: '              + str(instrument.read_register(0x1012, 1)))
        minimalmodbus._print_out('Output 2 value: '              + str(instrument.read_register(0x1013, 1)))
        minimalmodbus._print_out('System alarm setting: '        + str(instrument.read_register(0x1023)))
        minimalmodbus._print_out('LED status: '                  + str(instrument.read_register(0x102A)))
        minimalmodbus._print_out('Pushbutton status: '           + str(instrument.read_register(0x102B)))
        minimalmodbus._print_out('Firmware version: '            + str(instrument.read_register(0x102F)))

        minimalmodbus._print_out('LED AT: '                      + str(instrument.read_bit(0x0800)))
        minimalmodbus._print_out('LED Out1: '                    + str(instrument.read_bit(0x0801)))
        minimalmodbus._print_out('LED Out2: '                    + str(instrument.read_bit(0x0802)))
        minimalmodbus._print_out('RUN/STOP setting: '            + str(instrument.read_bit(0x0814)))

    if RUN_START_AND_STOP_REGULATOR:
        ###################################################
        ## Start and stop the regulator, change setpoint ##
        ###################################################
        instrument.debug = False

        SLEEP_TIME = 2

        instrument.write_bit(0x0814, 0) # Stop
        setpoint_value = 25
        instrument.write_register(0x1001,setpoint_value, 1, functioncode=6)
        minimalmodbus._print_out('\nSetpoint:'          + str(instrument.read_register(0x1001, 1)))
        minimalmodbus._print_out('RUN/STOP setting:'    + str(instrument.read_bit(0x0814)))
        time.sleep(SLEEP_TIME)

        instrument.write_bit(0x0814, 1) # Run
        minimalmodbus._print_out('\nSetpoint:'            + str(instrument.read_register(0x1001, 1)))
        minimalmodbus._print_out('RUN/STOP setting:'    + str(instrument.read_bit(0x0814)))
        time.sleep(SLEEP_TIME)

        setpoint_value = 35
        instrument.write_register(0x1001,setpoint_value, 1, functioncode=6)
        minimalmodbus._print_out('\nSetpoint:'            + str(instrument.read_register(0x1001, 1)))
        minimalmodbus._print_out('RUN/STOP setting:'    + str(instrument.read_bit(0x0814)))
        time.sleep(SLEEP_TIME)

        instrument.write_bit(0x0814, 0) # Stop
        minimalmodbus._print_out('\nSetpoint:'            + str(instrument.read_register(0x1001, 1)))
        minimalmodbus._print_out('RUN/STOP setting:'    + str(instrument.read_bit(0x0814)))

    if RUN_MEASURE_ROUNDTRIP_TIME:
        ####################################################
        ## Measure roundtrip time                         ##
        ## Loop setpoint value (20 to 50 deg C, and back) ##
        ####################################################
        instrument.debug = False

        NUMBER_OF_VALUES = 100

        START_VALUE = 200
        STOP_VALUE  = 500
        STEPSIZE    = 5

        value       = START_VALUE
        step        = STEPSIZE

        text = '\nSetting the SP value {} times. Baudrate {} bits/s.'.format(NUMBER_OF_VALUES, instrument.serial.baudrate)
        minimalmodbus._print_out(text)

        start_time = time.time()
        for i in range(NUMBER_OF_VALUES):
            if value > STOP_VALUE or value < START_VALUE:
                step = -step
            value += step
            instrument.write_register(0x1001, value, functioncode=6)

        time_per_value = (time.time() - start_time)*float(SECONDS_TO_MILLISECONDS)/NUMBER_OF_VALUES
        text = 'Time per value: {:0.1f} ms.'.format(time_per_value)
        minimalmodbus._print_out(text)

    if RUN_VERIFY_TWO_INSTRUMENTS:
        #######################################################
        ## Verify that two instruments can use the same port ##
        #######################################################

        instrument.debug = False
        minimalmodbus._print_out('\nInstrument1 SP:')
        minimalmodbus._print_out(str(instrument.read_register(0x1001, 1)))

        instrument2 = minimalmodbus.Instrument(PORT_NAME, SLAVE_ADDRESS, MODE)
        instrument2.debug = False
        instrument2.serial.baudrate = BAUDRATE
        instrument2.serial.timeout  = TIMEOUT

        minimalmodbus._print_out('\nInstrument2 SP:')
        minimalmodbus._print_out(str(instrument2.read_register(0x1001, 1)))

if __name__ == '__main__':
    main()
