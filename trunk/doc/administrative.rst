Developer documentation
=======================


Shortlist of most used SVN commands
-----------------------------------

svn update

svn status 
svn status -v
svn status -v --no-ignore

svn add FILENAME or DIRECTORYNAME
svn commit -m 'Write yout log message here'

In the 'trunk' directory:
svn propset svn:ignore html .
or if ignoring multiple items, edit the list using: 
svn propedit svn:ignore .


svn proplist
svn propget svn:ignore


Documentation generators
------------------------
pydoc -w modulename # Writes a HTML page in current directory
epydoc minimalmodbus eurotherm3500 # Writes HTML pages and javascript in the html subfolder

export PYTHONPATH=$PYTHONPATH:/home/jonas/pythonprogrammering/minimalmodbus/trunk
make html


Preparation for release
-----------------------

pychecker eurotherm3500.py 
pychecker minimalmodbus.py 

pydoc -w minimalmodbus
pydoc -w eurotherm3500


  * python setup.py sdist --formats=gztar,zip
  * remove MANIFEST and folder 'dist'
  * On PYPI page upload .gzip.tar .zip and windows installer files.
  * Also on sourceforge upload the files

  * On Windows machine: python setup.py bdist_wininst




Notes on distribution
---------------------

python setup.py register sdist --formats=gztar,zip upload

Generate distributions:
Creates a subfolder **dist** with zipped or gztared source folders.

<code>
python setup.py sdist
python setup.py sdist --formats=gztar,zip
</code>


Creates a subfolder **build** and **dist** ?

<code>
python setup.py bdist
</code>

Creates a subfolder **dist** with a windows installer.
<code>
python setup.py bdist --formats=wininst
</code>



Test distribution: Creates a subfolder **build**.

<code>
python setup.py build
</code>

<code>
sudo python setup.py install
</code>

target:

/usr/local/lib/python2.6/dist-packages

copying build\lib\packagetestfibo.py -> C:\python27\Lib\site-packages


The Windows installer also creates a .pyo file (and also the .pyc file).



Sphinx usage
------------

http://packages.python.org/an_example_pypi_project/sphinx.html
http://docs.geoserver.org/trunk/en/docguide/sphinx.html



echo $PYTHONPATH
export PYTHONPATH='/home/jonas/pythonprogrammering/minimalmodbus/trunk'

in the trunc/doc directory:
sphinx-build -a  . build

Top level heading: ==
Next lower level: --



TODO
----
Write a proper README.txt (describe modbus types, home page, other libraries)
Homepage with pydoc etc
Mailing list
Unittests
Include pydoc pages etc in source distributions
__version__ etc in source files
epydoc 
in setup.py, indicate the dependency of pySerial

CHANGE THIS: instrument.portname instead of  .port

