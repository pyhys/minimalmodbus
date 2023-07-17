"""Hardware testing of MinimalModbus using the Delta DTB temperature controller.

For use with Delta DTB4824VR.


Recommended test sequence
---------------------------

 * Run the tests under Linux, Windows and Mac OS
 * Use 2400 bps and 38400 bps
 * Use Modbus ASCII and Modbus RTU

 Sequence:

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

    # Adjust if necessary.
    instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1, debug=True)
    instrument.read_register(4143)  # Read firmware version (address in hex is 0x102F)
"""
import argparse
import os
import statistics
import sys
import time
from typing import Any, List, Optional, Tuple

import serial

sys.path.insert(0, "..")
import minimalmodbus  # noqa: E402

SLAVE_ADDRESS = 1
ADDRESS_SETPOINT = 0x1001
TIMEOUT = 0.3  # seconds. At least 0.3 seconds required for 2400 bits/s ASCII mode.
DEFAULT_PORT_NAME = "/dev/ttyUSB0"
DEFAULT_BAUDRATE = 38400  # baud (pretty much bit/s). Use 2400 or 38400 bit/s.


def _box(description: Optional[str] = None, value: Any = None) -> None:
    """Print a single line in a box."""
    MAX_WIDTH = 100
    DESCR_WIDTH = 30
    if description is None:
        print("#" * MAX_WIDTH)
    else:
        if value is None:
            line = "## {}".format(description)
        else:
            line = "## {}:".format(description).ljust(DESCR_WIDTH) + str(value)
        line = line.ljust(MAX_WIDTH - 2) + "##"
        print(line)


def show_test_settings(mode: str, baudrate: int, portname: str) -> None:
    _box()
    _box("Hardware test with Delta DTB4824")
    _box("Minimalmodbus version", minimalmodbus.__version__)
    _box("Minimalmodbus path", os.path.abspath(minimalmodbus.__file__))
    _box(" ")
    _box("Platform", sys.platform)
    _box(
        "Python version",
        "{}.{}.{}".format(
            sys.version_info[0], sys.version_info[1], sys.version_info[2]
        ),
    )
    _box("Modbus mode", mode)
    _box("Baudrate (-b)", baudrate)
    _box("Port name (-D)", portname)
    _box("Slave address", SLAVE_ADDRESS)
    _box("Timeout (s)", TIMEOUT)
    _box("Full file path", os.path.abspath(__file__))
    _box()
    print("")


def show_current_values(instr: minimalmodbus.Instrument) -> None:
    """Read current values via Modbus."""
    _box()
    _box("Current values")
    _box(" ")
    _box("Process value", instr.read_register(0x1000, 1))
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
    print(" ")


def show_instrument_settings(instr: minimalmodbus.Instrument) -> None:
    print("Instrument settings:")
    print(repr(instr).replace(",", ",\n"))
    print(" ")


def verify_value_for_register(instr: minimalmodbus.Instrument, value: int) -> None:
    """Write and read back a value to a register, and validate result.

    Also read back several registers.

    Args:
        * instr: Instrument instance
        * value: Value to be written
    """
    START_READ_ADDR = 0x1000
    NUMBER_OF_REGISTERS = 8
    assert NUMBER_OF_REGISTERS > ADDRESS_SETPOINT - START_READ_ADDR

    instr.write_register(ADDRESS_SETPOINT, value)
    assert value == instr.read_register(ADDRESS_SETPOINT)

    registers = instr.read_registers(START_READ_ADDR, NUMBER_OF_REGISTERS)
    print(registers)
    assert value == registers[ADDRESS_SETPOINT - START_READ_ADDR]


