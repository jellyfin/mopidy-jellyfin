.PHONY: init upload build clean

init:
	pipenv --two --site-packages
	pipenv install --dev

build:
	python setup.py sdist bdist_wheel

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf .tox
	rm -rf dist/

pypi: clean
	python setup.py sdist bdist_wheel
	twine upload dist/*
