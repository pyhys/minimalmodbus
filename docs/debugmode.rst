==========
Debug mode
==========

.. _debugmode:
   
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
https://docs.python.org/2/reference/lexical_analysis.html#string-literals for details on escape sequences.

For more information about hexadecimal numbers, see https://en.wikipedia.org/wiki/Hexadecimal.

Note that the letter A has the hexadecimal ASCII code 41, why the string ``'\x41'`` prints ``'A'``. 
The Latin-1 encoding is used (on most installations?), and the conversion table is found on 
https://en.wikipedia.org/wiki/Latin_1.

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

=================== ================= ========== ========== ======================
``repr()`` shows as Can be written as ASCII hex  ASCII dec  Description
=================== ================= ========== ========== ======================
``\t``              ``\x09``          09         9          Horizontal Tab (TAB)
``\n``              ``\x0a``          0a         10         Linefeed (LF)
``\r``              ``\x0d``          0d         13         Carriage Return (CR)
=================== ================= ========== ========== ======================

It is also possible to write for example ASCII Bell (BEL, hex = 07, dec = 7) 
as ``\a``, but its ``repr()`` will still print ``\x07``.

More about ASCII control characters is found on https://en.wikipedia.org/wiki/ASCII.

