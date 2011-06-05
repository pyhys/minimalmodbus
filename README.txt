=============
MinimalModbus
=============

There are several types of modbus protocols:


Typical usage::

 #!/usr/bin/env python

 import minimalmodbus

 instrument = minimalmodbus.minimalmodbus(56) # Slave address
 temperature = instrument.readRegister( 23541, 1 ) # Registernumber, number of decimals




Installation
============


Home page
=========


Author
======


   



