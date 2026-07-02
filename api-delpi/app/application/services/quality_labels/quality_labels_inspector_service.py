from __future__ import annotations

from typing import Any

from app.application.services.quality_labels.quality_labels_signature_storage import (
    QualityLabelsSignatureStorage,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_inspector_repository import (
    PostgresQualityLabelsInspectorRepository,
)


class QualityLabelsInspectorService:
    def __init__(
        self,
        *,
        repository: PostgresQualityLabelsInspectorRepository,
        signature_storage: QualityLabelsSignatureStorage,
    ) -> None:
        self._repository = repository
        self._signature_storage = signature_storage

    def get_profile(self, *, user_id: str) -> dict[str, Any] | None:
        return self._repository.to_payload(self._repository.get_by_user(user_id))

    def save_profile(
        self,
        *,
        user_id: str,
        display_name: str,
        role_title: str | None,
    ) -> dict[str, Any] | None:
        row = self._repository.upsert_profile(
            user_id=user_id,
            display_name=display_name.strip(),
            role_title=(role_title or "").strip() or None,
        )
        return self._repository.to_payload(row)

    def set_signature(
        self,
        *,
        user_id: str,
        display_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any] | None:
        previous = self._repository.get_by_user(user_id)
        stored_name = self._signature_storage.save(content=content, mime_type=mime_type)
        row = self._repository.set_signature(
            user_id=user_id,
            display_name=display_name.strip(),
            signature_filename=stored_name,
            signature_mime="image/png",
        )
        if previous and previous.get("signature_filename"):
            self._signature_storage.delete(previous["signature_filename"])
        return self._repository.to_payload(row)

    def read_signature(self, *, user_id: str) -> bytes | None:
        row = self._repository.get_by_user(user_id)
        if not row or not row.get("signature_filename"):
            return None
        return self._signature_storage.read(row["signature_filename"])
