MinimalModbus
=============

Introduction
------------
MinimalModbus is an easy-to-use Python module for talking to instruments (slaves) 
from a computer (master) using the Modbus protocol, and is intended to be running on the master. 
Example code includes drivers for Eurotherm and Omega process controllers. 
The only dependence is the pySerial module (also pure Python). 

This software supports the 'Modbus RTU' and 'Modbus ASCII' serial communication versions of the protocol, 
and is intended for use on Linux, OS X and Windows platforms. 
It is open source, and has the Apache License, Version 2.0. 
Tested with Python2.7 and Python3.2.


Home page
---------
Home page with full API documentation 
    http://minimalmodbus.sourceforge.net/ (this page if viewed on sourceforge.net).

Python package index (PyPI) with download 
    http://pypi.python.org/pypi/MinimalModbus/ (this page if viewed on python.org. 
    Note that no API is available). The  download section is at the end of the page.

The SourceForge project page
    http://sourceforge.net/projects/minimalmodbus/ with mailing list and 
    subversion repository ( http://sourceforge.net/p/minimalmodbus/code/ ).


General on Modbus protocol
--------------------------
Modbus is a serial communications protocol published by Modicon in 1979, 
according to http://en.wikipedia.org/wiki/Modbus. 
It is often used to communicate with industrial electronic devices. 

There are several types of Modbus protocols:

Modbus RTU
    A serial protocol that uses binary representation of the data. **Supported by this software**.

Modbus ASCII
    A serial protocol that uses ASCII representation of the data. **Supported by this software**.

Modbus TCP, and variants
    A protocol for communication over TCP/IP networks. Not supported by this software, consider donating some Modbus TCP equipment.

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

As an example on the usage of MinimialModbus, the driver I use for an 
Eurotherm 3504 process controller is included. It uses the MinimalModbus Python module 
for its communication. Also a driver for Omega CN7500 is included. 
For hardware details on these process controllers, see 
`Eurotherm 3500 <http://www.eurotherm.com/products/controllers/multi-loop/>`_ and 
`Omega CN7500 <http://www.omega.com/pptst/CN7500.html>`_.

There can be several instruments (slaves, nodes) on a single bus, 
and the slaves have addresses in the range 1 to 247. In the Modbus RTU protocol, 
only the master can initiate communication. The physical layer is most often 
the serial bus RS485, which is described at http://en.wikipedia.org/wiki/Rs485.

To connect your computer to the RS485 bus, a serial port is required. 
There are direct USB-to-RS485 converters, but I use a USB-to-RS232 converter 
together with an industrial RS232-to-RS485 converter (Westermo MDW-45). This has the advantage that 
the latter is galvanically isolated using opto-couplers, and has transient supression. 


Typical usage
-------------
The instrument is typically connected via a serial port, and a USB-to-serial 
adaptor should be used on most modern computers. How to configure such a serial 
port is described on the pySerial page: http://pyserial.sourceforge.net/

For example, consider an instrument (slave) with Modbus RTU mode and address number 1 
to which we are to communicate via a serial port with the name 
``/dev/ttyUSB1``. The instrument stores the measured temperature in register 289. 
For this instrument a temperature of 77.2 C is stored as (the integer) 772, 
why we use 1 decimal. To read this data from the instrument::

    #!/usr/bin/env python
    import minimalmodbus

    instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1) # port name, slave address (in decimal)

    ## Read temperature (PV = ProcessValue) ##
    temperature = instrument.read_register(289, 1) # Registernumber, number of decimals
    print temperature

    ## Change temperature setpoint (SP) ##
    NEW_TEMPERATURE = 95
    instrument.write_register(24, NEW_TEMPERATURE, 1) # Registernumber, value, number of decimals for storage

The full API for MinimalModbus is available on http://minimalmodbus.sourceforge.net/apiminimalmodbus.html, and the 
documentation in PDF format is found on http://minimalmodbus.sourceforge.net/minimalmodbus.pdf

Correspondingly for Modbus ASCII mode::

    instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1, minimalmodbus.MODE_ASCII)


