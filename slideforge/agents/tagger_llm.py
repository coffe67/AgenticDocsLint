from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from slideforge.models import Deck
from slideforge.llm import LLMClient, load_llm_config, LLMNotConfigured
from slideforge.agents.section_tagger import _infer_section


def tag_sections_llm(deck: Deck, config: Dict[str, Any]) -> Deck:
    llm_cfg = load_llm_config(config)
    if not llm_cfg:
        # Fallback to heuristic
        from slideforge.agents.section_tagger import tag_sections

        return tag_sections(deck, config)

    client = LLMClient(llm_cfg)
    allowed = list((config.get("section_rules") or {}).keys())
    sys = (
        "You are a helpful assistant that classifies slides into a section label. "
        "Respond with a compact JSON object only."
    )
    for s in deck.slides:
        prompt = build_prompt_for_slide(s.title, s.bullets, s.notes, allowed)
        try:
            ck = client._short_hash(f"tag:{llm_cfg.model}:{s.index}:{s.title}|{','.join(s.bullets)}|{','.join(allowed)}")
            data = client.call_json(prompt, system=sys, cache_key=ck, log_label=f"tag_slide_{s.index}")
            section = data.get("section")
            conf = float(data.get("confidence", 0)) if data.get("confidence") is not None else 0.0
            if isinstance(section, str) and section in allowed:
                s.section = section
                s.section_confidence = max(0.0, min(1.0, conf))
            else:
                # Guardrail: fallback to heuristic mapping
                section2, conf2 = _infer_section(s.title, s.text_content(), config.get("section_rules", {}))
                s.section, s.section_confidence = section2, conf2
        except (LLMNotConfigured, Exception):
            section2, conf2 = _infer_section(s.title, s.text_content(), config.get("section_rules", {}))
            s.section, s.section_confidence = section2, conf2
    return deck


def build_prompt_for_slide(title: str, bullets: List[str], notes: str | None, allowed_sections: List[str]) -> str:
    body = "\n".join([f"- {b}" for b in bullets])
    notes_s = f"\nNotes: {notes}" if notes else ""
    allowed = ", ".join(allowed_sections)
    return (
        "Classify this slide into exactly one section from the allowed list.\n"
        f"Allowed sections: [{allowed}]\n"
        "Return JSON with keys: section (string, exactly one of allowed), confidence (0..1).\n"
        f"Title: {title}\n"
        f"Bullets:\n{body}{notes_s}\n"
    )
