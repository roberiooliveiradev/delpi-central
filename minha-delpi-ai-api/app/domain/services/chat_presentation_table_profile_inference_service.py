"""Inferência canônica de `profile_name` para tabelas operacionais — Playbook 12 R23."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)


class ChatPresentationTableProfileInferenceService:
    """Resolve hints de `tableProfiles` a partir de entidade, rota e amostra de row."""

    @classmethod
    def infer_profile_name(
        cls,
        *,
        path: str = "",
        entity: str | None = None,
        sample_row: dict[str, Any] | None = None,
        column_labels: ExternalActionColumnLabelService | None = None,
    ) -> str | None:
        token = str(entity or "").strip()

        if token:
            hinted = ChatPresentationProfileService.table_profile_for_entity(token)

            if hinted:
                return hinted

        labels = column_labels or ExternalActionColumnLabelService()

        if isinstance(sample_row, dict) and sample_row:
            detected = labels.detect_table_profile(sample_row, path=path)

            if detected:
                return detected

        return None