Subclassing
-----------
It is better to put the details in a driver for the specific instrument. 
An example driver for Eurotherm3500 is included in this library, 
and it is recommended to have a look at its source code. 
To get the process value (PV from loop1)::

    #!/usr/bin/env python
    import eurotherm3500

    heatercontroller = eurotherm3500.Eurotherm3500('/dev/ttyUSB1', 1)  # port name, slave address

    ## Read temperature (PV) ##
    temperature = heatercontroller.get_pv_loop1()
    print temperature

    ## Change temperature setpoint (SP) ##
    NEW_TEMPERATURE = 95.0
    heatercontroller.set_sp_loop1(NEW_TEMPERATURE)

Correspondingly, to use the driver for Omega CN7500::

    #!/usr/bin/env python 
    import omegacn7500

    instrument = omegacn7500.OmegaCN7500('/dev/ttyUSB1', 1) # port name, slave address
    
    print instrument.get_pv() # print temperature

More on the usage of MinimalModbus is found on http://minimalmodbus.sourceforge.net/usage.html


Default values
--------------
Most of the serial port parameters have the default values defined in the Modbus standard (19200 8N1)::

    instrument.serial.port          # this is the serial port name
    instrument.serial.baudrate = 19200   # Baud
    instrument.serial.bytesize = 8
    instrument.serial.parity   = serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout  = 0.05   # seconds

    instrument.address     # this is the slave address number
    instrument.mode = minimalmodbus.MODE_RTU   # rtu or ascii mode

These can be overridden::
    
    instrument.serial.timeout = 0.2
    
To see which settings you actually are using::

    print instrument     

For details on the allowed parity values, see http://pyserial.sourceforge.net/pyserial_api.html#constants 

To change the parity setting, use::

    import serial
    instrument.serial.parity = serial.PARITY_EVEN

or alternatively (to avoid import of ``serial``)::

    instrument.serial.parity = minimalmodbus.serial.PARITY_EVEN


Dependencies
------------
Python versions 2.7 and higher are supported (including 3.x). 
Tested with Python2.7 and Python3.2. This module is pure Python.

This module relies on `pySerial <http://pyserial.sourceforge.net/>`_ (also pure Python) 
to do the heavy lifting, and it is the only dependency. 
You can find it at the Python package index: http://pypi.python.org/pypi/pyserial


