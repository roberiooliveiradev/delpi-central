import logging

import requests

from app.domain.ports.vision_llm_gateway_port import VisionLlmGatewayPort
from app.infrastructure.config.vision_llm_config import resolve_vision_llm_config


logger = logging.getLogger("minha-delpi-ai-api.vision.ollama")


class OllamaVisionLlmGateway(VisionLlmGatewayPort):
    def __init__(self):
        config = resolve_vision_llm_config()
        self.base_url = config.base_url.rstrip("/")
        self.model = config.model
        self.timeout = config.timeout_seconds

    def provider_name(self) -> str:
        return "ollama"

    def describe(
        self,
        *,
        prompt: str,
        images_b64: list[str],
        max_tokens: int,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": images_b64,
                }
            ],
            "stream": False,
            "options": {"num_predict": max(1, int(max_tokens))},
        }

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        message = data.get("message") if isinstance(data, dict) else {}
        return str((message or {}).get("content") or "").strip()
