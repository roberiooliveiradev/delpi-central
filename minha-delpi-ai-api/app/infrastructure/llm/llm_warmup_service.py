import logging
import threading

import os

import requests

from app.infrastructure.config.llm_text_config import (
    is_openai_compatible_provider,
    normalize_llm_provider,
    resolve_llm_provider_name,
    resolve_llm_text_config,
)


logger = logging.getLogger("minha-delpi-ai-api.llm-warmup")


def warmup_llm_on_startup() -> None:
    warmup_enabled = os.getenv(
        "LLM_WARMUP_ON_STARTUP",
        os.getenv("OLLAMA_WARMUP_ON_STARTUP", "true"),
    ).lower() == "true"

    if not warmup_enabled:
        return

    provider = resolve_llm_provider_name()

    if provider != "ollama":
        logger.info("llm_warmup_skip provider=%s", provider)
        return

    threading.Thread(target=_warmup_ollama, daemon=True).start()


def _warmup_ollama() -> None:
    config = resolve_llm_text_config()
    base_url = config.base_url
    model = config.model

    logger.info("llm_warmup_start provider=ollama model=%s", model)

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "oi"}],
                "stream": False,
                "options": {"num_predict": 1, "num_ctx": 64},
            },
            timeout=120,
        )
        response.raise_for_status()
        logger.info(
            "llm_warmup_done provider=ollama model=%s status=%d",
            model,
            response.status_code,
        )
    except requests.RequestException as exc:
        logger.warning("llm_warmup_failed provider=ollama model=%s error=%s", model, exc)


def should_skip_warmup_for_provider(provider: str) -> bool:
    return is_openai_compatible_provider(provider)
