from __future__ import annotations

import io
import os
import shutil
import tempfile
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slideforge.config import load_config
from slideforge.pipeline.orchestrator import run_pipeline
from slideforge.agents.sprint_report import build_deck_from_jira, export_pptx, export_png_summary


app = FastAPI(title="SlideForge API", version="0.1.0")

# Enable CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",  # adjust for production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def _prepare_workspace() -> str:
    base = os.path.abspath(os.path.join(os.getcwd(), "build_api"))
    os.makedirs(base, exist_ok=True)
    run_id = str(uuid.uuid4())
    ws = os.path.join(base, run_id)
    os.makedirs(ws, exist_ok=True)
    return ws


def _serialize_report(report_json_path: str) -> Dict[str, Any]:
    import json

    with open(report_json_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/evaluate")
async def evaluate(
    file: UploadFile = File(...),
    auto_fix: bool = Form(False),
    config_path: Optional[str] = Form(None),
) -> JSONResponse:
    """
    Upload a single file (pptx/pdf/json/md/txt), evaluate it, and return the report JSON.
    """
    ws = _prepare_workspace()
    try:
        input_path = os.path.join(ws, file.filename)
        with open(input_path, "wb") as out:
            shutil.copyfileobj(file.file, out)

        cfg = load_config(config_path)
        out_dir = os.path.join(ws, "out")
        outputs = run_pipeline(input_path, cfg, out_dir, auto_fix=auto_fix)
        report = _serialize_report(outputs["report_json"])  # type: ignore[index]
        # Include pointers to artifacts
        payload = {
            "report": report,
            "artifacts": outputs,
            "run_workspace": ws,
        }
        return JSONResponse(payload)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evaluate-url")
async def evaluate_url(
    url: str,
    auto_fix: bool = False,
    config_path: Optional[str] = None,
    allowed_exts: Optional[List[str]] = None,
    crawl_links: bool = False,
) -> JSONResponse:
    """
    Download and evaluate a file at a URL, or crawl a page for files when crawl_links=true.
    Returns an array of results (one per file).
    """
    try:
        import requests  # type: ignore
        from urllib.parse import urljoin, urlparse
        from bs4 import BeautifulSoup  # type: ignore
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "URL evaluation requires requests and beautifulsoup4. "
                "Install via: make install && . hackathon2026/bin/activate && pip install requests beautifulsoup4"
            ),
        )

    ws = _prepare_workspace()
    cfg = load_config(config_path)
    out_base = os.path.join(ws, "out")
    os.makedirs(out_base, exist_ok=True)

    def download_file(u: str, dest_dir: str) -> Optional[str]:
        r = requests.get(u, timeout=30)
        if r.status_code != 200:
            return None
        # Try to infer filename
        name = os.path.basename(urlparse(u).path) or f"download_{uuid.uuid4()}"
        path = os.path.join(dest_dir, name)
        with open(path, "wb") as f:
            f.write(r.content)
        return path

    def discover_links(page_url: str) -> List[str]:
        r = requests.get(page_url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            links.append(urljoin(page_url, a["href"]))
        return links

    # Build candidate URLs
    candidates: List[str] = []
    if crawl_links:
        try:
            for u in discover_links(url):
                candidates.append(u)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to crawl links: {e}")
    else:
        candidates = [url]

    # Filter by extension if provided
    if allowed_exts:
        allowed_set = {e.lower().lstrip(".") for e in allowed_exts}
        tmp = []
        for u in candidates:
            ext = os.path.splitext(urlparse(u).path)[1].lower().lstrip(".")
            if ext in allowed_set:
                tmp.append(u)
        candidates = tmp

    results = []
    for i, u in enumerate(candidates):
        try:
            input_path = download_file(u, ws)
            if not input_path:
                continue
            out_dir = os.path.join(out_base, f"f{i}")
            outputs = run_pipeline(input_path, cfg, out_dir, auto_fix=auto_fix)
            report = _serialize_report(outputs["report_json"])  # type: ignore[index]
            results.append({"url": u, "report": report, "artifacts": outputs})
        except Exception as e:
            results.append({"url": u, "error": str(e)})

    return JSONResponse({"results": results, "run_workspace": ws})


@app.post("/generate-sprint-report")
async def generate_sprint_report(
    jira: Dict[str, Any],
    formats: Optional[List[str]] = None,
    template_config_path: Optional[str] = None,
) -> JSONResponse:
    """
    Generate sprint report artifacts from a Jira JSON payload.
    formats: subset of ["pptx","md","json","png"]. Default: ["pptx","json"].
    """
    ws = _prepare_workspace()
    try:
        formats = formats or ["pptx", "json"]
        theme = load_config(template_config_path) if template_config_path else None
        deck = build_deck_from_jira(jira, theme=theme)
        out_dir = os.path.join(ws, "sprint")
        os.makedirs(out_dir, exist_ok=True)
        results: Dict[str, str] = {}
        if "pptx" in formats:
            pptx_path = os.path.join(out_dir, "sprint_report.pptx")
            export_pptx(deck, pptx_path, theme=theme)
            results["pptx"] = pptx_path
        if "md" in formats:
            from slideforge.agents.generator import export_deck_markdown

            md_path = os.path.join(out_dir, "sprint_report.md")
            export_deck_markdown(deck, md_path)
            results["md"] = md_path
        if "json" in formats:
            import json

            json_path = os.path.join(out_dir, "sprint_report.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(deck.to_dict(), f, indent=2, ensure_ascii=False)
            results["json"] = json_path
        if "png" in formats:
            png_path = os.path.join(out_dir, "sprint_report.png")
            export_png_summary(jira, png_path, theme=theme)
            results["png"] = png_path
        return JSONResponse({"artifacts": results, "run_workspace": ws})
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
