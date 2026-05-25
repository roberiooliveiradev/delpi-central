import logging
import threading

import requests

from app.infrastructure.config.settings import Settings

logger = logging.getLogger("minha-delpi-ai-api.ollama-warmup")


def warmup_ollama():
    """Envia uma requisição mínima ao Ollama para forçar o carregamento do modelo em RAM."""
    if not Settings.OLLAMA_WARMUP_ON_STARTUP:
        return

    threading.Thread(target=_do_warmup, daemon=True).start()


def _do_warmup():
    base_url = Settings.OLLAMA_BASE_URL.rstrip("/")
    model = Settings.OLLAMA_MODEL

    logger.info("ollama_warmup_start model=%s", model)

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
        logger.info("ollama_warmup_done model=%s status=%d", model, response.status_code)
    except requests.RequestException as exc:
        logger.warning("ollama_warmup_failed model=%s error=%s", model, exc)
