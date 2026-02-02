SHELL := /bin/bash

# Project-local virtual environment (named as requested)
VENV := hackathon2026
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Defaults (can be overridden):
INPUT ?= examples/deck_sample.json
OUT ?= build
CONFIG ?= config/default.yaml
RELAXED_CONFIG ?= config/strict_relaxed.yaml
P2S_CONFIG ?= config/paper2slides_example.yaml
P2S_OUT ?= build_p2s

.PHONY: help venv install env-info sample run run-relaxed run-paper2slides test clean clean-venv

help:
	@echo "Targets:"
	@echo "  venv             Create project-local virtualenv in $(VENV)"
	@echo "  install          Create venv and pip install -e . into $(VENV)"
	@echo "  env-info         Print Python and pip paths used by Makefile"
	@echo "  sample           Generate sample deck and copy default config (uses venv)"
	@echo "  run              Run pipeline (CONFIG=$(CONFIG), OUT=$(OUT))"
	@echo "                   Usage: make run [INPUT=...] [CONFIG=...] [OUT=...] [AUTO_FIX=1]"
	@echo "  run-relaxed      Run pipeline with relaxed strict config"
	@echo "  run-paper2slides Run with Paper2Slides config (P2S_CONFIG=$(P2S_CONFIG), P2S_OUT=$(P2S_OUT))"
	@echo "  test             Run smoke test (default & relaxed)"
	@echo "  clean            Remove build directories and examples"
	@echo "  clean-venv       Remove the local virtualenv ($(VENV))"

venv:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@$(PY) -m pip install --upgrade pip setuptools wheel >/dev/null

install: venv
	@$(PY) -m pip install -e .

env-info: venv
	@echo "Python: $(PY)" && $(PY) --version
	@echo "Pip:    $(PIP)" && $(PIP) --version

sample: install
	@$(PY) -m slideforge.cli sample --out examples

run: install
	@$(PY) -m slideforge.cli run --input $(INPUT) --config $(CONFIG) --out $(OUT) $(if $(AUTO_FIX),--auto-fix,)

run-relaxed:
	$(MAKE) run CONFIG=$(RELAXED_CONFIG) OUT=build_relaxed $(if $(AUTO_FIX),AUTO_FIX=$(AUTO_FIX),AUTO_FIX=1)

run-paper2slides:
	$(MAKE) run CONFIG=$(P2S_CONFIG) OUT=$(P2S_OUT) INPUT=$(INPUT) $(if $(AUTO_FIX),AUTO_FIX=$(AUTO_FIX),AUTO_FIX=1)

test: install
	@$(PY) scripts/smoke_test.py

clean:
	rm -rf build build_relaxed examples __pycache__ */__pycache__ .pytest_cache

clean-venv:
	rm -rf $(VENV)
