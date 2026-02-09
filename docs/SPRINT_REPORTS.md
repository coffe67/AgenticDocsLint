# Sprint Reports (Jira → Slides/Images)

This feature generates sprint reports from a Jira JSON payload using the same agentic approach (stateless functions, swappable outputs).

Input JSON (example)
--------------------

```
{
  "sprint": {"name": "Sprint 42", "start_date": "2026-02-01", "end_date": "2026-02-14"},
  "issues": [
    {"key": "ABC-1", "summary": "Implement feature X", "status": "Done", "story_points": 5, "assignee": "A"},
    {"key": "ABC-2", "summary": "Bug fix Y", "status": "In Progress", "story_points": 3, "assignee": "B"}
  ]
}
```

What it produces
----------------
- PPTX: Title + Summary + Top Issues slides (via python-pptx)
- MD/JSON: Same deck in Markdown or JSON
- PNG: Simple summary card (via Pillow), optional

API
---

- POST `/generate-sprint-report`
  - Body JSON: `{ "jira": {…}, "formats": ["pptx","json","png"], "template_config_path": "config/sprint_template.yaml", "generator_mode": "heuristic|llm" }`
  - Returns: `{ artifacts: { pptx?, md?, json?, png? }, run_workspace }`

CLI
---

- `slideforge generate-sprint --jira path/to/jira.json --out build_sprint --format pptx --template config/sprint_template.yaml [--mode llm]`

Templating
----------

- Minimal theme in `config/sprint_template.yaml` (fonts, colors).
- Extendable: add your brand assets and more slide types (velocity, burndown images) by expanding `slideforge/agents/sprint_report.py`.

LLM mode
--------

- Enable mode per request (`generator_mode: llm`) or CLI (`--mode llm`).
- Provide LLM config under `llm.*` (see `docs/LLM.md`). If not configured or unavailable, the system falls back to heuristic slides.

Notes
-----
- Install deps for outputs you need:
  - `make deps-pptx` for PPTX
  - `make deps-images` for PNG
- Docker build includes these by default.
