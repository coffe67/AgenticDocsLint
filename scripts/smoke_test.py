#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys

# Ensure local package is importable without installation
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from slideforge.cli import write_samples
from slideforge.config import load_config
from slideforge.pipeline.orchestrator import run_pipeline


def main() -> int:
    examples_dir = "examples"
    write_samples(examples_dir)

    # Default strict config should FAIL given sample deck (section avg < 0.6)
    cfg_default = load_config("config/default.yaml")
    out_default = "build"
    outputs_default = run_pipeline(
        os.path.join(examples_dir, "deck_sample.json"), cfg_default, out_default, auto_fix=True
    )
    with open(outputs_default["report_json"], "r", encoding="utf-8") as f:
        report_default = json.load(f)
    status_default = report_default["overall"]["status"]

    # Relaxed config should be NEEDS_UPDATE (not FAIL)
    cfg_relaxed = load_config("config/strict_relaxed.yaml")
    out_relaxed = "build_relaxed"
    outputs_relaxed = run_pipeline(
        os.path.join(examples_dir, "deck_sample.json"), cfg_relaxed, out_relaxed, auto_fix=True
    )
    with open(outputs_relaxed["report_json"], "r", encoding="utf-8") as f:
        report_relaxed = json.load(f)
    status_relaxed = report_relaxed["overall"]["status"]

    print(f"Default config status: {status_default}")
    print(f"Relaxed config status: {status_relaxed}")

    # Basic assertions
    if status_default != "FAIL":
        print("ERROR: Expected FAIL with default config", file=sys.stderr)
        return 1
    if status_relaxed != "NEEDS_UPDATE":
        print("ERROR: Expected NEEDS_UPDATE with relaxed config", file=sys.stderr)
        return 2

    # Check key outputs exist
    for key in ("report_json", "report_txt", "updated_deck_json", "updated_deck_md"):
        if not os.path.exists(outputs_default.get(key, "")):
            print(f"ERROR: Missing output: {key} in default run", file=sys.stderr)
            return 3
        if not os.path.exists(outputs_relaxed.get(key, "")):
            print(f"ERROR: Missing output: {key} in relaxed run", file=sys.stderr)
            return 4

    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
