import json
import logging
from collections.abc import Iterator

import requests

from app.domain.entities.llm_generation_result import LlmGenerationResult, LlmToolCall
from app.domain.exceptions.llm_exceptions import LlmProviderUnavailableError
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.llm_tool_argument_parser import parse_llm_tool_arguments
from app.infrastructure.config.settings import Settings


logger = logging.getLogger("minha-delpi-ai-api.ollama")


class OllamaLlmGateway(LlmGatewayPort):
    def __init__(self):
        self.base_url = Settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = Settings.OLLAMA_MODEL
        self.timeout = Settings.OLLAMA_TIMEOUT_SECONDS

    def supports_native_tools(self) -> bool:
        return True

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> LlmGenerationResult:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "options": {
                "temperature": Settings.LLM_TEMPERATURE,
                "num_predict": Settings.LLM_MAX_TOKENS,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            logger.exception("ollama_tools_request_failed")
            raise LlmProviderUnavailableError("Ollama tools request failed") from exc
        except ValueError as exc:
            logger.exception("ollama_tools_invalid_json")
            raise LlmProviderUnavailableError("Invalid Ollama tools response") from exc

        message = data.get("message") or {}
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
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": Settings.LLM_TEMPERATURE,
                "num_predict": Settings.LLM_MAX_TOKENS,
            },
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

    def stream(self, messages: list[dict]) -> Iterator[str]:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": Settings.LLM_TEMPERATURE,
                "num_predict": Settings.LLM_MAX_TOKENS,
            },
        }

        try:
            with requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                stream=True,
            ) as response:
                response.raise_for_status()

                for raw_line in response.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue

                    try:
                        data = json.loads(raw_line)
                    except json.JSONDecodeError:
                        logger.warning("ollama_invalid_stream_line")
                        continue

                    if data.get("done"):
                        break

                    content = (data.get("message") or {}).get("content")

                    if content:
                        yield str(content)

        except requests.RequestException as exc:
            logger.exception("ollama_stream_failed")
            raise LlmProviderUnavailableError("Ollama stream failed") from exc
