Detailed usage documentation
=============================

The location of the code is seen in the _getDiagnosticString() output.


 sudo python3 setup.py install


Install or uninstalling a distribution
--------------------------------------------------------------------------
Use::

    sudo python setup.py install

On a development machine, go to the minimalmodbus/trunk directory before running the command.



Uninstall
``````````

sudo pip uninstall minimalmodbus



Show versions of all installed packages
```````````````````````````````````````

pip freeze


Installation target
``````````````````````
On Linux machines, for example::

   /usr/local/lib/python2.6/dist-packages

On OS X it might end up in for example::

   /Library/Python/2.6/site-packages/minimalmodbus.py

Note that .pyc is a byte compiled version. Make the changes in the .py file, and delete the .pyc file (When available, .pyc files are used instead of .py files).
You might need root privileges to edit the file in this location. Otherwise it is better to uninstall it, put it instead in your home folder and add it to sys.path


On Windows machines, for example::

    C:\python27\Lib\site-packages

The Windows installer also creates a :file:`.pyo` file (and also the :file:`.pyc` file).

Python location
`````````````````

Python location on Linux machines::

    /usr/lib/python2.7/

    /usr/lib/python2.7/dist-packages
    
 
which python
/usr/bin/python


which python3.2
/usr/bin/python3.2


which pip


/usr/bin/pip   
    


Setting the PYTHONPATH
----------------------------------------------------------------------------

To set the path::
    
    echo $PYTHONPATH
    export PYTHONPATH='/home/jonas/pythonprogrammering/minimalmodbus/trunk'

or::

    export PYTHONPATH=$PYTHONPATH:/home/jonas/pythonprogrammering/minimalmodbus/trunk

It is better to set the path in the :file:`.basrc` file.


Diagnostic output
-----------------

print( minimalmodbus._getDiagnosticString() )


Known issues
----------------
Sending negative values to the slave is not yet implemented. If this is an issue for you, please provide the manual for your instrument.

Changing `close_port_after_each_call` after instantiation of Instrument() might be 
problematic. Set the value minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL=True instead.


Make drives for specific instruments
--------------------------------------

basically a collection of numerical constants

example Eurotherm3500

Note that I have one driver layer on top of Eurotherm3500 (which is one layer on top of Minimalmodbus). I use the process controller to run a heater, so I have a driver heater.py in which all my settings are done.

The idea is that MinimalModbus should be useful to most Modbus users, and Eurotherm3500 should be useful to most users of that controller. So my driver has functions like get_center_temperature() and get_edge_temperature(), and there I also define resistance values etc. I think you get the idea.

Here is a part of my driver heater.py::
     
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
--------------------------------------------------
It is very useful to make a graphical user interface (GUI) for your control/measurement program. 

One library for making GUIs is wxPython, found on http://www.wxpython.org/. One good tutorial (it start from the basics) is: http://www.zetcode.com/wxpython/

I strongly suggest that your measurement program should be possible to run without any GUI, as it then is much easier to actually get the GUI version of it to work. Your program should have some function like setTemperature(255).

The role of the GUI is this:
If you have a temperature text box where a user has entered 255 (possibly degrees C), and a button 'Run!' or 'Go!' or something similar, then the GUI program should read 255 from the box when the user presses the button, and call the function setTemperature(255).

This way it is easy to test the measurement program and the GUI separately.