def verify_state_for_bits(instr: minimalmodbus.Instrument, state: int) -> None:
    """Write and read back a value to a bit, and validate result.

    Also read back several bits.

    Args:
        * instr: Instrument instance
        * state: Value to be written (0 or 1)
    """
    START_READ_ADDR = 0x800
    NUMBER_OF_BITS = 24
    ADDR_UNITSELECTOR = 0x811
    ADDR_LED_F = 0x804
    ADDR_LED_C = 0x805
    assert (
        NUMBER_OF_BITS
        > max(ADDR_UNITSELECTOR, ADDR_LED_F, ADDR_LED_C) - START_READ_ADDR
    )

    # Write and read selector for Celsius or Farenheit
    instr.write_bit(ADDR_UNITSELECTOR, state)  # 1=deg C, 0=deg F
    bits = instr.read_bits(START_READ_ADDR, NUMBER_OF_BITS)
    print(repr(bits))
    assert bits[ADDR_UNITSELECTOR - START_READ_ADDR] == state
    assert instr.read_bit(ADDR_UNITSELECTOR) == state

    # Read LED for Celcius
    assert bits[ADDR_LED_C - START_READ_ADDR] == state
    assert instr.read_bit(ADDR_LED_C) == state

    # Read LED for Farenheit
    assert bits[ADDR_LED_F - START_READ_ADDR] != state
    assert instr.read_bit(ADDR_LED_F) != state


def verify_bits(instr: minimalmodbus.Instrument) -> None:
    NUMBER_OF_LOOPS = 5

    print("Verifying writing and reading bits")
    print("Contents of 24 bit registers (18th column is temperature unit setting):")
    states = [0, 1] * NUMBER_OF_LOOPS
    for state in states:
        verify_state_for_bits(instr, state)
    print("Passed test for writing and reading bits\n")


def verify_readonly_register(instr: minimalmodbus.Instrument) -> None:
    """Verify that we detect the slave reported error when we write to an read-only
    register."""
    ADDRESS_FIRMWARE_VERSION = 0x102F
    NEW_FIRMWARE_VERSION = 300

    print("Verify detecting a READONLY register (detect slave error)")
    did_report_error = False
    try:
        instr.write_register(ADDRESS_FIRMWARE_VERSION, NEW_FIRMWARE_VERSION)
    except minimalmodbus.SlaveReportedException:
        did_report_error = True

    if not did_report_error:
        raise ValueError("Failed to detect READONLY register")
    print("Passed test for READONLY register\n")


def verify_register(instr: minimalmodbus.Instrument) -> None:
    print("Verify writing and reading a register (and reading several registers)")
    print("Contents of 8 registers (second column is setpoint register):")
    for value in range(250, 400, 10):  # Setpoint 25 to 40 deg C
        verify_value_for_register(instr, value)
    print("Passed test for writing and reading a register\n")


def verify_two_instrument_instances(
    instr: minimalmodbus.Instrument, portname: str, mode: str, baudrate: int
) -> None:
    print("Verify using two instrument instances")
    instr2 = minimalmodbus.Instrument(portname, SLAVE_ADDRESS, mode=mode)
    if instr2.serial is None:
        raise ValueError("Failed to instanciate instr2")
    instr2.serial.timeout = TIMEOUT

    instr.read_register(ADDRESS_SETPOINT)
    instr2.read_register(ADDRESS_SETPOINT)

    print("... and verify port closure")
    instr.clear_buffers_before_each_transaction = False
    instr2.close_port_after_each_call = True
    instr.read_register(ADDRESS_SETPOINT)
    instr2.read_register(ADDRESS_SETPOINT)
    instr.read_register(ADDRESS_SETPOINT)
    instr2.read_register(ADDRESS_SETPOINT)
    print("Passing test for using two instrument instances\n")


def verify_external_instrument_instance(
    portname: str, mode: str, baudrate: int
) -> None:
    print("Verify using external serial port instance")
    extserial = serial.Serial(
        port=portname,
        baudrate=baudrate,
        parity=serial.PARITY_NONE,
        bytesize=8,
        stopbits=1,
        timeout=TIMEOUT,
        write_timeout=2.0,
    )

    instr3 = minimalmodbus.Instrument(extserial, SLAVE_ADDRESS, mode=mode)
    print("Setpoint", instr3.read_register(ADDRESS_SETPOINT))
    print("Passing test for using external serial port instance\n")


