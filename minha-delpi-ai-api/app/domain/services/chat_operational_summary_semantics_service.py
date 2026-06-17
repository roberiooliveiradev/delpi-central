"""Leitura canônica de flags de summary operacional (api-delpi → chat).

Presenters e use cases **não** interpretam `branch_filter_applied` / `consolidated_across_branches`
inline — consumir via este serviço ou delegados (`ChatOperationalResultCompletenessService`).
"""

from __future__ import annotations

from typing import Any


class ChatOperationalSummarySemanticsService:
    @classmethod
    def summary(cls, root: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(root, dict):
            return {}

        block = root.get("summary")

        return dict(block) if isinstance(block, dict) else {}

    @classmethod
    def branch_filter_applied(cls, root: dict[str, Any] | None) -> bool | None:
        summary = cls.summary(root)

        if "branch_filter_applied" in summary:
            return bool(summary.get("branch_filter_applied"))

        branch = summary.get("branch")

        if branch is not None:
            return bool(str(branch).strip())

        return None

    @classmethod
    def consolidated_across_branches(cls, root: dict[str, Any] | None) -> bool:
        summary = cls.summary(root)

        if "consolidated_across_branches" in summary:
            return bool(summary.get("consolidated_across_branches"))

        return False

    @classmethod
    def is_technical_summary_key(cls, key: str) -> bool:
        from app.domain.services.chat_presentation_operational_metadata_field_service import (
            ChatPresentationOperationalMetadataFieldService,
        )

        return ChatPresentationOperationalMetadataFieldService.is_technical_summary_key(key)

    @classmethod
    def filter_summary(cls, summary: dict[str, Any] | None) -> dict[str, Any]:
        from app.domain.services.chat_presentation_operational_metadata_field_service import (
            ChatPresentationOperationalMetadataFieldService,
        )

        return ChatPresentationOperationalMetadataFieldService.filter_summary(summary)
