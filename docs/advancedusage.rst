.. _detailedusage:

Detailed usage documentation
=============================
For introductive usage documentation, see :ref:`usage`.


.. _interactiveusage:

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

Note that when you call a function, in interactive mode the representation of the
return value is printed. The representation is kind of a debug information,
like seen here for the returned string (example from Omega CN7500 driver,
which previously was included in this package)::

    >>> instrument.get_all_pattern_variables(0)
    'SP0: 10.0  Time0: 10\nSP1: 20.0  Time1: 20\nSP2: 30.0  Time2: 30\nSP3: 333.3  Time3: 45\nSP4: 50.0  Time4: 50\nSP5: 60.0  Time5: 60\nSP6: 70.0  Time6: 70\nSP7: 80.0  Time7: 80\nActual step:        7\nAdditional cycles:  4\nLinked pattern:     1\n'

To see how the string look when printed, use instead::

    >>> print(instrument.get_all_pattern_variables(0))
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

    >>> print(repr(instrument.get_all_pattern_variables(0)))
    'SP0: 10.0  Time0: 10\nSP1: 20.0  Time1: 20\nSP2: 30.0  Time2: 30\nSP3: 333.3  Time3: 45\nSP4: 50.0  Time4: 50\nSP5: 60.0  Time5: 60\nSP6: 70.0  Time6: 70\nSP7: 80.0  Time7: 80\nActual step:        7\nAdditional cycles:  4\nLinked pattern:     1\n'

In case of problems using MinimalModbus, it is useful to switch on the debug mode to see the
communication details::

    >>> instr.debug = True
    >>> instr.read_register(24, 1)
    MinimalModbus debug mode. Writing to instrument: '\x01\x03\x00\x18\x00\x01\x04\r'
    MinimalModbus debug mode. Response from instrument: '\x01\x03\x02\x11\x94µ»'
    450.0

.. _specificdrivers:

Making drivers for specific instruments
------------------------------------------------------------------------------
With proper instrument drivers you can use commands like ``getTemperatureCenter()`` in your code
instead of ``read_register(289, 1)``. So the driver is a basically a collection of
numerical constants to make your code more readable.

This segment is part of the example driver eurotherm3500 which previously was included
in this distribution::

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

To get the process value (PV from loop1)::

    #!/usr/bin/env python3
    import eurotherm3500

    heatercontroller = eurotherm3500.Eurotherm3500('/dev/ttyUSB1', 1)  # port name, slave address

    ## Read temperature (PV) ##
    temperature = heatercontroller.get_pv_loop1()
    print(temperature)

    ## Change temperature setpoint (SP) ##
    NEW_TEMPERATURE = 95.0
    heatercontroller.set_sp_loop1(NEW_TEMPERATURE)


Note that I have one additional driver layer on top of eurotherm3500 (which is one layer on
top of :mod:`minimalmodbus`). I use this process controller to run a heater, so I have
a driver :file:`heater.py` in which all my settings are done.

The idea is that :mod:`minimalmodbus` should be useful to most Modbus users, and eurotherm3500
should be useful to most users of that controller type.
So my :file:`heater.py` driver has functions like ``getTemperatureCenter()``
and ``getTemperatureEdge()``, and there I also define resistance values etc.

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

One library for making GUIs is wxPython, found on https://www.wxpython.org/. One good tutorial
(it starts from the basics) is: https://zetcode.com/wxpython/

I strongly suggest that your measurement program should be possible to run without any GUI,
as it then is much easier to actually get the GUI version of it to work. Your program
should have some function like ``setTemperature(255)``.

The role of the GUI is this:
If you have a temperature text box where a user has entered ``255`` (possibly degrees C),
and a button 'Run!' or 'Go!' or something similar, then the GUI program should read ``255``
from the box when the user presses the button, and call the function ``setTemperature(255)``.

This way it is easy to test the measurement program and the GUI separately.


Handling extra 0xFE byte after some messages
--------------------------------------------------------------------------
Some users have reported errors due to instruments not fulfilling the Modbus standard.
For example can some additional byte be pasted at the end of the response from the instrument.
Here is an example how this can be handled by tweaking the minimalmodbus.py file.

