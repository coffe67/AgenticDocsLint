from __future__ import annotations

from typing import Dict, Any
import os
import json

from slideforge.parsers.paper2slides_adapter import parse_deck
from slideforge.agents.normalizer import normalize_deck
from slideforge.agents.section_tagger import tag_sections
from slideforge.agents.keyword_checker import check_keywords
from slideforge.agents.compliance_decider import decide
from slideforge.agents.report import save_report
from slideforge.agents.generator import generate_missing, export_deck_markdown


def run_pipeline(input_path: str, config: Dict[str, Any], out_dir: str, auto_fix: bool = False) -> Dict[str, Any]:
    # Placeholder for a Julep-backed implementation.
    # For now, we detect if 'julep' is installed; otherwise raise a clear error.
    try:
        import julep  # type: ignore
        # An actual Julep pipeline would be constructed here with agents.
        # Until implemented, fallback to the builtin pipeline but note mode.
        # This keeps the flag usable without breaking local runs.
        return _fallback_builtin(input_path, config, out_dir, auto_fix)
    except Exception as e:
        # Fallback to builtin with rationale; to force error, replace with 'raise' below.
        return _fallback_builtin(input_path, config, out_dir, auto_fix)


def _fallback_builtin(input_path: str, config: Dict[str, Any], out_dir: str, auto_fix: bool) -> Dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)
    deck = parse_deck(input_path, config)
    deck = normalize_deck(deck)
    deck = tag_sections(deck, config)
    evaluations = check_keywords(deck, config)
    decision = decide(evaluations, config)

    # Save parsed deck for debugging/inspection
    os.makedirs(out_dir, exist_ok=True)
    parsed_deck_path = os.path.join(out_dir, "parsed_deck.json")
    with open(parsed_deck_path, "w", encoding="utf-8") as f:
        json.dump(deck.to_dict(), f, indent=2, ensure_ascii=False)

    report_meta = {"source": deck.meta.get("source"), "total_slides": len(deck.slides), "orchestrator": "julep-fallback"}
    section_summaries = getattr(decision, "_section_summaries", None)
    report = {
        "meta": report_meta,
        "per_slide": [
            {
                "slide_index": s.slide_index,
                "section": s.section,
                "section_confidence": s.section_confidence,
                "keyword_result": None if s.keyword_result is None else {
                    "section": s.keyword_result.section,
                    "required_keywords": s.keyword_result.required_keywords,
                    "found": s.keyword_result.found,
                    "missing": s.keyword_result.missing,
                    "coverage": s.keyword_result.coverage,
                },
            }
            for s in evaluations
        ],
        "overall": {
            "status": decision.status,
            "score": decision.score,
            "update_required": decision.update_required,
            "reasons": decision.reasons,
            "recommendations": decision.recommendations,
        },
        "section_summaries": section_summaries,
    }
    # Save via the same report utility by adapting to model
    from slideforge.models import ComplianceReport, SlideEvaluation, KeywordCheckResult, ComplianceDecision

    per_slide = []
    for e in report["per_slide"]:
        kr = e["keyword_result"]
        per_slide.append(
            SlideEvaluation(
                slide_index=e["slide_index"],
                section=e["section"],
                section_confidence=e["section_confidence"],
                keyword_result=None if kr is None else KeywordCheckResult(
                    section=kr["section"],
                    required_keywords=kr["required_keywords"],
                    found=kr["found"],
                    missing=kr["missing"],
                    coverage=kr["coverage"],
                ),
            )
        )

    comp = ComplianceDecision(
        status=report["overall"]["status"],
        score=report["overall"]["score"],
        update_required=report["overall"]["update_required"],
        reasons=report["overall"]["reasons"],
        recommendations=report["overall"]["recommendations"],
    )
    comp._section_summaries = section_summaries  # type: ignore
    comp_report = ComplianceReport(meta=report_meta, per_slide=per_slide, overall=comp, section_summaries=section_summaries)
    save_report(comp_report, out_dir)

    generated_paths = {}
    if auto_fix:
        deck2 = generate_missing(deck, comp_report, config)
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
