"""Erros e resultados vazios — Playbook 06 (chat base)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_error_handling_classifier import (
    ChatErrorHandlingClassification,
    ChatErrorHandlingClassifier,
)
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ContentService.load_json("assistant/error_handling")


class ChatErrorHandlingService:
    @classmethod
    def type_config(cls, error_type: str) -> dict[str, Any]:
        types = _content().get("types") or {}

        if not isinstance(types, dict):
            return {}

        config = types.get(error_type)

        return config if isinstance(config, dict) else {}

    @classmethod
    def cold_answer_patterns(cls) -> list[str]:
        return list(_content().get("coldAnswerPatterns") or [])

    @classmethod
    def non_existence_phrases(cls) -> list[str]:
        return list(_content().get("apiFailureNonExistencePhrases") or [])

    @classmethod
    def classify(
        cls,
        *,
        message: str,
        answer: str,
        tool_calls: list | None = None,
        issues: list[str] | None = None,
        workspace_context: dict | None = None,
        attachments: list[dict] | None = None,
        trust_signals: list[str] | None = None,
    ) -> ChatErrorHandlingClassification | None:
        return ChatErrorHandlingClassifier.classify(
            message=message,
            answer=answer,
            tool_calls=tool_calls,
            issues=issues,
            workspace_context=workspace_context,
            attachments=attachments,
            trust_signals=trust_signals,
        )

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str,
        answer: str,
        tool_calls: list | None = None,
        issues: list[str] | None = None,
        workspace_context: dict | None = None,
        attachments: list[dict] | None = None,
        latency_ms: int | None = None,
    ) -> None:
        trust_signals = metadata.get("trustSignals")

        if not isinstance(trust_signals, list):
            trust_signals = None

        classification = cls.classify(
            message=message,
            answer=answer,
            tool_calls=tool_calls,
            issues=issues,
            workspace_context=workspace_context,
            attachments=attachments,
            trust_signals=trust_signals,
        )

        if not classification:
            return

        config = cls.type_config(classification.error_type)
        structured_answer = cls.build_structured_answer(classification, config=config)
        suggestions = cls.build_recovery_suggestions(classification.error_type)

        metadata["errorHandling"] = cls.build_metadata_payload(
            classification,
            config=config,
            suggestions=suggestions,
            latency_ms=latency_ms,
        )

        if suggestions:
            metadata["errorRecoveryFollowUpSuggestions"] = suggestions

        if structured_answer and cls._should_enrich_answer(answer, classification):
            metadata["errorHandlingEnrichedAnswer"] = structured_answer

        admin_debug = metadata.get("adminDebug")

        if isinstance(admin_debug, dict):
            admin_debug["errorHandling"] = metadata["errorHandling"]

    @classmethod
    def build_metadata_payload(
        cls,
        classification: ChatErrorHandlingClassification,
        *,
        config: dict[str, Any],
        suggestions: list[dict[str, str]],
        latency_ms: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": classification.error_type,
            "severity": classification.severity,
            "recoverable": classification.recoverable,
            "title": str(config.get("title") or "").strip(),
            "userMessage": classification.user_message
            or str(config.get("userMessage") or "").strip(),
            "reasons": list(config.get("reasons") or []),
            "alternativesIntro": str(config.get("alternativesIntro") or "").strip(),
            "apiFailed": classification.api_failed,
            "affirmsNonExistence": classification.affirms_non_existence,
            "suggestions": [item["label"] for item in suggestions],
        }

        if classification.action:
            payload["action"] = classification.action

        if classification.params:
            payload["params"] = classification.params

        if classification.attempted:
            payload["attempted"] = classification.attempted

        if classification.record_count is not None:
            payload["records"] = classification.record_count

        if latency_ms is not None:
            payload["durationMs"] = latency_ms

        return payload

    @classmethod
    def build_structured_answer(
        cls,
        classification: ChatErrorHandlingClassification,
        *,
        config: dict[str, Any],
    ) -> str:
        title = str(config.get("title") or "").strip()
        intro = (
            classification.user_message or str(config.get("userMessage") or "").strip()
        )

        if not intro:
            return ""

        parts = [intro]

        if classification.attempted:
            parts.append("")
            parts.append(f"Tentei: {classification.attempted}")

        reasons = [str(item).strip() for item in (config.get("reasons") or []) if str(item).strip()]

        if reasons:
            parts.append("")
            parts.append("Possíveis motivos:")
            parts.extend(f"- {reason}" for reason in reasons)

        alt_intro = str(config.get("alternativesIntro") or "").strip()

        if alt_intro:
            parts.append("")
            parts.append(alt_intro)

        if classification.api_failed and classification.affirms_non_existence:
            parts.append("")
            parts.append(
                "_Obs.: como a consulta não foi concluída, não afirmo que o dado não existe — "
                "apenas que não foi possível confirmar agora._"
            )

        if title and title not in intro:
            return "\n".join(parts).strip()

        return "\n".join(parts).strip()

    @classmethod
    def build_recovery_suggestions(cls, error_type: str) -> list[dict[str, str]]:
        config = cls.type_config(error_type)
        labels = list(config.get("chips") or [])
        queries = _content().get("chipQueries") or {}
        suggestions: list[dict[str, str]] = []

        for label in labels[:6]:
            template = str(queries.get(label) or label).strip()

            if not template:
                continue

            suggestions.append({"label": str(label), "query": template})

        return suggestions

    @classmethod
    def _should_enrich_answer(
        cls,
        answer: str,
        classification: ChatErrorHandlingClassification,
    ) -> bool:
        if classification.api_failed and classification.affirms_non_existence:
            return True

        stripped = str(answer or "").strip().lower()

        if not stripped:
            return True

        if stripped in cls.cold_answer_patterns():
            return True

        if len(stripped) < 80 and classification.error_type in {
            "empty_result",
            "api_unavailable",
            "timeout",
            "permission_denied",
        }:
            return True

        return False
