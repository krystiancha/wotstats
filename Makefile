all: isort black flake8 mypy pylint

isort:
	isort --apply wotstats

black:
	black wotstats

flake8:
	flake8 wotstats

mypy:
	mypy wotstats

pylint:
	pylint wotstats

