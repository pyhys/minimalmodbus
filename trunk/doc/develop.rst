Developer documentation
=======================

Follow the coding progress on this page (click on the revision number to see the actual file content):
http://minimalmodbus.svn.sourceforge.net/viewvc/minimalmodbus/trunk/

Design considerations
-----------------------------------------------------------------------------

My take on the design is that is should be as simple as possible, hence the name MinimalModbus, but it should implement the smallest number of functions needed for it to be useful. The target audience for this driver simply wants to talk to Modbus clients using serial interface (RTU is good enough), using some simple driver (preferably MinimalModbus).

Only functions for reading/writing one register or bit are implemented. It is very easy to implement lots of (seldom used) functions, resulting in buggy code with large fractions of it almost not tested. It is instead much better to implement the features when needed/requested. There are many Modbus function codes, but I guess that most are not used.

It is a goal is that the same driver should be compatible for both python2 and python3 programs. Some suggestions for making this possible are found here:
http://wiki.python.org/moin/PortingPythonToPy3k

There should be unittests for all functions, and mock communication data.

Note that the term 'address' is ambigous, why it is better to use the terms 'register address' or 'slave address'


General drive structure
-------------------------------------------------------------------------


read_register()
_genericCommand() Generates payload
_performCommand() Embeds payload
_communicate() Handles raw strings



Unittesting
------------------------------------------------------------------------------
A brief introduction to unittesting is found here: http://docs.python.org/release/2.5.2/lib/minimal-example.html

To run the unit tests::
     
    python test_all.py
    python3 test_all.py


    python3.2 test_all.py
    python2.6 test_all.py
    python2.7 test_all.py

Installing the module from  local svn files
--------------------------------------------
Then try to install it on your computer (by first building a sourcedist

Recording communication data for unittesting
-------------------------------------------------------------------------
With the known data output from an instrument, we can finetune the inner details 
of the driver (code refactoring) without worrying that we change the output from the code. 
This data will be the 'golden standard' to which we test the code. 
Use as many as possible of the commands, and paste all the output in a text document. 
From this it is pretty easy to reshuffle it into unittest code. 

Here is an example how to record communication data, which then is pasted 
into the test code (for use with a dummy serial port). See for example
:ref:`testminimalmodbus` (click '[source]' on right side, see at end of the page). Do like this::

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
see at end of the page).


Webpage
------------------------------------------------------------------------------
The HTML theme on http://minimalmodbus.sourceforge.net/ is the Sphinx 'Default' theme. 

* The colors etc are adjusted in the doc/config.py file. 
* Header sizes are adjusted in the doc/_static/default.css file.


Notes on distribution
-------------------------------------------------------------------------------
??

python setup.py register sdist --formats=gztar,zip upload

How to generate a source distribution of the present development code
`````````````````````````````````````````````````````````````````````

This will create a subfolder **dist** with zipped or gztared source folders::

    python setup.py sdist
    python setup.py sdist --formats=gztar,zip


Notes on generating binary distributions
````````````````````````````````````````

This will create the subfolders ``build`` and ``dist``::

    python setup.py bdist

This will create a subfolder ``dist`` with a Windows installer::

    python setup.py bdist --formats=wininst


Test a distribution before installing it
````````````````````````````````````````

This will create a subfolder ``build``::

    python setup.py build





Preparation for release
-------------------------------------------------------------------------------

Change version number etc
`````````````````````````
* Manually change the ``__version__`` and ``__status__`` fields in the :file:`.py` source files. setup.py ???
* Manually change the release date in CHANGES.txt


Code style checking etc
```````````````````````

(2to3 tool)

Check the code::

    pychecker eurotherm3500.py 
    pychecker minimalmodbus.py 
    pychecker omegacn7500.py


Unittesting
```````````
Run unit tests (in the :file:`trunc/test` directory)::
    
    python test_all.py





Test the source distribution build (look in the PKG-INFO file)::

    python setup.py sdist




Make sure the Subversion is updated::

    svn status -v --no-ignore

Make a tag in Subversion::
 
    svn copy https://minimalmodbus.svn.sourceforge.net/svnroot/minimalmodbus/trunk https://minimalmodbus.svn.sourceforge.net/svnroot/minimalmodbus/tags/0.20 -m "Release 0.20"

