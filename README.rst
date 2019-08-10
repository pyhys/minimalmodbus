===============================
MinimalModbus
===============================

.. image:: https://img.shields.io/travis/pyhys/minimalmodbus.svg
        :target: https://travis-ci.org/pyhys/minimalmodbus
        :alt: Build Status

.. image:: https://readthedocs.org/projects/minimalmodbus/badge/?version=master
        :target: https://readthedocs.org/projects/minimalmodbus/?badge=master
        :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/minimalmodbus.svg
        :target: https://pypi.org/project/MinimalModbus/
        :alt: PyPI page link

.. image:: https://codecov.io/gh/pyhys/minimalmodbus/branch/master/graphs/badge.svg?branch=master
        :target: https://codecov.io/github/pyhys/minimalmodbus?branch=master
        :alt: Test coverage report


Easy-to-use Modbus RTU and Modbus ASCII implementation for Python.

Web resources
-------------

* **Documentation**: https://minimalmodbus.readthedocs.io
* Source code on **GitHub**: https://github.com/pyhys/minimalmodbus
* Python package index (PyPI) with download: https://pypi.org/project/MinimalModbus/

Other web pages:

* Readthedocs project page: https://readthedocs.org/projects/minimalmodbus/
* Travis CI build status page: https://travis-ci.org/pyhys/minimalmodbus
* codecov.io project page: https://codecov.io/github/pyhys/minimalmodbus

Obsolete web pages:

* Old Sourceforge documentation page: http://minimalmodbus.sourceforge.net/
* Old Sourceforge project page: https://sourceforge.net/projects/minimalmodbus
* Old Sourceforge repository: https://sourceforge.net/p/minimalmodbus/code/HEAD/tree/


Features
--------
MinimalModbus is an easy-to-use Python module for talking to instruments (slaves)
from a computer (master) using the Modbus protocol, and is intended to be running on the master.
The only dependence is the pySerial module (also pure Python).

There are convenience functions to handle floats, strings and long integers
(in different byte orders).

This software supports the 'Modbus RTU' and 'Modbus ASCII' serial communication
versions of the protocol, and is intended for use on Linux, OS X and Windows platforms.
It is open source, and has the Apache License, Version 2.0.

Tested with Python 2.7, 3.5, 3.6 and 3.7.

Support for Python2 will be dropped in 2020.

This package uses semantic versioning.
