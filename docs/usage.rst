.. _usage:

========
Usage
========


General on Modbus protocol
--------------------------
Modbus is a serial communications protocol published by Modicon in 1979,
according to https://en.wikipedia.org/wiki/Modbus.
It is often used to communicate with industrial electronic devices.

There are several types of Modbus protocols:

Modbus RTU
    A serial protocol that uses binary representation of the data. **Supported by this software**.

Modbus ASCII
    A serial protocol that uses ASCII representation of the data. **Supported by this software**.

Modbus TCP, and variants
    A protocol for communication over TCP/IP networks. Not supported by this software.

For full documentation on the Modbus protocol, see `www.modbus.com <http://www.modbus.com/>`_.

Two important documents are:

  * `Modbus application protocol V1.1b <http://www.modbus.com/docs/Modbus_Application_Protocol_V1_1b.pdf>`_
  * `Modbus over serial line specification and implementation guide V1.02 <http://www.modbus.com/docs/Modbus_over_serial_line_V1_02.pdf>`_

Note that the computer (master) actually is a client, and the instruments (slaves) are servers.


Typical hardware
----------------
The application for which I wrote this software is to read and write data
from Eurotherm process controllers.
These come with different types of communication protocols,
but the controllers I prefer use the Modbus RTU protocol.
MinimalModbus is intended for general communication using the Modbus RTU protocol
(using a serial link), so there should be lots of applications.

There can be several instruments (slaves, nodes) on a single bus,
and the slaves have addresses in the range 1 to 247. In the Modbus RTU protocol,
only the master can initiate communication. The physical layer is most often
the serial bus RS485, which is described at https://en.wikipedia.org/wiki/RS-485.

To connect your computer to the RS485 bus, a serial port is required.
There are direct USB-to-RS485 converters, but I use a USB-to-RS232 converter
together with an industrial RS232-to-RS485 converter (Westermo MDW-45). This has the advantage that
the latter is galvanically isolated using opto-couplers, and has transient supression.


Typical usage
-------------
The instrument is typically connected via a serial port, and a USB-to-serial
adaptor should be used on most modern computers. How to configure such a serial
port is described on the pySerial page: https://pythonhosted.org/pyserial/

For example, consider an instrument (slave) with Modbus RTU mode and address number 1
to which we are to communicate via a serial port with the name
``/dev/ttyUSB1``. The instrument stores the measured temperature in register 289.
For this instrument a temperature of 77.2 C is stored as (the integer) 772,
why we use 1 decimal. To read this data from the instrument::

    #!/usr/bin/env python3
    import minimalmodbus

    instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1)  # port name, slave address (in decimal)

    ## Read temperature (PV = ProcessValue) ##
    temperature = instrument.read_register(289, 1)  # Registernumber, number of decimals
    print(temperature)

    ## Change temperature setpoint (SP) ##
    NEW_TEMPERATURE = 95
    instrument.write_register(24, NEW_TEMPERATURE, 1)  # Registernumber, value, number of decimals for storage

The valid slave address range for normal usage is 1 to 247.

The full API for MinimalModbus is available in :ref:`apiminimalmodbus`.

Correspondingly for Modbus ASCII mode::

    instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1, minimalmodbus.MODE_ASCII)


More on the usage of MinimalModbus is found in :ref:`detailedusage`.


Default values
--------------
Most of the serial port parameters have the default values defined in the Modbus standard (19200 8N1)::

    instrument.serial.port                     # this is the serial port name
    instrument.serial.baudrate = 19200         # Baud
    instrument.serial.bytesize = 8
    instrument.serial.parity   = serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout  = 0.05          # seconds

    instrument.address                         # this is the slave address number
    instrument.mode = minimalmodbus.MODE_RTU   # rtu or ascii mode
    instrument.clear_buffers_before_each_transaction = True

Change the values like this::

    instrument.serial.timeout = 0.2

To see which settings you actually are using::

    print(instrument)

For details on the allowed parity values, see
https://pyserial.readthedocs.io/en/latest/pyserial_api.html#constants

To change the parity setting, use::

    import serial
    instrument.serial.parity = serial.PARITY_EVEN

or alternatively (to avoid import of ``serial``)::

    instrument.serial.parity = minimalmodbus.serial.PARITY_EVEN

.. warning:: The module level constants minimalmodbus.BAUDRATE etc were removed in version 1.0


Confusing Modbus register addresses
-----------------------------------
Sometimes "entity numbers" are used in documentation for Modbus instruments. These
numbers are typically five or six digits long, and contains info about both
the register type and the register address. The first digit describes the register type,
for example 4 is a holding register. The rest of the digits describes the address plus one
(yes, very confusing).

According to the example on https://en.wikipedia.org/wiki/Modbus, an entity number of
40100 describes a holding register with address 99.

More details on different types of Modbus registers are found in :ref:`modbusdetails`.


Using multiple instruments
--------------------------
Use a single script for talking to all your instruments (if connected via the
same serial port). Create several instrument objects like::

    instrumentA = minimalmodbus.Instrument('/dev/ttyUSB1', 1)
    instrumentA.serial.baudrate = 9600
    instrumentA.serial.timeout = 0.2
    instrumentA.mode = minimalmodbus.MODE_RTU

    instrumentB = minimalmodbus.Instrument('/dev/ttyUSB1', 2)
    instrumentB.mode = minimalmodbus.MODE_ASCII

    instrumentC = minimalmodbus.Instrument('/dev/ttyUSB2', 1)

The instruments sharing the same serial port share the same ``serial`` Python object, so
``instrumentB`` will have the same baudrate and timeout as ``instrumentA``.

You can use instruments on different serial ports in the same script, but
running several scripts using the same port will give problems.


Closing serial port after each call
-----------------------------------

In some cases (mostly on Windows) the serial port must be closed after each call.

Enable that behavior with::

    instrument.close_port_after_each_call = True

This will slow down the port considerably.


Handling communication errors
-----------------------------
Your top-level code should be able to handle communication errors.
Glitches in the serial communication might happen now and then.

Instead of running::

    print(instrument.read_register(4143))

Use::

    try:
        print(instrument.read_register(4143))
    except IOError:
        print("Failed to read from instrument")

Different types of errors should be handled separately.

Errors related to wrong argument to functions raises TypeError or ValueError.
When there is communication problems etc the exceptions raised are ModbusException
(with subclasses) and serial.serialutil.SerialException, which both are inheriting
from IOError.

Note that in Python3 the IOError is an alias for OSError.


Byte order for floating point values and long integers
------------------------------------------------------
The byte order used by manufacturers differ. See See :ref:`byteorder`.


Subclassing
-----------

It is better to put the details on registers etc in a driver for the specific instrument.
See :ref:`specificdrivers`.


Extending
---------

It is pretty easy to extend this module to support other functioncodes or special
cases. See :ref:`extending`.

