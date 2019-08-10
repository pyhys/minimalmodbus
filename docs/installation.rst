============
Installation
============

At the command line::

    pip3 install -U minimalmodbus

or possibly::

    sudo pip3 install -U minimalmodbus

For legacy Python (2.7), use ``pip`` instead of ``pip3``.

Dependencies
------------
Python versions 2.7 and higher are supported (including 3.x).
Tested with Python 2.7, 3.5, 3.6 and 3.7. This module is pure Python.

This module relies on `pySerial <https://github.com/pyserial/pyserial>`_ (also pure Python)
to do the heavy lifting, and it is the only dependency. It is BSD-3-Clause licensed.
You can find it at the Python package index: https://pypi.org/project/pyserial
The version of pyserial should be 3.0 or later.

.. note:: Since MinimalModbus 1.0 you need to use pySerial version at least 3.0

Alternate installation on Linux
-------------------------------------
You can also manually download the compressed source files from
https://pypi.org/project/MinimalModbus/.
In that case you first need to manually install pySerial from https://pypi.org/project/pyserial.

There are compressed source files for Unix/Linux (.tar.gz) and Windows (.zip).
To install a manually downloaded file, uncompress it and run (from within the directory)::

   python3 setup.py install

or possibly::

   sudo python3 setup.py install

If using Python2, use ``python`` instead of ``python3``.

To make sure it is installed properly, print the :func:`._get_diagnostic_string` message.
See the :ref:`support` section for instructions.

You can also download the source directly from Linux command line::

    wget https://pypi.python.org/packages/source/M/MinimalModbus/MinimalModbus-0.7.tar.gz
    TODO

Change version number to the appropriate value.

Downloading from GitHub::

    wget https://github.com/pyhys/minimalmodbus/archive/master.zip
    unzip master.zip

This will create a directory 'minimalmodbus-master'.


Alternate installation on Windows
-------------------------------------
Install from GitHub, using pip::

    C:\Python34\Scripts>pip3.4 install https://github.com/pyhys/minimalmodbus/archive/master.zip
    TODO

It will be installed in::

    C:\Python34\Lib\site-packages
    TODO

In order to run Python from command line, you might need::

    set PATH=%PATH%;C:\Python34
    TODO


If everything else fails
-------------------------
You can download the raw minimalmodbus.py file from GitHub, and put it in the
same directory as your other code. Note that you must have pySerial installed.
