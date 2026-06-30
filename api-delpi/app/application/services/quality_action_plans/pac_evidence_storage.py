from __future__ import annotations

import mimetypes
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import settings

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/plain",
    "text/csv",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_EVIDENCE_BYTES = 25 * 1024 * 1024


class PacEvidenceStorageError(ValueError):
    pass


class PacEvidenceStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.PAC_EVIDENCE_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def plan_id_candidates(*, plan_ref: str, evidence: dict[str, Any] | None = None) -> list[str]:
        from app.domain.services.quality_action_plans.quality_action_plan_reference_service import (
            normalize_plan_code,
        )

        candidates: list[str] = []
        if evidence and evidence.get("plan_id"):
            candidates.append(str(evidence["plan_id"]))
        ref = (plan_ref or "").strip()
        if ref:
            candidates.append(ref)
            normalized_code = normalize_plan_code(ref)
            if normalized_code and normalized_code not in candidates:
                candidates.append(normalized_code)
        return candidates

    def validate_upload(self, *, mime_type: str | None, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise PacEvidenceStorageError("Arquivo vazio.")
        if size_bytes > MAX_EVIDENCE_BYTES:
            raise PacEvidenceStorageError("Arquivo excede o limite de 25 MB.")
        normalized = (mime_type or "").lower()
        if normalized not in ALLOWED_MIME_TYPES:
            raise PacEvidenceStorageError(
                "Formato inválido. Use imagem, PDF, planilha ou documento de texto."
            )

    def save(
        self,
        *,
        plan_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> str:
        self.validate_upload(mime_type=mime_type, size_bytes=len(content))

        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension(mime_type or "") or ".bin"

        stored_name = f"{uuid4().hex}{extension}"
        target_dir = self.base_dir / plan_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / stored_name
        target_path.write_bytes(content)
        return stored_name

    def resolve_file(self, *, plan_id: str, stored_name: str) -> Path:
        return self.resolve_evidence_file(
            stored_name=stored_name,
            plan_id_candidates=[plan_id],
        )

    def resolve_evidence_file(
        self,
        *,
        stored_name: str,
        plan_id_candidates: list[str],
    ) -> Path:
        normalized_name = (stored_name or "").strip()
        if not normalized_name:
            raise PacEvidenceStorageError("Arquivo não encontrado.")

        base = self.base_dir.resolve()
        seen: set[str] = set()
        for candidate in plan_id_candidates:
            plan_key = (candidate or "").strip()
            if not plan_key or plan_key in seen:
                continue
            seen.add(plan_key)
            path = (self.base_dir / plan_key / normalized_name).resolve()
            if not str(path).startswith(str(base)):
                raise PacEvidenceStorageError("Caminho de arquivo inválido.")
            if path.is_file():
                return path

        raise PacEvidenceStorageError("Arquivo não encontrado.")

    def delete_file(self, *, plan_id: str, stored_name: str) -> None:
        path = self.resolve_file(plan_id=plan_id, stored_name=stored_name)
        path.unlink(missing_ok=True)
