# LLM Integration Draft

This project is agentic-ready. You can enable LLM-driven section tagging (and later generation) with minimal changes.

Enable LLM Tagger
-----------------

1) Configure provider (OpenAI example) in `config/default.yaml` or your config:

```
tagger:
  mode: llm   # switch from heuristic → llm
llm:
  provider: openai
  model: gpt-4o-mini
  # api_key: ""  # optional; otherwise set env var OPENAI_API_KEY or LLM_API_KEY
  timeout_s: 30
  max_tokens: 256
```

2) Set your API key:

```
export OPENAI_API_KEY=sk-...
# or
export LLM_API_KEY=sk-...
```

3) Run as usual (CLI/API/FE). The tagger uses the LLM to assign `slide.section` and `slide.section_confidence`. If the provider is not configured or fails, it safely falls back to the heuristic tagger.

What it does
------------

- For each slide, it prompts the LLM with title + bullets + notes and the allowed section names from `section_rules`.
- The LLM must return JSON `{ "section": string, "confidence": number }`.
- Guardrails: if the section is not in the allowed list, the system falls back to the heuristic inference.

Provider notes
--------------

- OpenAI SDK is optional; install with `pip install openai` (or add a Makefile target).
- If you want Azure/OpenRouter/other, add a provider branch in `slideforge/llm.py` and wire its env/config.

Observability & cost
--------------------

- Prompt/response logging: enable via `llm.enable_logs: true`. Logs are written to `build/llm_logs/` by default (override with `llm.log_dir`).
- Caching: enable via `llm.enable_cache: true` (default). Cache files are stored in `build/llm_cache/` (override with `llm.cache_dir`).
- Both can also be controlled by env vars `LLM_LOG_DIR` / `LLM_CACHE_DIR`.
- Keep redaction in mind if your content contains PII.

Next: LLM Generator (optional)
------------------------------

- Swap the heuristic placeholder generator with an LLM that produces a few concise bullets covering missing keywords.
- Similar guardrails apply (JSON responses, length/style constraints).
