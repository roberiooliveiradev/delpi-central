"""Classificação de erros e vazios — Playbook 06."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService

from app.application.services.chat_follow_up_suggestion_service import (
    ChatFollowUpSuggestionService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@lru_cache(maxsize=1)
def _error_handling_content() -> dict[str, Any]:
    return ContentService.load_json("assistant/error_handling")


@dataclass(frozen=True)
class ChatErrorHandlingClassification:
    error_type: str
    severity: str
    recoverable: bool
    user_message: str
    action: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    attempted: str | None = None
    record_count: int | None = None
    api_failed: bool = False
    affirms_non_existence: bool = False


class ChatErrorHandlingClassifier:
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
        attachment_type = cls._classify_attachments(attachments)

        if attachment_type:
            return cls._stub_classification(attachment_type)

        from app.application.services.chat_canvas_ambiguity_service import (
            ChatCanvasAmbiguityService,
        )

        if ChatCanvasAmbiguityService.is_deictic_canvas_request(message):
            clarification = ChatCanvasAmbiguityService.build_clarification_answer(
                previous_messages=(workspace_context or {}).get("previousMessages"),
            )

            if clarification:
                return cls._stub_classification("context_missing")

        missing_answer = ChatOperationalParameterService.resolve_missing_product_code_answer(
            message,
            previous_messages=(workspace_context or {}).get("previousMessages"),
        )

        if missing_answer and str(answer or "").strip() == str(missing_answer).strip():
            return cls._stub_classification(
                "missing_parameter",
                attempted="product_code_required",
            )

        tool_summary = cls._summarize_tool_calls(tool_calls)

        if tool_summary.get("permission_denied"):
            return cls._stub_classification(
                "permission_denied",
                action=tool_summary.get("action"),
                params=tool_summary.get("params") or {},
                attempted=tool_summary.get("attempted"),
                api_failed=True,
            )

        if tool_summary.get("timeout"):
            return cls._stub_classification(
                "timeout",
                action=tool_summary.get("action"),
                params=tool_summary.get("params") or {},
                attempted=tool_summary.get("attempted"),
                api_failed=True,
            )

        if tool_summary.get("sql_syntax_error"):
            return cls._stub_classification(
                "sql_syntax_error",
                action=tool_summary.get("action"),
                params=tool_summary.get("params") or {},
                attempted=tool_summary.get("attempted"),
                api_failed=False,
            )

        if tool_summary.get("api_unavailable"):
            return cls._stub_classification(
                "api_unavailable",
                action=tool_summary.get("action"),
                params=tool_summary.get("params") or {},
                attempted=tool_summary.get("attempted"),
                api_failed=True,
            )

        if tool_summary.get("partial"):
            return cls._stub_classification(
                "partial_result",
                action=tool_summary.get("action"),
                params=tool_summary.get("params") or {},
                attempted=tool_summary.get("attempted"),
                record_count=tool_summary.get("record_count"),
            )

        inventory_empty_type = cls._resolve_empty_result_type(message, tool_calls)

        if (
            inventory_empty_type == "empty_inventory_minimum"
            and tool_summary.get("success_count")
            and cls._tool_calls_have_empty_records(tool_calls)
        ):
            return cls._stub_classification(
                inventory_empty_type,
                action=tool_summary.get("action"),
                params=tool_summary.get("params") or {},
                attempted=tool_summary.get("attempted"),
                record_count=0,
                affirms_non_existence=True,
            )

        if issues:
            return cls._stub_classification(
                "tool_error",
                attempted="; ".join(str(item) for item in issues[:3]),
            )

        signals = [str(item).strip() for item in (trust_signals or []) if str(item).strip()]

        if "no_source" in signals and cls._looks_like_rag_turn(workspace_context, answer):
            return cls._stub_classification("rag_no_source")

        if "api_unavailable" in signals:
            return cls._stub_classification("api_unavailable", api_failed=True)

        outcome = ChatFollowUpSuggestionService.classify_outcome(
            answer=answer,
            tool_calls=tool_calls or [],
            issues=issues,
        )

        if outcome == "empty":
            empty_type = cls._resolve_empty_result_type(message, tool_calls)

            return cls._stub_classification(
                empty_type,
                action=tool_summary.get("action"),
                params=tool_summary.get("params") or {},
                attempted=tool_summary.get("attempted"),
                record_count=0,
                affirms_non_existence=empty_type == "empty_inventory_minimum",
            )

        if outcome == "error":
            if cls._looks_invalid_parameter(answer):
                return cls._stub_classification("invalid_parameter")

            return cls._stub_classification(
                "tool_error",
                api_failed=tool_summary.get("had_failure", False),
            )

        if outcome == "warning" and tool_summary.get("had_failure"):
            return cls._stub_classification("partial_result")

        if cls._is_cold_answer(answer):
            return cls._stub_classification("empty_result")

        return None

    @classmethod
    def _resolve_empty_result_type(cls, message: str, tool_calls: list | None) -> str:
        from app.domain.services.chat_sql_inventory_query_service import (
            ChatSqlInventoryQueryService,
        )
        from app.domain.services.external_actions.external_action_sql_capability_service import (
            ExternalActionSqlCapabilityService,
        )

        if ChatSqlInventoryQueryService.resolve(message):
            return "empty_inventory_minimum"

        for call in tool_calls or []:
            if not isinstance(call, dict):
                continue

            if str(call.get("name") or "") != "execute_external_action":
                continue

            metadata = call.get("metadata")

            if isinstance(metadata, dict):
                executed_sql = metadata.get("executedSql")

                if ExternalActionSqlCapabilityService.looks_like_inventory_below_minimum_sql(
                    executed_sql
                ):
                    return "empty_inventory_minimum"

            arguments = call.get("arguments")

            if not isinstance(arguments, dict):
                continue

            body = arguments.get("body")

            if not isinstance(body, dict):
                continue

            for key in ("sql", "query", "statement"):
                if ExternalActionSqlCapabilityService.looks_like_inventory_below_minimum_sql(
                    body.get(key)
                ):
                    return "empty_inventory_minimum"

        return "empty_result"

    @classmethod
    def _tool_calls_have_empty_records(cls, tool_calls: list | None) -> bool:
        for call in tool_calls or []:
            if not isinstance(call, dict):
                continue

            if str(call.get("name") or "") != "execute_external_action":
                continue

            metadata = call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            humanized = metadata.get("humanizedSummary")

            if isinstance(humanized, dict):
                linhas = [
                    str(line).strip()
                    for line in (humanized.get("linhas") or [])
                    if str(line).strip()
                ]

                empty_phrases = (
                    "nenhum registro",
                    "nenhum produto",
                    "não retornou registros",
                    "nao retornou registros",
                    "não encontrei",
                    "nao encontrei",
                )

                if linhas and any(
                    phrase in line.lower()
                    for line in linhas
                    for phrase in empty_phrases
                ):
                    return True

            preview = str(metadata.get("responsePreview") or "")

            if '"total": 0' in preview or '"rows": 0' in preview:
                return True

        return False

    @classmethod
    def _stub_classification(
        cls,
        error_type: str,
        *,
        action: str | None = None,
        params: dict | None = None,
        attempted: str | None = None,
        record_count: int | None = None,
        api_failed: bool = False,
        affirms_non_existence: bool = False,
    ) -> ChatErrorHandlingClassification:
        config = (_error_handling_content().get("types") or {}).get(error_type) or {}
        severity = str(config.get("severity") or "warning")

        return ChatErrorHandlingClassification(
            error_type=error_type,
            severity=severity,
            recoverable=bool(config.get("recoverable", True)),
            user_message=str(config.get("userMessage") or "").strip(),
            action=action,
            params=params or {},
            attempted=attempted,
            record_count=record_count,
            api_failed=api_failed,
            affirms_non_existence=affirms_non_existence,
        )

    @classmethod
    def _looks_like_sql_syntax_error(cls, error_text: str, metadata: dict) -> bool:
        path = str(metadata.get("path") or "").lower()
        action_id = str(metadata.get("actionId") or metadata.get("action_id") or "").lower()

        if "/data/sql" not in path and "sql" not in action_id:
            return False

        lowered = str(error_text or "").lower()

        return any(
            token in lowered
            for token in (
                "incorrect syntax",
                "syntax near",
                "syntax error",
                "42000",
                "sintaxe incorreta",
                "erro de sintaxe",
            )
        )

    @classmethod
    def _summarize_tool_calls(cls, tool_calls: list | None) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "had_failure": False,
            "partial": False,
            "success_count": 0,
            "failure_count": 0,
            "empty_count": 0,
        }

        for call in tool_calls or []:
            if not isinstance(call, dict):
                continue

            if str(call.get("name") or "") != "execute_external_action":
                continue

            metadata = call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            action_id = str(metadata.get("actionId") or metadata.get("action_id") or "")
            path = str(metadata.get("path") or "")
            summary["action"] = action_id or path
            summary["attempted"] = path or action_id

            args = call.get("arguments")

            if isinstance(args, dict):
                parameters = args.get("parameters")

                if isinstance(parameters, dict):
                    code = parameters.get("code")

                    if code not in (None, ""):
                        summary["params"] = {
                            "productCode": ChatProductQueryIntentService.normalize_product_code(
                                str(code),
                            )
                        }

            try:
                status_code = int(metadata.get("statusCode") or 0)
            except (TypeError, ValueError):
                status_code = 0

            error_text = str(
                metadata.get("error")
                or metadata.get("errorMessage")
                or metadata.get("detail")
                or "",
            ).lower()

            if not metadata.get("ok"):
                summary["had_failure"] = True
                summary["failure_count"] += 1

                if status_code in (401, 403):
                    summary["permission_denied"] = True

                if cls._looks_like_sql_syntax_error(error_text, metadata):
                    summary["sql_syntax_error"] = True
                elif status_code >= 500 or "unavailable" in error_text:
                    summary["api_unavailable"] = True

                if "timeout" in error_text or status_code == 408:
                    summary["timeout"] = True

                continue

            summary["success_count"] += 1

            humanized = metadata.get("humanizedSummary")

            if isinstance(humanized, dict):
                linhas = humanized.get("linhas") or []

                if isinstance(linhas, list) and not [
                    line for line in linhas if str(line).strip()
                ]:
                    summary["empty_count"] += 1

        if summary["failure_count"] and summary["success_count"]:
            summary["partial"] = True

        if summary["failure_count"] and not summary["success_count"]:
            if summary.get("permission_denied"):
                return summary

            if summary.get("timeout"):
                return summary

            if summary.get("sql_syntax_error"):
                return summary

            summary["api_unavailable"] = summary.get("api_unavailable", True)

        if summary["empty_count"] and summary["success_count"] and summary["failure_count"]:
            summary["partial"] = True

        return summary

    @classmethod
    def _classify_attachments(cls, attachments: list[dict] | None) -> str | None:
        items = attachments if isinstance(attachments, list) else []

        if not items:
            return None

        if all(str(item.get("status") or "") == "index_failed" for item in items if isinstance(item, dict)):
            return "file_unreadable"

        if any(str(item.get("status") or "") == "unsupported" for item in items if isinstance(item, dict)):
            return "unsupported_file"

        return None

    @classmethod
    def _looks_like_rag_turn(cls, workspace_context: dict | None, answer: str) -> bool:
        stages = (workspace_context or {}).get("pipelineStages") or []

        if isinstance(stages, list) and any("rag" in str(stage).lower() for stage in stages):
            return True

        lowered = str(answer or "").lower()

        return "documentação" in lowered or "norma" in lowered or "manual" in lowered

    @classmethod
    def _looks_invalid_parameter(cls, answer: str) -> bool:
        lowered = ChatMessageNormalizationService.normalize_for_matching(answer)

        return any(
            token in lowered
            for token in (
                "invalido",
                "inválid",
                "formato esperado",
                "valor informado",
                "data informada",
            )
        )

    @classmethod
    def _is_cold_answer(cls, answer: str) -> bool:
        stripped = str(answer or "").strip().lower()

        if len(stripped) > 120:
            return False

        patterns = _error_handling_content().get("coldAnswerPatterns") or []

        return stripped in patterns or any(stripped == pattern for pattern in patterns)

    @classmethod
    def _affirms_non_existence(cls, answer: str, *, api_failed: bool) -> bool:
        if api_failed:
            return False

        lowered = str(answer or "").lower()

        phrases = _error_handling_content().get("apiFailureNonExistencePhrases") or []

        return any(phrase in lowered for phrase in phrases)
