from __future__ import annotations

import json
import os
from typing import Dict, Any

from slideforge.models import ComplianceReport
from slideforge.parsers.paper2slides_adapter import parse_deck
from slideforge.agents.normalizer import normalize_deck
from slideforge.agents.section_tagger import tag_sections
from slideforge.agents.keyword_checker import check_keywords
from slideforge.agents.compliance_decider import decide
from slideforge.agents.report import save_report
from slideforge.agents.generator import generate_missing, export_deck_markdown


def run_pipeline(input_path: str, config: Dict[str, Any], out_dir: str, auto_fix: bool = False) -> Dict[str, Any]:
    # Dispatch to Julep orchestrator if configured
    if (config.get("orchestrator") or "builtin").lower() == "julep":
        from .julep_orchestrator import run_pipeline as run_pipeline_julep
        return run_pipeline_julep(input_path, config, out_dir, auto_fix)

    os.makedirs(out_dir, exist_ok=True)

    deck = parse_deck(input_path, config)
    # Save parsed deck for debugging/inspection
    parsed_deck_path = os.path.join(out_dir, "parsed_deck.json")
    with open(parsed_deck_path, "w", encoding="utf-8") as f:
        json.dump(deck.to_dict(), f, indent=2, ensure_ascii=False)
    deck = normalize_deck(deck)
    deck = tag_sections(deck, config)
    evaluations = check_keywords(deck, config)
    decision = decide(evaluations, config)

    # Get section summaries from decision if available
    section_summaries = getattr(decision, "_section_summaries", None)

    report = ComplianceReport(
        meta={"source": deck.meta.get("source"), "total_slides": len(deck.slides)},
        per_slide=evaluations,
        overall=decision,
        section_summaries=section_summaries,
    )
    save_report(report, out_dir)

    generated_paths = {}
    if auto_fix:
        deck2 = generate_missing(deck, report, config)
        # Save updated deck JSON and Markdown
        deck_json = os.path.join(out_dir, "updated_deck.json")
        deck_md = os.path.join(out_dir, "updated_deck.md")
        with open(deck_json, "w", encoding="utf-8") as f:
            json.dump(deck2.to_dict(), f, indent=2, ensure_ascii=False)
        export_deck_markdown(deck2, deck_md)
        generated_paths = {"updated_deck_json": deck_json, "updated_deck_md": deck_md}

    return {
        "report_json": os.path.join(out_dir, "compliance_report.json"),
        "report_txt": os.path.join(out_dir, "compliance_report.txt"),
        "parsed_deck_json": parsed_deck_path,
        **generated_paths,
    }