Download and installation
-------------------------
From command line (if you have the *pip installer*, available at http://pypi.python.org/pypi/pip)::

   pip install -U minimalmodbus
   
or possibly::

   sudo pip install -U pyserial
   sudo pip install -U minimalmodbus

You can also manually download the compressed source files from 
http://pypi.python.org/pypi/MinimalModbus/ (see the end of that page). 
In that case you first need to manually install pySerial from http://pypi.python.org/pypi/pyserial.

There are compressed source files for Unix/Linux (.tar.gz) and Windows (.zip). 
To install a manually downloaded file, uncompress it and run (from within the directory)::

   python setup.py install

or possibly::

   sudo python setup.py install

If using Python 3, then install with::

   sudo python3 setup.py install

There is also a Windows installer (.exe) available. Just start it and follow the instructions.

For Python3 there might be problems with *easy_install* and *pip*. 
In that case, first manually install pySerial and then manually install MinimalModbus.

To make sure it is installed properly, print the _getDiagnosticString() message. 
See the support section below for instructions.

You can also download the source directly from Linux command line::

    wget http://downloads.sourceforge.net/project/minimalmodbus/0.5/MinimalModbus-0.5.tar.gz
    wget https://pypi.python.org/packages/source/M/MinimalModbus/MinimalModbus-0.5.tar.gz

Change version number to the appropriate value.

Modbus data types
-----------------
The Modbus standard defines storage in:

* Bits
* Registers (16-bit). Can hold integers in the range 0 to 65535 (dec), which is 0 to ffff (hex). Also called 'unsigned INT16' or 'unsigned short'.

Some deviations from the official standard:

**Scaling of register values**
    Some manufacturers store a temperature value of 77.0 C as 770 in the register, to allow room for one decimal.

**Negative numbers (INT16 = short)**
    Some manufacturers allow negative values for some registers. Instead of an allowed integer range 0-65535, a range -32768 to 32767 is allowed. This is implemented as any received value in the upper range (32768-65535) is interpreted as negative value (in the range -32768 to -1). This is two's complement and is described at http://en.wikipedia.org/wiki/Two%27s_complement. Help functions to calculate the two's complement value (and back) are provided in MinimalModbus.
    
**Long integers ('Unsigned INT32' or 'INT32')**
    These require 32 bits, and are implemented as two consecutive 16-bit registers. The range is 0 to 4294967295, which is called 'unsigned INT32'. Alternatively negative values can be stored if the instrument is defined that way, and is then called 'INT32' which has the range -2147483648 to 2147483647.
    
**Floats (single or double precision)**
    Single precision floating point values (binary32) are defined by 32 bits (4 bytes), and are implemented as two consecutive 16-bit registers. Correspondingly, double precision floating point values (binary64) use 64 bits (8 bytes) and are implemented as four consecutive 16-bit registers. How to convert from the bit values to the floating point value is described in the standard IEEE 754, as seen in http://en.wikipedia.org/wiki/Floating_point. Unfortunately the byte order might differ between manufacturers of Modbus instruments.    
    
**Strings**
    Each register (16 bits) is interpreted as two characters (each 1 byte = 8 bits). Often 16 consecutive registers are used, allowing 32 characters in the string. 

**8-bit registers**
    For example Danfoss use 8-bit registers for storage of some settings internally in the instruments. The data is nevertherless transmitted as 16 bit over the serial link, so you can read and write like normal (but with values limited to the range 0-255).
    

Implemented functions
---------------------
These are the functions to use for reading and writing registers and bits of your instrument. Study the 
documentation of your instrument to find which Modbus function code to use. The function codes are 
given in decimal in this table.

+---------------------------------------+------------------+---------------+-------------------+---------------+
| Data type in slave                    | Read             | Function code | Write             | Function code |
+=======================================+==================+===============+===================+===============+
| **Bit**                               | read_bit()       | 2 [or 1]      | write_bit()       | 5 [or 15]     |
+---------------------------------------+------------------+---------------+-------------------+---------------+
| **Register** Integer, possibly scaled | read_register()  | 3 [or 4]      | write_register()  | 16 [or 6]     |
+---------------------------------------+------------------+---------------+-------------------+---------------+
| **Long** (32 bits = 2 registers)      | read_long()      | 3 [or 4]      | write_long()      | 16            |
+---------------------------------------+------------------+---------------+-------------------+---------------+
| **Float** (32 or 64 bits)             | read_float()     | 3 [or 4]      | write_float()     | 16            |
+---------------------------------------+------------------+---------------+-------------------+---------------+
| **String**                            | read_string()    | 3 [or 4]      | write_string()    | 16            |
+---------------------------------------+------------------+---------------+-------------------+---------------+
| **Registers** Integers                | read_registers() | 3 [or 4]      | write_registers() | 16            |
+---------------------------------------+------------------+---------------+-------------------+---------------+

See the API for MinimalModbus on http://minimalmodbus.sourceforge.net/apiminimalmodbus.html


Using multiple instruments
--------------------------
Use a single script for talking to all your instruments. Create several instrument objects like::

    instrumentA = minimalmodbus.Instrument('/dev/ttyUSB1', 1)
    instrumentB = minimalmodbus.Instrument('/dev/ttyUSB1', 2)

Running several scripts using the same port will give problems. 


Issues when running under Windows
---------------------------------
Since MinimalModbus version 0.5, the handling of several instruments on the same
serial port has been improved for Windows.

It should no longer be necessary to use ````minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True```` 
when running on Windows, as this now is handled in a better way internally. 
This gives a significantly increased communication speed.

If the underlying pySerial complains that the serial port is already open, 
it is still possible to make MinimalModbus close the serial port after each call. Use it like::

    #!/usr/bin/env python
    import minimalmodbus
    minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
    
    instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1) # port name, slave address (in decimal)
    print instrument.read_register(289, 1) 

    
Modbus implementation details
-----------------------------
In Modbus RTU, the request message is sent from the master in this format::
    
    Slave address [1 Byte], Function code [1 Byte], Payload data [0 to 252 Bytes], CRC [2 Bytes].

* For the function code, the allowed range is 1 to 127 (in decimal). 
* The CRC is a cyclic redundancy check code, for error checking of the message. 
* The response from the client is similar, but with other payload data.

