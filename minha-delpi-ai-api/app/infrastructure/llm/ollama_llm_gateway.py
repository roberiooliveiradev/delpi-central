import logging

import requests

from app.domain.exceptions.llm_exceptions import LlmProviderUnavailableError
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.infrastructure.config.settings import Settings


logger = logging.getLogger("minha-delpi-ai-api.ollama")


class OllamaLlmGateway(LlmGatewayPort):
    def __init__(self):
        self.base_url = Settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = Settings.OLLAMA_MODEL
        self.timeout = Settings.OLLAMA_TIMEOUT_SECONDS

    def generate(self, messages: list[dict]) -> str:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            logger.exception("ollama_request_failed")
            raise LlmProviderUnavailableError("Ollama request failed") from exc
        except ValueError as exc:
            logger.exception("ollama_invalid_json")
            raise LlmProviderUnavailableError("Invalid Ollama response") from exc

        content = (data.get("message") or {}).get("content")

        if not content:
            raise LlmProviderUnavailableError("Empty Ollama response")

        return str(content).strip()
