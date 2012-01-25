Developer documentation
=======================

Follow the coding progress in the SVN repository (click on the revision number to see the actual file content):
http://minimalmodbus.svn.sourceforge.net/viewvc/minimalmodbus/trunk/

Design considerations
-----------------------------------------------------------------------------

My take on the design is that is should be as simple as possible, hence the name MinimalModbus, but it should implement the smallest number of functions needed for it to be useful. The target audience for this driver simply wants to talk to Modbus clients using a serial interface (RTU is good enough), using some simple driver (preferably MinimalModbus).

Only functions for reading/writing one register or bit are implemented. It is very easy to implement lots of (seldom used) functions, resulting in buggy code with large fractions of it almost never used. It is instead much better to implement the features when needed/requested. There are many Modbus function codes, but I guess that most are not used.

It is a goal that the same driver should be compatible for both Python2 and Python3 programs. Some suggestions for making this possible are found here:
http://wiki.python.org/moin/PortingPythonToPy3k

There should be unittests for all functions, and mock communication data.

Errors should be caught as early as possible, and the error messages should be informative.

Note that the term 'address' is ambigous, why it is better to use the terms 'register address' or 'slave address'.

Use only external links in the README.txt, otherwise they will not work on Python Package Index (PyPI). No Sphinx-specific constructs are allowed in that file.


General driver structure
-------------------------------------------------------------------------

The general structure of the program is shown here:

=========================== ================================================================================
Function                    Description
=========================== ================================================================================
:meth:`.read_register`      One of the facades for :meth:`._genericCommand`.
:meth:`._genericCommand`    Generates payload, then calls :meth:`._performCommand`.
:meth:`._performCommand`    Embeds payload into error-checking codes etc, then calls :meth:`._communicate`.
:meth:`._communicate`       Handles raw strings for communication via pySerial.
=========================== ================================================================================

Most of the logic is located in separate (easy to test) functions on module level. For a desctription of them, see :ref:`internalminimalmodbus`. 


Unittesting
------------------------------------------------------------------------------
A brief introduction to unittesting is found here: http://docs.python.org/release/2.5.2/lib/minimal-example.html

Inside the unpacked folder go to :file:`test` and run the unit tests with::
     
    python test_all.py
    python3 test_all.py

    python3.2 test_all.py
    python2.6 test_all.py
    python2.7 test_all.py

It is also possible to run the individual test files::

    python test_minimalmodbus.py
    python test_eurotherm3500.py
    python test_omegacn7500.py


Making sure that error messages are informative for the user
------------------------------------------------------------------------------
To have a look on the error messages raised during unit testing of :mod:`minimalmodbus`, 
monkey-patch :data:`test_minimalmodbus.SHOW_ERROR_MESSAGES_FOR_ASSERTRAISES` as seen here::

    >>> import unittest
    >>> import test_minimalmodbus
    >>> test_minimalmodbus.SHOW_ERROR_MESSAGES_FOR_ASSERTRAISES = True
    >>> suite = unittest.TestLoader().loadTestsFromModule(test_minimalmodbus)
    >>> unittest.TextTestRunner(verbosity=2).run(suite)

This is part of the output::

    testFunctioncodeNotInteger (test_minimalmodbus.TestEmbedPayload) ... 
        TypeError('The functioncode must be an integer. Given: 1.0',)

        TypeError("The functioncode must be an integer. Given: '1'",)

        TypeError('The functioncode must be an integer. Given: [1]',)

        TypeError('The functioncode must be an integer. Given: None',)
    ok
    testKnownValues (test_minimalmodbus.TestEmbedPayload) ... ok
    testPayloadNotString (test_minimalmodbus.TestEmbedPayload) ... 
        TypeError('The payload should be a string. Given: 1',)

        TypeError('The payload should be a string. Given: 1.0',)

        TypeError("The payload should be a string. Given: ['ABC']",)

        TypeError('The payload should be a string. Given: None',)
    ok
    testSlaveaddressNotInteger (test_minimalmodbus.TestEmbedPayload) ... 
        TypeError('The slaveaddress must be an integer. Given: 1.0',)

        TypeError("The slaveaddress must be an integer. Given: 'DEF'",)
    ok
    testWrongFunctioncodeValue (test_minimalmodbus.TestEmbedPayload) ... 
        ValueError('The functioncode is too large: 222, but maximum value is 127.',)

        ValueError('The functioncode is too small: -1, but minimum value is 1.',)
    ok
    testWrongSlaveaddressValue (test_minimalmodbus.TestEmbedPayload) ... 
        ValueError('The slaveaddress is too large: 248, but maximum value is 247.',)

        ValueError('The slaveaddress is too small: -1, but minimum value is 0.',)
    ok