============================== ============================================================================================== ======================================================
Function code (in decimal)     Payload data to slave (Request)                                                                Payload data from slave (Response)                  
============================== ============================================================================================== ====================================================== 
1 Read bits (coils)            Start address [2 Bytes], Number of coils [2 Bytes]                                             Byte count [1 Byte], Value [k Bytes] 
2 Read discrete inputs         Start address [2 Bytes], Number of inputs [2 Bytes]                                            Byte count [1 Byte], Value [k Bytes]         
3 Read holding registers       Start address [2 Bytes], Number of registers [2 Bytes]                                         Byte count [1 Byte], Value [n*2 Bytes]
4 Read input registers         Start address [2 Bytes], Number of registers [2 Bytes]                                         Byte count [1 Byte], Value [n*2 Bytes]
5 Write single bit (coil)      Output address [2 Bytes], Value [2 Bytes]                                                      Output address [2 Bytes], Value [2 Bytes]           
6 Write single register        Register address [2 Bytes], Value [2 Bytes]                                                    Register address [2 Bytes], Value [2 Bytes] 
15 Write multiple bits (coils) Start address [2 Bytes], Number of outputs [2 Bytes], Byte count [1 Byte], Value [k Bytes]     Start address [2 Bytes], Number of outputs [2 Bytes]
16 Write multiple registers    Start address [2 Bytes], Number of registers [2 Bytes], Byte count [1 Byte], Value [n*2 Bytes] Start address [2 Bytes], Number of registers [2 Bytes]
============================== ============================================================================================== ====================================================== 

For function code 5, the only valid values are 0000 (hex) or FF00 (hex), representing OFF and ON respectively.

It is seen in the table above that the request and response messages are similar for function code 1 to 4. The same 
can be said about function code 5 and 6, and also about 15 and 16. 

For finding how the k Bytes for the value relates to the number of registers etc (n), see the Modbus documents referred to above.
    
    
Debug mode
----------
To switch on the debug mode, where the communication details are printed::

    #!/usr/bin/env python
    import minimalmodbus

    instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1) # port name, slave address (in decimal)
    instrument.debug = True
    print instrument.read_register(289, 1)  # Remember to use print() for Python3

With this you can easily see what is sent to and from your instrument, and immediately see what is wrong. 
This is very useful also if developing your own Modbus compatible electronic instruments.

Similar in interactive mode::

    >>> instrument.read_register(4097,1)
    MinimalModbus debug mode. Writing to instrument: '\n\x03\x10\x01\x00\x01\xd0q'
    MinimalModbus debug mode. Response from instrument: '\n\x03\x02\x07\xd0\x1e)'
    200.0

The data is stored internally in this driver as byte strings (representing byte values). 
For example a byte with value 18 (dec) = 12 (hex) = 00010010 (bin) is stored in a string of length one.
This can be created using the function ``chr(18)``, or by simply typing the 
string ``'\x12'`` (which is a string of length 1). See 
http://docs.python.org/reference/lexical_analysis.html#string-literals for details on escape sequences.

For more information about hexadecimal numbers, see http://en.wikipedia.org/wiki/Hexadecimal.

Note that the letter A has the hexadecimal ASCII code 41, why the string ``'\x41'`` prints ``'A'``. 
The Latin-1 encoding is used (on most installations?), and the conversion table is found on 
http://en.wikipedia.org/wiki/Latin_1.

The byte strings can look pretty strange when printed, as values 0 to 31 (dec) are
ASCII control signs (not corresponding to any letter). For example 'vertical tab' 
and 'line feed' are among those. To make the output easier to understand, print the representation, ``repr()``. Use::

    print repr(bytestringname)

Registers are 16 bit wide (2 bytes), and the data is sent with the most 
significant byte (MSB) before the least significant byte (LSB). This is 
called big-endian byte order. To find the register data value, multiply the 
MSB by 256 (dec) and add the LSB.

Error checking is done using CRC (cyclic redundancy check), and the result is two bytes.

Example
````````
We use this example in debug mode. It reads one register (number 5) and 
interpret the data as having 1 decimal. The slave has address 1 (as set 
when creating the ``instrument`` instance), and we are using MODBUS 
function code 3 (the default value for ``read_register()``)::

    >>> instrument.read_register(5,1)
    
This will be displayed::

    MinimalModbus debug mode. Writing to instrument: '\x01\x03\x00\x05\x00\x01\x94\x0b'

In the section 'Modbus implementation details' above, the request message 
structure is described. See the table entry for function code 3.

Interpret the request message (8 bytes) as:

