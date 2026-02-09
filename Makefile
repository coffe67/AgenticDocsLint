SHELL := /bin/bash

# Defaults (can be overridden):
INPUT ?= examples/deck_sample.json
OUT ?= build
CONFIG ?= config/default.yaml
RELAXED_CONFIG ?= config/strict_relaxed.yaml
P2S_CONFIG ?= config/paper2slides_example.yaml
P2S_OUT ?= build_p2s

# Project-local virtual environment
VENV := venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help venv env-info shell install sample run run-relaxed run-paper2slides test clean clean-venv deps-api run-api deps-pptx deps-docx deps-images deps-llm-openai bootstrap-api start-api fe-install fe-dev fe-build docker-build docker-up docker-down

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
	@echo "  deps-api        Install API dependencies (FastAPI, Uvicorn, requests, bs4)"
	@echo "  run-api         Start FastAPI server with uvicorn (uses venv)"
	@echo "  bootstrap-api   Install project + API deps (+pptx by default)"
	@echo "  start-api       Bootstrap then run API (set NO_PPTX=1 to skip pptx dep)"
	@echo "  fe-install      Install frontend dependencies (in ./frontend)"
	@echo "  fe-dev          Start frontend dev server (Vite)"
	@echo "  fe-build        Build frontend for production"
	@echo "  docker-build    Build API and web images"
	@echo "  docker-up       Start full stack with docker-compose"
	@echo "  docker-down     Stop stack and remove containers"
	@echo "  deps-docx       Install DOCX parsing dependency (python-docx)"
	@echo "  deps-images     Install Pillow for PNG exports"
	@echo "  deps-llm-openai Install OpenAI SDK for LLM tagger"

venv:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@$(PY) -m pip install --upgrade pip setuptools wheel >/dev/null

install: venv
	@$(PY) -m pip install -e .

deps-pptx: venv
	@$(PY) -m pip install python-pptx

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

deps-api: install
	@$(PY) -m pip install fastapi uvicorn[standard] requests beautifulsoup4 python-multipart

run-api: deps-api
	@$(PY) -m uvicorn slideforge.api:app --reload --host 0.0.0.0 --port 8000

# Convenience: install everything needed for the API in one go
bootstrap-api: install deps-api
	@if [ -z "$(NO_PPTX)" ]; then $(MAKE) deps-pptx; else echo "Skipping pptx dep (NO_PPTX=1)"; fi
	@if [ -z "$(NO_DOCX)" ]; then $(MAKE) deps-docx; else echo "Skipping docx dep (NO_DOCX=1)"; fi
	@if [ -z "$(NO_IMAGES)" ]; then $(MAKE) deps-images; else echo "Skipping Pillow dep (NO_IMAGES=1)"; fi
	@if [ -n "$(LLM_OPENAI)" ]; then $(MAKE) deps-llm-openai; else echo "Skipping LLM SDK (set LLM_OPENAI=1 to install)"; fi

start-api:
	@$(MAKE) bootstrap-api
	@$(MAKE) run-api

fe-install:
	@cd frontend && npm install

fe-dev:
	@cd frontend && npm run dev

fe-build:
	@cd frontend && npm run build

deps-docx: venv
	@$(PY) -m pip install python-docx

deps-images: venv
	@$(PY) -m pip install pillow

deps-llm-openai: venv
	@$(PY) -m pip install openai

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
