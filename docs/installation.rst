============
Installation
============

At the command line::

    $ pip install minimalmodbus

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv minimalmodbus
    $ pip install minimalmodbus


Dependencies
------------
Python versions 2.7 and higher are supported (including 3.x). 
Tested with Python 2.7, 3.2, 3.3 and 3.4. This module is pure Python.

This module relies on `pySerial <http://pyserial.sourceforge.net/>`_ (also pure Python) 
to do the heavy lifting, and it is the only dependency. 
You can find it at the Python package index: https://pypi.python.org/pypi/pyserial


Alternate installation on Linux
-------------------------------------
From command line (if you have the *pip installer*, available at https://pypi.python.org/pypi/pip)::

   pip install -U minimalmodbus
   
or possibly::

   sudo pip install -U pyserial
   sudo pip install -U minimalmodbus

You can also manually download the compressed source files from 
https://pypi.python.org/pypi/MinimalModbus/ (see the end of that page). 
In that case you first need to manually install pySerial from https://pypi.python.org/pypi/pyserial.

There are compressed source files for Unix/Linux (.tar.gz) and Windows (.zip). 
To install a manually downloaded file, uncompress it and run (from within the directory)::

   python setup.py install

or possibly::

   sudo python setup.py install

If using Python 3, then install with::

   sudo python3 setup.py install

For Python3 there might be problems with *easy_install* and *pip*. 
In that case, first manually install pySerial and then manually install MinimalModbus.

To make sure it is installed properly, print the _getDiagnosticString() message. 
See the :ref:`support` section for instructions.

You can also download the source directly from Linux command line::

    wget https://pypi.python.org/packages/source/M/MinimalModbus/MinimalModbus-0.7.tar.gz

Change version number to the appropriate value.

Downloading from Github::
 
    wget https://github.com/pyhys/minimalmodbus/archive/master.zip
    unzip master.zip

This will create a directory 'minimalmodbus-master'.



Alternate installation on Windows
-------------------------------------
Install from Github, using pip::

    C:\Python34\Scripts>pip3.4 install https://github.com/pyhys/minimalmodbus/archive/master.zip

It will be installed in::

    C:\Python34\Lib\site-packages

In order to run Python from command line, you might need::

    set PATH=%PATH%;C:\Python34





If everything else fails
-------------------------
You can download the raw minimalmodbus.py file from GitHub, and put it in the same directory as your other code. Note that you must have pySerial installed.

