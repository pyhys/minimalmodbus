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

From command line:
   pip install minimalmodbus

or

download the compressed source file (.zip or .tar.gz), uncompress it and run:
   python setup.py install

There is also a Windows installer.
   

Home page
=========
http://minimalmodbus.sourceforge.net/

SoourceForge project page: http://sourceforge.net/projects/minimalmodbus/

Python package index: http://pypi.python.org/pypi/MinimalModbus/


Author
======
Jonas Berg

   



