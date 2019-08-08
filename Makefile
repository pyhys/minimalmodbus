.PHONY: clean-pyc clean-build docs clean clean-docs

help:
	@echo "devdeps - install dependencies required for development"
	@echo "lint - check style with flake8"
	@echo "black - modify code style using the black tool"
	@echo " "
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo " "
	@echo "docs - generate Sphinx HTML documentation"
	@echo "pdf - generate Sphinx PDF documentation"
	@echo "linkcheck - check documentation html links"
	@echo " "
	@echo "install - install the package to the active Python's site-packages"
	@echo "installdev - install the package for as symlink, for development"
	@echo "uninstall - uninstall the package"
	@echo "list - list installed packages package"
	@echo "show - show details on this package"
	@echo "dist - package source and wheel"
	@echo "upload - upload to PyPI"
	@echo " "
	@echo "clean - remove all build, test, coverage, docs and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "clean-docs - remove docs artifacts"

clean: clean-build clean-pyc clean-test clean-docs

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -f coverage.xml
	rm -fr htmlcov/

clean-docs:
	$(MAKE) -C docs clean

devdeps:
	pip3 install --user --upgrade \
		coverage \
		flake8 \
		pip \
		pycodestyle \
		pydocstyle \
		pylint \
		setuptools \
		sphinx_rtd_theme \
		sphinx \
		tox \
		twine \
		wheel

lint:
	@echo "Show non-ascii characters (for Python2 compability)"
	grep --color='auto' -P -n "[\x80-\xFF]" minimalmodbus.py || true
	grep --color='auto' -P -n "[\x80-\xFF]" dummy_serial.py || true
	grep --color='auto' -P -n "[\x80-\xFF]" setup.py || true
	grep --color='auto' -P -n "[\x80-\xFF]" tests/test_minimalmodbus.py || true
	grep --color='auto' -P -n "[\x80-\xFF]" tests/test_deltaDTB4824.py || true
	@echo " "
	@echo " "
	flake8 minimalmodbus.py --max-line-length=100 || true  # Includes pycodestyle
	@echo " "
	@echo " "
	pydocstyle minimalmodbus.py || true
	@echo " "
	@echo " "
	pylint minimalmodbus.py -d C0103 -d C0330 -d R0913 || true

black:
	black minimalmodbus.py dummy_serial.py setup.py

test:
	python3 tests/test_minimalmodbus.py

test-all:
	rm -fr .tox/
	tox

coverage:
	rm -fr htmlcov/
	coverage3 run setup.py test
	coverage3 report -m
	coverage3 html
	@echo "    "
	@echo "    "
	@echo "    "
	@echo "Opening web browser ..."
	xdg-open htmlcov/index.html

docs:	clean-docs
	$(MAKE) -C docs html
	@echo "    "
	@echo "    "
	@echo "    "
	@echo "Opening web browser ..."
	xdg-open docs/_build/html/index.html

pdf:
	$(MAKE) -C docs latexpdf
	@echo "    "
	@echo "    "
	@echo "    "
	@echo "Opening PDF reader ..."
	xdg-open docs/_build/latex/minimalmodbus.pdf

linkcheck:
	$(MAKE) -C docs linkcheck

install: clean
	pip3 install

installdev: clean
	pip3 install -e .

list:
	pip3 list

show:
	pip3 show

dist: clean
	python3 setup.py sdist bdist_wheel
	ls -l dist

upload:
	twine upload dist/*
