from __future__ import annotations

from typing import List, Dict, Any, Tuple, DefaultDict, Optional
from collections import defaultdict

from slideforge.models import SlideEvaluation, ComplianceDecision


def decide(evaluations: List[SlideEvaluation], config: Dict[str, Any], keyword_summary: Optional[Dict[str, Any]] = None) -> ComplianceDecision:
    thresholds = config.get("thresholds", {})
    coverage_pass = float(thresholds.get("coverage_pass", 0.8))
    coverage_needs = float(thresholds.get("coverage_needs_update", 0.5))
    strict = config.get("strict", {})
    min_per_section_cov = float(strict.get("min_per_section_coverage", 0.0))
    min_slide_cov = float(strict.get("min_slide_coverage", 0.0))
    min_conf = float(strict.get("min_section_confidence", 0.0))
    disallow_unassigned = bool(strict.get("disallow_unassigned", False))
    require_all_sections = bool(strict.get("require_all_sections", True))
    fail_on_section_avg_below = bool(strict.get("fail_on_section_avg_below", True))

    # Prefer global required coverage if provided
    overall_cov = 1.0
    if keyword_summary and keyword_summary.get("required"):
        overall_cov = float(keyword_summary["required"].get("coverage", 1.0))
    else:
        coverages = []
        for e in evaluations:
            if e.keyword_result is not None:
                coverages.append(e.keyword_result.coverage)
        overall_cov = sum(coverages) / len(coverages) if coverages else 1.0

    # Collect reasons and recommendations (why)
    reasons: List[str] = []
    recommendations: List[str] = []

    slides_with_missing = [
        e for e in evaluations if e.keyword_result and e.keyword_result.missing
    ]
    if slides_with_missing:
        idxs = ", ".join(str(e.slide_index) for e in slides_with_missing[:10])
        reasons.append(f"Slides missing required keywords: {idxs}")
        for e in slides_with_missing:
            miss = ", ".join(e.keyword_result.missing[:5])
            recommendations.append(
                f"Slide {e.slide_index} ({e.section}): add missing keywords -> {miss}"
            )

    # Identify missing sections (seen vs required)
    required_sections = set((config.get("required_keywords") or {}).keys())
    present_sections = set([e.section for e in evaluations if e.section])
    missing_sections = sorted(list(required_sections - present_sections))
    if require_all_sections and missing_sections:
        reasons.append(
            f"Missing required sections: {', '.join(missing_sections[:10])}"
        )

    # Per-section aggregates and strict checks
    per_section: DefaultDict[str, List[Tuple[int, float]]] = defaultdict(list)
    unassigned_slides: List[int] = []
    for e in evaluations:
        # Treat low-confidence tags as unassigned for strict rules
        if not e.section or (e.section_confidence is not None and e.section_confidence < min_conf):
            unassigned_slides.append(e.slide_index)
            continue
        cov = e.keyword_result.coverage if e.keyword_result else 1.0
        per_section[e.section].append((e.slide_index, cov))

    section_summaries: List[Dict[str, Any]] = []
    for sec in sorted(per_section.keys()):
        vals = per_section[sec]
        if not vals:
            continue
        avg = sum(c for _, c in vals) / len(vals)
        below_min = [i for i, c in vals if c < min_slide_cov]
        section_summaries.append({
            "section": sec,
            "slides": len(vals),
            "avg_coverage": round(avg, 3),
            "below_min_slides": below_min,
        })
        if min_per_section_cov > 0 and avg < min_per_section_cov:
            reasons.append(f"Section {sec} average coverage {avg:.2f} < {min_per_section_cov:.2f}")
        if below_min:
            reasons.append(f"Slides below per-slide coverage in {sec}: {', '.join(map(str, below_min[:10]))}")

    # Min slides per section rule
    min_slides_map: Dict[str, int] = strict.get("min_slides_per_section", {}) or {}
    for sec, min_count in min_slides_map.items():
        actual = len(per_section.get(sec, []))
        if actual < int(min_count):
            reasons.append(f"Section {sec} has {actual} slides; requires >= {int(min_count)}")

    # Unassigned slides rule
    if disallow_unassigned and unassigned_slides:
        reasons.append(f"Unassigned or low-confidence slides: {', '.join(map(str, unassigned_slides[:20]))}")

    # Global required keyword rationale
    if keyword_summary and keyword_summary.get("required"):
        req = keyword_summary["required"]
        missing = req.get("missing") or []
        if missing:
            reasons.append(f"Missing required keywords (global): {', '.join(missing[:10])}")

    # Forbidden keyword rationale
    if keyword_summary and keyword_summary.get("forbidden"):
        forb = keyword_summary["forbidden"]
        found_f = forb.get("found") or []
        if found_f:
            reasons.append(f"Forbidden keywords present: {', '.join(found_f[:10])}")

    # Coverage-based rationale
    if overall_cov < coverage_pass:
        reasons.append(
            f"Overall coverage {overall_cov:.2f} < pass threshold {coverage_pass:.2f}"
        )

    # Decision policy:
    # - FAIL if overall coverage < needs threshold
    # - NEEDS_UPDATE if any missing keywords/sections OR overall < pass
    # - PASS only if overall >= pass and no missing keywords/sections
    # Severity-based decision
    hard_violations = []
    if require_all_sections and missing_sections:
        hard_violations.append("missing_sections")
    # Any section avg coverage < needs threshold could be treated as hard
    if min_per_section_cov and any(
        (s.get("avg_coverage", 1.0) < min_per_section_cov) for s in section_summaries
    ):
        if fail_on_section_avg_below:
            hard_violations.append("low_section_avg")
    if overall_cov < coverage_needs:
        hard_violations.append("overall_low")

    if hard_violations:
        status = "FAIL"
    elif (
        slides_with_missing or missing_sections or overall_cov < coverage_pass or unassigned_slides
        or any(s.get("below_min_slides") for s in section_summaries)
        or (keyword_summary and keyword_summary.get("forbidden") and (keyword_summary["forbidden"].get("found") or []))
        or (keyword_summary and keyword_summary.get("required") and (keyword_summary["required"].get("missing") or []))
    ):
        status = "NEEDS_UPDATE"
    else:
        status = "PASS"

    update_required = status != "PASS"

    decision = ComplianceDecision(
        status=status,
        score=overall_cov,
        update_required=update_required,
        reasons=reasons,
        recommendations=recommendations,
    )
    # Attach section summaries dynamically via attribute for the report layer to pick up
    decision._section_summaries = section_summaries  # type: ignore[attr-defined]
    return decision