========= ==== ==== ============
Displayed  Hex  Dec  Description
========= ==== ==== ============
``\x01``  01   1    Slave address (here 1)
``\x03``  03   3    Function code (here 3 = read registers)
``\x00``  00   0    Start address MSB
``\x05``  05   5    Start address LSB
``\x00``  00   0    Number of registers MSB
``\x01``  01   1    Number of registers LSB
``\x94``  94   148  CRC LSB
``\x0b``  0b   11   CRC MSB
========= ==== ==== ============

So the data in the request is:
  * Start address: 0*256 + 5 = 5 (dec)
  * Number of registers: 0*256 + 1 = 1 (dec)

The response will be displayed as::

    MinimalModbus debug mode. Response from instrument: '\x01\x03\x02\x00º9÷'

Interpret the response message (7 bytes) as:

========= ==== ==== ============
Displayed  Hex  Dec  Description
========= ==== ==== ============
``\x01``  01   1    Slave address (here 1)
``\x03``  03   3    Function code (here 3 = read registers)
``\x02``  02   2    Byte count
``\x00``  00   0    Value MSB
``º``     ba   186  Value LSB
``9``     37   57   CRC LSB
``÷``     f7   247  CRC MSB
========= ==== ==== ============

Out of the response, this is the payload part: ``\x02\x00º`` (3 bytes)

So the data in the request is:
  * Byte count: 2 (dec)
  * Register value: 0*256 + 186 = 186 (dec)

We know since earlier that this instrument stores a temperature of 18.6 C as 186. 
We provide this information as the second argument in the function call ``read_register(5,1)``, 
why it automatically divides the register data by 10 and returns ``18.6``.


Special characters
``````````````````
Some ASCII control characters have representations like ``\n``, 
and their meanings are described in this table:

=================== ================= =============== =============== ======================
``repr()`` shows as Can be written as ASCII hex value ASCII dec value Description
=================== ================= =============== =============== ======================
``\t``              ``\x09``           09              9               Horizontal Tab (TAB)
``\n``              ``\x0a``           0a              10              Linefeed (LF)
``\r``              ``\x0d``           0d              13              Carriage Return (CR)
=================== ================= =============== =============== ======================

It is also possible to write for example ASCII Bell (BEL, hex = 07, dec = 7) 
as ``\a``, but its ``repr()`` will still print ``\x07``.

More about ASCII control characters is found on http://en.wikipedia.org/wiki/ASCII.

Timing of the serial communications
-----------------------------------
The Modbus RTU standard prescribes a silent period corresponding to 3.5 characters 
between each message, to be able fo figure out where one message ends and the 
next one starts.

The silent period after the message to the slave is the responsibility of the slave.

The silent period after the message from the slave has previously been 
implemented in MinimalModbus by setting a generous timeout value, and let the 
serial ``read()`` function wait for timeout.

The character time corresponds to 11 bit times, according to http://www.automation.com/library/articles-white-papers/fieldbus-serial-bus-io-networks/introduction-to-modbus.

========== ============== ========== =============== ======================
Baud rate  Bit rate       Bit time   Character time  3.5 character times
========== ============== ========== =============== ======================
2400       2400 bits/s    417 us     4.6 ms          16 ms
4800       4800 bits/s    208 us     2.3 ms          8.0 ms
9600       9600 bits/s    104 us     1.2 ms          4.0 ms
19200      19200 bits/s   52 us      573 us          2.0 ms
38400      38400 bits/s   26 us      286 us          1.0 ms
115200     115200 bit/s   8.7 us     95 us           0.33 ms
========== ============== ========== =============== ======================

RS-485 introduction
-------------------
Several nodes (instruments) can be connected to one RS485 bus. The bus consists of two lines, 
A and B, carrying differential voltages. In both ends of the bus, 
a 120 Ohm termination resistor is connected between line A and B. 
Most often a common ground line is connected between the nodes as well.

At idle, both line A and B rest at the same voltage (or almost the same voltage). 
When a logic 1 is transmitted, line A is pulled towards lower voltage and 
line B is pulled towards higher voltage. 
Note that the A/B nameing is sometimes mixed up by some manufacturers.

Each node uses a transceiver chip, containing a transmitter (sender) and a receiver. 
Only one transmitter can be active on the bus simultaneously. 

Pins on the RS485 bus side of the transceiver chip:

* A: inverting line
* B: non-inverting line
* GND

Pins on the microcontroller side of the transceiver chip:

* TX: Data to be transmitted
* TXENABLE: For enabling/disabling the transmitter
* RX: Received data
* RXENABLE: For enabling/disabling the receiver