See :mod:`test_minimalmodbus` for details on how this is implemented.

Recording communication data for unittesting
-------------------------------------------------------------------------
With the known data output from an instrument, we can finetune the inner details 
of the driver (code refactoring) without worrying that we change the output from the code. 
This data will be the 'golden standard' to which we test the code. 
Use as many as possible of the commands, and paste all the output in a text document. 
From this it is pretty easy to reshuffle it into unittest code. 

Here is an example how to record communication data, which then is pasted 
into the test code (for use with a mock/dummy serial port). See for example
:ref:`testminimalmodbus` (click '[source]' on right side, see RESPONSES at end of the page). Do like this::

   >>> import minimalmodbus
   >>> minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True # Seems mandatory for Windows
   >>> instrument_1 = minimalmodbus.Instrument('/dev/ttyUSB0',10)
   >>> instrument_1.debug = True
   >>> instrument_1.read_register(4097,1)
   MinimalModbus debug mode. Writing to instrument: '\n\x03\x10\x01\x00\x01\xd0q'
   MinimalModbus debug mode. Response from instrument: '\n\x03\x02\x07\xd0\x1e)'
   200.0
   >>> instrument_1.write_register(4097,325.8,1)
   MinimalModbus debug mode. Writing to instrument: '\n\x10\x10\x01\x00\x01\x02\x0c\xbaA\xc3'
   MinimalModbus debug mode. Response from instrument: '\n\x10\x10\x01\x00\x01U\xb2'
   >>> instrument_1.read_register(4097,1)
   MinimalModbus debug mode. Writing to instrument: '\n\x03\x10\x01\x00\x01\xd0q'
   MinimalModbus debug mode. Response from instrument: '\n\x03\x02\x0c\xba\x996'
   325.8
   >>> instrument_1.read_bit(2068)
   MinimalModbus debug mode. Writing to instrument: '\n\x02\x08\x14\x00\x01\xfa\xd5'
   MinimalModbus debug mode. Response from instrument: '\n\x02\x01\x00\xa3\xac'
   0
   >>> instrument_1.write_bit(2068,1)
   MinimalModbus debug mode. Writing to instrument: '\n\x05\x08\x14\xff\x00\xcf%'
   MinimalModbus debug mode. Response from instrument: '\n\x05\x08\x14\xff\x00\xcf%'

This is also very useful for debugging drivers built on top of MinimalModbus. See 
for example the test code for omegacn7500 :ref:`testomegacn7500` (click '[source]', 
see RESPONSES at end of the page).


Using the dummy serial port
-------------------------------------------------------------------------------
A dummy serial port is included for testing purposes, see :mod:`dummy_serial`. Use it like this::

    >>> import dummy_serial
    >>> import test_minimalmodbus
    >>> dummy_serial.RESPONSES = test_minimalmodbus.RESPONSES # Load previously recorded responses
    >>> import minimalmodbus
    >>> minimalmodbus.serial.Serial = dummy_serial.Serial # Monkey-patch a dummy serial port
    >>> instrument = minimalmodbus.Instrument('DUMMYPORTNAME', 1) # port name, slave address (in decimal)
    >>> instrument.read_register(4097, 1)
    823.6

In the example above there is recorded data available for ``read_register(4097, 1)``. If no 
recorded data is available, an error message is displayed::

    >>> instrument.read_register(4098, 1)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/jonas/pythonprogrammering/minimalmodbus/trunk/minimalmodbus.py", line 174, in read_register
        return self._genericCommand(functioncode, registeraddress, numberOfDecimals=numberOfDecimals)
      File "/home/jonas/pythonprogrammering/minimalmodbus/trunk/minimalmodbus.py", line 261, in _genericCommand
        payloadFromSlave = self._performCommand(functioncode, payloadToSlave)
      File "/home/jonas/pythonprogrammering/minimalmodbus/trunk/minimalmodbus.py", line 317, in _performCommand
        response            = self._communicate(message)
      File "/home/jonas/pythonprogrammering/minimalmodbus/trunk/minimalmodbus.py", line 395, in _communicate
        raise IOError('No communication with the instrument (no answer)')
    IOError: No communication with the instrument (no answer)

