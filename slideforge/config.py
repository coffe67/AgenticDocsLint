from __future__ import annotations

import json
import os
from typing import Any, Dict


def load_config(path: str | None) -> Dict[str, Any]:
    if path is None:
        # Load default packaged config
        default_path = os.path.join(os.path.dirname(__file__), "..", "config", "default.yaml")
        path = os.path.abspath(default_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config not found: {path}")
    if path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # Minimal YAML loader without external deps; supports subset used in default.yaml
    return _load_simple_yaml(path)


def _load_simple_yaml(path: str) -> Dict[str, Any]:
    # Warning: Very naive YAML reader for key: value, nested via indentation and lists with '-'.
    root: Dict[str, Any] = {}
    stack: list[tuple[int, Dict[str, Any] | list]] = [(0, root)]

    def current_container(indent: int):
        # Find the most recent container with indent less than current
        while stack and stack[-1][0] >= indent:
            stack.pop()
        return stack[-1][1] if stack else root

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            container = current_container(indent)
            stripped = line.strip()
            if stripped.startswith("-"):
                # list item
                item = stripped[1:].strip()
                value: Any
                if ":" in item and not item.endswith(":"):
                    # inline dict in list: key: value
                    key, val = [p.strip() for p in item.split(":", 1)]
                    value = {key: _coerce(val)}
                else:
                    value = _coerce(item)
                if isinstance(container, dict):
                    # find last dict key to append a list to
                    if not container:
                        raise ValueError("Malformed YAML: list under empty dict")
                    last_key = list(container.keys())[-1]
                    if not isinstance(container[last_key], list):
                        container[last_key] = []
                    container[last_key].append(value)
                elif isinstance(container, list):
                    container.append(value)
                continue
            if ":" in stripped:
                key, val = [p.strip() for p in stripped.split(":", 1)]
                if val == "":
                    # start of a nested mapping
                    new_map: Dict[str, Any] = {}
                    if isinstance(container, dict):
                        container[key] = new_map
                    else:
                        raise ValueError("Malformed YAML nesting")
                    stack.append((indent, new_map))
                else:
                    if isinstance(container, dict):
                        container[key] = _coerce(val)
                    else:
                        raise ValueError("Malformed YAML key under list")
            else:
                # bare value line (not expected in our default config)
                pass
    return root


def _coerce(val: str):
    # Handle bracketed inline lists: [a, b, c]
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        parts = [p.strip() for p in inner.split(",")]
        # strip optional quotes
        def strip_quotes(s: str) -> str:
            if (s.startswith("\"") and s.endswith("\"")) or (s.startswith("'") and s.endswith("'")):
                return s[1:-1]
            return s

        return [strip_quotes(p) for p in parts if p]

    # try bool, int, float, or keep as string
    low = val.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val
