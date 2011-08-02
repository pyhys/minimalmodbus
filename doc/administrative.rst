Developer documentation
=======================


Shortlist of most used SVN commands
-----------------------------------
These are the most used commands::

    svn update
    svn status 
    svn status -v
    svn status -v --no-ignore
    svn add FILENAME or DIRECTORYNAME
    svn commit -m 'Write your log message here'

In the 'trunk' directory::

    svn propset svn:ignore html .
    svn proplist
    svn propget svn:ignore

or if ignoring multiple items, edit the list using:: 

    svn propedit svn:ignore .


Documentation generators
------------------------
pydoc -w modulename # Writes a HTML page in current directory

pydoc -w minimalmodbus

pydoc -w eurotherm3500

epydoc minimalmodbus eurotherm3500 # Writes HTML pages and javascript in the html subfolder

export PYTHONPATH=$PYTHONPATH:/home/jonas/pythonprogrammering/minimalmodbus/trunk
make html


Preparation for release
-----------------------



Check the code::

    pychecker eurotherm3500.py 
    pychecker minimalmodbus.py 

Run tests::

    ??

Make sure the Subversion is updated.

Make a tag in Subversion::
 
  ??

Build the source distribution::

    python setup.py sdist --formats=gztar,zip

Build the documentation ( in /doc after making sure that PYTHONPATH is correct)::

    make html
    make latexpdf

Upload the .gzip.tar and .zip files to PYPI (use web form?). What about README.txt?

Upload the .gzip.tar and .zip files to Sourceforge (use web form?), and upload the generated documentation.

On a Windows machine, build the windows installer:: 

    python setup.py bdist_wininst


Notes on distribution
---------------------
??

python setup.py register sdist --formats=gztar,zip upload

Notes on generating source distributions
----------------------------------------

Create a subfolder **dist** with zipped or gztared source folders::

    python setup.py sdist
    python setup.py sdist --formats=gztar,zip


Notes on generating binary distributions
----------------------------------------

Create subfolders **build** and **dist**::

    python setup.py bdist

Create a subfolder **dist** with a Windows installer::

    python setup.py bdist --formats=wininst


Test distributions
------------------

Create a subfolder **build**::

    python setup.py build


Install a distribution
----------------------
Use::

    sudo python setup.py install


Installation target
-------------------
On Linux machines, for example::

    /usr/local/lib/python2.6/dist-packages

On Windows machines, for example::
    C:\python27\Lib\site-packages

The Windows installer also creates a .pyo file (and also the .pyc file).


Sphinx usage
------------
| Sphinx reStructuredText Primer: http://sphinx.pocoo.org/rest.html
| Example usage for API documentation: http://packages.python.org/an_example_pypi_project/sphinx.html
| Sphinx syntax shortlist http://docs.geoserver.org/trunk/en/docguide/sphinx.html
| reStructuredText Markup Specification http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html


Spinx formatting conventions
----------------------------

Top level heading: ==

Next lower level: --

Sphinx build commands
---------------------

To set the path::
    
    echo $PYTHONPATH
    export PYTHONPATH='/home/jonas/pythonprogrammering/minimalmodbus/trunk'

In the trunc/doc directory::

    sphinx-build -b html -d build/doctrees  -a . build/html

or use the makefile::

    make html
    make latexpdf
    
If the python source files not are updated in the html output, then remove the contents of *trunk/doc/build/doctrees* and rebuild the documentation. 


TODO
----
* In README.txt: Describe modbus types
* Homepage with Sphinx-based API documentation etc
* Mailing list
* Unittests
* Include pydoc pages etc in source distributions
* __version__ etc in source files
* epydoc 
* in setup.py, indicate the dependency of pySerial

CHANGE THIS: instrument.portname instead of  .port

