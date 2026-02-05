# Troubleshooting & Tuning

This guide helps explain common outputs (like “unknown” or “no keywords”) and how to tune extraction, tagging, and rules.

Key artifacts
- parsed_deck.json: Saved for each run in the output directory. Inspect to confirm what text was actually extracted per slide.
- compliance_report.json and .txt: See assigned sections, keyword coverage, and rationale.

Why “Slide N [unknown] (no keywords)” appears
- unknown: The SectionTagger didn’t match the slide to any section based on `config/…yaml` → `section_rules`.
- no keywords: KeywordChecker only validates slides with a section. Without a section, there’s no per‑section keyword list to check, so it prints “(no keywords)”.

How to diagnose
1) Inspect extracted text: open `<out>/parsed_deck.json` and check `slides[i].title` and `slides[i].bullets`.
2) Compare with config:
   - `section_rules.<Section>.keywords` — do these terms exist in the slide title/text?
   - `required_keywords.<Section>` — are they realistic for your content?
3) If text looks missing, your deck may use shapes without text frames (images, charts, grouped shapes).

How to fix quickly
- Tune tagging keywords: add synonyms/localized terms to `section_rules`.
  - Example: add `agenda`, `overview`, `introducción` to Introduction.
- Adjust thresholds: if confident titles contain exact section names, relax reliance on keywords (we added a fallback that maps titles to section names directly).
- Improve extraction for PPTX: extend the parser to cover more shape types.
- Use Paper2Slides CLI: for formats it supports, configure `parser.backend: paper2slides` and set a CLI command that outputs our deck JSON.

PPTX specifics
- Current extractor (python-pptx) reads:
  - Title: first TITLE placeholder text if present, else “Untitled”.
  - Bullets: text frames from non‑title shapes.
- It does not read text embedded in images, charts, or arbitrary grouped shapes without text frames. If your deck relies on that, consider:
  - Converting important content into text frames
  - Enhancing the extractor to traverse more object types

Config tuning checklist
- Add terms under `section_rules` that match your slide titles/bullets.
- Ensure `required_keywords` per section reflect your policy and language.
- For stricter policies, use `strict.*` (e.g., `require_all_sections`, `min_section_confidence`).
- Decide FAIL vs NEEDS_UPDATE for section‑avg shortfalls via `strict.fail_on_section_avg_below`.

Paper2Slides
- Use `config/paper2slides_example.yaml` and set a CLI command that prints deck JSON to stdout (or to a file you point to with `{output}`).
- If the CLI JSON doesn’t match `schemas/deck.schema.json`, add a mapping adapter.

LLM agents (future)
- Replace SectionTagger or Generator with LLM‑powered agents via the `orchestrator: julep` path, keeping output shapes consistent.

