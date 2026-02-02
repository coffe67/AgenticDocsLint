from __future__ import annotations

from typing import Dict, Any, List

from slideforge.models import Deck, KeywordCheckResult, SlideEvaluation


def check_keywords(deck: Deck, config: Dict[str, Any]) -> List[SlideEvaluation]:
    required_map: Dict[str, List[str]] = config.get("required_keywords", {})
    evaluations: List[SlideEvaluation] = []
    for s in deck.slides:
        if not s.section:
            evaluations.append(SlideEvaluation(slide_index=s.index, section=None, section_confidence=s.section_confidence, keyword_result=None))
            continue
        required = required_map.get(s.section, [])
        text = s.text_content().lower()
        found = sorted([k for k in required if k.lower() in text])
        missing = sorted([k for k in required if k.lower() not in text])
        coverage = (len(found) / len(required)) if required else 1.0
        result = KeywordCheckResult(section=s.section, required_keywords=required, found=found, missing=missing, coverage=coverage)
        evaluations.append(
            SlideEvaluation(
                slide_index=s.index,
                section=s.section,
                section_confidence=s.section_confidence,
                keyword_result=result,
            )
        )
    return evaluations

