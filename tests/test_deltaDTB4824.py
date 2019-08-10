"""
Hardware testing of MinimalModbus using the Delta DTB temperature controller.

For use with Delta DTB4824VR.

Usage
-------------

::

    python3 scriptname [-rtu] [-ascii] [-b38400] [-D/dev/ttyUSB0]

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

SLAVE_ADDRESS = 1
TIMEOUT = 0.2  # seconds. At least 0.2 seconds required for 2400 bits/s.
DEFAULT_PORT_NAME = "/dev/ttyUSB0"
DEFAULT_BAUDRATE = 38400  # baud (pretty much bits/s). Use 2400 or 38400 bits/s.


def _print_out(text):
    # Python2 and 3 compatible
    sys.stdout.write("{}\n".format(text))
    sys.stdout.flush()


def _box(description=None, value=None):
    MAX_WIDTH = 85
    DESCR_WIDTH = 30
    if description is None:
        _print_out("#"*MAX_WIDTH)
    else:
        if value is None:
            line = "## {}".format(description)
        else:
            line = "## {}:".format(description).ljust(DESCR_WIDTH) + str(value)
        line = line.ljust(MAX_WIDTH - 2) + "##"
        _print_out(line)


def show_test_settings(mode, baudrate, portname):
    _box()
    _box("Hardware test with Delta DTB4824")
    _box("Minimalmodbus version", minimalmodbus.__version__)
    _box(" ")
    _box("Platform", sys.platform)
    _box("Python version", "{}.{}.{}".format(sys.version_info[0], sys.version_info[1], sys.version_info[2]))
    _box("Modbus mode", mode)
    _box("Baudrate (-b)", baudrate)
    _box("Port name (-D)", portname)
    _box("Slave address", SLAVE_ADDRESS)
    _box("Timeout", TIMEOUT)
    _box("Full file path", os.path.abspath(__file__))
    _box()
    _print_out("")


def show_current_values(instr):
    _box()
    _box("Current values")
    _box(" ")
    _box("Process value", instr.read_register(0x1000))
    _box("Setpoint", instr.read_register(0x1001, 1))
    _box("Sensor type", instr.read_register(0x1004))
    _box("Heating/cooling selection", instr.read_register(0x1006))
    _box("Output 1 value", instr.read_register(0x1012, 1))
    _box("Output 2 value", instr.read_register(0x1013, 1))
    _box("System alarm setting", instr.read_register(0x1023))
    _box("LED status", instr.read_register(0x102A))
    _box("Pushbutton status", instr.read_register(0x102B))
    _box("Firmware version", instr.read_register(0x102F))
    _box("LED AT", instr.read_bit(0x0800))
    _box("LED Out1", instr.read_bit(0x0801))
    _box("LED Out2", instr.read_bit(0x0802))
    _box("LED degF", instr.read_bit(0x0804))
    _box("LED degC", instr.read_bit(0x0805))
    _box("RUN/STOP setting", instr.read_bit(0x0814))
    _box()
    _print_out(" ")


def show_instrument_settings(instr):
    _print_out("Instrument settings:")
    _print_out(repr(instr).replace(",", ",\n"))
    _print_out(" ")


def verify_value_for_register(instr, value):
    # value should be an integer
    START_READ_ADDR = 0x1000
    ADDRESS_SETPOINT = 0x1001

    instr.write_register(ADDRESS_SETPOINT, value)
    assert value == instr.read_register(ADDRESS_SETPOINT)
    registers = instr.read_registers(START_READ_ADDR, 8)
    _print_out(registers)
    assert value == registers[ADDRESS_SETPOINT - START_READ_ADDR]


def verify_state_for_bits(instr, state):
    START_READ_ADDR = 0x800
    ADDR_UNITSELECTOR = 0x811
    ADDR_LED_F = 0x804
    ADDR_LED_C = 0x805

    instr.write_bit(ADDR_UNITSELECTOR, state)  # 1=deg C, 0=deg F
    bits = instr.read_bits(START_READ_ADDR, 24)
    _print_out(repr(bits))

    assert bits[ADDR_UNITSELECTOR - START_READ_ADDR] == state
    assert instr.read_bit(ADDR_UNITSELECTOR) == state

    assert bits[ADDR_LED_C - START_READ_ADDR] == state
    assert instr.read_bit(ADDR_LED_C) == state

    assert bits[ADDR_LED_F - START_READ_ADDR] != state
    assert instr.read_bit(ADDR_LED_F) != state


def verify_bits(instr):
    NUMBER_OF_LOOPS = 5

    _print_out("Verifying writing and reading bits")
    states = [0, 1] * NUMBER_OF_LOOPS
    for state in states:
        verify_state_for_bits(instr, state)
    _print_out("Passed test for writing and reading bits\n")


def verify_readonly_register(instr):
    ADDRESS_FIRMWARE_VERSION = 0x102F
    NEW_FIRMWARE_VERSION = 300

    _print_out("Verify detecting a READONLY register")
    did_report_error = False
    try:
        instr.write_register(ADDRESS_FIRMWARE_VERSION, NEW_FIRMWARE_VERSION)
    except minimalmodbus.SlaveReportedException:
        did_report_error = True

    if not did_report_error:
        raise ValueError("Failed to detect READONLY register")
    _print_out("Passed test for READONLY register\n")


def verify_register(instr):
    _print_out("Verify writing and reading a register")
    for value in range(250, 400, 10):  # Setpoint 25 to 40 deg C
        verify_value_for_register(instr, value)
    _print_out("Passed test for writing and reading a register\n")


def verify_two_instrument_instances(instr, portname, mode, baudrate):
    ADDRESS_SETPOINT = 0x1001

    _print_out("Verify using two instrument instances")
    instr2 = minimalmodbus.Instrument(portname, SLAVE_ADDRESS, mode=mode)
    instr2.serial.timeout = TIMEOUT

    instr.read_register(ADDRESS_SETPOINT)
    instr2.read_register(ADDRESS_SETPOINT)

    _print_out("... and verify port closure")
    instr.clear_buffers_before_each_transaction = False
    instr2.close_port_after_each_call = True
    instr.read_register(ADDRESS_SETPOINT)
    instr2.read_register(ADDRESS_SETPOINT)
    instr.read_register(ADDRESS_SETPOINT)
    instr2.read_register(ADDRESS_SETPOINT)
    _print_out("Passing test for using two instrument instances")


def measure_roundtrip_time(instr):
    ADDR_SETPOINT = 0x1001
    SECONDS_TO_MILLISECONDS = 1000
    NUMBER_OF_VALUES = 100
    START_VALUE = 200
    STOP_VALUE = 500
    STEPSIZE = 5

    _print_out("Measure request-response round trip time")
    _print_out("Setting the setpoint value {} times. Baudrate {} bits/s.".format(
        NUMBER_OF_VALUES, instr.serial.baudrate
    ))

    value = START_VALUE
    step = STEPSIZE
    start_time = time.time()
    for i in range(NUMBER_OF_VALUES):
        if value > STOP_VALUE or value < START_VALUE:
            step = -step
        value += step
        instr.write_register(ADDR_SETPOINT, value, functioncode=6)

    time_per_value = (
        (time.time() - start_time)
        * float(SECONDS_TO_MILLISECONDS)
        / NUMBER_OF_VALUES
    )
    _print_out("Time per value: {:0.1f} ms.\n".format(time_per_value))


def parse_commandline(argv):
    # Do manual parsing of command line,
    # as none of the modules in the standard library handles python 2.6 to 3.x

    mode = minimalmodbus.MODE_RTU
    baudrate = DEFAULT_BAUDRATE
    portname = DEFAULT_PORT_NAME

    for arg in argv:
        if arg.startswith("-ascii"):
            mode = minimalmodbus.MODE_ASCII

        elif arg.startswith("-rtu"):
            mode = minimalmodbus.MODE_RTU

        elif arg.startswith("-b"):
            if len(arg) < 3:
                _print_out("Wrong usage of the -b option. Use -b9600")
                sys.exit()
            baudrate = int(arg[2:])

        elif arg.startswith("-D"):
            if len(arg) < 3:
                _print_out(
                    "Wrong usage of the -D option. Use -D/dev/ttyUSB0 or -DCOM4"
                )
                sys.exit()
            portname = arg[2:]

    return portname, mode, baudrate


def main():
    portname, mode, baudrate = parse_commandline(sys.argv)
    show_test_settings(mode, baudrate, portname)

    inst = minimalmodbus.Instrument(portname, SLAVE_ADDRESS, mode=mode)
    inst.serial.timeout = TIMEOUT
    inst.serial.baudrate = baudrate

    show_instrument_settings(inst)
    show_current_values(inst)
    measure_roundtrip_time(inst)

    verify_register(inst)
    verify_readonly_register(inst)
    verify_bits(inst)
    verify_two_instrument_instances(inst, portname, mode, baudrate)
    _print_out(" ")
    _print_out("All tests did pass")


if __name__ == "__main__":
    main()