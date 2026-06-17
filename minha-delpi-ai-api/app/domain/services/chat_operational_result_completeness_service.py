"""Contrato de resultado incompleto — rotas operacionais (playbook_report).

Detecção e textos vivem aqui; consumidores (cobertura, dataAnswer, LLM) leem este
serviço — não presenters visuais (tabela/texto/markdown).
"""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "data_coverage"


class ChatOperationalResultCompletenessService:
    @classmethod
    def enrich_context(
        cls,
        root: dict[str, Any],
        *,
        response_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        enriched = dict(root)
        pagination = enriched.get("pagination")

        if not isinstance(pagination, dict) and isinstance(response_meta, dict):
            meta_pagination = response_meta.get("pagination")

            if isinstance(meta_pagination, dict):
                enriched["pagination"] = meta_pagination

        return enriched

    @classmethod
    def resolve_pagination(cls, root: dict[str, Any]) -> dict[str, Any] | None:
        pagination = root.get("pagination")

        if isinstance(pagination, dict):
            return pagination

        return None

    @classmethod
    def branch_filter_applied(cls, root: dict[str, Any]) -> bool | None:
        summary = root.get("summary")

        if isinstance(summary, dict) and "branch_filter_applied" in summary:
            return bool(summary.get("branch_filter_applied"))

        if isinstance(summary, dict):
            branch = summary.get("branch")

            if branch is not None:
                return bool(str(branch).strip())

        return None

    @classmethod
    def is_incomplete(
        cls,
        root: dict[str, Any],
        *,
        response_meta: dict[str, Any] | None = None,
    ) -> bool:
        context = cls.enrich_context(root, response_meta=response_meta)
        pagination = cls.resolve_pagination(context)

        if isinstance(pagination, dict):
            if pagination.get("is_complete") is False:
                return True

            if pagination.get("is_complete") is True:
                return False

            total = pagination.get("total")
            returned = pagination.get("returned")

            if total is not None and returned is not None:
                return int(returned) < int(total)

            limit = pagination.get("limit")

            if limit is not None and returned is not None:
                return int(returned) >= int(limit)

        summary = context.get("summary")

        if isinstance(summary, dict) and summary.get("is_complete") is False:
            return True

        return False

    @classmethod
    def build_notice_message(
        cls,
        root: dict[str, Any],
        *,
        response_meta: dict[str, Any] | None = None,
    ) -> str | None:
        payload = cls.build_notice_payload(root, response_meta=response_meta)

        if not payload:
            return None

        return str(payload.get("message") or "").strip() or None

    @classmethod
    def build_notice_payload(
        cls,
        root: dict[str, Any],
        *,
        response_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        context = cls.enrich_context(root, response_meta=response_meta)

        if not cls.is_incomplete(context):
            return None

        pagination = cls.resolve_pagination(context) or {}
        summary = context.get("summary") if isinstance(context.get("summary"), dict) else {}
        returned = cls._as_int(pagination.get("returned")) or cls._as_int(
            summary.get("total_records")
        ) or 0
        limit = cls._as_int(pagination.get("limit"))
        limit_text = str(limit) if limit is not None else "—"

        if cls.branch_filter_applied(context) is False:
            message = ChatAssistantContentService.format(
                _BUNDLE,
                "operationalIncompleteNoBranch",
                returned=returned,
                limit=limit_text,
            )
        else:
            total = cls._as_int(pagination.get("total"))

            if total is not None:
                message = ChatAssistantContentService.format(
                    _BUNDLE,
                    "operationalIncompleteWithTotal",
                    returned=returned,
                    total=total,
                    limit=limit_text,
                )
            else:
                message = ChatAssistantContentService.format(
                    _BUNDLE,
                    "operationalIncomplete",
                    returned=returned,
                    limit=limit_text,
                )

        hint = ChatAssistantContentService.get(_BUNDLE, "operationalIncompleteHint")

        if hint:
            message = f"{message} {hint}".strip()

        return {
            "message": message,
            "returned": returned,
            "limit": limit,
            "isComplete": False,
        }

    @classmethod
    def apply_to_commentary(
        cls,
        commentary: dict[str, Any],
        *,
        metadata: dict[str, Any],
        data: dict[str, Any],
    ) -> None:
        if not isinstance(commentary, dict):
            return

        response_meta = metadata.get("apiDelpiResponseMeta")
        response_meta = response_meta if isinstance(response_meta, dict) else None
        message = cls.build_notice_message(data, response_meta=response_meta)

        if not message:
            return

        commentary["paginated"] = True

        existing_attention = [
            str(line).strip()
            for line in (commentary.get("attention") or [])
            if str(line or "").strip()
        ]

        if message not in existing_attention:
            existing_attention.insert(0, message)
            commentary["attention"] = existing_attention[:8]

        existing_limitations = [
            str(line).strip()
            for line in (commentary.get("limitations") or [])
            if str(line or "").strip()
        ]

        if message not in existing_limitations:
            commentary["limitations"] = [message, *existing_limitations]

    @classmethod
    def _as_int(cls, value: Any) -> int | None:
        if value in (None, ""):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None
