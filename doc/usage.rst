Detailed usage documentation
=============================


Interactive usage
--------------------------------------------------------------------------------
To use interactive mode, start the Python interpreter and import minimalmodbus::

    >>> import minimalmodbus
    >>> instr = minimalmodbus.Instrument('/dev/ttyUSB0', 1)
    >>> instr
    minimalmodbus.Instrument<id=0xb7437b2c, address=1, close_port_after_each_call=False, debug=False, serial=Serial<id=0xb7437b6c, open=True>(port='/dev/ttyUSB0', baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=0.05, xonxoff=False, rtscts=False, dsrdtr=False)>
    >>> instr.read_register(24, 1)
    5.0
    >>> instr.write_register(24, 450, 1)
    >>> instr.read_register(24, 1)
    450.0

Note that when you call a function, in interactive mode the representation of the return value is printed. The representation is kind of a debug information, like seen here for the returned string::

    >>> instrument.get_all_pattern_variables(0)
    'SP0: 10.0  Time0: 10\nSP1: 20.0  Time1: 20\nSP2: 30.0  Time2: 30\nSP3: 333.3  Time3: 45\nSP4: 50.0  Time4: 50\nSP5: 60.0  Time5: 60\nSP6: 70.0  Time6: 70\nSP7: 80.0  Time7: 80\nActual step:        7\nAdditional cycles:  4\nLinked pattern:     1\n'

To see how the string look when printed, use instead::

    >>> print instrument.get_all_pattern_variables(0)
    SP0: 10.0  Time0: 10
    SP1: 20.0  Time1: 20
    SP2: 30.0  Time2: 30
    SP3: 333.3  Time3: 45
    SP4: 50.0  Time4: 50
    SP5: 60.0  Time5: 60
    SP6: 70.0  Time6: 70
    SP7: 80.0  Time7: 80
    Actual step:        7
    Additional cycles:  4
    Linked pattern:     1

It is possible to show the representation also when printing, if you use the function ``repr()``::

    >>> print repr(instrument.get_all_pattern_variables(0))
    'SP0: 10.0  Time0: 10\nSP1: 20.0  Time1: 20\nSP2: 30.0  Time2: 30\nSP3: 333.3  Time3: 45\nSP4: 50.0  Time4: 50\nSP5: 60.0  Time5: 60\nSP6: 70.0  Time6: 70\nSP7: 80.0  Time7: 80\nActual step:        7\nAdditional cycles:  4\nLinked pattern:     1\n'

In case of problems using MinimalModbus, it is useful to switch on the debug mode to see the 
communication details::

    >>> instr.debug = True
    >>> instr.read_register(24, 1)
    MinimalModbus debug mode. Writing to instrument: '\x01\x03\x00\x18\x00\x01\x04\r'
    MinimalModbus debug mode. Response from instrument: '\x01\x03\x02\x11\x94µ»'
    450.0

Making drivers for specific instruments
------------------------------------------------------------------------------
With proper instrument drivers you can use commands like ``getTemperatureCenter()`` in your code 
instead of ``read_register(289, 1)``. So the driver is a basically a collection of 
numerical constants to make your code more readable.

This segment is part of the example driver :mod:`eurotherm3500` which is included in this distribution::

    import minimalmodbus

    class Eurotherm3500( minimalmodbus.Instrument ):
        """Instrument class for Eurotherm 3500 process controller. 

        Args:
            * portname (str): port name
            * slaveaddress (int): slave address in the range 1 to 247

        """
        
        def __init__(self, portname, slaveaddress):
            minimalmodbus.Instrument.__init__(self, portname, slaveaddress)
        
        def get_pv_loop1(self):
            """Return the process value (PV) for loop1."""
            return self.read_register(289, 1)
        
        def is_manual_loop1(self):
            """Return True if loop1 is in manual mode."""
            return self.read_register(273, 1) > 0

        def get_sptarget_loop1(self):
            """Return the setpoint (SP) target for loop1."""
            return self.read_register(2, 1)
        
        def get_sp_loop1(self):
            """Return the (working) setpoint (SP) for loop1."""
            return self.read_register(5, 1)
        
        def set_sp_loop1(self, value):
            """Set the SP1 for loop1.
            
            Note that this is not necessarily the working setpoint.

            Args:
                value (float): Setpoint (most often in degrees)
            """
            self.write_register(24, value, 1)
        
        def disable_sprate_loop1(self):
            """Disable the setpoint (SP) change rate for loop1. """
            VALUE = 1
            self.write_register(78, VALUE, 0) 


See :mod:`eurotherm3500` (click [source]) for more details.

Note that I have one additional driver layer on top of :mod:`eurotherm3500` (which is one layer on top of :mod:`minimalmodbus`). 
I use this process controller to run a heater, so I have a driver :file:`heater.py` in which all my settings are done.