If the receiver is enabled simultaneusly with the transmitter, the sent data 
is echoed back to the microcontroller. This echo functionality is sometimes useful, 
but most often the TXENABLE and RXENABLE pins are connected in such a way 
that the receiver is disabled when the transmitter is active.

For detailed information, see http://en.wikipedia.org/wiki/RS-485.

Controlling the RS485 transmitter
````````````````````````````````````
Controlling the TXENABLE pin on the transceiver chip is the tricky part 
when it comes to RS485 communication. There are some options:

**Using a USB-to-serial conversion chip that is capable of setting the TXENABLE pin properly**
    See for example the FTDI chip 
    `FT232RL <http://www.ftdichip.com/Products/ICs/FT232R.htm>`_, which has a separate 
    output for this purpose (TXDEN in their terminology). The Sparkfun 
    breakout board `BOB-09822 <https://www.sparkfun.com/products/9822>`_ 
    combines this FTDI chip with a RS485 transceiver chip. The TXDEN output 
    from the FTDI chip is high (+5 V) when the transmitter is to be activated. 
    The FTDI chip calculates when the transmitter should be activated, so you 
    do not have to do anything in your application software.

**Using a RS232-to-RS485 converter capable of figuring out this by it self**
    This typically requires a microcontroller in the converter, and that you 
    configure the baud rate, stop bits etc. This is a straight-forward and 
    easy-to-use alternative, as you can use it together with a standard 
    USB-to-RS232 cable and nothing needs to be done in your application software. 
    One example of this type of converter is `Westermo MDW-45 <http://www.westermo.com>`_, 
    which I have been using with great success.

**Using a converter where the TXENABLE pin is controlled by the TX pin, sometimes via some timer circuit**
    I am not conviced that it is a good idea to control the TXENABLE pin by the TX pin, 
    as only one of the logic levels are actively driving the bus voltage. 
    If using a timer circuit, the hardware needs to be adjusted to the baudrate.
    
**Have the transmitter constantly enabled**
    Some users have been reporting on success for this strategy. The problem is that the master and
    slaves have their transmitters enabled simultaneously. I guess for certain situations (and
    being lucky with the transceiver chip) it might work. Note that you will receive your own transmitted 
    message (local echo). To handle local echo, see http://minimalmodbus.sourceforge.net/usage.html 

**Controlling a separate GPIO pin from kernelspace software on embedded Linux machines** 
    See for example http://blog.savoirfairelinux.com/en/2013/rs-485-for-beaglebone-a-quick-peek-at-the-omap-uart/ 
    This is a very elegant solution, as the TXENABLE pin is controlled by the 
    kernel driver and you don't have to worry about it in your application program. 
    Unfortunately this is not available for all boards, for example the standard distribution for 
    Beaglebone (September 2014).

**Controlling a separate GPIO pin from userspace software on embedded Linux machines**
    This will give large time delays, but might be acceptable for low speeds. See below.

**Controlling the RTS pin in the RS232 interface (from userspace), and connecting it to the TXENABLE pin of the transceiver**
    This will give large time delays, but might be acceptable for low speeds. See below.
    
**RTS toggle on Windows machines
    TODO: Look into this
    
Controlling the RS-485 transceiver from userspace
----------------------------------------------------
As described above, this should be avoided. Nevertheless, for low speeds (maybe up to 9600 bits/s) it might be useful.

   This can be done from userspace, but will then lead to large time delays. 
    I have tested this with a 3.3V FTDI  USB-to-serial cable using pySerial 
    on a Linux laptop. The cable has a RTS output, 
    but no TXDEN output. Note that the RTS output is +3.3 V at idle, and 0 V when 
    RTS is set to True. The delay time is around 1 ms, as measured with an oscilloscope. 
    This corresponds to approx 100 bit times when running at 115200 bps, but this 
    value also includes delays caused by the Python intepreter.


MODBUS ASCII format
-----------------------
This driver also supports Modbus ASCII mode.

Basically, a byte with value 0-255 in Modbus RTU mode will in Modbus ASCII 
mode be sent as two characters corresponding to the hex value of that byte.

For example a value of 76 (dec) = 4C (hex) is sent as the byte 0x4C in Modbus 
RTU mode. This byte happens to correspond to the character 'L' in the ASCII encoding. 
Thus for Modbus RTU this is sent: ``'\x4C'``, which is a string of length 1 and will print as 'L'.