def measure_roundtrip_time(instr: minimalmodbus.Instrument) -> None:
    ADDR_SETPOINT = 0x1001
    SECONDS_TO_MILLISECONDS = 1000
    NUMBER_OF_VALUES = 100
    START_VALUE = 200
    STOP_VALUE = 500
    STEPSIZE = 5
    instrument_roundtrip_measurements: List[float] = []

    print("Measure request-response round trip time")
    if instr.serial is None:
        raise ValueError("Instrument.serial is None")
    print(
        "Setting the setpoint value {} times. Baudrate {} bits/s.".format(
            NUMBER_OF_VALUES, instr.serial.baudrate
        )
    )

    value = START_VALUE
    step = STEPSIZE
    start_time = time.time()
    for i in range(NUMBER_OF_VALUES):
        if value > STOP_VALUE or value < START_VALUE:
            step = -step
        value += step
        instr.write_register(ADDR_SETPOINT, value, functioncode=6)
        assert isinstance(instr.roundtrip_time, float)
        instrument_roundtrip_measurements.append(instr.roundtrip_time)

    time_per_value = (
        (time.time() - start_time) * float(SECONDS_TO_MILLISECONDS) / NUMBER_OF_VALUES
    )
    print("Average measured time per loop: {:0.1f} ms.".format(time_per_value))
    print(
        "Instrument-reported round trip "
        + "time: Mean {:0.1f} ms  Min {:0.1f} ms  Max {:0.1f} ms\n".format(
            statistics.mean(instrument_roundtrip_measurements)
            * SECONDS_TO_MILLISECONDS,
            min(instrument_roundtrip_measurements) * SECONDS_TO_MILLISECONDS,
            max(instrument_roundtrip_measurements) * SECONDS_TO_MILLISECONDS,
        )
    )


def parse_commandline(argv: List[str]) -> Tuple[str, str, int]:
    parser = argparse.ArgumentParser(
        description="Run tests with a Delta DTB4824 instrument"
    )
    parser.add_argument("-a", action="store_true", help="Use ASCII mode")
    parser.add_argument(
        "-r", action="store_true", help="Use RTU mode (default). Overrides -a flag."
    )
    parser.add_argument(
        "-b",
        help="Baud rate. Defaults to %(default)s bit/s",
        default=DEFAULT_BAUDRATE,
        metavar="BAUD",
        type=int,
    )
    parser.add_argument(
        "-d",
        help='Device name. Defaults to "%(default)s"',
        default=DEFAULT_PORT_NAME,
        metavar="DEVICE",
        type=str,
    )
    arguments = parser.parse_args(args=argv[1:])

    mode = minimalmodbus.MODE_RTU
    if arguments.a and not arguments.r:
        mode = minimalmodbus.MODE_ASCII

    return arguments.d, mode, arguments.b


def main() -> None:
    portname, mode, baudrate = parse_commandline(sys.argv)
    show_test_settings(mode, baudrate, portname)

    inst = minimalmodbus.Instrument(portname, SLAVE_ADDRESS, mode=mode)
    if inst.serial is None:
        raise ValueError("Instrument.serial is None")

    inst.serial.timeout = TIMEOUT
    inst.serial.baudrate = baudrate

    show_instrument_settings(inst)
    show_current_values(inst)
    measure_roundtrip_time(inst)

    verify_register(inst)
    verify_readonly_register(inst)
    verify_bits(inst)
    verify_two_instrument_instances(inst, portname, mode, baudrate)
    verify_external_instrument_instance(portname, mode, baudrate)
    verify_readonly_register(inst)
    print(" ")
    print("All tests did pass")


if __name__ == "__main__":
    main()
