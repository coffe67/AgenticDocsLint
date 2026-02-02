SHELL := /bin/bash

# Defaults (can be overridden):
INPUT ?= examples/deck_sample.json
OUT ?= build
CONFIG ?= config/default.yaml
RELAXED_CONFIG ?= config/strict_relaxed.yaml
P2S_CONFIG ?= config/paper2slides_example.yaml
P2S_OUT ?= build_p2s

# Project-local virtual environment
VENV := hackathon2026
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help venv env-info shell install sample run run-relaxed run-paper2slides test clean clean-venv

help:
	@echo "Targets:"
	@echo "  venv            Create local venv at $(VENV)"
	@echo "  install         Install into venv (pip install -e .)"
	@echo "  env-info        Show Python/pip resolved from venv"
	@echo "  shell           Open an interactive shell with venv activated"
	@echo "  sample          Generate sample deck (uses venv)"
	@echo "  run             Run pipeline (uses venv)"
	@echo "                  Usage: make run [INPUT=...] [CONFIG=...] [OUT=...] [AUTO_FIX=1]"
	@echo "  run-relaxed     Run pipeline with relaxed strict config"
	@echo "  run-paper2slides Run with Paper2Slides config"
	@echo "  test            Run smoke test (default & relaxed)"
	@echo "  clean           Remove build directories and examples"
	@echo "  clean-venv      Remove local venv"

venv:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@$(PY) -m pip install --upgrade pip setuptools wheel >/dev/null

install: venv
	@$(PY) -m pip install -e .

env-info: venv
	@echo "Python: $(PY)" && $(PY) --version
	@echo "Pip:    $(PIP)" && $(PIP) --version

shell: venv
	@bash -lc 'source $(VENV)/bin/activate && echo "Activated: $$VIRTUAL_ENV" && exec $$SHELL'

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
