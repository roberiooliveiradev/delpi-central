from __future__ import annotations

from datetime import date
from typing import Any

from cx_app.application.services.photo_storage import PhotoStorage
from cx_app.application.services.qr_service import (
    QrService,
    build_feedback_url,
    build_public_url,
)
from cx_app.application.services.token_service import generate_public_token
from cx_app.config import settings
from cx_app.domain.participant import ParticipantInput, ParticipantUpdate
from cx_app.infrastructure.persistence.participant_repository import ParticipantRepository

_API_BASE = settings.CX_API_ROOT_PATH.rstrip("/")


class ParticipantNotFoundError(LookupError):
    """Participante inexistente."""


class ParticipantService:
    def __init__(
        self,
        repository: ParticipantRepository | None = None,
        photo_storage: PhotoStorage | None = None,
        qr_service: QrService | None = None,
    ) -> None:
        self.repository = repository or ParticipantRepository()
        self.photo_storage = photo_storage or PhotoStorage()
        self.qr_service = qr_service or QrService()

    # ----- comandos (admin) ------------------------------------------------

    def create(
        self,
        data: ParticipantInput,
        *,
        photo_bytes: bytes,
        photo_mime: str | None,
        created_by: str | None,
        created_by_name: str | None,
    ) -> dict[str, Any]:
        token = generate_public_token()
        photo_filename, normalized_mime = self.photo_storage.save(
            content=photo_bytes, mime_type=photo_mime
        )
        qr_filename = self.qr_service.generate(token=token)
        feedback_qr_filename = self.qr_service.generate_feedback(token=token)

        row = self.repository.create(
            {
                "public_token": token,
                "full_name": data.full_name,
                "company_name": data.company_name,
                "visit_date": data.visit_date,
                "participant_info": data.participant_info,
                "photo_filename": photo_filename,
                "photo_mime": normalized_mime,
                "qr_filename": qr_filename,
                "feedback_qr_filename": feedback_qr_filename,
                "thank_you_message": data.thank_you_message,
                "created_by": created_by,
                "created_by_name": created_by_name,
            }
        )
        return self.to_admin_view(row)

    def update(
        self,
        participant_id: str,
        data: ParticipantUpdate,
        *,
        photo_bytes: bytes | None = None,
        photo_mime: str | None = None,
    ) -> dict[str, Any]:
        existing = self.repository.get_by_id(participant_id)
        if not existing:
            raise ParticipantNotFoundError(participant_id)

        fields: dict[str, Any] = {}
        if data.full_name is not None:
            fields["full_name"] = data.full_name
        if data.company_name is not None:
            fields["company_name"] = data.company_name
        if data.visit_date is not None:
            fields["visit_date"] = data.visit_date
        if data.participant_info is not None:
            fields["participant_info"] = data.participant_info
        if data.thank_you_message is not None:
            fields["thank_you_message"] = data.thank_you_message

        if photo_bytes is not None:
            new_photo, normalized_mime = self.photo_storage.save(
                content=photo_bytes, mime_type=photo_mime
            )
            fields["photo_filename"] = new_photo
            fields["photo_mime"] = normalized_mime

        updated = self.repository.update(participant_id, fields)
        if not updated:
            raise ParticipantNotFoundError(participant_id)

        # Remove a foto antiga só depois de persistir a nova.
        if photo_bytes is not None and existing.get("photo_filename"):
            self.photo_storage.delete(existing["photo_filename"])

        return self.to_admin_view(updated)

    def deactivate(self, participant_id: str) -> dict[str, Any]:
        updated = self.repository.set_active(participant_id, False)
        if not updated:
            raise ParticipantNotFoundError(participant_id)
        return self.to_admin_view(updated)

    # ----- consultas -------------------------------------------------------

    def get_admin(self, participant_id: str) -> dict[str, Any]:
        row = self.repository.get_by_id(participant_id)
        if not row:
            raise ParticipantNotFoundError(participant_id)
        return self.to_admin_view(row)

    def list_admin(
        self,
        *,
        limit: int,
        offset: int,
        company: str | None = None,
        visit_date: date | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        rows, total = self.repository.list(
            limit=limit, offset=offset, company=company, visit_date=visit_date
        )
        return [self.to_admin_view(row) for row in rows], total

    def get_public(self, token: str) -> dict[str, Any]:
        row = self.repository.get_by_token(token)
        if not row or not row.get("is_active"):
            raise ParticipantNotFoundError(token)
        self.repository.increment_view_count(token)
        return self.to_public_view(row)

    def read_photo_by_token(self, token: str) -> tuple[bytes, str] | None:
        row = self.repository.get_by_token(token)
        if not row or not row.get("is_active"):
            return None
        content = self.photo_storage.read(row.get("photo_filename") or "")
        if content is None:
            return None
        return content, row.get("photo_mime") or "image/jpeg"

    def read_qr_by_id(self, participant_id: str) -> tuple[bytes, str] | None:
        row = self.repository.get_by_id(participant_id)
        if not row:
            return None
        content = self.qr_service.read(row.get("qr_filename") or "")
        if content is None:
            return None
        return content, "image/png"

    def read_feedback_qr_by_id(self, participant_id: str) -> tuple[bytes, str] | None:
        row = self.repository.get_by_id(participant_id)
        if not row:
            return None

        filename = row.get("feedback_qr_filename")
        content = self.qr_service.read(filename or "") if filename else None

        # Geração lazy para participantes criados antes do QR de feedback existir.
        if content is None:
            token = row.get("public_token")
            if not token:
                return None
            filename = self.qr_service.generate_feedback(token=token)
            self.repository.update(participant_id, {"feedback_qr_filename": filename})
            content = self.qr_service.read(filename)
            if content is None:
                return None

        return content, "image/png"

    # ----- apresentação ----------------------------------------------------

    def to_admin_view(self, row: dict[str, Any]) -> dict[str, Any]:
        token = row.get("public_token")
        return {
            "id": row.get("id"),
            "publicToken": token,
            "fullName": row.get("full_name"),
            "companyName": row.get("company_name"),
            "visitDate": row.get("visit_date"),
            "participantInfo": row.get("participant_info"),
            "thankYouMessage": row.get("thank_you_message"),
            "photoUrl": f"{_API_BASE}/public/participants/{token}/photo",
            "qrUrl": f"{_API_BASE}/participants/{row.get('id')}/qr",
            "feedbackQrUrl": f"{_API_BASE}/participants/{row.get('id')}/feedback-qr",
            "publicUrl": build_public_url(token) if token else None,
            "feedbackPublicUrl": build_feedback_url(token) if token else None,
            "viewCount": row.get("view_count"),
            "isActive": row.get("is_active"),
            "createdByName": row.get("created_by_name"),
            "createdAt": row.get("created_at"),
            "updatedAt": row.get("updated_at"),
        }

    def to_public_view(self, row: dict[str, Any]) -> dict[str, Any]:
        token = row.get("public_token")
        return {
            "fullName": row.get("full_name"),
            "companyName": row.get("company_name"),
            "visitDate": row.get("visit_date"),
            "participantInfo": row.get("participant_info"),
            "thankYouMessage": row.get("thank_you_message"),
            "photoUrl": f"{_API_BASE}/public/participants/{token}/photo",
        }
