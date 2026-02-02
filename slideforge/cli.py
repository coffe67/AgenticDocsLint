from __future__ import annotations

import argparse
import json
import os
from typing import Any

from slideforge import __version__
from slideforge.config import load_config
from slideforge.pipeline.orchestrator import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="slideforge",
        description="Extract structure from slides, evaluate them, and optionally generate missing content.",
    )
    parser.add_argument("--version", action="version", version=f"slideforge {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_p = subparsers.add_parser("run", help="Run end-to-end pipeline")
    run_p.add_argument("--input", required=True, help="Path to input deck (json/md/txt)")
    run_p.add_argument("--config", default=None, help="Path to config YAML/JSON; defaults to config/default.yaml")
    run_p.add_argument("--out", required=True, help="Output directory")
    run_p.add_argument("--auto-fix", action="store_true", help="Generate missing slides and updated deck")

    sample_p = subparsers.add_parser("sample", help="Write sample deck and config")
    sample_p.add_argument("--out", default="examples", help="Directory to write samples")

    args = parser.parse_args()

    if args.command == "run":
        cfg = load_config(args.config)
        outputs = run_pipeline(args.input, cfg, args.out, auto_fix=args.auto_fix)
        print("Pipeline complete. Outputs:")
        for k, v in outputs.items():
            print(f"- {k}: {v}")
        # Print decision summary for quick visibility
        try:
            rep_path = outputs.get("report_json")
            if rep_path and os.path.exists(rep_path):
                with open(rep_path, "r", encoding="utf-8") as f:
                    rep = json.load(f)
                overall = rep.get("overall", {})
                status = overall.get("status")
                update_required = overall.get("update_required")
                print(f"Decision: {status}; Update required: {update_required}")
                if overall.get("reasons"):
                    print("Why:")
                    for r in overall.get("reasons")[:5]:
                        print(f"- {r}")
        except Exception:
            pass
    elif args.command == "sample":
        write_samples(args.out)
        print(f"Samples written to {args.out}")


def write_samples(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    deck = {
        "meta": {"title": "Demo Deck", "author": "Example", "source": "deck_sample.json"},
        "slides": [
            {"index": 0, "title": "Introduction", "bullets": ["Project goals", "Motivation"], "notes": ""},
            {"index": 1, "title": "Methodology", "bullets": ["Data", "Model", "Training"], "notes": ""},
            {"index": 2, "title": "Results", "bullets": ["Accuracy", "Latency"], "notes": ""},
            {"index": 3, "title": "Conclusion", "bullets": ["Summary", "Next steps"], "notes": ""},
        ],
    }
    with open(os.path.join(out_dir, "deck_sample.json"), "w", encoding="utf-8") as f:
        json.dump(deck, f, indent=2)

    md = """# Introduction
- Project goals
- Motivation

---

# Methodology
- Data
- Model
- Training

---

# Results
- Accuracy
- Latency

---

# Conclusion
- Summary
- Next steps
"""
    with open(os.path.join(out_dir, "deck_sample.md"), "w", encoding="utf-8") as f:
        f.write(md)

    cfg_dir = os.path.join(os.path.dirname(__file__), "..", "config")
    cfg_src = os.path.abspath(os.path.join(cfg_dir, "default.yaml"))
    cfg_dst_dir = os.path.join(out_dir, "config")
    os.makedirs(cfg_dst_dir, exist_ok=True)
    with open(cfg_src, "r", encoding="utf-8") as fsrc, open(
        os.path.join(cfg_dst_dir, "default.yaml"), "w", encoding="utf-8"
    ) as fdst:
        fdst.write(fsrc.read())


if __name__ == "__main__":
    main()
