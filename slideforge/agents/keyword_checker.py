from __future__ import annotations

from typing import Dict, Any, List, Tuple, Dict as TDict

from slideforge.models import Deck, KeywordCheckResult, SlideEvaluation


def check_keywords(deck: Deck, config: Dict[str, Any]) -> Tuple[List[SlideEvaluation], TDict[str, Any]]:
    # Global required/forbidden policy takes precedence if provided.
    required_global: List[str] = config.get("required_keywords_global", []) or []
    forbidden_global: List[str] = config.get("forbidden_keywords", []) or []

    evaluations: List[SlideEvaluation] = []

    # If global required keywords are provided, compute document-level coverage.
    keyword_summary: TDict[str, Any] = {}
    if required_global:
        found_set = set()
        missing_set = set(k.lower() for k in required_global)
        occurrences: TDict[str, List[int]] = {k: [] for k in required_global}
        for s in deck.slides:
            text = s.text_content().lower()
            for k in required_global:
                kl = k.lower()
                if kl in text:
                    found_set.add(kl)
                    occurrences[k].append(s.index)
        missing = sorted([k for k in required_global if k.lower() not in found_set])
        found = sorted([k for k in required_global if k.lower() in found_set])
        coverage = (len(found) / len(required_global)) if required_global else 1.0
        keyword_summary["required"] = {
            "required_keywords": required_global,
            "found": found,
            "missing": missing,
            "coverage": coverage,
            "occurrences": occurrences,
        }

        # Per-slide evaluations set to None to avoid misleading per-slide coverage
        for s in deck.slides:
            evaluations.append(
                SlideEvaluation(
                    slide_index=s.index,
                    section=s.section,
                    section_confidence=s.section_confidence,
                    keyword_result=None,
                )
            )
    else:
        # Fallback: section-based checks (legacy behavior)
        required_map: Dict[str, List[str]] = config.get("required_keywords", {})
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

    # Forbidden keywords detection
    if forbidden_global:
        occurrences_f: TDict[str, List[int]] = {k: [] for k in forbidden_global}
        found_forbidden = set()
        for s in deck.slides:
            text = s.text_content().lower()
            for k in forbidden_global:
                if k.lower() in text:
                    found_forbidden.add(k)
                    occurrences_f[k].append(s.index)
        keyword_summary["forbidden"] = {
            "forbidden_keywords": forbidden_global,
            "found": sorted(found_forbidden),
            "occurrences": occurrences_f,
        }

    return evaluations, keyword_summary
