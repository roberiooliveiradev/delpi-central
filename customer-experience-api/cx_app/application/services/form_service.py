from __future__ import annotations

from typing import Any

from cx_app.application.services.form_image_storage import FormImageStorage
from cx_app.application.services.qr_service import QrService, build_form_url
from cx_app.application.services.token_service import generate_public_token
from cx_app.config import settings
from cx_app.domain.form import (
    ALL_BACKGROUND_FITS,
    ALL_QUESTION_TYPES,
    CHOICE_QUESTION_TYPES,
    DEFAULT_BACKGROUND_FIT,
    FormInput,
    FormUpdate,
    PageInput,
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
        image_storage: FormImageStorage | None = None,
    ) -> None:
        self.repository = repository or FormRepository()
        self.qr_service = qr_service or QrService()
        self.image_storage = image_storage or FormImageStorage()

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
                "one_question_per_page": bool(data.one_question_per_page),
                "background_fit": _normalize_background_fit(data.background_fit),
                "created_by": created_by,
                "created_by_name": created_by_name,
            }
        )
        return self.to_admin_view(row, questions=[], pages=[])

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
        if data.one_question_per_page is not None:
            fields["one_question_per_page"] = bool(data.one_question_per_page)
        if data.background_fit is not None:
            fields["background_fit"] = _normalize_background_fit(data.background_fit)
        updated = self.repository.update(form_id, fields)
        return self._admin_full(updated or {})

    def set_structure(
        self,
        form_id: str,
        *,
        questions: list[QuestionInput],
        pages: list[PageInput] | None = None,
        one_question_per_page: bool | None = None,
    ) -> dict[str, Any]:
        row = self._require(form_id)
        if one_question_per_page is not None:
            self.repository.update(form_id, {"one_question_per_page": one_question_per_page})
            row = self.repository.get_by_id(form_id) or row

        normalized_pages = [self._validate_page(p) for p in (pages or [])]
        normalized_questions = [self._validate_question(q) for q in questions]

        existing_pages = {str(p["id"]): p for p in self.repository.list_pages(form_id)}
        merged_pages: list[dict[str, Any]] = []
        for page in normalized_pages:
            existing = existing_pages.get(str(page.get("id") or ""), {})
            merged_pages.append(
                {
                    **page,
                    "background_image_filename": page.get("background_image_filename")
                    or existing.get("background_image_filename"),
                    "point_image_filename": page.get("point_image_filename")
                    or existing.get("point_image_filename"),
                    "point_image_fit": page.get("point_image_fit")
                    or existing.get("point_image_fit")
                    or "scale",
                }
            )

        wizard = bool(row.get("one_question_per_page"))
        if wizard and not merged_pages:
            merged_pages = [
                {
                    "title": q["label"],
                    "background_image_filename": None,
                    "point_image_filename": None,
                    "point_image_fit": "scale",
                }
                for q in normalized_questions
            ]

        stored_pages = self.repository.replace_pages(form_id, merged_pages)

        existing_questions = {
            str(q["id"]): q
            for q in self.repository.list_questions(form_id, active_only=True)
        }
        for q in normalized_questions:
            existing = existing_questions.get(str(q.get("id") or ""), {})
            if not q.get("point_image_filename"):
                q["point_image_filename"] = existing.get("point_image_filename")
            if not q.get("point_image_fit"):
                q["point_image_fit"] = existing.get("point_image_fit") or "scale"

        page_ids = [str(p["id"]) for p in stored_pages]
        for index, q in enumerate(normalized_questions):
            if wizard and index < len(page_ids):
                q["page_id"] = page_ids[index]
            elif q.get("page_index") is not None:
                page_index = q["page_index"]
                if 0 <= page_index < len(page_ids):
                    q["page_id"] = page_ids[page_index]
            elif q.get("page_id"):
                q["page_id"] = q["page_id"]

        self.repository.replace_questions(form_id, normalized_questions)
        return self._admin_full(self.repository.get_by_id(form_id) or row)

    def set_questions(
        self, form_id: str, questions: list[QuestionInput]
    ) -> dict[str, Any]:
        return self.set_structure(form_id, questions=questions)

    def upload_background(
        self, form_id: str, *, content: bytes, mime_type: str | None
    ) -> dict[str, Any]:
        row = self._require(form_id)
        old = row.get("background_image_filename")
        stored_name, _ = self.image_storage.save(content=content, mime_type=mime_type)
        self.image_storage.delete(old)
        updated = self.repository.update(form_id, {"background_image_filename": stored_name})
        return self._admin_full(updated or row)

    def remove_background(self, form_id: str) -> dict[str, Any]:
        row = self._require(form_id)
        self.image_storage.delete(row.get("background_image_filename"))
        updated = self.repository.update(form_id, {"background_image_filename": None})
        return self._admin_full(updated or row)

    def upload_page_background(
        self,
        form_id: str,
        page_id: str,
        *,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]:
        self._require(form_id)
        page = self._require_page(form_id, page_id)
        old = page.get("background_image_filename")
        stored_name, _ = self.image_storage.save(content=content, mime_type=mime_type)
        self.image_storage.delete(old)
        self.repository.replace_pages(
            form_id,
            [
                {
                    **p,
                    "background_image_filename": stored_name
                    if str(p["id"]) == page_id
                    else p.get("background_image_filename"),
                }
                for p in self.repository.list_pages(form_id)
            ],
        )
        return self._admin_full(self.repository.get_by_id(form_id) or {})

    def upload_page_point_image(
        self,
        form_id: str,
        page_id: str,
        *,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]:
        self._require(form_id)
        page = self._require_page(form_id, page_id)
        old = page.get("point_image_filename")
        stored_name, _ = self.image_storage.save(content=content, mime_type=mime_type)
        self.image_storage.delete(old)
        self.repository.replace_pages(
            form_id,
            [
                {
                    **p,
                    "point_image_filename": stored_name
                    if str(p["id"]) == page_id
                    else p.get("point_image_filename"),
                }
                for p in self.repository.list_pages(form_id)
            ],
        )
        return self._admin_full(self.repository.get_by_id(form_id) or {})

    def remove_page_background(self, form_id: str, page_id: str) -> dict[str, Any]:
        self._require(form_id)
        page = self._require_page(form_id, page_id)
        self.image_storage.delete(page.get("background_image_filename"))
        self.repository.replace_pages(
            form_id,
            [
                {
                    **p,
                    "background_image_filename": None
                    if str(p["id"]) == page_id
                    else p.get("background_image_filename"),
                }
                for p in self.repository.list_pages(form_id)
            ],
        )
        return self._admin_full(self.repository.get_by_id(form_id) or {})

    def remove_page_point_image(self, form_id: str, page_id: str) -> dict[str, Any]:
        self._require(form_id)
        page = self._require_page(form_id, page_id)
        self.image_storage.delete(page.get("point_image_filename"))
        self.repository.replace_pages(
            form_id,
            [
                {
                    **p,
                    "point_image_filename": None
                    if str(p["id"]) == page_id
                    else p.get("point_image_filename"),
                }
                for p in self.repository.list_pages(form_id)
            ],
        )
        return self._admin_full(self.repository.get_by_id(form_id) or {})

    def remove_question_point_image(self, form_id: str, question_id: str) -> dict[str, Any]:
        self._require(form_id)
        question = self._require_question(form_id, question_id)
        self.image_storage.delete(question.get("point_image_filename"))
        questions = self.repository.list_questions(form_id, active_only=True)
        self.repository.replace_questions(
            form_id,
            [
                {
                    "id": str(q["id"]),
                    "label": q["label"],
                    "question_type": q["question_type"],
                    "help_text": q.get("help_text"),
                    "is_required": q.get("is_required"),
                    "options": q.get("options") or [],
                    "page_id": str(q["page_id"]) if q.get("page_id") else None,
                    "point_image_filename": None
                    if str(q["id"]) == question_id
                    else q.get("point_image_filename"),
                }
                for q in questions
            ],
        )
        return self._admin_full(self.repository.get_by_id(form_id) or {})

    def upload_question_point_image(
        self,
        form_id: str,
        question_id: str,
        *,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]:
        self._require(form_id)
        question = self._require_question(form_id, question_id)
        old = question.get("point_image_filename")
        stored_name, _ = self.image_storage.save(content=content, mime_type=mime_type)
        self.image_storage.delete(old)
        questions = self.repository.list_questions(form_id, active_only=True)
        self.repository.replace_questions(
            form_id,
            [
                {
                    "id": str(q["id"]),
                    "label": q["label"],
                    "question_type": q["question_type"],
                    "help_text": q.get("help_text"),
                    "is_required": q.get("is_required"),
                    "options": q.get("options") or [],
                    "page_id": str(q["page_id"]) if q.get("page_id") else None,
                    "point_image_filename": stored_name
                    if str(q["id"]) == question_id
                    else q.get("point_image_filename"),
                }
                for q in questions
            ],
        )
        return self._admin_full(self.repository.get_by_id(form_id) or {})

    def activate(self, form_id: str) -> dict[str, Any]:
        updated = self.repository.set_active(form_id, True)
        if not updated:
            raise FormNotFoundError(form_id)
        return self._admin_full(updated)

    def deactivate(self, form_id: str) -> dict[str, Any]:
        updated = self.repository.set_active(form_id, False)
        if not updated:
            raise FormNotFoundError(form_id)
        return self._admin_full(updated)

    def duplicate(
        self,
        form_id: str,
        *,
        created_by: str | None,
        created_by_name: str | None,
    ) -> dict[str, Any]:
        """Copia estrutura (páginas, perguntas, imagens). Não copia respostas."""
        source = self._require(form_id)
        pages = self.repository.list_pages(form_id)
        questions = self.repository.list_questions(form_id, active_only=True)

        base_title = _clean(source.get("title")) or "Formulário"
        copy_title = f"{base_title} (cópia)"[:MAX_TITLE_LEN]
        token = generate_public_token()
        qr_filename = self.qr_service.generate_form(token=token)

        row = self.repository.create(
            {
                "public_token": token,
                "title": copy_title,
                "description": source.get("description"),
                "qr_filename": qr_filename,
                "one_question_per_page": bool(source.get("one_question_per_page")),
                "background_fit": _normalize_background_fit(source.get("background_fit")),
                "created_by": created_by,
                "created_by_name": created_by_name,
            }
        )
        new_id = str(row["id"])

        background_name = self._clone_stored_image(source.get("background_image_filename"))
        if background_name:
            updated = self.repository.update(
                new_id, {"background_image_filename": background_name}
            )
            if updated:
                row = updated

        page_id_map: dict[str, str] = {}
        cloned_pages: list[dict[str, Any]] = [
            {
                "title": page.get("title"),
                "background_image_filename": self._clone_stored_image(
                    page.get("background_image_filename")
                ),
                "point_image_filename": self._clone_stored_image(
                    page.get("point_image_filename")
                ),
                "point_image_fit": _normalize_background_fit(page.get("point_image_fit")),
            }
            for page in pages
        ]
        new_pages = self.repository.replace_pages(new_id, cloned_pages)
        for old, new in zip(pages, new_pages):
            page_id_map[str(old["id"])] = str(new["id"])

        cloned_questions: list[dict[str, Any]] = []
        for q in questions:
            old_page = str(q["page_id"]) if q.get("page_id") else None
            cloned_questions.append(
                {
                    "label": q["label"],
                    "question_type": q["question_type"],
                    "help_text": q.get("help_text"),
                    "is_required": q.get("is_required"),
                    "options": list(q.get("options") or []),
                    "page_id": page_id_map.get(old_page) if old_page else None,
                    "point_image_filename": self._clone_stored_image(
                        q.get("point_image_filename")
                    ),
                    "point_image_fit": _normalize_background_fit(q.get("point_image_fit")),
                }
            )
        self.repository.replace_questions(new_id, cloned_questions)
        return self._admin_full(self.repository.get_by_id(new_id) or row)

    def _clone_stored_image(self, filename: str | None) -> str | None:
        if not filename:
            return None
        content = self.image_storage.read(str(filename))
        if content is None:
            return None
        mime = _mime_from_filename(str(filename))
        stored_name, _ = self.image_storage.save(content=content, mime_type=mime)
        return stored_name

    def delete(self, form_id: str) -> None:
        row = self.repository.get_by_id(form_id)
        if not row:
            raise FormNotFoundError(form_id)
        self.qr_service.delete(row.get("qr_filename"))
        self.image_storage.delete(row.get("background_image_filename"))
        for page in self.repository.list_pages(form_id):
            self.image_storage.delete(page.get("background_image_filename"))
            self.image_storage.delete(page.get("point_image_filename"))
        for question in self.repository.list_questions(form_id, active_only=False):
            self.image_storage.delete(question.get("point_image_filename"))
        self.repository.delete(form_id)

    # ----- consultas -------------------------------------------------------

    def list_admin(self) -> list[dict[str, Any]]:
        return [self.to_admin_view(row) for row in self.repository.list()]

    def get_admin(self, form_id: str) -> dict[str, Any]:
        row = self._require(form_id)
        return self._admin_full(row)

    def get_public(self, token: str) -> dict[str, Any]:
        row = self.repository.get_by_token(token)
        if not row or not row.get("is_active"):
            raise FormNotFoundError(token)
        questions = self.repository.list_questions(row["id"], active_only=True)
        pages = self.repository.list_pages(row["id"])
        return self.to_public_view(row, questions, pages)

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

    def read_public_background(self, token: str) -> tuple[bytes, str] | None:
        row = self._require_public_row(token)
        filename = row.get("background_image_filename")
        if not filename:
            return None
        content = self.image_storage.read(filename)
        if content is None:
            return None
        return content, _mime_from_filename(filename)

    def read_public_page_background(self, token: str, page_id: str) -> tuple[bytes, str] | None:
        row = self._require_public_row(token)
        page = self._require_page(row["id"], page_id)
        filename = page.get("background_image_filename")
        if not filename:
            return None
        content = self.image_storage.read(filename)
        if content is None:
            return None
        return content, _mime_from_filename(filename)

    def read_public_page_point(self, token: str, page_id: str) -> tuple[bytes, str] | None:
        row = self._require_public_row(token)
        page = self._require_page(row["id"], page_id)
        filename = page.get("point_image_filename")
        if not filename:
            return None
        content = self.image_storage.read(filename)
        if content is None:
            return None
        return content, _mime_from_filename(filename)

    def read_public_question_point(
        self, token: str, question_id: str
    ) -> tuple[bytes, str] | None:
        row = self._require_public_row(token)
        question = self._require_question(row["id"], question_id)
        filename = question.get("point_image_filename")
        if not filename:
            return None
        content = self.image_storage.read(filename)
        if content is None:
            return None
        return content, _mime_from_filename(filename)

    # ----- internos --------------------------------------------------------

    def _require(self, form_id: str) -> dict[str, Any]:
        row = self.repository.get_by_id(form_id)
        if not row:
            raise FormNotFoundError(form_id)
        return row

    def _require_public(self, token: str) -> dict[str, Any]:
        row = self.repository.get_by_token(token)
        if not row or not row.get("is_active"):
            raise FormNotFoundError(token)
        return row

    def _require_public_row(self, token: str) -> dict[str, Any]:
        """Formulário por token (ativo ou rascunho) — usado só para assets de prévia."""
        row = self.repository.get_by_token(token)
        if not row:
            raise FormNotFoundError(token)
        return row

    def _require_page(self, form_id: str, page_id: str) -> dict[str, Any]:
        for page in self.repository.list_pages(form_id):
            if str(page["id"]) == page_id:
                return page
        raise FormNotFoundError(page_id)

    def _require_question(self, form_id: str, question_id: str) -> dict[str, Any]:
        for question in self.repository.list_questions(form_id, active_only=False):
            if str(question["id"]) == question_id:
                return question
        raise FormNotFoundError(question_id)

    def _admin_full(self, row: dict[str, Any]) -> dict[str, Any]:
        questions = self.repository.list_questions(row["id"], active_only=True)
        pages = self.repository.list_pages(row["id"])
        return self.to_admin_view(row, questions=questions, pages=pages)

    def _validate_page(self, p: PageInput) -> dict[str, Any]:
        return {
            "id": _clean(p.id),
            "title": _clean(p.title),
            "background_image_filename": _clean(p.background_image_filename),
            "point_image_filename": _clean(p.point_image_filename),
            "point_image_fit": _normalize_background_fit(p.point_image_fit),
        }

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
            "page_id": _clean(q.page_id),
            "page_index": q.page_index,
            "point_image_filename": _clean(q.point_image_filename),
            "point_image_fit": _normalize_background_fit(q.point_image_fit),
        }

    # ----- apresentação ----------------------------------------------------

    def to_admin_view(
        self,
        row: dict[str, Any],
        questions: list[dict[str, Any]] | None = None,
        pages: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        token = row.get("public_token")
        form_id = row.get("id")
        view = {
            "id": form_id,
            "publicToken": token,
            "title": row.get("title"),
            "description": row.get("description"),
            "isActive": row.get("is_active"),
            "responseCount": row.get("response_count"),
            "oneQuestionPerPage": bool(row.get("one_question_per_page")),
            "backgroundFit": _normalize_background_fit(row.get("background_fit")),
            "backgroundImageUrl": self._form_background_url(token)
            if row.get("background_image_filename")
            else None,
            "qrUrl": f"{_API_BASE}/forms/{form_id}/qr",
            "publicUrl": build_form_url(token) if token else None,
            "createdByName": row.get("created_by_name"),
            "createdAt": row.get("created_at"),
            "updatedAt": row.get("updated_at"),
        }
        if questions is not None:
            view["questions"] = [self.to_question_view(q, token) for q in questions]
        if pages is not None:
            view["pages"] = [self.to_page_view(p, token) for p in pages]
        return view

    def to_public_view(
        self,
        row: dict[str, Any],
        questions: list[dict[str, Any]],
        pages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        token = row.get("public_token")
        return {
            "token": token,
            "title": row.get("title"),
            "description": row.get("description"),
            "oneQuestionPerPage": bool(row.get("one_question_per_page")),
            "backgroundFit": _normalize_background_fit(row.get("background_fit")),
            "backgroundImageUrl": self._form_background_url(token)
            if row.get("background_image_filename")
            else None,
            "pages": [self.to_page_view(p, token) for p in pages],
            "questions": [self.to_question_view(q, token) for q in questions],
        }

    def to_page_view(self, p: dict[str, Any], token: str | None) -> dict[str, Any]:
        page_id = p.get("id")
        bg = p.get("background_image_filename")
        point = p.get("point_image_filename")
        return {
            "id": page_id,
            "position": p.get("position"),
            "title": p.get("title"),
            "backgroundImageUrl": self._page_background_url(token, page_id) if bg else None,
            "pointImageUrl": self._page_point_url(token, page_id) if point else None,
            "pointImageFit": _normalize_background_fit(p.get("point_image_fit")),
        }

    def to_question_view(self, q: dict[str, Any], token: str | None = None) -> dict[str, Any]:
        question_id = q.get("id")
        point = q.get("point_image_filename")
        return {
            "id": question_id,
            "position": q.get("position"),
            "pageId": q.get("page_id"),
            "type": q.get("question_type"),
            "label": q.get("label"),
            "helpText": q.get("help_text"),
            "required": q.get("is_required"),
            "options": q.get("options") or [],
            "pointImageUrl": self._question_point_url(token, question_id) if point else None,
            "pointImageFit": _normalize_background_fit(q.get("point_image_fit")),
        }

    def _form_background_url(self, token: str | None) -> str | None:
        if not token:
            return None
        return f"{_API_BASE}/public/forms/{token}/background"

    def _page_background_url(self, token: str | None, page_id: str | None) -> str | None:
        if not token or not page_id:
            return None
        return f"{_API_BASE}/public/forms/{token}/pages/{page_id}/background"

    def _page_point_url(self, token: str | None, page_id: str | None) -> str | None:
        if not token or not page_id:
            return None
        return f"{_API_BASE}/public/forms/{token}/pages/{page_id}/point-image"

    def _question_point_url(self, token: str | None, question_id: str | None) -> str | None:
        if not token or not question_id:
            return None
        return f"{_API_BASE}/public/forms/{token}/questions/{question_id}/point-image"


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped[:MAX_TEXT_LEN] if stripped else None


def _normalize_background_fit(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return DEFAULT_BACKGROUND_FIT
    if raw not in ALL_BACKGROUND_FITS:
        raise FormValidationError(
            "Modo de fundo inválido. Use fixed, scale ou tile."
        )
    return raw


def _mime_from_filename(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"
