#!/usr/bin/env python

from distutils.core import setup
import minimalmodbus

with open('README.txt') as file:
    long_description = file.read()

setup(name='MinimalModbus',
    version = minimalmodbus.__version__,
    description = 'Easy-to-use Modbus RTU implementation for Python',
    long_description = long_description,
    keywords = 'modbus serial RTU',
    author='Jonas Berg',
    author_email='pyhys@users.sourceforge.net',
    url='http://minimalmodbus.sourceforge.net/',
    py_modules=['minimalmodbus', 'eurotherm3500', 'omegacn7500', 'dummy_serial'],
    license = 'Apache License, Version 2.0',
    install_requires = ['pyserial'],
    classifiers=[ 
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
        'Programming Language :: Python :: 2.6', 
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

# Note that additional files for inclusion are defined in MANIFEST.in


