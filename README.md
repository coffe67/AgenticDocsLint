SlideForge / SlideCheck
========================

Goal: “We extract structure from slides, evaluate them with specialized AI agents, and optionally generate missing content — all in one automated workflow.”

This repo provides an initial, local-first scaffold inspired by Paper2Slides (extraction) and Julep (agentic orchestration). It includes:

- A simple slide deck model (JSON) and schema
- An orchestrated pipeline of agents:
  - SlideNormalizer
  - SectionTagger
  - KeywordChecker
  - ComplianceDecider
  - Report generator
- Optional Slide Generator to draft missing sections
- A CLI to run end-to-end or individual stages

Note: Real PDF/PPTX parsing and LLM-based generation are stubbed with pluggable interfaces, so you can later integrate Paper2Slides and your preferred model provider. For now, JSON and Markdown inputs are supported.

Quick start
-----------

1) Create a virtual environment (optional)

   - python -m venv .venv && source .venv/bin/activate

2) Install (editable)

   - pip install -e .

3) If you plan to evaluate PPTX files, install the PPTX parser dependency

   - make deps-pptx

4) Use a curated static example (checked in)

   - slideforge run --input examples_static/deck_curated.json --config config/default.yaml --out build_static --auto-fix

   Or generate fresh samples:

   - slideforge sample --out examples/

5) Run end-to-end on the sample deck

   - slideforge run --input examples/deck_sample.json --config config/default.yaml --out build/ --auto-fix

Outputs
-------

- Compliance report (JSON + text) in the output directory
- Optionally, an updated deck (JSON + Markdown) when --auto-fix is used

Design
------

