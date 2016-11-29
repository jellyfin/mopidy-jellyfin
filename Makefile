.PHONY: upload build

build:
	python setup.py sdist bdist_wheel


pypi:
	python setup.py sdist bdist_wheel
	twine upload dist/*
