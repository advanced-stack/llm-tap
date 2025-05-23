.PHONY: setup

PKG_NAME := llm-tap
MOD_NAME := llm_tap
PKG_VERSION := 0.0.1
PKG_DIR := $(shell pwd)
BUILD_DIR := dist
SRC_DIR := $(PKG_DIR)/src
GIT_REPO_URL := https://github.com/advanced-stack/$(PKG_NAME).git
PYTHON := venv/bin/python3
PYTHON_VERSION := 3.13
PIP := venv/bin/pip3
SETUPTOOLS := $(PIP) install --upgrade setuptools
TWINE := venv/bin/twine
BUILD := $(PYTHON) -m build
CHECK := $(TWINE) check $(BUILD_DIR)/*

venv:
	@python${PYTHON_VERSION} -m venv venv
	-ln -s venv/bin .
	-ln -s venv/bin/activate .

dev: venv
	@bin/pip3 install ipython

setup: venv
	@bin/pip3 install -U pip build twine
	@bin/pip3 install -e .

tag:
	@echo "Creating new Git tag $(PKG_VERSION)"
	@git tag -a $(PKG_VERSION) -m "Release version $(PKG_VERSION)"

push:
	@echo "Pushing Git tag $(PKG_VERSION) to remote repository"
	@git push --follow-tags

build:
	@echo "Building package $(PKG_NAME)-$(PKG_VERSION)"
	@$(SETUPTOOLS)
	@$(BUILD)

check:
	@echo "Checking built packages"
	@$(CHECK)

upload:
	@echo "Uploading built packages to PyPI"
	$(TWINE) upload $(BUILD_DIR)/*

display-version:
	echo ${PKG_VERSION}

release:
	make build
	make tag
	make upload
	git push --follow-tags
