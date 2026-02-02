from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional, List
import subprocess, shlex, tempfile

from slideforge.models import Deck, Slide


def parse_deck(input_path: str, config: Optional[Dict[str, Any]] = None) -> Deck:
    ext = os.path.splitext(input_path)[1].lower()
    # If configured for Paper2Slides backend, delegate for supported types
    if config and (config.get("parser", {}).get("backend") == "paper2slides"):
        return _parse_via_paper2slides_cli(input_path, config)

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
    if ext == ".pptx":
        return _parse_pptx(input_path)
    if ext == ".pdf":
        raise NotImplementedError(
            "PDF parsing not implemented in builtin path. Use Paper2Slides backend or provide JSON/MD/TXT."
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


def _parse_via_paper2slides_cli(input_path: str, config: Dict[str, Any]) -> Deck:
    ps_cfg = (config.get("parser", {}) or {}).get("paper2slides", {}) or {}
    cmd_tpl = ps_cfg.get("command")
    output_mode = (ps_cfg.get("output") or "stdout").lower()
    if not cmd_tpl:
        raise RuntimeError("parser.backend=paper2slides but no command configured under parser.paper2slides.command")

    # Build command string
    # Support a temporary directory placeholder {tmp}
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = cmd_tpl.replace("{input}", shlex.quote(input_path)).replace("{tmp}", shlex.quote(tmpdir))
        if output_mode == "stdout":
            proc = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"Paper2Slides CLI failed: code={proc.returncode}\n{proc.stderr}")
            try:
                data = json.loads(proc.stdout)
            except json.JSONDecodeError as e:
                raise RuntimeError("Paper2Slides CLI did not return valid JSON on stdout") from e
            return Deck.from_dict(data)
        else:
            out_path = ps_cfg.get("output")
            if not out_path or "{" in out_path:
                # allow template using {tmp} in output path
                out_path = (out_path or "{tmp}/deck.json").replace("{tmp}", tmpdir)
            # Append output path to command if it contains {output}
            if "{output}" in cmd_tpl:
                cmd = cmd_tpl.replace("{input}", shlex.quote(input_path)).replace("{tmp}", shlex.quote(tmpdir)).replace("{output}", shlex.quote(out_path))
            proc = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"Paper2Slides CLI failed: code={proc.returncode}\n{proc.stderr}")
            if not os.path.exists(out_path):
                raise RuntimeError(f"Paper2Slides CLI expected output not found: {out_path}")
            with open(out_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Deck.from_dict(data)


def _parse_pptx(path: str) -> Deck:
    try:
        from pptx import Presentation  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "PPTX parsing requires the 'python-pptx' package. Install it, e.g.:\n"
            "  pip install python-pptx"
        ) from e

    prs = Presentation(path)
    slides: List[Slide] = []

    def text_from_shape(shape) -> List[str]:
        lines: List[str] = []
        if not hasattr(shape, "has_text_frame"):
            return lines
        if not shape.has_text_frame:
            return lines
        for p in shape.text_frame.paragraphs:
            txt = "".join([run.text for run in p.runs]).strip() if p.runs else (p.text or "").strip()
            if txt:
                lines.append(txt)
        return lines

    for idx, s in enumerate(prs.slides):
        title = "Untitled"
        bullets: List[str] = []
        # Try title placeholders first
        for shp in s.shapes:
            if shp.is_placeholder and getattr(shp.placeholder_format, "type", None) == 1:  # TITLE
                lines = text_from_shape(shp)
                if lines:
                    title = lines[0]
                    break
        # Collect text from non-title shapes
        for shp in s.shapes:
            if shp.is_placeholder and getattr(shp.placeholder_format, "type", None) == 1:
                continue
            bullets += text_from_shape(shp)
        # Trim bullets if they duplicate title
        bullets = [b for b in bullets if b != title]
        slides.append(Slide(index=idx, title=title, bullets=bullets))

    meta: Dict[str, Any] = {"source": os.path.basename(path), "format": "pptx"}
    return Deck(meta=meta, slides=slides)
