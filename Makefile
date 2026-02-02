SHELL := /bin/bash

# Defaults (can be overridden):
INPUT ?= examples/deck_sample.json
OUT ?= build
CONFIG ?= config/default.yaml
RELAXED_CONFIG ?= config/strict_relaxed.yaml
P2S_CONFIG ?= config/paper2slides_example.yaml
P2S_OUT ?= build_p2s

.PHONY: help install sample run run-relaxed run-paper2slides test clean

help:
	@echo "Targets:"
	@echo "  install         Create venv and pip install -e ."
	@echo "  sample          Generate sample deck and copy default config"
	@echo "  run             Run pipeline (CONFIG=$(CONFIG), OUT=$(OUT))"
	@echo "                  Usage: make run [INPUT=...] [CONFIG=...] [OUT=...] [AUTO_FIX=1]"
	@echo "  run-relaxed     Run pipeline with relaxed strict config"
	@echo "  run-paper2slides Run with Paper2Slides config (P2S_CONFIG=$(P2S_CONFIG), P2S_OUT=$(P2S_OUT))"
	@echo "  test            Run smoke test (default & relaxed)"
	@echo "  clean           Remove build directories and examples"

install:
	python3 -m venv .venv && . .venv/bin/activate && pip install -e .

sample:
	python3 -m slideforge.cli sample --out examples

run:
	python3 -m slideforge.cli run --input $(INPUT) --config $(CONFIG) --out $(OUT) $(if $(AUTO_FIX),--auto-fix,)

run-relaxed:
	$(MAKE) run CONFIG=$(RELAXED_CONFIG) OUT=build_relaxed $(if $(AUTO_FIX),AUTO_FIX=$(AUTO_FIX),AUTO_FIX=1)

run-paper2slides:
	$(MAKE) run CONFIG=$(P2S_CONFIG) OUT=$(P2S_OUT) INPUT=$(INPUT) $(if $(AUTO_FIX),AUTO_FIX=$(AUTO_FIX),AUTO_FIX=1)

test:
	python3 scripts/smoke_test.py

clean:
	rm -rf build build_relaxed examples __pycache__ */__pycache__ .pytest_cache
