MinimalModbus
=============

Introduction
------------
An easy-to-use Python module for talking to instruments (slaves) from a computer (master) using the Modbus protocol. Example code includes drivers for Eurotherm process controllers. The only dependence is the pySerial module.

Modbus RTU serial communication.


General on Modbus protocol
--------------------------
http://en.wikipedia.org/wiki/Modbus
There are several types of modbus protocols:

  * Modbus RTU
  * Modbus ??


Typical hardware
----------------
The application for which I wrote this software is to read and write data for Eurotherm process controllers. These come with different types of communication protocols, but the ones I prefare use Modbus RTU protocol. This software is intended for communication using the Modbus RTU protocol using a serial link, so there should be lots of applications.

As an example usage, the driver I use for an Eurotherm 3504 process controller is included. It uses the minimalmodbus Python module for its communication.

http://en.wikipedia.org/wiki/Rs485

RS232
RS485

USB-to-RS485 converter


several instruments (slaves) on a bus, and the slaves have addresses 1 to 247 ???.



USB-to-RS232 converter and an industrial RS232-to-RS485 converter. This has the advantage that the latter is galvanically isolated using opto-couplers,and has transient supression. This software has been tested using a Westermo MDW-45 RS232-to-RS485 converter.


Typical usage
-------------

The instrument is typically connected via a serial port, and a USB-to-serial adaptor should be used on most modern PCs. How to configure such a port is described on the pySerial page: http://pyserial.sourceforge.net/

For example, consider an instrument(slave) with address number 1 to which we are to communicate via port /dev/ttyUSB1 . The instrument stores the measured temperature in register 289. For this instrument a temperature of 77.2 C is stored as 772, why we use 1 decimal. To read this data from the instrument::

    #!/usr/bin/env python
    import minimalmodbus

    instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1) # port name, slave address

    ## Read temperature (PV) ##
    temperature = instrument.read_register( 289, 1 ) # Registernumber, number of decimals
    print temperature

    ## Change temperature setpoint (SP) ##
    NEW_TEMPERATURE = 95.0
    instrument.write_register(24, NEW_TEMPERATURE, 1) # Registernumber, value, number of decimals

The full API for minimalmodbus is available on INSERT!!!

It is better to put this in a driver for the specific instrument. An example driver for Eurotherm3500 is included in this library. To get the process value (PV from loop1)::

    #!/usr/bin/env python
    import eurotherm3500

    heatercontroller = eurotherm3500.Eurotherm3500('/dev/ttyUSB1', 1)  # port name, slave address

    ## Read temperature (PV) ##
    temperature = heatercontroller.get_pv_loop1()
    print temperature

    ## Change temperature setpoint (SP) ##
    NEW_TEMPERATURE = 95.0
    heatercontroller.set_sp_loop1(NEW_TEMPERATURE)


Serial port parameters default values

instrument.baudrate = 19200 # Baud
instrument.timeout = 0.05 # seconds
instrument.parity = serial.PARITY_NONE
instrument.bytesize = 8
instrument.stopbits = 1
instrument.address # this is the slave address number
instrument.portname # this is the port name

CHANGE THIS
NOTE:    instrument.portname was .port



Dependencies
------------
This module relies on pySerial to do the heavy lifting, and it is the only dependency. You can find it at the Python package index: http://pypi.python.org/pypi/pyserial

Download and installation
-------------------------
From command line (if you have the *pip installer*, available at http://pypi.python.org/pypi/pip)::

   pip install minimalmodbus

or manually download the compressed source file from http://pypi.python.org/pypi/MinimalModbus/ . There are compressed source files for Unix/Linux (.tar.gz) and Windows (.zip). Uncompress it and run::

   python setup.py install

There is also a Windows installer (.win32.exe) available. Just start it and follow the instructions.


Licence
-------
Apache License, Version 2.0


Home page
---------
Home page with full API documentation http://minimalmodbus.sourceforge.net/ (this page if viewed on sourceforge.net).

Python package index: http://pypi.python.org/pypi/MinimalModbus/ (this page if viewed on python.org. Note that no API is available).

The SourceForge project page: http://sourceforge.net/projects/minimalmodbus/ with Subversion repository, bug tracker and mailing list.


Author
------
Jonas Berg, pyhys@users.sourceforge.net

Related software
----------------
The minimalmodbus module is intended for easy-to-use communication with instruments using the Modbus (RTU) protocol. There are a few other Python modules for Modbus protocol implementation. For more advanced use, you should consider using one of these:

 - **pyModbus** From the page http://code.google.com/p/pymodbus/ : 'Pymodbus is a full Modbus protocol implementation using twisted for its asynchronous communications core.'
 - **modbus-tk** From the page http://code.google.com/p/modbus-tk/ : 'Make possible to write modbus TCP and RTU master and slave mainly for testing purpose. It is shipped with slave simulator and a master with a web-based hmi. It is a full-stack implementation and as a consequence could also be used on real-world project. '