The idea is that :mod:`minimalmodbus` should be useful to most Modbus users, and :mod:`eurotherm3500` should be useful to most users of that controller type. 
So my :file:`heater.py` driver has functions like ``get_center_temperature()`` and ``get_edge_temperature()``, and there I also define resistance values etc.

Here is a part of :file:`heater.py`::
     
    """Driver for the heater in the CVD system. Talks to the heater controller and the heater policeman. 

    Implemented with the modules :mod:`eurotherm3500` and :mod:`eurotherm3216i`.

    """

    import eurotherm3500
    import eurotherm3216i

    class heater():
        """Class for the heater in the CVD system. Talks to the heater controller and the heater policeman.

        """
        
        ADDRESS_HEATERCONTROLLER = 1
        """Modbus address for the heater controller."""

        ADDRESS_POLICEMAN = 2
        """Modbus address for the heater over-temperature protection unit."""
        
        SUPPLY_VOLTAGE = 230
        """Supply voltage (V)."""
        
        def __init__(self, port):
            self.heatercontroller = eurotherm3500.Eurotherm3500(   port, self.ADDRESS_HEATERCONTROLLER)
            self.policeman        = eurotherm3216i.Eurotherm3216i( port, self.ADDRESS_POLICEMAN)
        
        def getTemperatureCenter(self):
            """Return the temperature (in deg C)."""
            return self.heatercontroller.get_pv_loop1()
        
        def getTemperatureEdge(self):
            """Return the temperature (in deg C) for the edge heater zone."""
            return self.heatercontroller.get_pv_loop2()
        
        def getTemperaturePolice(self):
            """Return the temperature (in deg C) for the overtemperature protection sensor."""
            return self.policeman.get_pv()
        
        def getOutputCenter(self):
            """Return the output (in %) for the heater center zone."""
            return self.heatercontroller.get_op_loop1()
       


Using this module as part of a measurement system
----------------------------------------------------------------------------
It is very useful to make a graphical user interface (GUI) for your control/measurement program. 

One library for making GUIs is wxPython, found on http://www.wxpython.org/. One good tutorial (it start from the basics) is: http://www.zetcode.com/wxpython/

I strongly suggest that your measurement program should be possible to run without any GUI, as it then is much easier to actually get the GUI version of it to work. Your program should have some function like ``setTemperature(255)``.

The role of the GUI is this:
If you have a temperature text box where a user has entered ``255`` (possibly degrees C), and a button 'Run!' or 'Go!' or something similar, then the GUI program should read ``255`` from the box when the user presses the button, and call the function ``setTemperature(255)``.

This way it is easy to test the measurement program and the GUI separately.


Known issues
-----------------------------------------------------------------------------
Sending negative values to the slave is not yet implemented. If this is an issue for you, please provide the manual for your instrument.

Changing `close_port_after_each_call` after instantiation of :class:`.Instrument` might be 
problematic. Set the value ``minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL=True`` immediately after ``import minimalmodbus`` instead.


Install or uninstalling a distribution
--------------------------------------------------------------------------
To install a python (downloaded) package, uncompress it and use::

    sudo python setup.py install

or::

    sudo python3 setup.py install

On a development machine, go to the :file:`trunk` directory before running the command.


Uninstall
``````````
Pip-installed packages can be unistalled with::

    sudo pip uninstall minimalmodbus


Show versions of all installed packages
```````````````````````````````````````
Use::

    pip freeze


Installation target
``````````````````````
The location of the installed files is seen in the :meth:`._getDiagnosticString` output::

    import minimalmodbus
    print minimalmodbus._getDiagnosticString() 

On Linux machines, for example::

   /usr/local/lib/python2.6/dist-packages

On OS X it might end up in for example::

   /Library/Python/2.6/site-packages/minimalmodbus.py

Note that :file:`.pyc` is a byte compiled version. Make the changes in the :file:`.py` file, and delete the :file:`.pyc` file (When available, :file:`.pyc` files are used instead of :file:`.py` files).
You might need root privileges to edit the file in this location. Otherwise it is better to uninstall it, put it instead in your home folder and add it to sys.path

On Windows machines, for example::

    C:\python27\Lib\site-packages

The Windows installer also creates a :file:`.pyo` file (and also the :file:`.pyc` file).

Python location
`````````````````
Python location on Linux machines::

    /usr/lib/python2.7/

    /usr/lib/python2.7/dist-packages
    
To find locations::
 
    ~$ which python
    /usr/bin/python
    ~$ which python3
    /usr/bin/python3
    ~$ which python2.7
    /usr/bin/python2.7
    ~$ which python3.2
    /usr/bin/python3.2


Setting the PYTHONPATH
----------------------------------------------------------------------------
To set the path::
    
    echo $PYTHONPATH
    export PYTHONPATH='/home/jonas/pythonprogrammering/minimalmodbus/trunk'

or::

    export PYTHONPATH=$PYTHONPATH:/home/jonas/pythonprogrammering/minimalmodbus/trunk

It is better to set the path in the :file:`.basrc` file.

