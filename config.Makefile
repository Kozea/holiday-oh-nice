export PROJECT_NAME = holiday

# Python env
VENV = $(PWD)/.env
PIP = $(VENV)/bin/pip
PYTHON = $(VENV)/bin/python
PYTEST = $(VENV)/bin/py.test
FLASK = $(VENV)/bin/flask

URL_TEST = http://test-$(CI_PROJECT_NAME)-$(BRANCH_NAME).kozea.fr
URL_PROD = http://holiday.kozea.fr/calendar.ics
