.PHONY: clean-pyc clean-build docs clean clean-docs

help:
	@echo "devdeps - install dependencies required for development"
	@echo "pylint - check style with pylint"
	@echo "flake8 - check style with flake8"
	@echo "ruff - check style with ruff"
	@echo "pydocstyle - check documentation with pydocstyle"
	@echo "black - modify code style using the black tool"
	@echo "mypy - type checking"
	@echo " "
	@echo "test - run tests quickly with the default Python"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo " "
	@echo "docs - generate Sphinx HTML documentation"
	@echo "linkcheck - check documentation html links"
	@echo " "
	@echo "install - install the package to the active Python's site-packages"
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
	rm -fr .mypy_cache
	rm -f .coverage
	rm -f coverage.xml
	rm -fr htmlcov/

clean-docs:
	$(MAKE) -C docs clean

devdeps:
	pip3 install --user --upgrade \
		black \
		build \
		coverage \
		coverage[toml] \
		flake8 \
		mypy \
		pip \
		pycodestyle \
		pydocstyle \
		pylint \
		ruff \
		setuptools \
		sphinx \
		sphinx_rtd_theme \
		sphinxcontrib-programoutput \
		twine \
		wheel

pylint:
	pylint minimalmodbus.py -d C0103 -d C0302 -d C0330 -d C0413 -d R0902 -d R0911 -d R0912 -d R0913 -d R0914 -d R0915 -d W0613 -d W0703 -d W0707 || true

flake8:
	flake8 minimalmodbus.py tests/dummy_serial.py tests/test_deltaDTB4824.py tests/test_minimalmodbus.py

black:
	python3 -m black .

ruff:
	ruff check .

docformatter:
	docformatter -i --black minimalmodbus.py

pydocstyle:
	pydocstyle minimalmodbus.py

mypy:
	python3 -m mypy minimalmodbus.py tests/ --strict --no-warn-unused-ignores

test:
	python3 tests/test_minimalmodbus.py

coverage:
	rm -fr htmlcov/
	coverage3 run tests/test_minimalmodbus.py
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

linkcheck:
	$(MAKE) -C docs linkcheck

install: dist
	pip3 install --force-reinstall dist/minimalmodbus*.whl

uninstall:
	pip3 uninstall -y minimalmodbus

list:
	pip3 list

show:
	pip3 show minimalmodbus

dist: clean
	@echo "    "
	@echo "    "
	flit build
	@echo "    "
	@echo "    "
	ls -l dist

upload:
	flit publish
