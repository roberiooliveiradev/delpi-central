from __future__ import annotations

from typing import Any

from cx_app.application.services.qr_service import QrService, build_form_url
from cx_app.application.services.token_service import generate_public_token
from cx_app.config import settings
from cx_app.domain.form import (
    ALL_QUESTION_TYPES,
    CHOICE_QUESTION_TYPES,
    FormInput,
    FormUpdate,
    QuestionInput,
)
from cx_app.infrastructure.persistence.form_repository import FormRepository

_API_BASE = settings.CX_API_ROOT_PATH.rstrip("/")

MAX_TITLE_LEN = 200
MAX_TEXT_LEN = 2000
MIN_CHOICE_OPTIONS = 2


class FormNotFoundError(LookupError):
    """Formulário inexistente."""


class FormValidationError(ValueError):
    """Dados do formulário inválidos."""


class FormService:
    def __init__(
        self,
        repository: FormRepository | None = None,
        qr_service: QrService | None = None,
    ) -> None:
        self.repository = repository or FormRepository()
        self.qr_service = qr_service or QrService()

    # ----- comandos (admin) ------------------------------------------------

    def create(
        self,
        data: FormInput,
        *,
        created_by: str | None,
        created_by_name: str | None,
    ) -> dict[str, Any]:
        title = _clean(data.title)
        if not title:
            raise FormValidationError("Informe um título para o formulário.")
        token = generate_public_token()
        qr_filename = self.qr_service.generate_form(token=token)
        row = self.repository.create(
            {
                "public_token": token,
                "title": title[:MAX_TITLE_LEN],
                "description": _clean(data.description),
                "qr_filename": qr_filename,
                "created_by": created_by,
                "created_by_name": created_by_name,
            }
        )
        return self.to_admin_view(row, questions=[])

    def update(self, form_id: str, data: FormUpdate) -> dict[str, Any]:
        self._require(form_id)
        fields: dict[str, Any] = {}
        if data.title is not None:
            title = _clean(data.title)
            if not title:
                raise FormValidationError("Informe um título para o formulário.")
            fields["title"] = title[:MAX_TITLE_LEN]
        if data.description is not None:
            fields["description"] = _clean(data.description)
        updated = self.repository.update(form_id, fields)
        return self._admin_with_questions(updated or {})

    def set_questions(
        self, form_id: str, questions: list[QuestionInput]
    ) -> dict[str, Any]:
        self._require(form_id)
        normalized = [self._validate_question(q) for q in questions]
        self.repository.replace_questions(form_id, normalized)
        return self._admin_with_questions(self.repository.get_by_id(form_id) or {})

    def activate(self, form_id: str) -> dict[str, Any]:
        updated = self.repository.set_active(form_id, True)
        if not updated:
            raise FormNotFoundError(form_id)
        return self._admin_with_questions(updated)

    def deactivate(self, form_id: str) -> dict[str, Any]:
        updated = self.repository.set_active(form_id, False)
        if not updated:
            raise FormNotFoundError(form_id)
        return self._admin_with_questions(updated)

    def delete(self, form_id: str) -> None:
        row = self.repository.get_by_id(form_id)
        if not row:
            raise FormNotFoundError(form_id)
        self.qr_service.delete(row.get("qr_filename"))
        self.repository.delete(form_id)

    # ----- consultas -------------------------------------------------------

    def list_admin(self) -> list[dict[str, Any]]:
        return [self.to_admin_view(row) for row in self.repository.list()]

    def get_admin(self, form_id: str) -> dict[str, Any]:
        row = self._require(form_id)
        return self._admin_with_questions(row)

    def get_public(self, token: str) -> dict[str, Any]:
        row = self.repository.get_by_token(token)
        if not row or not row.get("is_active"):
            raise FormNotFoundError(token)
        questions = self.repository.list_questions(row["id"], active_only=True)
        return self.to_public_view(row, questions)

    def read_qr_by_id(self, form_id: str) -> tuple[bytes, str] | None:
        row = self.repository.get_by_id(form_id)
        if not row:
            return None
        filename = row.get("qr_filename")
        content = self.qr_service.read(filename or "") if filename else None
        if content is None:
            token = row.get("public_token")
            if not token:
                return None
            filename = self.qr_service.generate_form(token=token)
            self.repository.update(form_id, {"qr_filename": filename})
            content = self.qr_service.read(filename)
            if content is None:
                return None
        return content, "image/png"

    # ----- internos --------------------------------------------------------

    def _require(self, form_id: str) -> dict[str, Any]:
        row = self.repository.get_by_id(form_id)
        if not row:
            raise FormNotFoundError(form_id)
        return row

    def _admin_with_questions(self, row: dict[str, Any]) -> dict[str, Any]:
        questions = self.repository.list_questions(row["id"], active_only=True)
        return self.to_admin_view(row, questions=questions)

    def _validate_question(self, q: QuestionInput) -> dict[str, Any]:
        label = _clean(q.label)
        if not label:
            raise FormValidationError("Toda pergunta precisa de um enunciado.")
        if q.question_type not in ALL_QUESTION_TYPES:
            raise FormValidationError(f"Tipo de pergunta inválido: {q.question_type}.")
        options: list[str] = []
        if q.question_type in CHOICE_QUESTION_TYPES:
            options = [opt for opt in (_clean(o) or "" for o in q.options) if opt]
            if len(options) < MIN_CHOICE_OPTIONS:
                raise FormValidationError(
                    f"'{label}' precisa de pelo menos {MIN_CHOICE_OPTIONS} opções."
                )
        return {
            "id": _clean(q.id),
            "label": label[:MAX_TITLE_LEN],
            "question_type": q.question_type,
            "help_text": _clean(q.help_text),
            "is_required": bool(q.is_required),
            "options": options,
        }

    # ----- apresentação ----------------------------------------------------

    def to_admin_view(
        self, row: dict[str, Any], questions: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        token = row.get("public_token")
        view = {
            "id": row.get("id"),
            "publicToken": token,
            "title": row.get("title"),
            "description": row.get("description"),
            "isActive": row.get("is_active"),
            "responseCount": row.get("response_count"),
            "qrUrl": f"{_API_BASE}/forms/{row.get('id')}/qr",
            "publicUrl": build_form_url(token) if token else None,
            "createdByName": row.get("created_by_name"),
            "createdAt": row.get("created_at"),
            "updatedAt": row.get("updated_at"),
        }
        if questions is not None:
            view["questions"] = [self.to_question_view(q) for q in questions]
        return view

    def to_public_view(
        self, row: dict[str, Any], questions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return {
            "token": row.get("public_token"),
            "title": row.get("title"),
            "description": row.get("description"),
            "questions": [self.to_question_view(q) for q in questions],
        }

    @staticmethod
    def to_question_view(q: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": q.get("id"),
            "position": q.get("position"),
            "type": q.get("question_type"),
            "label": q.get("label"),
            "helpText": q.get("help_text"),
            "required": q.get("is_required"),
            "options": q.get("options") or [],
        }


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped[:MAX_TEXT_LEN] if stripped else None
