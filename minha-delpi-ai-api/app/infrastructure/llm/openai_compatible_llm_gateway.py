import json
import logging
from collections.abc import Iterator

import requests

from app.domain.entities.llm_generation_result import LlmGenerationResult, LlmToolCall
from app.domain.exceptions.llm_exceptions import LlmProviderUnavailableError
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.llm_tool_argument_parser import parse_llm_tool_arguments
from app.infrastructure.config.llm_text_config import resolve_llm_text_config
from app.infrastructure.llm.llm_request_context import get_active_config


logger = logging.getLogger("minha-delpi-ai-api.openai-compatible-llm")


class OpenAiCompatibleLlmGateway(LlmGatewayPort):
    def __init__(self):
        config = resolve_llm_text_config()
        self.base_url = config.base_url.rstrip("/")
        self.model = config.model
        self.api_key = config.api_key
        self.timeout = config.timeout_seconds

    def _active(self):
        return get_active_config()

    def _resolve_model(self) -> str:
        return self._active().model

    def supports_native_tools(self) -> bool:
        return True

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> LlmGenerationResult:
        active = self._active()
        payload = {
            "model": self._resolve_model(),
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": active.temperature,
            "max_tokens": active.max_tokens,
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
            logger.exception("openai_compatible_tools_request_failed")
            raise LlmProviderUnavailableError(
                "OpenAI-compatible tools request failed"
            ) from exc
        except ValueError as exc:
            logger.exception("openai_compatible_tools_invalid_json")
            raise LlmProviderUnavailableError(
                "Invalid OpenAI-compatible tools response"
            ) from exc

        choices = data.get("choices") or []

        if not choices:
            raise LlmProviderUnavailableError("Empty OpenAI-compatible tools response")

        message = choices[0].get("message") or {}
        content = str(message.get("content") or "").strip()
        tool_calls: list[LlmToolCall] = []

        for item in message.get("tool_calls") or []:
            function = item.get("function") or {}
            name = str(function.get("name") or "").strip()

            if not name:
                continue

            tool_calls.append(
                LlmToolCall(
                    id=str(item.get("id") or name),
                    name=name,
                    arguments=parse_llm_tool_arguments(function.get("arguments")),
                )
            )

        return LlmGenerationResult(content=content, tool_calls=tool_calls)

    def generate(self, messages: list[dict]) -> str:
        active = self._active()
        payload = {
            "model": self._resolve_model(),
            "messages": messages,
            "temperature": active.temperature,
            "max_tokens": active.max_tokens,
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
            logger.exception("openai_compatible_request_failed")
            raise LlmProviderUnavailableError(
                "OpenAI-compatible request failed"
            ) from exc
        except ValueError as exc:
            logger.exception("openai_compatible_invalid_json")
            raise LlmProviderUnavailableError(
                "Invalid OpenAI-compatible response"
            ) from exc

        choices = data.get("choices") or []

        if not choices:
            raise LlmProviderUnavailableError("Empty OpenAI-compatible response")

        content = (choices[0].get("message") or {}).get("content")

        if not content:
            raise LlmProviderUnavailableError("Empty OpenAI-compatible message")

        return str(content).strip()

    def stream(self, messages: list[dict]) -> Iterator[str]:
        active = self._active()
        payload = {
            "model": self._resolve_model(),
            "messages": messages,
            "temperature": active.temperature,
            "max_tokens": active.max_tokens,
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
                        logger.warning("openai_compatible_invalid_stream_line")
                        continue

                    choices = data.get("choices") or []

                    if not choices:
                        continue

                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")

                    if content:
                        yield str(content)

        except requests.RequestException as exc:
            logger.exception("openai_compatible_stream_failed")
            raise LlmProviderUnavailableError(
                "OpenAI-compatible stream failed"
            ) from exc

    def _headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers
