from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from slideforge.models import Deck, Slide
from slideforge.llm import load_llm_config, LLMClient, LLMNotConfigured
from slideforge.agents.sprint_report import summarize_jira, _select_top_issues


def build_deck_from_jira_llm(jira: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Deck:
    """
    Use an LLM to generate concise, audience-ready slides for a sprint report.

    Expects the model to return a JSON object:
      { slides: [ { title: str, bullets: [str], notes?: str, section?: str } ] }

    Falls back to heuristic deck on any error or missing configuration.
    """
    from slideforge.agents.sprint_report import build_deck_from_jira as build_heuristic

    cfg = config or {}
    llm_cfg = load_llm_config(cfg)
    if not llm_cfg:
        return build_heuristic(jira, theme=cfg)

    client = LLMClient(llm_cfg)

    sprint = jira.get("sprint", {}) or {}
    name = sprint.get("name") or "Sprint"
    start = sprint.get("start_date") or ""
    end = sprint.get("end_date") or ""
    summary = summarize_jira(jira)

    # Build a compact context with top issues to keep prompts small
    issues = jira.get("issues", []) or []
    top = _select_top_issues(issues, limit=8)
    top_min = [
        {
            "key": it.get("key"),
            "summary": it.get("summary"),
            "status": it.get("status"),
            "sp": it.get("story_points"),
        }
        for it in top
    ]

    system = (
        "You are an expert technical writer. Create concise, executive-ready slide content for sprint reports. "
        "Always respond with a compact JSON object only."
    )
    user = (
        "Create 2-4 slides for this sprint report. Use short, informative bullets (max 8 words).\n"
        "Slides to include:\n"
        "- Title slide with sprint name and date range\n"
        "- Summary with total issues, story points (done/total), and key statuses\n"
        "- Top Issues (select notable items)\n"
        "If risk or blockers are evident, add a 'Risks & Next Steps' slide.\n\n"
        f"Sprint: {name} ({start} – {end})\n"
        f"Totals: issues={summary['total_issues']}, sp_done={summary['story_points_done']:.0f}, sp_total={summary['story_points_total']:.0f}\n"
        f"StatusCounts: {json.dumps(summary['status_counts'])}\n"
        f"TopIssues: {json.dumps(top_min)}\n\n"
        "Respond as JSON: {\n  \"slides\": [ { \"title\": str, \"bullets\": [str], \"notes\"?: str } ]\n}"
    )

    try:
        data = client.call_json(user, system=system)
        slides_json = data.get("slides") if isinstance(data, dict) else None
        slides_out: List[Slide] = []
        if isinstance(slides_json, list):
            for idx, sl in enumerate(slides_json):
                title = str(sl.get("title")) if isinstance(sl, dict) else "Untitled"
                bullets = [str(b) for b in (sl.get("bullets") or [])][:8] if isinstance(sl, dict) else []
                notes = sl.get("notes") if isinstance(sl, dict) else None
                slides_out.append(
                    Slide(index=idx, title=title or f"Slide {idx}", bullets=bullets, notes=notes)
                )
        if not slides_out:
            return build_heuristic(jira, theme=cfg)
        deck_meta = {"source": "jira-llm", "sprint": name, "start": start, "end": end}
        return Deck(meta=deck_meta, slides=slides_out)
    except (LLMNotConfigured, Exception):
        return build_heuristic(jira, theme=cfg)

