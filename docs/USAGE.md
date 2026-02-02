SlideForge Usage
================

Install (editable)
------------------

- python3 -m venv .venv && source .venv/bin/activate
- pip install -e .

Generate samples
----------------

- slideforge sample --out examples/

Run the pipeline
----------------

- slideforge run --input examples/deck_sample.json --config config/default.yaml --out build --auto-fix

Config options (strict)
-----------------------

- strict.require_all_sections: enforce presence of all sections
- strict.min_per_section_coverage: average coverage per section must meet this
- strict.min_slide_coverage: minimum per-slide coverage
- strict.min_section_confidence: treat tags below as unassigned
- strict.min_slides_per_section: required slide counts per section
- strict.disallow_unassigned: require all slides to have an acceptable tag
- strict.fail_on_section_avg_below:
  - true: section-average shortfalls cause FAIL
  - false: section-average shortfalls cause NEEDS_UPDATE (with rationale)

Relaxed example
---------------

- slideforge run --input examples/deck_sample.json --config config/strict_relaxed.yaml --out build_relaxed --auto-fix

Outputs
-------

- build/compliance_report.json: machine-readable report
- build/compliance_report.txt: human-readable summary
- build/updated_deck.json / .md: present when --auto-fix is supplied

Paper2Slides via CLI
--------------------

- Ensure the Paper2Slides CLI is installed and available in PATH.
- Use the example config:
  - `slideforge run --input /path/to/slides.pdf --config config/paper2slides_example.yaml --out build_p2s --auto-fix`
- The config uses `parser.backend: paper2slides` with a command template that supports `{input}`.
- If your CLI writes to a file, set `parser.paper2slides.output` and include `{output}` in the command template. The adapter loads that JSON file.
