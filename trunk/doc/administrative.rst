Developer documentation
=======================

Useful development tools
------------------------


SVN
   Version control software. See http://subversion.apache.org/  

PyChecker 
   This is a tool for finding bugs in python source code. See http://pychecker.sourceforge.net/    
   
Sphinx
   For generating HTML documentation. See http://sphinx.pocoo.org/ 

Coverage.py
   Unittest coverage tool. See http://nedbatchelder.com/code/coverage/ 

Each of these have some additional information below on this page.
   
Shortlist of most used SVN commands
-----------------------------------
These are the most used commands::

    svn update
    svn status 
    svn status -v
    svn status -v --no-ignore
    svn diff
    svn add FILENAME or DIRECTORYNAME
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
------------

SVN uses the computer ``locale`` settings for selecting the language (including keyword substitution). 

Language settings::

    locale      # Shows present locale settings
    locale -a   # Shows available locales
    export LC_ALL="en_US.utf8"

Preparation for release
-----------------------
* Manually change the ``__version__`` and ``__status__`` fields in the :file:`.py` source files.
* Manually change the release date in CHANGES.txt

Check the code::

    pychecker eurotherm3500.py 
    pychecker minimalmodbus.py 
    pychecker omegacn7500.py

Run unit tests (in the :file:`trunc/test` directory)::
    
    python test_all.py


2to3 tool


Test the source distribution build (look in the PKG-INFO file)::

    python setup.py sdist

Make sure the Subversion is updated::

    svn status -v --no-ignore

Make a tag in Subversion::
 
    svn copy https://minimalmodbus.svn.sourceforge.net/svnroot/minimalmodbus/trunk https://minimalmodbus.svn.sourceforge.net/svnroot/minimalmodbus/tags/0.20 -m "Release 0.20"

Build the source distribution (as :file:`.gzip.tar` and :file:`.zip`) , and upload it to PYPI (will use the README.txt etc)::

    python setup.py register
    python setup.py sdist --formats=gztar,zip upload

Build the HTML and PDF documentation  ( in :file:`/doc` after making sure that ``PYTHONPATH`` is correct)::

    make html
    make latexpdf

Build the test coverage report::

    coverage run test_all.py
	coverage html
	
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

On a Windows machine, build the windows installer:: 

    python setup.py bdist_wininst

Upload the windows installer to PYPI by logging in, and uploading it manually.

Upload the windows installer to Sourceforge.

Notes on distribution
---------------------
??

python setup.py register sdist --formats=gztar,zip upload

How to generate a source distribution of the present development code
-----------------------------------------------------------------------

This will create a subfolder **dist** with zipped or gztared source folders::

    python setup.py sdist
    python setup.py sdist --formats=gztar,zip


Notes on generating binary distributions
----------------------------------------

This will create the subfolders ``build`` and ``dist``::

    python setup.py bdist

This will create a subfolder ``dist`` with a Windows installer::

    python setup.py bdist --formats=wininst


Test a distribution before installing it
----------------------------------------

This will create a subfolder ``build``::

    python setup.py build


Install a distribution
----------------------
Use::

    sudo python setup.py install

On a development machine, go to the minimalmodbus/trunk directory before running the command.


Installation target
-------------------
On Linux machines, for example::

    /usr/local/lib/python2.6/dist-packages

On Windows machines, for example::

    C:\python27\Lib\site-packages

The Windows installer also creates a :file:`.pyo` file (and also the :file:`.pyc` file).


Sphinx usage
------------
The documentation is generated with the Sphinx tool: http://sphinx.pocoo.org/

Install it with::

   ?


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


Spinx formatting conventions
----------------------------

Top level heading underlining symbol: = (equals)

Next lower level: - (minus)

A third level if necessary (avoid this): ` (backquote)


Sphinx build commands
---------------------
Note that the PYTHONPATH must be set properly, so that Sphinx can import the modules to document. See below.

In the :file:`trunc/doc` directory::

    sphinx-build -b html -d build/doctrees  -a . build/html

or use the :file:`Makefile`::

    make html
    make latexpdf
    
If the python source files not are updated in the html output, then remove the contents of :file:`trunk/doc/build/doctrees` and rebuild the documentation. (This has now been included in the :file:`Makefile`).

Remember that the :file:`Makefile` uses tabs for indentation, not spaces.

Unittest coverage measurement
----------------------------------

Install the script coverage.py::

    sudo easy_install coverage

Collect test data::

    coverage run test_minimalmodbus.py
    
Generate html report (ends up in trunk/test/htmlcov)::

    coverage html
    
Or to exclude some third party modules (adapt to your file structure):
    
    coverage html --omit=/usr/share/*
    

Setting the PYTHONPATH
----------------------

To set the path::
    
    echo $PYTHONPATH
    export PYTHONPATH='/home/jonas/pythonprogrammering/minimalmodbus/trunk'

or::

    export PYTHONPATH=$PYTHONPATH:/home/jonas/pythonprogrammering/minimalmodbus/trunk

It is better to set the path in the :file:`.basrc` file.


Downloading backups from the Sourceforge server
-----------------------------------------------
To download the svn repository in archive format, type this in the destination directory on your computer::

    rsync -av minimalmodbus.svn.sourceforge.net::svn/minimalmodbus/* .

Known issues
----------------
Sending negative values to the slave is not yet implemented. If this is an issue for you, please provide the manual for your instrument.

Changing `close_port_after_each_call` after instantiation of Instrument() might be 
problematic. Set the value minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL=True instead.


TODO
----

  * Write more unittests
  * Check error codes
  * Write documentation with examples.
  * Test with Python3 and 2to3
  * Test the dependency of pySerial in setup.py
  
  * Upload files with ``scp -r`` instead

For next release:
  * Bug tracker settings
  * dummy_serial: Use isOpen() to make sure opening and closing works fine.

.