The dummy serial port can be used also with instrument drivers built on top of MinimalModbus::

    >>> import dummy_serial
    >>> import test_omegacn7500
    >>> dummy_serial.RESPONSES = test_omegacn7500.RESPONSES # Load previously recorded responses
    >>> import omegacn7500
    >>> omegacn7500.minimalmodbus.serial.Serial = dummy_serial.Serial # Monkey-patch a dummy serial port
    >>> instrument = omegacn7500.OmegaCN7500('DUMMYPORTNAME', 1) # port name, slave address
    >>> instrument.get_pv()
    24.6


Data encoding in Python2 and Python3
------------------------------------------------------------------------------
The **string** type has changed in Python3 compared to Python2. In Python3 the type 
**bytes** is used when communicating via pySerial.

Dependent on the Python version number, the data sent from MinimalModbus to pySerial has different types.

String constants
````````````````````
This is a **string** constant both in Python2 and Python3::

    st = 'abc\x69\xe6\x03'
    
This is a **bytes** constant in Python3, but a **string** constant in Python2 (allowed for 2.6 and higher)::

    by = b'abc\x69\xe6\x03' 
    
Type conversion in Python3
```````````````````````````
To convert a **string** to **bytes**, use one of these::

    bytes(st, 'latin1') # Note that 'ascii' encoding gives error for some values.
    st.encode('latin1')
 
To convert **bytes** to **string**, use one of these::    

    str(by, encoding='latin1')
    by.decode('latin1')
    
======== =============    
Encoding Allowed range
======== =============
ascii    0-127
latin-1  0-255
======== =============

Corresponding in Python2
````````````````````````
Ideally, we would like to use the same source code for Python2 and Python3. In Python 2.6 and higher 
there is the :func:`bytes` function for forward compatibility, but it is merely a 
synonym for :func:`str`.

To convert from '**bytes**'(**string**) to **string**::

    str(by) # not possible to give encoding    
    by.decode('latin1') # Gives unicode

To convert from **string** to '**bytes**'(**string**)::

    bytes(st) # not possible to give encoding   
    st.encode('latin1') # Can not be used for values larger than 127

It is thus not possible to use exactly the same code for both Python2 and Python3.
Where it is unavoidable, use::

    if sys.version_info[0] > 2:
        whatever


Extending MinimalModbus
------------------------------------------------------------------------------
It is straight-forward to extend MinimalModbus to handle more Modbus function codes.
Use the the method :meth:`_performCommand` to send data to the 
slave, and to receive the response. Note that the API might change, as this is 
outside the official API.

This is easily tested in interactive mode. For example the method :meth:`.read_register` 
generates payload, which internally is sent to the instrument using :meth:`_performCommand`::

    >>> instr.debug = True
    >>> instr.read_register(5,1)
    MinimalModbus debug mode. Writing to instrument: '\x01\x03\x00\x05\x00\x01\x94\x0b'
    MinimalModbus debug mode. Response from instrument: '\x01\x03\x02\x00º9÷'
    18.6

It is possible to use :meth:`_performCommand` directly. You can use any Modbus function code (1-127),
but you need to generate the payload yourself. Note that the same data is sent::

    >>> instr._performCommand(3, '\x00\x05\x00\x01')
    MinimalModbus debug mode. Writing to instrument: '\x01\x03\x00\x05\x00\x01\x94\x0b'
    MinimalModbus debug mode. Response from instrument: '\x01\x03\x02\x00º9÷'
    '\x02\x00º'

Use this if you are to implement other Modbus function codes, as it takes care of
CRC generation etc.

There are several useful helper functions available in the :mod:`minimalmodbus` module. 
See :ref:`internalminimalmodbus`. 


Found a bug?
------------------------------------------------------------------------------
Try to isolate the bug by running in interactive mode (Python interpreter) with debug mode activated. Send a mail to the mailing list with the output, and also the output from :meth:`._getDiagnosticString`.

Of course it is appreciated if you can spend a few moments trying to locate the 
problem, as it might possibly be related to your particular instrument (and thus 
difficult to reproduce without it). The source code is very readable, so 
is should be straight-forward to work with. Then please send your findings to 
the mailing list.


Webpage
------------------------------------------------------------------------------
The HTML theme on http://minimalmodbus.sourceforge.net/ is the Sphinx 'Default' theme. 

* The colors etc are adjusted in the :file:`doc/config.py` file. 
* Header sizes are adjusted in the :file:`doc/_static/default.css` file.

Note that Sphinx version 1.1.2 or later is required to build the documentation.


Notes on distribution
-------------------------------------------------------------------------------

Installing the module from local svn files
````````````````````````````````````````````
In the trunk directory::

    sudo python setup.py install
    
If there are conditional ``__name__ == '__main__'`` clauses in the module, 
these can be tested using (adapt path to your system)::

    python /usr/local/lib/python2.6/dist-packages/eurotherm3500.py
    python /usr/local/lib/python2.6/dist-packages/minimalmodbus.py    


How to generate a source distribution from the present development code
`````````````````````````````````````````````````````````````````````````
This will create a subfolder :file:`dist` with zipped or gztared source folders::

    python setup.py sdist
    python setup.py sdist --formats=gztar,zip


