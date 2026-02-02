from __future__ import annotations

import json
import os
from typing import Dict, Any

from slideforge.models import Deck, Slide


def parse_deck(input_path: str) -> Deck:
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".json":
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Deck.from_dict(data)
    if ext in (".md", ".markdown"):
        return _parse_markdown(input_path)
    if ext in (".txt",):
        return _parse_text(input_path)

    # Stubs for PDF/PPTX; replace with Paper2Slides integration.
    # For now, raise a friendly message.
    if ext in (".pdf", ".pptx"):
        raise NotImplementedError(
            f"Parsing {ext} is not implemented in the scaffold. "
            f"Use JSON/Markdown for now or integrate Paper2Slides."
        )

    raise ValueError(f"Unsupported input format: {ext}")


def _parse_markdown(path: str) -> Deck:
    slides = []
    title = "Untitled"
    bullets: list[str] = []
    notes: str | None = None
    slide_index = 0

    def flush_slide():
        nonlocal slides, title, bullets, notes, slide_index
        if title.strip() or bullets or notes:
            slides.append(Slide(index=slide_index, title=title.strip() or f"Slide {slide_index}", bullets=bullets[:], notes=notes))
            slide_index += 1
        title = "Untitled"
        bullets = []
        notes = None

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                flush_slide()
                title = line[2:].strip()
            elif line.startswith("- ") or line.startswith("* "):
                bullets.append(line[2:].strip())
            elif line.strip() == "---":
                flush_slide()
            else:
                # treat as notes paragraph continuation
                if line.strip():
                    notes = (notes + "\n" if notes else "") + line.strip()
    flush_slide()
    meta: Dict[str, Any] = {"source": os.path.basename(path), "format": "markdown"}
    return Deck(meta=meta, slides=slides)


def _parse_text(path: str) -> Deck:
    # Simple parser where '---' splits slides, first non-empty line is title, others are bullets
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    raw_slides = [s.strip() for s in content.split("---") if s.strip()]
    slides: list[Slide] = []
    for i, block in enumerate(raw_slides):
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        title = lines[0]
        bullets = lines[1:]
        slides.append(Slide(index=i, title=title, bullets=bullets))
    meta = {"source": os.path.basename(path), "format": "text"}
    return Deck(meta=meta, slides=slides)

