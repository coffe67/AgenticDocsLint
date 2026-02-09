from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional
import hashlib
from datetime import datetime
from pathlib import Path


class LLMNotConfigured(Exception):
    pass


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    timeout_s: int = 30
    max_tokens: int = 512
    enable_cache: bool = True
    enable_logs: bool = False
    cache_dir: Optional[str] = None
    log_dir: Optional[str] = None


def load_llm_config(config: Dict[str, Any]) -> Optional[LLMConfig]:
    llm_cfg = (config.get("llm") or {}) if isinstance(config, dict) else {}
    provider = llm_cfg.get("provider") or os.getenv("LLM_PROVIDER")
    model = llm_cfg.get("model") or os.getenv("LLM_MODEL")
    api_key = llm_cfg.get("api_key") or os.getenv("LLM_API_KEY")
    timeout_s = int(llm_cfg.get("timeout_s", os.getenv("LLM_TIMEOUT_S", 30)))
    max_tokens = int(llm_cfg.get("max_tokens", os.getenv("LLM_MAX_TOKENS", 512)))
    if not provider or not model:
        return None
    enable_cache = bool(llm_cfg.get("enable_cache", True))
    enable_logs = bool(llm_cfg.get("enable_logs", llm_cfg.get("debug", False)))
    cache_dir = llm_cfg.get("cache_dir") or os.getenv("LLM_CACHE_DIR")
    log_dir = llm_cfg.get("log_dir") or os.getenv("LLM_LOG_DIR")
    return LLMConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        timeout_s=timeout_s,
        max_tokens=max_tokens,
        enable_cache=enable_cache,
        enable_logs=enable_logs,
        cache_dir=cache_dir,
        log_dir=log_dir,
    )


class LLMClient:
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg

    def call_json(self, prompt: str, system: Optional[str] = None, cache_key: Optional[str] = None, log_label: Optional[str] = None) -> Dict[str, Any]:
        """Call an LLM and expect a JSON object response. Supports 'openai' provider.
        Raises LLMNotConfigured if provider is not available.
        """
        cache_path: Optional[Path] = None
        if self.cfg.enable_cache:
            cdir = Path(self.cfg.cache_dir or (Path.cwd() / "build" / "llm_cache"))
            cdir.mkdir(parents=True, exist_ok=True)
            ck = cache_key or self._default_cache_key(prompt, system)
            cache_path = cdir / f"{ck}.json"
            if cache_path.exists():
                try:
                    return json.loads(cache_path.read_text(encoding="utf-8"))
                except Exception:
                    pass

        provider = (self.cfg.provider or "").lower()
        if provider == "openai":
            data = self._call_openai_json(prompt, system)
        else:
            raise LLMNotConfigured(f"Unsupported LLM provider: {self.cfg.provider}")

        if cache_path:
            try:
                cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass

        if self.cfg.enable_logs:
            ldir = Path(self.cfg.log_dir or (Path.cwd() / "build" / "llm_logs"))
            ldir.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            tag = log_label or (cache_key or self._short_hash(prompt))
            try:
                (ldir / f"{ts}_{tag}_prompt.txt").write_text(
                    (f"[SYSTEM]\n{system}\n\n" if system else "") + f"[USER]\n{prompt}\n",
                    encoding="utf-8",
                )
                (ldir / f"{ts}_{tag}_response.json").write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass

        return data

    def _call_openai_json(self, prompt: str, system: Optional[str]) -> Dict[str, Any]:
        try:
            # New OpenAI SDK (python>=1.0)
            from openai import OpenAI  # type: ignore
        except Exception as e:
            raise LLMNotConfigured("openai SDK not installed. Try: pip install openai") from e
        if not (self.cfg.api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")):
            raise LLMNotConfigured("OpenAI API key not provided (set OPENAI_API_KEY or llm.api_key)")
        client = OpenAI()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = client.chat.completions.create(
                model=self.cfg.model,
                messages=messages,
                temperature=0,
                max_tokens=self.cfg.max_tokens,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content  # type: ignore[attr-defined]
            return json.loads(content or "{}")
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")

    def _default_cache_key(self, prompt: str, system: Optional[str]) -> str:
        raw = f"{self.cfg.provider}|{self.cfg.model}|{system or ''}|{prompt}"
        return self._short_hash(raw)

    @staticmethod
    def _short_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
