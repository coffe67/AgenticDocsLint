from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


class LLMNotConfigured(Exception):
    pass


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    timeout_s: int = 30
    max_tokens: int = 512


def load_llm_config(config: Dict[str, Any]) -> Optional[LLMConfig]:
    llm_cfg = (config.get("llm") or {}) if isinstance(config, dict) else {}
    provider = llm_cfg.get("provider") or os.getenv("LLM_PROVIDER")
    model = llm_cfg.get("model") or os.getenv("LLM_MODEL")
    api_key = llm_cfg.get("api_key") or os.getenv("LLM_API_KEY")
    timeout_s = int(llm_cfg.get("timeout_s", os.getenv("LLM_TIMEOUT_S", 30)))
    max_tokens = int(llm_cfg.get("max_tokens", os.getenv("LLM_MAX_TOKENS", 512)))
    if not provider or not model:
        return None
    return LLMConfig(provider=provider, model=model, api_key=api_key, timeout_s=timeout_s, max_tokens=max_tokens)


class LLMClient:
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg

    def call_json(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """Call an LLM and expect a JSON object response. Supports 'openai' provider.
        Raises LLMNotConfigured if provider is not available.
        """
        provider = (self.cfg.provider or "").lower()
        if provider == "openai":
            return self._call_openai_json(prompt, system)
        raise LLMNotConfigured(f"Unsupported LLM provider: {self.cfg.provider}")

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

