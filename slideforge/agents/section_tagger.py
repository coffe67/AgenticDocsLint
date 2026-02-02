from __future__ import annotations

from typing import Dict, Any, Tuple

from slideforge.models import Deck


def tag_sections(deck: Deck, config: Dict[str, Any]) -> Deck:
    rules: Dict[str, Any] = config.get("section_rules", {})
    # rules: { section_name: {keywords: [..]} }
    for s in deck.slides:
        section, conf = _infer_section(s.title, s.text_content(), rules)
        s.section = section
        s.section_confidence = conf
    return deck


def _infer_section(title: str, text: str, rules: Dict[str, Any]) -> Tuple[str | None, float]:
    title_l = title.lower()
    text_l = text.lower()
    best_section = None
    best_score = 0
    for sec, cfg in rules.items():
        kws = [k.lower() for k in cfg.get("keywords", [])]
        score = 0
        for k in kws:
            if k in title_l:
                score += 2
            if k in text_l:
                score += 1
        if score > best_score:
            best_score = score
            best_section = sec
    conf = min(1.0, best_score / 5.0) if best_score > 0 else 0.0
    return best_section, conf

