from __future__ import annotations

OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_MODELS = {
    "analyst": "qwen2.5-coder:32b",
    "judge": "deepseek-r1:32b",
    "russian_revisor": "akdengi/saiga-llama3-8b:latest",
    "rewrite": "akdengi/saiga-llama3-8b:latest",
}
OLLAMA_FALLBACK_MODELS = {
    "analyst": "qwen3-coder:30b",
    "judge": "mistral-small:latest",
    "russian_revisor": "qwen2.5-coder:32b",
    "rewrite": "qwen2.5-coder:32b",
}
OLLAMA_FAST_FALLBACK_MODEL = "mistral-small:latest"
OLLAMA_ROUTING_NOTE = "default_memo_pipeline_analyst_judge_russian_revisor_from_config_ollama_memo_routing"


def model_for_role(role: str) -> str:
    return OLLAMA_MODELS.get(role, OLLAMA_FAST_FALLBACK_MODEL)


def fallback_model_for_role(role: str) -> str:
    return OLLAMA_FALLBACK_MODELS.get(role, OLLAMA_FAST_FALLBACK_MODEL)
