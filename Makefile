# Build the Python source package & upload to PyPi

all:
	python setup.py sdist


install: all
	python setup.py register
	python setup.py sdist --formats=gztar upload
