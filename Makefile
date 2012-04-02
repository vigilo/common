NAME := common
all: build

include buildenv/Makefile.common

install: $(PYTHON) build
	$(PYTHON) setup.py install --record=INSTALLED_FILES
install_pkg: $(PYTHON) build
	$(PYTHON) setup.py install --single-version-externally-managed --root=$(DESTDIR)

lint: lint_pylint
tests: tests_nose
doc: apidoc
clean: clean_python

.PHONY: install_python install_pkg
