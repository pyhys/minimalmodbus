.. :changelog:

History
=======


Release 0.7 (2015-07-30)
-------------------------
* Faster CRC calculation by using a lookup table (thanks to Peter)
* Handling of local echo (thanks to Luca Di Gregorio)
* Improved behavior of dummy_serial (number of bytes to read)
* Improved debug messages (thanks to Dino)
* Using project setup by the cookie-cutter tool.
* Reshuffled source files and documentation.
* Moved source to Github from Sourceforge.
* Moved documentation to readthedocs.org
* Using the tox tool for testing on multiple Python versions.
* Using Travis CI test framework
* Using codecov.io code coverage measurement framework
* Added support for Python 3.3 and 3.4.
* Dropped support for Python 2.6.


Release 0.6 (2014-06-22)
--------------------------
* Support for Modbus ASCII mode.


Release 0.5 (2014-03-23)
--------------------------
* Precalculating number of bytes to read, in order to increase the speed.
* Better handling of several instruments on the same serial port, especially 
  for Windows.
* Improved timing for better compliance with Modbus timing requirements.


Release 0.4 (2012-09-08)
--------------------------
* Read and write multiple registers.
* Read and write floating point values.
* Read and write long integers.
* Read and write strings.
* Support for negative numbers.
* Use of the Python struct module instead of own bit-tweaking internally.
* Improved documentation.


Release 0.3.2 (2012-01-25)
--------------------------
* Fine-tuned setup.py for smoother installation.
* Improved documentation.


Release 0.3.1 (2012-01-24)
--------------------------
* Improved requirements handling in setup.py
* Adjusted MANIFEST.in not to include doc/_templates
* Adjusted RST text formatting in README.txt


Release 0.3 (2012-01-23)
------------------------
This is a major rewrite, but the API is backward compatible.

* Extended functionality to support more Modbus function codes.
* Option to close the serial port after each call (useful for Windows XP etc).
* Diagnostic string output available (for support).
* Debug mode available.
* Improved __repr__ for Instrument instances.
* Improved Python3 compatibility.
* Improved validity checking for function arguments.
* The error messages are made more informative.
* The new example driver omegacn7500 is included.
* Unit tests included in the distribution.
* A dummy serial port for unit testing is provided (including recorded communication data).
* Updated documentation.


Release 0.2 (2011-08-19)
------------------------
* Changes in how to reference the serial port. 
* Updated documentation.


Release 0.1 (2011-06-16)
------------------------
* First public release.
