import logging

import requests

from app.domain.ports.vision_llm_gateway_port import VisionLlmGatewayPort
from app.infrastructure.config.vision_llm_config import resolve_vision_llm_config


logger = logging.getLogger("minha-delpi-ai-api.vision.openai-compatible")


class OpenAiCompatibleVisionLlmGateway(VisionLlmGatewayPort):
    def __init__(self):
        config = resolve_vision_llm_config()
        self.base_url = config.base_url.rstrip("/")
        self.model = config.model
        self.api_key = config.api_key
        self.timeout = config.timeout_seconds

    def provider_name(self) -> str:
        return "openai_compatible"

    def describe(
        self,
        *,
        prompt: str,
        images_b64: list[str],
        max_tokens: int,
    ) -> str:
        content: list[dict] = [{"type": "text", "text": prompt}]

        for image_b64 in images_b64:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_b64}",
                    },
                }
            )

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max(1, int(max_tokens)),
            "stream": False,
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []

        if not choices:
            return ""

        return str((choices[0].get("message") or {}).get("content") or "").strip()

    def _headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers
