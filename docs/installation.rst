============
Installation
============

At the command line::

    pip3 install -U minimalmodbus

or possibly::

    sudo pip3 install -U minimalmodbus


Dependencies
------------
Python versions 3.8 and higher are supported. This module is pure Python.

This module relies on `pySerial <https://github.com/pyserial/pyserial>`_ (also pure Python)
to do the heavy lifting, and it is the only dependency. It is BSD-3-Clause licensed.
You can find it at the Python package index: https://pypi.org/project/pyserial
The version of pyserial should be 3.0 or later.

.. note:: Since MinimalModbus 1.0 you need to use pySerial version at least 3.0

Alternate installation on Linux
-------------------------------------
You can also manually download the compressed source files from
https://pypi.org/project/minimalmodbus/.
In that case you first need to manually install pySerial from https://pypi.org/project/pyserial.

There are compressed source files for Unix/Linux (.tar.gz) and Windows (.zip).
To install a manually downloaded file use the pip tool::

    python3 -m pip install filename.tar.gz


If everything else fails
-------------------------
You can download the raw :file:`minimalmodbus.py` file from GitHub, and put it in the
same directory as your other code. Note that you must have pySerial installed.
