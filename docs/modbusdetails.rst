.. _modbusdetails:

==============
Modbus details
==============

Modbus data types
-----------------
The Modbus standard defines storage in:

* Bits. Each bit has its own address.
* Registers (16-bit). Each register has its own address. Can hold integers in the
  range 0 to 65535 (dec), which is 0 to ffff (hex). Also called 'unsigned INT16'
  or 'unsigned short'.

Modbus defines "table" names dependent on whether the storage is in a single bit
or in a 16-bit register, and whether it is possible to write to the storage.

+-----------------+----------------+------------------------+-------------------------------------------------+
| Storage in      | Access         | Modbus "table"         | Example use on instrument                       |
+=================+================+========================+=================================================+
| Bits            | Read only      | Discrete inputs        | A digital input                                 |
+-----------------+----------------+------------------------+-------------------------------------------------+
| Bits            | Read and write | Coils                  | A digital output                                |
+-----------------+----------------+------------------------+-------------------------------------------------+
| 16-bit register | Read only      | Input registers        | Several digital inputs, or an analog input      |
+-----------------+----------------+------------------------+-------------------------------------------------+
| 16-bit register | Read and write | Holding registers      | Several digital outputs, or a setting parameter |
+-----------------+----------------+------------------------+-------------------------------------------------+

Function codes are used to describe the read or write operations (shown in decimal in the table below)

+----------------------------------------------+--------+----------+---------+----------+
|                                              |      Read         |       Write        |
|                                              +--------+----------+---------+----------+
| Storage                                      | Single | Multiple | Single  | Multiple |
+==============================================+========+==========+=========+==========+
| Read-and-write bits (coils)                  |        | 1        | 5       | 15       |
+----------------------------------------------+--------+----------+---------+----------+
| Read-only bits (discrete inputs)             |        | 2        | None    | None     |
+----------------------------------------------+--------+----------+---------+----------+
| Read-and-write registers (holding registers) |        | 3, 23    | 6       | 16, 23   |
+----------------------------------------------+--------+----------+---------+----------+
| Read-only registers (input registers)        |        | 4, 23    | None    | None     |
+----------------------------------------------+--------+----------+---------+----------+

Note that function code 23 not is implemented by this software (it is for
reading and writing in same request).

Function codes 128 and larger are used by slaves to indicate errors.

Some extensions not covered by the official standard
----------------------------------------------------

**Scaling of register values**
    Some manufacturers store a temperature value of 77.0 C as 770 in the register,
    to allow room for one decimal.

**Negative numbers (INT16 = short)**
    Some manufacturers allow negative values for some registers. Instead of an
    allowed integer range 0-65535, a range -32768 to 32767 is allowed. This is
    implemented as any received value in the upper range (32768-65535) is
    interpreted as negative value (in the range -32768 to -1). This is two's
    complement and is described at https://en.wikipedia.org/wiki/Two%27s_complement.
    Help functions to calculate the two's complement value (and back) are
    provided in MinimalModbus.

**Long integers ('Unsigned INT32' or 'INT32')**
    These require 32 bits, and are implemented as two consecutive 16-bit registers.
    The range is 0 to 4294967295, which is called 'unsigned INT32'. Alternatively
    negative values can be stored if the instrument is defined that way, and is
    then called 'INT32' which has the range -2147483648 to 2147483647. Unfortunately
    the byte order might differ between manufacturers of Modbus instruments.

**Floats (single or double precision)**
    Single precision floating point values (binary32) are defined by 32 bits (4 bytes),
    and are implemented as two consecutive 16-bit registers.
    Correspondingly, double precision floating point values (binary64) use
    64 bits (8 bytes) and are implemented as four consecutive 16-bit registers.
    How to convert from the bit values to the floating point value is described in
    the standard IEEE 754, as seen in https://en.wikipedia.org/wiki/Floating_point.
    Unfortunately the byte order might differ between manufacturers of Modbus instruments.

**Strings**
    Each register (16 bits) is interpreted as two ASCII characters (each 1 byte = 8 bits).
    Often 16 consecutive registers are used, allowing 32 characters in the string.
    Unicode/UTF-8 is typically not supported.

**8-bit registers**
    For example Danfoss use 8-bit registers for storage of some settings internally
    in the instruments. The data is nevertherless transmitted as 16 bit over the serial link,
    so you can read and write like normal (but with values limited to the range 0-255).

**32-bit registers**
    "Enron Modbus" allows larger registers where you can store 32 bits in a single register
    (instead of two consecutive 16 bit registers). Not supported by this software.

**Bit fields in integers**
    Some manufacturers store multiple bits in a 16-bit register, instead of as individually
    adressable bits. This is also known as flag registers. See below for how to use them
    with this software.

