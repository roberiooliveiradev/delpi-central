import json
import logging
from collections.abc import Iterator

import requests

from app.domain.entities.llm_generation_result import LlmGenerationResult, LlmToolCall
from app.domain.exceptions.llm_exceptions import LlmProviderUnavailableError
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.llm_tool_argument_parser import parse_llm_tool_arguments
from app.infrastructure.config.llm_text_config import resolve_llm_text_config
from app.infrastructure.llm.http_stream_utf8 import (
    force_response_utf8,
    iter_utf8_lines,
    repair_utf8_mojibake,
)
from app.infrastructure.llm.llm_request_context import get_active_config


logger = logging.getLogger("minha-delpi-ai-api.openai-compatible-llm")


def _prompt_cache_enabled() -> bool:
    from app.infrastructure.config.settings import Settings

    raw = str(getattr(Settings, "LLM_PROMPT_CACHE_ENABLED", "true") or "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def apply_prompt_prefix_cache(messages: list[dict]) -> list[dict]:
    """Marca o primeiro system estável com cache_control (OpenRouter/Anthropic-compatible).

    Mantém o prefixo de system como string estável no início do prompt para hit de cache
    entre turnos; não altera contrato de mensagens para o chamador.
    """
    if not _prompt_cache_enabled() or not messages:
        return messages

    prepared: list[dict] = []
    marked = False

    for message in messages:
        if not isinstance(message, dict):
            prepared.append(message)
            continue

        role = str(message.get("role") or "").strip().lower()
        content = message.get("content")

        if marked or role != "system" or not isinstance(content, str) or not content.strip():
            prepared.append(message)
            continue

        prepared.append(
            {
                **message,
                "content": [
                    {
                        "type": "text",
                        "text": content,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            }
        )
        marked = True

    return prepared


def _visible_assistant_text(message: dict, *, finish_reason: object = None) -> str:
    """Texto visível da mensagem OpenAI-compatible.

    Modelos reasoning (ex. Kimi K3 / OpenRouter) às vezes devolvem só ``reasoning``
    com ``content`` nulo — sem fallback o chat vira 503 ``llm.unavailable``.
    Se o ``reasoning`` parecer CoT/meta-instrução, não promove: usa safeFallback.
    """
    from app.domain.services.chat_llm_generation_context_service import (
        mark_reasoning_fallback,
    )
    from app.domain.services.chat_llm_synthesis_delivery_content_service import (
        ChatLlmSynthesisDeliveryContentService,
    )
    from app.domain.services.chat_llm_synthesis_leak_guard_service import (
        ChatLlmSynthesisLeakGuardService,
    )

    content = message.get("content")

    if content:
        text = str(content).strip()
        if text and ChatLlmSynthesisLeakGuardService.needs_fallback(answer=text):
            guarded = ChatLlmSynthesisLeakGuardService.guard_answer(
                answer=text,
                fallback=None,
            )
            if guarded and guarded != text:
                logger.warning("openai_compatible_content_looks_like_cot_using_guard")
                mark_reasoning_fallback(True)
                return guarded
            safe = ChatLlmSynthesisDeliveryContentService.safe_fallback_answer()
            logger.warning("openai_compatible_content_looks_like_cot_using_safe_fallback")
            mark_reasoning_fallback(True)
            return safe or ""
        return text

    reasoning = message.get("reasoning")

    if not reasoning:
        return ""

    text = str(reasoning).strip()
    mark_reasoning_fallback(True)
    logger.warning(
        "openai_compatible_empty_content_using_reasoning finish=%s",
        finish_reason,
    )

    if ChatLlmSynthesisLeakGuardService.needs_fallback(answer=text):
        safe = ChatLlmSynthesisDeliveryContentService.safe_fallback_answer()
        logger.warning(
            "openai_compatible_reasoning_looks_like_cot_using_safe_fallback"
        )
        return safe or ""

    return text


def _reasoning_delta_for_stream(reasoning: object) -> str | None:
    """Promove delta.reasoning só se não parecer CoT/instrução vazada."""
    from app.domain.services.chat_llm_generation_context_service import (
        mark_reasoning_fallback,
    )
    from app.domain.services.chat_llm_synthesis_leak_guard_service import (
        ChatLlmSynthesisLeakGuardService,
    )

    text = str(reasoning or "").strip()
    if not text:
        return None

    mark_reasoning_fallback(True)

    if ChatLlmSynthesisLeakGuardService.needs_fallback(answer=text):
        logger.warning("openai_compatible_stream_skip_reasoning_cot_delta")
        return None

    return text


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
            "messages": apply_prompt_prefix_cache(messages),
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
            force_response_utf8(response)
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
        content = repair_utf8_mojibake(str(message.get("content") or "").strip())
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
            "messages": apply_prompt_prefix_cache(messages),
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
            force_response_utf8(response)
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

        message = choices[0].get("message") or {}
        content = _visible_assistant_text(message, finish_reason=choices[0].get("finish_reason"))

        if not content:
            raise LlmProviderUnavailableError("Empty OpenAI-compatible message")

        return repair_utf8_mojibake(content)

    def stream(self, messages: list[dict]) -> Iterator[str]:
        active = self._active()
        payload = {
            "model": self._resolve_model(),
            "messages": apply_prompt_prefix_cache(messages),
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
                reasoning_parts: list[str] = []
                content_seen = False

                for line in iter_utf8_lines(response):
                    line = line.strip()

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
                        content_seen = True
                        yield repair_utf8_mojibake(str(content))
                        continue

                    # Não faz stream de reasoning: Kimi costuma emitir CoT sem espaços
                    # e vaza no UI. Acumula só como fallback se content vier vazio.
                    reasoning = delta.get("reasoning")
                    if reasoning:
                        reasoning_parts.append(str(reasoning))

                if not content_seen and reasoning_parts:
                    from app.domain.services.chat_llm_generation_context_service import (
                        mark_reasoning_fallback,
                    )
                    from app.domain.services.chat_llm_synthesis_delivery_content_service import (
                        ChatLlmSynthesisDeliveryContentService,
                    )
                    from app.domain.services.chat_llm_synthesis_leak_guard_service import (
                        ChatLlmSynthesisLeakGuardService,
                    )

                    mark_reasoning_fallback(True)
                    joined = repair_utf8_mojibake("".join(reasoning_parts)).strip()
                    if not joined:
                        return
                    if ChatLlmSynthesisLeakGuardService.needs_fallback(answer=joined):
                        safe = ChatLlmSynthesisDeliveryContentService.safe_fallback_answer()
                        logger.warning(
                            "openai_compatible_stream_reasoning_only_cot_using_safe_fallback"
                        )
                        if safe:
                            yield safe
                        return
                    yield joined

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
