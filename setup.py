#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Do not import non-standard modules here, as it will mess up the installation in clients.
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read().replace(".. :changelog:", "")

# Read version number etc from other file
# http://stackoverflow.com/questions/2058802/how-can-i-get-the-version-defined
# -in-setup-py-setuptools-in-my-package
with open("minimalmodbus.py") as mainfile:
    main_py = mainfile.read()
metadata = dict(re.findall('__([a-z]+)__ *= *"([^"]+)"', main_py))

setup(
    name="minimalmodbus",
    version=metadata["version"],
    license=metadata["license"],
    author=metadata["author"],
    url=metadata["url"],
    project_urls={
        "Documentation": "https://minimalmodbus.readthedocs.io",
        "Source Code": metadata["url"],
        "Bug Tracker": "https://github.com/pyhys/minimalmodbus/issues",
    },
    description="Easy-to-use Modbus RTU and Modbus ASCII implementation for Python",
    keywords="minimalmodbus modbus modbus-serial modbus-RTU modbus-ASCII",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/x-rst",
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
    install_requires=["pyserial>=3.0"],
    py_modules=["minimalmodbus"],
    test_suite="tests",  # Discover all testcases in all files in this subdir
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Communications",
        "Topic :: Home Automation",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Topic :: Terminals :: Serial",
    ],
)