**JBUS adressing**
    From Eurotherm Modbus/ProfibusCommunications Handbook: "The JBUS protocol is identical
    in all respects but one to the Modbus protocol. The one difference concerns the parameter
    or register address. Both use a numeric index but the JBUS index starts at 0 while
    the Modbus index starts at 1."

**Slave addresses larger than 255**
    Sometimes the slave address is encoded in two bytes to allow values larger than 255.
    Not supported by this software.


Implemented functions
---------------------
These are the functions to use for reading and writing registers and bits of your instrument. Study the
documentation of your instrument to find which Modbus function code to use. The function codes (F code) are
given in decimal in this table.

+---------------------------------------+-------------------------+---------------+--------------------------+---------------+
| Data type in slave                    | Read                    | F code        | Write                    | F code        |
+=======================================+=========================+===============+==========================+===============+
| | **Bit**                             | :meth:`.read_bit`       | 2 [or 1]      | :meth:`.write_bit`       | 5 [or 15]     |
+---------------------------------------+-------------------------+---------------+--------------------------+---------------+
| | **Bits**                            | :meth:`.read_bits`      | 2 [or 1]      | :meth:`.write_bits`      | 15            |
| | Simultaneous reading                |                         |               |                          |               |
+---------------------------------------+-------------------------+---------------+--------------------------+---------------+
| | **Register**                        | :meth:`.read_register`  | 3 [or 4]      | :meth:`.write_register`  | 16 [or 6]     |
| | Integer, possibly scaled            |                         |               |                          |               |
+---------------------------------------+-------------------------+---------------+--------------------------+---------------+
| | **Long integer**                    | :meth:`.read_long`      | 3 [or 4]      | :meth:`.write_long`      | 16            |
| | (32 bits = 2 registers)             |                         |               |                          |               |
+---------------------------------------+-------------------------+---------------+--------------------------+---------------+
| | **Float**                           | :meth:`.read_float`     | 3 [or 4]      | :meth:`.write_float`     | 16            |
| | (32 or 64 bits =                    |                         |               |                          |               |
| | 2 or 4 registers)                   |                         |               |                          |               |
+---------------------------------------+-------------------------+---------------+--------------------------+---------------+
| | **String**                          | :meth:`.read_string`    | 3 [or 4]      | :meth:`.write_string`    | 16            |
| | 2 characters per register           |                         |               |                          |               |
+---------------------------------------+-------------------------+---------------+--------------------------+---------------+
| | **Registers**                       | :meth:`.read_registers` | 3 [or 4]      | :meth:`.write_registers` | 16            |
| | Integers                            |                         |               |                          |               |
+---------------------------------------+-------------------------+---------------+--------------------------+---------------+

See the API for MinimalModbus: :ref:`apiminimalmodbus`.


.. _byteorder:

Byte order for data stored in serveral registers
------------------------------------------------
Floats and long integers does not fit in a single 16-bit register, so typically consecutive
registers are used. However different manufacturers store the bytes in different order.

The functions handling floats and long integers have a parameter for changing
which byte order that is used.

===================== ============================ ====================== =======
Name                  Description                  Use                    Example
===================== ============================ ====================== =======
Big endian (Motorola) High order byte first        BYTEORDER_BIG          ABCD
?                     Big endian with byte swap    BYTEORDER_BIG_SWAP     BADC
?                     Little endian with byte swap BYTEORDER_LITTLE_SWAP  CDAB
Little endian (Intel) Low order byte first         BYTEORDER_LITTLE       DCBA
===================== ============================ ====================== =======

The example column show how the bytes are ordered on the wire (assuming byte A is
the most significant byte).

Read more on Modbus byte ordering in these articles:

* https://store.chipkin.com/articles/how-real-floating-point-and-32-bit-data-is-encoded-in-modbus-rtu-messages
* https://www.modbustools.com/poll_display_formats.html
* https://www.simplymodbus.ca/FAQ.htm#Ext

Modbus implementation details
-----------------------------
In Modbus RTU, the request message is sent from the master in this format:

 * Slave address [1 Byte]
 * Function code [1 Byte]. Allowed range is 1 to 127 (in decimal).
 * Payload data [0 to 252 Bytes]
 * CRC [2 Bytes]. It is a Cyclic Redundancy Check code, for error checking of the message

The response from the client is similar, but with other payload data.

