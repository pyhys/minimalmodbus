MinimalModbus
=============

Introduction
------------
MinimalModbus is an easy-to-use Python module for talking to instruments (slaves) from a computer (master) using the Modbus protocol. Example code includes drivers for Eurotherm process controllers. The only dependence is the pySerial module. This software supports the 'Modbus RTU' serial communication version of the protocol, and is intended for use on Linux and Windows platforms.

General on Modbus protocol
--------------------------
Modbus is a serial communications protocol published by Modicon in 1979, according to http://en.wikipedia.org/wiki/Modbus. It is often used to communicate with industrial electronic devices. 

There are several types of Modbus protocols:

Modbus RTU
    A serial protocol that uses binary representation of the data. **Supported by this software**.

Modbus ASCII
    A serial protocol that uses ASCII representation of the data. Not supported by this software.

Modbus TCP/IP and variants
    A protocol for communication over TCP/IP networks. Not supported by this software.

For full documentation on the Modbus protocol, see http://www.modbus.com/. One important document is 'MODBUS over serial line specification and implementation guide V1.02', found at http://www.modbus.com/docs/Modbus_over_serial_line_V1_02.pdf


Typical hardware
----------------
The application for which I wrote this software is to read and write data from Eurotherm process controllers. These come with different types of communication protocols, but the controllers I prefer use the Modbus RTU protocol. MinimalModbus is intended for general communication using the Modbus RTU protocol (using a serial link), so there should be lots of applications.

As an example on the usage of MinimialModbus, the driver I use for an Eurotherm 3504 process controller is included. It uses the MinimalModbus Python module for its communication.

There can be several instruments (slaves) on a single bus, and the slaves have addresses in the range 1 to 247. In the Modbus RTU protocol, only the master can initiate communication. The physical layer is most often the serial bus RS485, which is described at http://en.wikipedia.org/wiki/Rs485.

To connect your computer to the RS485 bus, a serial port is required. There are direct USB-to-RS485 converters, but I use a USB-to-RS232 converter together with an industrial RS232-to-RS485 converter. This has the advantage that the latter is galvanically isolated using opto-couplers, and has transient supression. This software has been tested using a Westermo MDW-45 RS232-to-RS485 converter.


Typical usage
-------------

The instrument is typically connected via a serial port, and a USB-to-serial adaptor should be used on most modern computers. How to configure such a serial port is described on the pySerial page: http://pyserial.sourceforge.net/

For example, consider an instrument(slave) with address number 1 to which we are to communicate via a serial port with the name ``/dev/ttyUSB1``. The instrument stores the measured temperature in register 289. For this instrument a temperature of 77.2 C is stored as 772, why we use 1 decimal. To read this data from the instrument::

    #!/usr/bin/env python
    import minimalmodbus

    instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1) # port name, slave address

    ## Read temperature (PV = ProcessValue) ##
    temperature = instrument.read_register( 289, 1 ) # Registernumber, number of decimals
    print temperature

    ## Change temperature setpoint (SP) ##
    NEW_TEMPERATURE = 95
    instrument.write_register(24, NEW_TEMPERATURE, 1) # Registernumber, value, number of decimals for storage

The full API for minimalmodbus is available on http://minimalmodbus.sourceforge.net/apiminimalmodbus.html, and the documentation in PDF format is found on http://minimalmodbus.sourceforge.net/minimalmodbus.pdf

Subclassing
-----------

It is better to put the details in a driver for the specific instrument. An example driver for Eurotherm3500 is included in this library, and it is recommended to have a look at its source code. To get the process value (PV from loop1)::

    #!/usr/bin/env python
    import eurotherm3500

    heatercontroller = eurotherm3500.Eurotherm3500('/dev/ttyUSB1', 1)  # port name, slave address

    ## Read temperature (PV) ##
    temperature = heatercontroller.get_pv_loop1()
    print temperature

    ## Change temperature setpoint (SP) ##
    NEW_TEMPERATURE = 95.0
    heatercontroller.set_sp_loop1(NEW_TEMPERATURE)

Default values
--------------
Most of the serial port parameters have the default values which are defined in the Modbus standard::

    instrument.serial.port          # this is the serial port name
    instrument.serial.baudrate = 19200   # Baud
    instrument.serial.parity   = serial.PARITY_NONE
    instrument.serial.bytesize = 8
    instrument.serial.stopbits = 1
    instrument.serial.timeout  = 0.05   # seconds

    instrument.address     # this is the slave address number

These can be overridden::
    
    instrument.serial.timeout = 0.2

For details on the allowed parity values, see http://pyserial.sourceforge.net/pyserial_api.html#serial.PARITY_NONE.


Dependencies
------------
This module relies on pySerial to do the heavy lifting, and it is the only dependency. You can find it at the Python package index: http://pypi.python.org/pypi/pyserial

Python version 2.6 and 2.7 have been used to develop this software, but it is **probably** compatible with Python 3 (according to the 2to3 tool).

Download and installation
-------------------------
From command line (if you have the *pip installer*, available at http://pypi.python.org/pypi/pip)::

   pip install minimalmodbus

or manually download the compressed source files from http://pypi.python.org/pypi/MinimalModbus/. There are compressed source files for Unix/Linux (.tar.gz) and Windows (.zip). Uncompress it, and run::

   python setup.py install

There is also a Windows installer (.win32.exe) available. Just start it and follow the instructions.


Licence
-------
Apache License, Version 2.0


Home page
---------
Home page with full API documentation 
    http://minimalmodbus.sourceforge.net/ (this page if viewed on sourceforge.net).

Python package index
    http://pypi.python.org/pypi/MinimalModbus/ (this page if viewed on python.org. Note that no API is available).

The SourceForge project page
    http://sourceforge.net/projects/minimalmodbus/ with bug tracker, mailing list and subversion repository ( http://minimalmodbus.svn.sourceforge.net/viewvc/minimalmodbus/trunk/ ).


Author
------
Jonas Berg, pyhys@users.sourceforge.net

Related software
----------------
The MinimalModbus module is intended for easy-to-use communication with instruments using the Modbus (RTU) protocol. There are a few other Python modules for Modbus protocol implementation. For more advanced use, you should consider using one of these:

pyModbus 
    From http://code.google.com/p/pymodbus/: 'Pymodbus is a full Modbus protocol implementation using twisted for its asynchronous communications core.'

modbus-tk
    From the page http://code.google.com/p/modbus-tk/: 'Make possible to write modbus TCP and RTU master and slave mainly for testing purpose. It is shipped with slave simulator and a master with a web-based hmi. It is a full-stack implementation and as a consequence could also be used on real-world project. '


References
----------
* Python: http://www.python.org/


Text revision
-------------
This README file was changed (committed) at $Date$, which was $Revision$.