Build the source distribution (as :file:`.gzip.tar` and :file:`.zip`) , and upload it to PYPI (will use the README.txt etc)::

    python setup.py register
    python setup.py sdist --formats=gztar,zip upload


Documentation
``````````````
Build the HTML and PDF documentation  ( in :file:`/doc` after making sure that ``PYTHONPATH`` is correct)::

    make html
    make latexpdf

Build the test coverage report::

    coverage run test_all.py
	coverage html
	
	
Upload
```````	
	
Upload the :file:`.gzip.tar` and :file:`.zip` files to Sourceforge by logging in and manually using the web form.

Upload the generated documentation to Sourceforge. In directory trunk/doc/build/html::

    sftp pyhys@web.sourceforge.net
    cd /home/project-web/minimalmodbus/htdocs
    put *.*     

    mkdir _modules
    cd _modules/
    lcd _modules/
    lls
    put *.*

    etc

Upload the test coverage report::

    ?	
	
Upload the documentation PDF by (in proper directory)::

    put *.pdf


Generate Windows installer
``````````````````````````

On a Windows machine, build the windows installer:: 

    python setup.py bdist_wininst

Upload the windows installer to PYPI by logging in, and uploading it manually.

Upload the windows installer to Sourceforge.





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

Download the files
```````````````````   
In a proper directory on your computer, download the files (not only the trunk subfolder) using::

  svn co https://minimalmodbus.svn.sourceforge.net/svnroot/minimalmodbus minimalmodbus   
   
Submit contributions
``````````````````````
First run the ``svn update`` command to download the latest changes from the repository. Then make the changes in the files. Use the ``svn status`` command to see which files you have changed. Then upload your changes with the commit version of the command. Note that it easy to revert any changes in the svn, so feel free to test.

   
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
The documentation is generated with the Sphinx tool: http://sphinx.pocoo.org/

It is used to automatically generate HTML documentation from the source code.
See for example :ref:`internalminimalmodbus`.

To install, use::

   easy_install sphinx
   
or possibly::

    sudo easy_install sphinx

Check installed version by typing::

    sphinx-build   



Spinx formatting conventions
````````````````````````````
There is a good introduction to the formatting used (reStructuredText):
http://sphinx.pocoo.org/rest.html

Top level heading underlining symbol: = (equals)

Next lower level: - (minus)

A third level if necessary (avoid this): ` (backquote)


Use ```Link text <http://example.com/>`_`` for inline web links.

Use backquotes ````text```` for code samples.

Add an internal marker ``.. _my-reference-label:`` before a heading.
Then make an internal link to it using::

    :ref:`my-reference-label` 

Sphinx build commands
`````````````````````
To build the documentation, go to the directory ../trunk/doc and then run::

   make html

That should generate HTML files to the directory ../trunk/doc/build/html

To generate PDF::

   make latexpdf

Note that the PYTHONPATH must be set properly, so that Sphinx can import the modules to document. See below.

It is also possible to run without the ``make`` command. In the :file:`trunc/doc` directory::

    sphinx-build -b html -d build/doctrees  -a . build/html
    
If the python source files not are updated in the html output, then remove the contents of :file:`trunk/doc/build/doctrees` and rebuild the documentation. (This has now been included in the :file:`Makefile`).

Remember that the :file:`Makefile` uses tabs for indentation, not spaces.

Sometimes there are warnings and errors when  generating the HTML pages. They can appear different, but are most often related to problems importing files. In that case start the Python interpreter and try to import the module, for example::

   >>> import test_minimalmodbus
 
From there you can most often solve the problem.


Useful Sphinx-related links
```````````````````````````

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


Unittest coverage measurement using coverage.py
-----------------------------------------------------------------------------

Install the script coverage.py::

    sudo easy_install coverage

Collect test data::

    coverage run test_minimalmodbus.py

or::

    coverage run test_all.py    
    
Generate html report (ends up in trunk/test/htmlcov)::

    coverage html
    
Or to exclude some third party modules (adapt to your file structure)::

    coverage html --omit=/usr/share/*


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

  * Write documentation with examples.
  * Test run with process controller, using python2 and python3
  * Proofread and test aapi
  
  * Upload files with ``scp -r`` instead

For next release:
  * Bug tracker settings
  * dummy_serial: Use isOpen() to make sure opening and closing works fine.

.




