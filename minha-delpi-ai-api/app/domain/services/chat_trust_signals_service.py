"""Sinais de confiança na resposta — Playbook 08 (metadata para UI)."""

from __future__ import annotations

from typing import Any

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ChatTrustSignalsService:
    @classmethod
    def build(
        cls,
        *,
        message: str,
        answer: str,
        tool_calls: list | None,
        sources: list | None,
        workspace_context: dict | None = None,
        direct_response: bool = False,
    ) -> list[dict[str, str]]:
        labels = ExternalActionResponseContentService.get_mapping(
            "security",
            "trustSignalLabels",
        )
        signals: list[dict[str, str]] = []
        seen: set[str] = set()

        def add(signal_id: str) -> None:
            if signal_id in seen:
                return

            label = str(labels.get(signal_id) or signal_id).strip()

            if not label:
                return

            seen.add(signal_id)
            signals.append({"id": signal_id, "label": label})

        workspace = workspace_context or {}
        text_task = bool(workspace.get("textTaskCategory"))

        if text_task or cls._answer_looks_like_draft(answer):
            add("draft")

        for source in sources or []:
            if isinstance(source, dict) and (source.get("documentId") or source.get("title")):
                add("document_source")
                break

        calls = [call for call in (tool_calls or []) if isinstance(call, dict)]

        if calls:
            any_ok = False
            any_permission = False
            any_failed = False

            for call in calls:
                if call.get("name") != "execute_external_action":
                    continue

                meta = call.get("metadata") or {}
                status = meta.get("statusCode") or meta.get("status_code")
                detail = str(meta.get("detail") or meta.get("error") or "").lower()

                if meta.get("ok"):
                    any_ok = True
                    continue

                any_failed = True

                if status in (401, 403) or detail in ("unauthorized", "forbidden"):
                    any_permission = True

            if any_ok:
                add("authorized_data")

            if any_permission:
                add("permission_limited")

            if any_failed and not any_ok:
                add("api_unavailable")

            if any(
                (call.get("metadata") or {}).get("blockReason") == "confirmation_required"
                for call in calls
                if call.get("name") == "execute_external_action"
            ):
                add("draft")

            if cls._looks_partial(calls):
                add("partial_result")

        elif not direct_response and cls._looks_operational_without_tools(message, workspace):
            if not sources:
                add("no_source")

        return signals

    @classmethod
    def _answer_looks_like_draft(cls, answer: str) -> bool:
        lowered = str(answer or "").lower()

        return any(
            term in lowered
            for term in (
                "rascunho",
                "revise antes",
                "validação",
                "validacao",
                "não é documento oficial",
                "nao e documento oficial",
            )
        )

    @classmethod
    def _looks_partial(cls, tool_calls: list[dict]) -> bool:
        for call in tool_calls:
            meta = call.get("metadata") or {}

            if meta.get("truncated") or meta.get("hasMore"):
                return True

            presentation = meta.get("presentation") or meta.get("humanizedSummary")

            if isinstance(presentation, dict):
                hint = str(presentation.get("truncatedHint") or "").strip()

                if hint:
                    return True

        answer_hints = ("resultado parcial", "próxima página", "mais linhas")

        return False

    @classmethod
    def _looks_operational_without_tools(
        cls,
        message: str,
        workspace: dict,
    ) -> bool:
        if workspace.get("textTaskCategory"):
            return False

        lowered = str(message or "").lower()

        return any(
            term in lowered
            for term in (
                "estoque",
                "produto",
                "fornecedor",
                "venda",
                "faturamento",
                "compra",
                "ov ",
                "pedido",
            )
        )
