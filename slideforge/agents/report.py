from __future__ import annotations

import json
import os
from typing import List

from slideforge.models import ComplianceReport, SlideEvaluation, ComplianceDecision


def save_report(report: ComplianceReport, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "compliance_report.json")
    txt_path = os.path.join(out_dir, "compliance_report.txt")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(format_human(report))


def format_human(report: ComplianceReport) -> str:
    lines = []
    lines.append(f"Status: {report.overall.status}")
    lines.append(f"Score: {report.overall.score:.2f}")
    lines.append(f"Update required: {str(report.overall.update_required)}")
    lines.append("")
    if report.overall.reasons:
        lines.append("Decision rationale:")
        for r in report.overall.reasons:
            lines.append(f"- {r}")
        lines.append("")
    if report.section_summaries:
        lines.append("Section summaries:")
        for s in report.section_summaries:
            below = s.get("below_min_slides", [])
            below_str = ", ".join(map(str, below)) if below else "-"
            lines.append(
                f"- {s.get('section')}: slides={s.get('slides')} avg_cov={s.get('avg_coverage')} below_min=[{below_str}]"
            )
        lines.append("")
    lines.append("Per-slide summary:")
    for e in report.per_slide:
        sec = e.section or "(unknown)"
        if e.keyword_result:
            cov = e.keyword_result.coverage
            miss = ", ".join(e.keyword_result.missing) if e.keyword_result.missing else "-"
            lines.append(f"- Slide {e.slide_index} [{sec}] coverage={cov:.2f} missing=[{miss}]")
        else:
            lines.append(f"- Slide {e.slide_index} [{sec}] coverage=N/A missing=[-]")
    lines.append("")
    if report.overall.recommendations:
        lines.append("Recommendations:")
        for r in report.overall.recommendations:
            lines.append(f"- {r}")
    return "\n".join(lines) + "\n"
