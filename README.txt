=============
MinimalModbus
=============

There are several types of modbus protocols:

  * Modbus RTU
  * Modbus ??

Typical usage::

    #!/usr/bin/env python
    import minimalmodbus

    instrument = minimalmodbus.Instrument('/dev/ttyUSB1', 1) # port name, slave address
    temperature = instrument.read_register( 23541, 1 ) # Registernumber, number of decimals




Installation
============


Home page
=========


Author
======


   