The same value will in Modbus ASCII be sent as the string '4C', which has a length of 2.

The frame format is slightly different for Modbus ASCII. The request message 
is sent from the master in this format::

    Start [1 character], Slave Address [2 characters], Function code [2 characters], Payload data [0 to 2*252 characters], LRC [2 characters], Stop [2 characters].

Where:
 * The start character is the colon (:).
 * The LRC is a longitudinal redundancy check code, for error checking of the message.
 * The stop characters are carriage return ('\r' = ``'\x0D'``) and line feed ('\n' = ``'\x0A'``).

Manual testing of Modbus equipment
------------------------------------------
Look in your equipment's manual to find working communication examples.

You can make a small Python program to test the communication::

    TODO: RTU example

    import serial
    ser = serial.Serial('/dev/ttyUSB0', 19200, timeout=1)
    print ser

    ser.write(':010310010001EA\r\n')
    print repr(ser.read(1000)) # Read 1000 bytes, or wait for timeout

It should print something like::

    Serial<id=0x9faa08c, open=True>(port='/dev/ttyUSB0', baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=1, xonxoff=False, rtscts=False, dsrdtr=False)
    :0103020136C3

Correspondingly for Modbus ASCII, change the write command to for example::

    TODO: Verify

    ser.write(':010310010001EA\r\n')

It should then print something like::

    Serial<id=0x9faa08c, open=True>(port='/dev/ttyUSB0', baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=1, xonxoff=False, rtscts=False, dsrdtr=False)
    :0103020136C3

It is also easy to test Modbus ASCII equipment from Linux command line. First must 
the appropriate serial port be set up properly:

 * Print port settings: ``stty -F /dev/ttyUSB0``
 * Print all settings for a port: ``stty -F /dev/ttyUSB0 -a``
 * Reset port to default values: ``stty -F /dev/ttyUSB0 sane``
 * Change port to raw behavior: ``stty -F /dev/ttyUSB0 raw``
 * and: ``stty -F /dev/ttyUSB0 -echo -echoe -echok``
 * Change port baudrate: ``stty -F /dev/ttyUSB0 19200``

To send out a Modbus ASCII request (read register 0x1001 on slave 1), and print out the response::

    cat /dev/ttyUSB0 &
    echo -e ":010310010001EA\r\n" > /dev/ttyUSB0

The reponse will be something like::

    :0103020136C3
    
    
Trouble shooting
----------------

No communication
````````````````
If there is no communication, make sure that the settings on your instrument are OK:

* Wiring is correct
* Communication module is set for digital communication
* Correct protocol (Modbus, and the RTU or ASCII version)
* Baud rate
* Parity 
* Delay (most often not necessary)
* Address

The corresponding settings should also be used in MinimalModbus. Check also your:

* Port name

For troubleshooting, it is recommended to use interactive mode with debug 
enabled. See http://minimalmodbus.sourceforge.net/usage.html#interactive-usage

If there is no response from your instrument, you can try using a lower 
baud rate, or to adjust the timeout setting.

See also the pySerial pages: http://pyserial.sourceforge.net/

To make sure you are sending something valid, start with the examples in 
the users manual of your instrument. Use MinimalModbus in debug mode and make sure that each sent byte is correct.

The terminiation resistors of the RS-485 bus must be set correctly. Use a 
multimeter to verify that there is termination in the appropriate nodes of 
your RS-485 bus.

To troubleshoot the communication in more detail, an oscilloscope can be very 
useful to verify transmitted data. 


Local echo
``````````
Local echo of the USB-to-RS485 adaptor can also be the cause of some problems, 
and give rise to strange error messages (like "CRC error" or "wrong number of bytes error" etc). 
Switch on the debug mode to see the request and response messages. 
If the full request message can be found as the first part of the response, 
then local echo is likely the cause.

Make a test to remove the adaptor from the instrument (but still connected 
to the computer), and see if you still have a response. 

Most adaptors have switches to select echo ON/OFF. Turning off the local 
echo can be done in a number of ways:

* A DIP-switch inside the plastic cover.
* A jumper inside the plastic cover.
* Shorting two of the pins in the 9-pole D-SUB connector turns off the echo for some models.
* If based on a FTDI chip, some special program can be used to change a chip setting for disabling echo.

To handle local echo, see http://minimalmodbus.sourceforge.net/usage.html 