+---------------------------------------+---------------------------------+---------------------------------+
| | Function code                       | | Payload data to slave         | | Payload data from slave       |
| | (in decimal)                        | | (Request)                     | | (Response)                    |
+=======================================+=================================+=================================+
| | **1**                               | | Start address [2 Bytes]       | | Byte count [1 Byte]           |
| | Read bits (coils)                   | | Number of coils [2 Bytes]     | | Value [k Bytes]               |
+---------------------------------------+---------------------------------+---------------------------------+
| | **2**                               | | Start address [2 Bytes]       | | Byte count [1 Byte]           |
| | Read discrete inputs                | | Number of inputs [2 Bytes]    | | Value [k Bytes]               |
+---------------------------------------+---------------------------------+---------------------------------+
| | **3**                               | | Start address [2 Bytes]       | | Byte count [1 Byte]           |
| | Read holding registers              | | Number of registers [2 Bytes] | | Value [n*2 Bytes]             |
+---------------------------------------+---------------------------------+---------------------------------+
| | **4**                               | | Start address [2 Bytes]       | | Byte count [1 Byte]           |
| | Read input registers                | | Number of registers [2 Bytes] | | Value [n*2 Bytes]             |
+---------------------------------------+---------------------------------+---------------------------------+
| | **5**                               | | Output address [2 Bytes]      | | Output address [2 Bytes]      |
| | Write single bit (coil)             | | Value [2 Bytes]               | | Value [2 Bytes]               |
+---------------------------------------+---------------------------------+---------------------------------+
| | **6**                               | | Register address  [2 Bytes]   | | Register address [2 Bytes]    |
| | Write single register               | | Value [2 Bytes]               | | Value [2 Bytes]               |
+---------------------------------------+---------------------------------+---------------------------------+
| | **15**                              | | Start address [2 Bytes]       | | Start address [2 Bytes]       |
| | Write multiple bits (coils)         | | Number of outputs [2 Bytes]   | | Number of outputs [2 Bytes]   |
| |                                     | | Byte count [1 Byte]           | |                               |
| |                                     | | Value [k Bytes]               | |                               |
+---------------------------------------+---------------------------------+---------------------------------+
| | **16**                              | | Start address [2 Bytes]       | | Start address [2 Bytes]       |
| | Write multiple registers            | | Number of registers [2 Bytes] | | Number of regist [2 Bytes]    |
| |                                     | | Byte count [1 Byte]           | |                               |
| |                                     | | Value [n*2 Bytes]             | |                               |
+---------------------------------------+---------------------------------+---------------------------------+
| | **23**                              | | ?                             | | ?                             |
| | Read and write multiple registers   | |                               | |                               |
| |                                     | |                               | |                               |
| |                                     | |                               | |                               |
+---------------------------------------+---------------------------------+---------------------------------+

For function code 5, the only valid values are 0000 (hex) or FF00 (hex), representing OFF and ON respectively.

It is seen in the table above that the request and response messages are similar for function code 1 to 4. The same
can be said about function code 5 and 6, and also about 15 and 16.

For finding how the k Bytes for the value relates to the number of registers etc (n), see the Modbus documents referred to above.


Reading individual bits from a 16-bit register
----------------------------------------------

Some manufacturers use 16-bit registers to store individual boolean values (bits), so with
a single read from a single address, 16 booleans could be retrieved.
This is sometimes called a flag register.

You need to read the register as an integer, and then
extract the bit you are interested in. For example to extract the
third bit from right::

    registervalue = instrument.read_register(4143)
    is_my_bit_set = (registervalue & 0b0000000000000100) > 0

or if using hexadecimal numbers in your code instead::

    is_my_bit_set = (registervalue & 0x0004) > 0

More information on bit manipulation in Python, see the "Single bits" section
of https://wiki.python.org/moin/BitManipulation


Known deviations from the standard
-----------------------------------
Some instruments:

* sets more than one bit in the response when one bit is requested.
* add an extra 0xFE byte after some messages.


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
is sent from the master in this format:

 * Start [1 character]. It is the colon (:).
 * Slave Address [2 characters]
 * Function code [2 characters]
 * Payload data [0 to 2*252 characters]
 * LRC [2 characters]. The LRC is a Longitudinal Redundancy Check code, for error checking of the message.
 * Stop [2 characters].
   The stop characters are carriage return (``'\r'`` = ``'\x0D'``) and line feed (``'\n'`` = ``'\x0A'``).



Manual testing of Modbus equipment
------------------------------------------
Look in your equipment's manual to find working communication examples.

You can make a small Python program to test the communication::

    TODO: Change this to a RTU example

    import serial
    ser = serial.Serial('/dev/ttyUSB0', 19200, timeout=1)
    print(ser)

    ser.write(':010310010001EA\r\n')
    print(repr(ser.read(1000)))  # Read 1000 bytes, or wait for timeout

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
