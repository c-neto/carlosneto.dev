SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build
# Virtualenv with the dependencies; the Docker image sets VENV=/venv
VENV          ?= venv

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

setup:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip3 install -r requirements.txt
	$(VENV)/bin/pip3 install -r requirements-dev.txt

live:
	$(VENV)/bin/sphinx-autobuild --ignore _build -b dirhtml . _build/dirhtml/

build:
	$(VENV)/bin/sphinx-build -b dirhtml . _build/dirhtml/

.PHONY: help Makefile

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