Empty bytes added in the beginning or the end on the received message
``````````````````````````````````````````````````````````````````````
This is due to interfercece. Use biasing of modbus lines, by connecting resistors 
to gnd and Vcc from the the two lines. This is sometimes named "failsafe".

Serial adaptors not recognized
``````````````````````````````
There have been reports on problems with serial adaptors on some platforms, 
for example Raspberry Pi. It seems to lack kernel drives for some chips, like PL2303. 
Serial adaptors based on FTDI FT232RL are known to work.

Make sure to run the ``dmesg`` command before and after plugging in your 
serial adaptor, to verify that the proper kernel driver is loaded.


Known issues
--------------
For the data types involving more than one register (float, long etc), 
there are differences in the byte order used by different manufacturers. 
A floating point value of 1.0 is encoded (in single precision) as 3f800000 (hex). 
In this implementation the data will be sent as ``'\x3f\x80'`` and ``'\x00\x00'`` to two consecutetive registers. 
Make sure to test that it makes sense for your instrument. 
It is pretty straight-forward to change this code if some other byte order is required by anyone (see support section).

Changing ``close_port_after_each_call`` after instantiation of ``Instrument`` might be 
problematic. Set the value ``minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL=True`` 
immediately after ``import minimalmodbus`` instead.

When running under Python2.6, for some conversion errors no exception is raised. 
For example when trying to convert a negative value to a bytestring representing an unsigned long.


Support
-------
Send a mail to minimalmodbus-list@lists.sourceforge.net

Describe the problem in detail, and include any error messsages. Please also include the output after running::

  >>> import minimalmodbus 
  >>> print minimalmodbus._getDiagnosticString()

Note that it can be very helpful to switch on the debug mode, where the communication 
details are printed. See the 'Debug mode' section.

Describe which instrument model you are using, and possibly a link to online PDF documentation for it.


Develop
-------
The details printed in debug mode (messages and responses) are very useful 
for using the included dummy_serial port for unit testing purposes. 
For examples, see the file test/test_minimalmodbus.py.
    
More implementation details are found on http://minimalmodbus.sourceforge.net/develop.html  
    
    
Unit testing
------------
Unit tests are provided in the test subfolder. To run them::

    python test_minimalmodbus.py
    
Also a dummy/mock/stub for the serial port, dummy_serial, is provided for 
test purposes. See http://minimalmodbus.sourceforge.net/apidummyserial.html

The test coverage analysis is found at http://minimalmodbus.sourceforge.net/htmlcov/index.html. 
To see which parts of the code that have been tested, click the corresponding file name.    
        
Hardware tests are performed using a Delta DTB4824 process controller. See the test subfolder for more information.
        
More details on the unittests are found on http://minimalmodbus.sourceforge.net/develop.html  


Related software
----------------
The MinimalModbus module is intended for easy-to-use communication with 
instruments using the Modbus (RTU) protocol. 
There are a few other Python modules for Modbus protocol implementation. 
For more advanced use, you should consider using one of these:

pyModbus 
    From http://code.google.com/p/pymodbus/: 'Pymodbus is a full Modbus protocol implementation using twisted for its asynchronous communications core.'

modbus-tk
    From http://code.google.com/p/modbus-tk/: 'Make possible to write modbus TCP and RTU master and slave mainly for testing purpose. It is shipped with slave simulator and a master with a web-based hmi. It is a full-stack implementation and as a consequence could also be used on real-world project.'


Licence
-------
Apache License, Version 2.0.


Author
------
Jonas Berg, pyhys@users.sourceforge.net


Credits
-------
Significant contributions by Angelo Compagnucci, Aaron LaLonde, Asier Abalos, 
Simon Funke, Edwin van den Oetelaar, Dominik Socha, Luca Di Gregorio and Michael Penza.


Feedback
--------
If you find this software useful, then please like it on Facebook via http://sourceforge.net/projects/minimalmodbus/. 

You can also leave a review on the SourceForge project page 
http://sourceforge.net/projects/minimalmodbus/ (then first make a SourceForge account).

Please also subscribe to the (low volume) mailing list 
minimalmodbus-list@lists.sourceforge.net 
(see https://lists.sourceforge.net/lists/listinfo/minimalmodbus-list) 
so you can help other users getting started.


References
----------
* Python: http://www.python.org/


Text revision
-------------
This README file was changed (committed) at $Date$, which was $Revision$.

