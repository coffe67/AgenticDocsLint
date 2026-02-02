from __future__ import annotations

import os
from typing import Dict, Any

from slideforge.models import Deck, Slide, ComplianceReport


def generate_missing(deck: Deck, report: ComplianceReport, config: Dict[str, Any]) -> Deck:
    # Create placeholder slides for sections that never appear or have poor coverage
    min_coverage = float(config.get("thresholds", {}).get("coverage_needs_update", 0.5))
    required_keywords = config.get("required_keywords", {})

    present_sections = {s.section for s in deck.slides if s.section}
    all_sections = set(required_keywords.keys())
    missing_sections = sorted(list(all_sections - present_sections))

    next_index = len(deck.slides)
    for sec in missing_sections:
        deck.slides.append(_placeholder_slide(next_index, sec, required_keywords.get(sec, [])))
        next_index += 1

    # For low coverage slides, append a helper slide with draft content
    for e in report.per_slide:
        if e.keyword_result and e.keyword_result.coverage < min_coverage:
            sec = e.section or "Unknown"
            missing = e.keyword_result.missing
            if not missing:
                continue
            deck.slides.append(
                Slide(
                    index=next_index,
                    title=f"Draft additions for {sec}",
                    bullets=[f"Include: {m}" for m in missing],
                    notes="Auto-generated placeholder content. Replace with real material.",
                    section=sec,
                    section_confidence=0.4,
                )
            )
            next_index += 1
    return deck


def _placeholder_slide(index: int, section: str, keywords: list[str]) -> Slide:
    return Slide(
        index=index,
        title=f"[Placeholder] {section}",
        bullets=[f"Add content covering: {k}" for k in keywords[:5]] or ["Add relevant content"],
        notes="This slide was auto-added to cover a required section.",
        section=section,
        section_confidence=0.3,
    )


def export_deck_markdown(deck: Deck, out_path: str) -> None:
    lines = []
    for s in deck.slides:
        lines.append(f"# {s.title}")
        for b in s.bullets:
            lines.append(f"- {b}")
        if s.notes:
            lines.append("")
            lines.append(s.notes)
        lines.append("\n---\n")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