Notes on generating binary distributions
````````````````````````````````````````
This will create the subfolders :file:`build` and :file:`dist`::

    python setup.py bdist

This will create a subfolder :file:`dist` with a Windows installer::

    python setup.py bdist --formats=wininst


Build a distribution before installing it
`````````````````````````````````````````
This will create a subfolder :file:`build`::

    python setup.py build


Preparation for release
-------------------------------------------------------------------------------

Change version number etc
`````````````````````````
* Manually change the ``__version__`` and ``__status__`` fields in the :file:`minimalmodbus.py` source file.
* Manually change the ``version`` field in the :file:`setup.py` file.
* Manually change the release date in :file:`CHANGES.txt`

(Note that the version number in the Sphinx configuration file :file:`doc/conf.py` is changed automatically. Unfortunately this is not yet valid :file:`setup.py`).


Code style checking etc
```````````````````````
Check the code::

    pychecker eurotherm3500.py 
    pychecker minimalmodbus.py 
    pychecker omegacn7500.py

(The 2to3 tool is not necessary, as we run unittests under both Python2 and Python3).

Unittesting
```````````
Run unit tests (in the :file:`trunk/test` directory)::
    
    python test_all.py
    python3 test_all.py

Test the source distribution generation (look in the :file:`PKG-INFO` file)::

    python setup.py sdist

Also make sure that these are functional (see sections below):
  * Documentation generation 
  * Test coverage report generation

Prepare subversion
```````````````````
Make sure the Subversion is updated::

    svn update
    svn status -v --no-ignore

Make a tag in Subversion (adapt to version number)::
     
    svn copy https://minimalmodbus.svn.sourceforge.net/svnroot/minimalmodbus/trunk https://minimalmodbus.svn.sourceforge.net/svnroot/minimalmodbus/tags/0.3 -m "Release 0.3"

Upload to PyPI
``````````````
Build the source distribution (as :file:`.gzip.tar` and :file:`.zip`) , and upload it to PYPI (will use the :file:`README.txt` etc)::

    python setup.py register
    python setup.py sdist --formats=gztar,zip upload


Generate documentation
``````````````````````
Build the HTML and PDF documentation  (in :file:`doc` after making sure that :envvar:`PYTHONPATH` is correct)::

    make html
    make latexpdf

Build the test coverage report (first manually clear the directory :file:`htmlcov`)::
   
    coverage run ./test/test_all.py
    coverage html --omit=/usr/*
    
	
Upload to Sourceforge
``````````````````````
Upload the :file:`.gzip.tar` and :file:`.zip` files to Sourceforge by logging in and manually using the web form.

Upload the generated documentation to Sourceforge. In directory :file:`trunk/doc/build/html`::

    scp -r * pyhys,minimalmodbus@web.sourceforge.net:htdocs

Upload the documentation PDF. In directory :file:`trunk/doc/build/latex`::

    scp minimalmodbus.pdf pyhys,minimalmodbus@web.sourceforge.net:htdocs

Upload the test coverage report. In directory :file:`trunk`::

    scp -r htmlcov pyhys,minimalmodbus@web.sourceforge.net:htdocs


Test documentation
`````````````````````
Test links on the Sourceforge and PyPI pages. If adjustments are required on the PyPI page, log in and manually adjust the text. This might be for exampe parsing problems with the ReSTR text (allows no Sphinx-specific constructs).


Generate Windows installer
``````````````````````````
On a Windows machine, build the windows installer:: 

    python setup.py bdist_wininst

Upload the Windows installer to PYPI by logging in, and uploading it manually.

