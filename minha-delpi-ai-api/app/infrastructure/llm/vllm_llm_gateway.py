import json
import logging
from collections.abc import Iterator

import requests

from app.domain.exceptions.llm_exceptions import LlmProviderUnavailableError
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.infrastructure.config.settings import Settings


logger = logging.getLogger("minha-delpi-ai-api.vllm")


class VllmLlmGateway(LlmGatewayPort):
    def __init__(self):
        self.base_url = Settings.VLLM_BASE_URL.rstrip("/")
        self.model = Settings.VLLM_MODEL
        self.api_key = Settings.VLLM_API_KEY
        self.timeout = Settings.VLLM_TIMEOUT_SECONDS

    def generate(self, messages: list[dict]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": Settings.LLM_TEMPERATURE,
            "max_tokens": Settings.LLM_MAX_TOKENS,
            "stream": False,
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            logger.exception("vllm_request_failed")
            raise LlmProviderUnavailableError("vLLM request failed") from exc
        except ValueError as exc:
            logger.exception("vllm_invalid_json")
            raise LlmProviderUnavailableError("Invalid vLLM response") from exc

        choices = data.get("choices") or []

        if not choices:
            raise LlmProviderUnavailableError("Empty vLLM response")

        content = (choices[0].get("message") or {}).get("content")

        if not content:
            raise LlmProviderUnavailableError("Empty vLLM message")

        return str(content).strip()

    def stream(self, messages: list[dict]) -> Iterator[str]:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": Settings.LLM_TEMPERATURE,
            "max_tokens": Settings.LLM_MAX_TOKENS,
            "stream": True,
        }

        try:
            with requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
                stream=True,
            ) as response:
                response.raise_for_status()

                for raw_line in response.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue

                    line = raw_line.strip()

                    if not line.startswith("data:"):
                        continue

                    data_text = line.removeprefix("data:").strip()

                    if data_text == "[DONE]":
                        break

                    try:
                        data = json.loads(data_text)
                    except json.JSONDecodeError:
                        logger.warning("vllm_invalid_stream_line")
                        continue

                    choices = data.get("choices") or []

                    if not choices:
                        continue

                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")

                    if content:
                        yield str(content)

        except requests.RequestException as exc:
            logger.exception("vllm_stream_failed")
            raise LlmProviderUnavailableError("vLLM stream failed") from exc

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