- slideforge/parsers/paper2slides_adapter.py: pluggable parser interface; supports JSON/Markdown today
- slideforge/agents/*: stateless, testable components for each stage
- slideforge/pipeline/orchestrator.py: ties everything together following the flowchart
- schemas/: JSON Schemas for deck and report payloads
- config/: Default rules (required keywords per section, thresholds)
- docs/: Mermaid flowchart and architecture notes

Future integration
------------------

- Replace parser adapter with Paper2Slides output
- Swap heuristics with LLM-backed agents (Julep-style orchestration)
- Add exporters (PPTX, GitHub PR, Confluence)

Paper2Slides integration (CLI)
------------------------------

- Set in `config/default.yaml` (or your config):
  - `parser.backend: paper2slides`
  - `parser.paper2slides.command`: command that outputs JSON to stdout, supports `{input}` and optional `{tmp}` placeholders.
  - Example: `paper2slides --input {input} --output-format json`
- Supported inputs via Paper2Slides backend include `.pdf`/`.pptx` as provided by your CLI.

Julep orchestrator flag
-----------------------

- Set `orchestrator: julep` in config to use the Julep path.
- Current implementation falls back to the builtin pipeline unless Julep is installed and wired. It preserves outputs and structure while enabling a migration path to real Julep agents.

Paper2Slides setup
------------------

- Install Paper2Slides following its upstream docs or make the CLI available on PATH.
- Verify the CLI works, e.g.: `paper2slides --help`
- Use the sample config `config/paper2slides_example.yaml` and run:
  - `slideforge run --input /path/to/slides.pdf --config config/paper2slides_example.yaml --out build_p2s --auto-fix`
- The adapter expects the CLI to print structured deck JSON to stdout with the placeholder `{input}` replaced by the input file path. If your CLI writes to a file, set `parser.paper2slides.output` and use `{output}` in the command template as documented in the config.

License
-------

Open source friendly — add your preferred license file when ready.

Configuration
-------------

Use YAML config files to tune rules. Defaults live in `config/default.yaml`. A relaxed example is provided at `config/strict_relaxed.yaml`.

- section_rules: heuristic hints for tagging sections
- required_keywords: per-section keywords to validate coverage
- thresholds:
  - coverage_pass: overall coverage to get PASS
  - coverage_needs_update: overall coverage below this yields FAIL
- strict:
  - require_all_sections: if true, all sections in `required_keywords` must appear
  - min_per_section_coverage: average coverage each section must meet
  - min_slide_coverage: minimum coverage for individual slides (when section has keywords)
  - min_section_confidence: below this, a tag is considered unassigned
  - min_slides_per_section: map of section -> required slide count
  - disallow_unassigned: flag unassigned/low-confidence slides
  - fail_on_section_avg_below: when true, section-average shortfalls cause FAIL; otherwise NEEDS_UPDATE

Keys with spaces
----------------

- Section and keyword map keys may contain spaces, e.g., `"Expert Package"` or `"Control System"`.
- Use quotes in YAML when writing keys with spaces.
- See `config/with_spaces.yaml` for a working example. The pipeline’s tagger and checker fully support spaced keys.

Global keyword policy
---------------------

- Prefer a document-wide policy:
  - `required_keywords_global`: list applied across the entire document (coverage computed globally)
  - `forbidden_keywords`: list of terms that should NOT appear anywhere; presence triggers updates
- If `required_keywords_global` is present, the pipeline ignores per-section `required_keywords` for coverage scoring (it still computes section summaries).

CLI usage
---------

- Generate samples: `slideforge sample --out examples/`
- Run pipeline: `slideforge run --input <deck.json|.md|.txt> --config config/default.yaml --out build/ [--auto-fix]`

Reports
-------

- JSON: `compliance_report.json` includes `overall.status`, `overall.update_required`, `overall.reasons`, `per_slide`, and `section_summaries`.
- Text: `compliance_report.txt` is a human-readable summary with decision rationale and section summaries.
PPTX ingestion (builtin)
------------------------

- Install the optional dependency once: `make deps-pptx` (installs `python-pptx` into the local venv).
- Then run with a PowerPoint file:
  - `make run INPUT=/absolute/path/to/deck.pptx AUTO_FIX=1`
- The parser extracts slide titles and text boxes as bullets; the pipeline then tags sections, checks keywords, and decides PASS/NEEDS_UPDATE/FAIL.

DOCX ingestion (builtin)
------------------------

- Install the optional dependency once: `make deps-docx` (installs `python-docx` into the local venv).
- Then run with a Word document:
  - `make run INPUT=/absolute/path/to/deck.docx AUTO_FIX=1`
- Parser behavior: uses Heading 1/Title paragraphs as slide titles; treats other paragraphs as bullets; table cell text is appended to the last slide.

API (FastAPI)
-------------

- One-shot start (installs everything then runs):
  - make start-api
  - Skip PPTX dep if not needed: NO_PPTX=1 make start-api

- Or run step-by-step:
  - make install        # project into local venv
  - make deps-api       # FastAPI, uvicorn, requests, bs4, multipart
  - make deps-pptx      # optional, for .pptx parsing
  - make run-api        # start server
  - Server runs at http://localhost:8000
- Endpoints:
  - POST `/evaluate` (multipart): fields `file` (upload), `auto_fix` (bool), `config_path` (optional)
  - POST `/evaluate-url` (JSON): `{ "url": "https://...", "auto_fix": true, "config_path": "config/default.yaml", "allowed_exts": ["pptx","pdf"], "crawl_links": true }`
- Example (upload PPTX via curl):
  - curl -F "file=@/absolute/path/deck.pptx" -F "auto_fix=true" -F "config_path=config/default.yaml" http://localhost:8000/evaluate
- Example (evaluate a URL):
  - curl -X POST -H "Content-Type: application/json" -d '{"url":"https://example.com/page.html","auto_fix":true,"config_path":"config/default.yaml","allowed_exts":["pptx","md"],"crawl_links":true}' http://localhost:8000/evaluate-url

More docs
---------

- Deep dive with sequence diagram and Julep mapping: `HowItWorksStepByStep.md`
- Troubleshooting & tuning tips: `docs/TROUBLESHOOTING.md`
- Sprint report generation from Jira JSON: `docs/SPRINT_REPORTS.md`
- LLM integration (draft usage): `docs/LLM.md`

Frontend (React)
----------------

- Dev server: `make fe-dev` (after `npm install` in `frontend/` or `make fe-install`)
- Configure API base: `frontend/.env` with `VITE_API_BASE_URL=http://localhost:8000`
- Pages:
  - Upload: upload PPTX/MD/TXT/JSON to `/evaluate`
  - From URL: send URL to `/evaluate-url` (optionally crawl links)