Upload the Windows installer to Sourceforge by manually using the web form.


Test installer
``````````````
Make sure that the installer works, and the dependencies are handled correctly.
Try at least Linux and Windows.


Marketing
````````````
  * Mailing list
  * Sourceforge project news
  * Freecode (former Freshmeat)
  * Facebook


Downloading backups from the Sourceforge server
-----------------------------------------------
To download the svn repository in archive format, type this in the destination directory on your computer::

    rsync -av minimalmodbus.svn.sourceforge.net::svn/minimalmodbus/* .


Useful development tools
------------------------------------------------------------------------------
Each of these have some additional information below on this page.

SVN
   Version control software. See http://subversion.apache.org/  
   
Sphinx
   For generating HTML documentation. See http://sphinx.pocoo.org/ 

Coverage.py
   Unittest coverage tool. See http://nedbatchelder.com/code/coverage/ 

PyChecker 
   This is a tool for finding bugs in python source code. See http://pychecker.sourceforge.net/   

pep8.py
   Code style checker. See https://github.com/jcrocholl/pep8#readme 
  
   
Subversion (svn) usage
-----------------------------------------------------------------------------   
Subversion provides an easy way to share code with each other. You can find all MinimalModbus files on the subversion repository on http://minimalmodbus.svn.sourceforge.net/viewvc/minimalmodbus/ Look in the trunk subfolder.

Some usage instructions are found on http://sourceforge.net/scm/?type=svn&group_id=548418


Install SVN on some Linux machines
``````````````````````````````````
Install it with::

    sudo apt-get install subversion

Download the files
```````````````````   
The usage is::

    svn checkout URL NewSubfolder

where *NewSubfolder* is the name of a subfolder that will be created in present directory. You can also write ``svn co`` instead of ``svn checkout``.

In a proper directory on your computer, download the files (not only the :file:`trunk` subfolder) using::

  svn co https://minimalmodbus.svn.sourceforge.net/svnroot/minimalmodbus minimalmodbus   
   
   
Submit contributions
``````````````````````
First run the ``svn update`` command to download the latest changes from the repository. Then make the changes in the files. Use the ``svn status`` command to see which files you have changed. Then upload your changes with the ``svn commit -m 'comment'`` command. Note that it easy to revert any changes in SVN, so feel free to test.

   
Shortlist of frequently used SVN commands
``````````````````````````````````````````
These are the most used commands::

    svn update
    svn status 
    svn status -v
    svn status -v --no-ignore
    svn diff
    svn add FILENAME or DIRECTORYNAME
    svn remove FILENAME or DIRECTORYNAME
    svn commit -m 'Write your log message here'

In the 'trunk' directory::

    svn propset svn:ignore html .
    svn proplist
    svn propget svn:ignore

or if ignoring multiple items, edit the list using:: 

    svn propedit svn:ignore .

Automatic keyword substitution::

    svn propset svn:keywords "Date Revision" minimalmodbus.py
    svn propset svn:keywords "Date Revision" eurotherm3500.py
    svn propset svn:keywords "Date Revision" README.txt
    svn propget svn:keywords minimalmodbus.py


SVN settings
`````````````
SVN uses the computer ``locale`` settings for selecting the language (including keyword substitution). 

Language settings::

    locale      # Shows present locale settings
    locale -a   # Shows available locales
    export LC_ALL="en_US.utf8"


Sphinx usage
-------------------------------------------------------------------------------
This documentation is generated with the Sphinx tool: http://sphinx.pocoo.org/

It is used to automatically generate HTML documentation from docstrings in the source code.
See for example :ref:`internalminimalmodbus`. To see the source code of the Python 
file, click [source] on the right part of that side. To see the source of the 
Sphinx page definition file, click 'Show Source' in the left column.

To install, use::

   easy_install sphinx
   
or possibly::

    sudo easy_install sphinx

Check installed version by typing::

    sphinx-build   

Spinx formatting conventions
````````````````````````````
=================== =============================================== =====================================
What                Usage                                           Result
=================== =============================================== =====================================
Inline web link     ```Link text <http://example.com/>`_``          `Link text <http://example.com/>`_
Internal link       ``:ref:`testminimalmodbus```                    :ref:`testminimalmodbus`
Inline code         ````code text````                               ``code text``
Environment var     ``:envvar:`PYTHONPATH```                        :envvar:`PYTHONPATH`
OS-level command    ``:command:`make```                             :command:`make`
File                ``:file:`minimalmodbus.py```                    :file:`minimalmodbus.py`
Path                ``:file:`path/to/myfile.txt```                  :file:`path/to/myfile.txt` 
Type                ``**bytes**``                                   **bytes**
Module              ``:mod:`minimalmodbus```                        :mod:`minimalmodbus`     
Data                ``:data:`.BAUDRATE```                           :data:`.BAUDRATE`
Data (full)         ``:data:`minimalmodbus.BAUDRATE```              :data:`minimalmodbus.BAUDRATE`
Constant            ``:const:`False```                              :const:`False`
Function            ``:func:`._checkInt```                          :func:`._checkInt` 
Function (full)     ``:func:`minimalmodbus._checkInt```             :func:`minimalmodbus._checkInt` 
Argument            ``*payload*``                                   *payload*
Class               ``:class:`.Instrument```                        :class:`.Instrument`   
Class (full)        ``:class:`minimalmodbus.Instrument```           :class:`minimalmodbus.Instrument`  
Method              ``:meth:`.read_bit```                           :meth:`.read_bit`
Method (full)       ``:meth:`minimalmodbus.Instrument.read_bit```   :meth:`minimalmodbus.Instrument.read_bit`
=================== =============================================== =====================================

Note that only the functions and methods that are listed in the index will show as links.

Headings
  * Top level heading underlining symbol: = (equals)
  * Next lower level: - (minus)
  * A third level if necessary (avoid this): ` (backquote)

Internal links
  * Add an internal marker ``.. _my-reference-label:`` before a heading.
  * Then make an internal link to it using ``:ref:`my-reference-label```.

Useful Sphinx-related links
```````````````````````````
Online resources for the formatting used (reStructuredText):

Sphinx reStructuredText Primer
    http://sphinx.pocoo.org/rest.html

Spinx autodoc features
    http://sphinx.pocoo.org/ext/autodoc.html

Sphinx cross-referencing Python objects
    http://sphinx.pocoo.org/domains.html#python-roles

Example usage for API documentation
    http://packages.python.org/an_example_pypi_project/sphinx.html

Sphinx syntax shortlist
    http://docs.geoserver.org/trunk/en/docguide/sphinx.html

reStructuredText Markup Specification 
    http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html

Sphinx build commands
`````````````````````
To build the documentation, go to the directory :file:`trunk/doc` and then run::

   make html

That should generate HTML files to the directory :file:`trunk/doc/build/html`. 

To generate PDF::

   make latexpdf

Note that the :envvar:`PYTHONPATH` must be set properly, so that Sphinx can import the modules to document. See below.

It is also possible to run without the :command:`make` command. In the :file:`trunk/doc` directory::

    sphinx-build -b html -d build/doctrees  -a . build/html
    
If the python source files not are updated in the HTML output, then remove the contents of :file:`trunk/doc/build/doctrees` and rebuild the documentation. (This has now been included in the :file:`Makefile`).

Remember that the :file:`Makefile` uses tabs for indentation, not spaces.

Sometimes there are warnings and errors when  generating the HTML pages. They can appear different, but are most often related to problems importing files. In that case start the Python interpreter and try to import the module, for example::

   >>> import test_minimalmodbus
 
From there you can most often solve the problem.


Unittest coverage measurement using coverage.py
-----------------------------------------------------------------------------
Install the script :file:`coverage.py`::

    sudo easy_install coverage

Collect test data::

    coverage run test_minimalmodbus.py

or::

    coverage run test_all.py    
    
Generate html report (ends up in :file:`trunk/test/htmlcov`)::

    coverage html
    
Or to exclude some third party modules (adapt to your file structure)::

    coverage html --omit=/usr/*


Using the pep8 style checker tool
------------------------------------------------------------------------------
This tool checks the coding style. See http://pypi.python.org/pypi/pep8/

Install the pep8 checker tool::

    sudo pip install pep8

Run it::

    pep8 minimalmodbus.py

or:: 

    pep8 --statistics minimalmodbus.py
    
    pep8 --show-pep8  minimalmodbus.py
    
    pep8 --show-source  minimalmodbus.py 
    

TODO
----
 
For next release:
  * Read ``version`` from minimalmodbus to setup.py 
  * Bug tracker settings
  * Finetune coding style (pep8.py)
  * dummy_serial: Use isOpen() to make sure opening and closing works fine.

.




