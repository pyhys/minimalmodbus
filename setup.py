#!/usr/bin/env python

from distutils.core import setup

with open('README.txt') as file:
    long_description = file.read()

setup(name='MinimalModbus',
    version='0.1',
    description='Simple Modbus RTU implementation',
    long_description = long_description
    author='Jonas Berg',
    author_email='pyhys@ ???++',
    url='http://sourceforge.net/projects/minimalmodbus/',
    modules=['minimalmodbus', 'eurotherm3504'],
    licence = 'Apache License, Version 2.0',
    classifiers=[ 
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Manufacturing',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python', 
        'Topic :: Communications',
        'Topic :: Home Automation',
        'Topic :: Scientific/Engineering',
        'Topic :: System :: Hardware :: Hardware Drivers',
        ],
    )








