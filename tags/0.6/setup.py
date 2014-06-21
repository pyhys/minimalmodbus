#!/usr/bin/env python

# Do not import non-standard modules here, as it will mess up the installation in clients.
import re
from distutils.core import setup

with open('README.txt') as readmefile:
    long_description = readmefile.read()

# Read version number etc from other file
# http://stackoverflow.com/questions/2058802/how-can-i-get-the-version-defined-in-setup-py-setuptools-in-my-package
with open('minimalmodbus.py') as mainfile:
    main_py = mainfile.read()
metadata = dict( re.findall(r"__([a-z]+)__ *= *'([^']+)'", main_py) )

setup(name       = 'MinimalModbus',
    version      = metadata['version'],
    license      = metadata['license'],
    author       = metadata['author'],
    author_email = metadata['email'],
    url          = metadata['url'],
    keywords     = 'modbus serial RTU ASCII',
    description  = 'Easy-to-use Modbus RTU and Modbus ASCII implementation for Python',
    long_description = long_description,
    py_modules = ['minimalmodbus', 'eurotherm3500', 'omegacn7500', 'dummy_serial'],
    install_requires = ['pyserial'],
    classifiers = [ 
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Manufacturing',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7', 
        'Programming Language :: Python :: 3', 
        'Programming Language :: Python :: 3.2', 
        'Topic :: Communications',
        'Topic :: Home Automation',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Hardware :: Hardware Drivers',
        'Topic :: Terminals :: Serial',
        ],
    )

# See PEP396 how to derive the version number from the source file: http://www.python.org/dev/peps/pep-0396/#deriving

# Note that additional files for inclusion are defined in MANIFEST.in


