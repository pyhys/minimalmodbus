Developer documentation
=======================


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
* Manually change ``version`` in the :file:`setup.py` file.
* Manually change the ``__version__`` and ``__status__`` fields in the :file:`.py` source files.
* Manually change the release date in CHANGES.txt

Check the code::

    pychecker eurotherm3500.py 
    pychecker minimalmodbus.py 

Run tests::

    (not yet implemented)

Make sure the Subversion is updated::

    svn status -v --no-ignore

Make a tag in Subversion::
 
    svn copy https://minimalmodbus.svn.sourceforge.net/svnroot/minimalmodbus/trunk https://minimalmodbus.svn.sourceforge.net/svnroot/minimalmodbus/tags/0.20 -m "Release 0.20"

Build the source distribution::

    python setup.py sdist --formats=gztar,zip

Build the HTML and PDF documentation  ( in :file:`/doc` after making sure that ``PYTHONPATH`` is correct)::

    make html
    make latexpdf

Upload the :file:`.gzip.tar` and :file:`.zip` files to PYPI (use web form?). What about README.txt?

Upload the :file:`.gzip.tar` and :file:`.zip` files to Sourceforge (use web form?), and upload the generated documentation.

Upload the documentation PDF and HTML files to Sourceforge.

On a Windows machine, build the windows installer:: 

    python setup.py bdist_wininst

Upload the windows installer to PYPI and Sourceforge.

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

Create subfolders ``build`` and ``dist``::

    python setup.py bdist

Create a subfolder ``dist`` with a Windows installer::

    python setup.py bdist --formats=wininst


Test distributions
------------------

Create a subfolder ``build``::

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

The Windows installer also creates a :file:`.pyo` file (and also the :file:`.pyc` file).


Sphinx usage
------------
The documentation is generated with the Sphinx tool: http://sphinx.pocoo.org/

Sphinx reStructuredText Primer
    http://sphinx.pocoo.org/rest.html

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


TODO
----
* Test documentation
* Release

* Test with Python3
* Test the dependency of pySerial in setup.py
* Mailing list

For next release:
* Unittests in folder test/test*.py