Add this to :func:`._extract_payload` function, after the argument validity testing section::

    # Fix for broken T3-PT10 which outputs extra 0xFE byte after some messages
    # Patch by Edwin van den Oetelaar
    # check length of message when functioncode in 3,4
    # if received buffer length longer than expected, truncate it,
    # this makes sure CRC bytes are taken from right place, not the end of the buffer, it ignores the extra bytes in the buffer
    if functioncode in (0x03, 0x04) :
        try:
            modbuslen = ord(response[NUMBER_OF_RESPONSE_STARTBYTES])
            response = response[:modbuslen+5] # the number of bytes used for CRC(2),slaveid(1),functioncode(1),bytecount(1) = 5
        except IndexError:
            pass


Install or uninstalling a distribution
--------------------------------------------------------------------------

Uninstall
``````````
Pip-installed packages can be unistalled with::

    sudo pip3 uninstall minimalmodbus


Show versions of all installed packages
```````````````````````````````````````
Use::

    pip3 freeze


Installation target
``````````````````````
The location of the installed files is seen in the :meth:`._get_diagnostic_string` output::

    import minimalmodbus
    print(minimalmodbus._get_diagnostic_string())

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

To see which python version that is used::

    python3 --version


Setting the PYTHONPATH
----------------------------------------------------------------------------
To set the path::

    echo $PYTHONPATH
    export PYTHONPATH='/home/jonas/pythonprogrammering/minimalmodbus/trunk'

or::

    export PYTHONPATH=$PYTHONPATH:/home/jonas/pythonprogrammering/minimalmodbus/trunk

It is better to set the path in the :file:`.basrc` file.


Including MinimalModbus in a Yocto build
----------------------------------------------------------------------------
It is easy to include MinimalModbus in a Yocto build, which is using Bitbake. Yocto is a
collaboration with the Open Embedded initiative.

A Yocto recipe for MinimalModbus looks something like this::

    SUMMARY = "Easy-to-use Modbus RTU and Modbus ASCII implementation for Python"
    HOMEPAGE = "https://github.com/pyhys/minimalmodbus"
    AUTHOR = "Jonas Berg"
    LICENSE = "Apache-2.0"

    PYPI_PACKAGE = "minimalmodbus"
    LIC_FILES_CHKSUM = "file://LICENSE;md5=27da4ba4e954f7f4ba8d1e08a2c756c4"
    SRC_URI[md5sum] = "3fe320f7be761b6a2c3373257c431c31"
    SRC_URI[sha256sum] = "cf873a2530be3f4b86467c3e4d47b5f69fd345d47451baca4adbf59e2ac36d00"

    RDEPENDS:${PN} += "python3-core python3-pyserial"

    inherit pypi setuptools3
    # TODO Use python_flit_core instead of setuptools3 for newer Yocto releases

    # Handle that there is no setup.py in the project
    # TODO Remove this once we use python_flit_core
    do_configure:prepend() {
    cat > ${S}/setup.py <<-EOF
    from setuptools import setup

    setup(
        name="${PYPI_PACKAGE}",
        version="${PV}",
        license="${LICENSE}",
    )
    EOF
    }

Save your recipe to a file :file:`python3-minimalmodbus_2.0.1.bb`.

Put the recipe file in one of your Yocto layers.

If you need to create a new layer, a brief introduction is given here.
In the :file:`build` directory, run the *bitbake-layers* command to create a new layer.
We use the layer name ``meta-minimalmodbustutorial`` in this tutorial::

    bitbake-layers create-layer ../meta-minimalmodbustutorial

Put the :file:`python3-minimalmodbus_VERSION.bb` recipe file in a subdirectory
:file:`recipes-devtools/python` within the new layer directory.

Add the layer name to the ``BBLAYERS`` variable in the :file:`build/conf/bblayers.conf`
file. Note that also the ``meta-openembedded/meta-python`` layer must be present.

You also need to add this to your :file:`build/conf/local.conf` file::

    IMAGE_INSTALL:append = " python3-minimalmodbus"

When using the recipe for another version of MinimalModbus, change the version
number in the filename. Bitbake will complain that the md5sum and sha256sum not
are correct, but Bitbake will print out the correct values so you can change
the recipe accordingly.

