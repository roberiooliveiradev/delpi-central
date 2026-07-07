from __future__ import annotations

import uuid

import pytest

from cx_app.application.services.form_service import (
    FormNotFoundError,
    FormService,
    FormValidationError,
)
from cx_app.domain.form import FormInput, FormUpdate, PageInput, QuestionInput, QuestionType


class FakeFormRepository:
    def __init__(self) -> None:
        self.forms: dict[str, dict] = {}
        self.questions: dict[str, list[dict]] = {}
        self.pages: dict[str, list[dict]] = {}
        self.deleted: list[str] = []

    def create(self, data: dict) -> dict:
        fid = str(uuid.uuid4())
        row = {
            "id": fid,
            "is_active": True,
            "response_count": 0,
            "one_question_per_page": False,
            "background_image_filename": None,
            "created_at": "2026-07-01T12:00:00Z",
            "updated_at": "2026-07-01T12:00:00Z",
            **data,
        }
        self.forms[fid] = row
        self.questions[fid] = []
        self.pages[fid] = []
        return dict(row)

    def get_by_id(self, form_id: str):
        row = self.forms.get(form_id)
        return dict(row) if row else None

    def get_by_token(self, token: str):
        for row in self.forms.values():
            if row["public_token"] == token:
                return dict(row)
        return None

    def list(self):
        return [dict(r) for r in self.forms.values()]

    def update(self, form_id: str, fields: dict):
        row = self.forms.get(form_id)
        if not row:
            return None
        row.update(fields)
        return dict(row)

    def set_active(self, form_id: str, is_active: bool):
        return self.update(form_id, {"is_active": is_active})

    def increment_response_count(self, form_id: str) -> None:
        self.forms[form_id]["response_count"] += 1

    def delete(self, form_id: str) -> bool:
        if form_id in self.forms:
            del self.forms[form_id]
            self.deleted.append(form_id)
            return True
        return False

    def list_questions(self, form_id: str, *, active_only: bool = False):
        rows = self.questions.get(form_id, [])
        if active_only:
            rows = [q for q in rows if q.get("is_active")]
        return [dict(q) for q in rows]

    def list_pages(self, form_id: str):
        return [dict(p) for p in self.pages.get(form_id, [])]

    def replace_pages(self, form_id: str, pages: list[dict]):
        stored = []
        for pos, page in enumerate(pages):
            stored.append(
                {
                    "id": page.get("id") or str(uuid.uuid4()),
                    "form_id": form_id,
                    "position": pos,
                    "title": page.get("title"),
                    "background_image_filename": page.get("background_image_filename"),
                    "point_image_filename": page.get("point_image_filename"),
                }
            )
        self.pages[form_id] = stored
        return [dict(p) for p in stored]

    def replace_questions(self, form_id: str, questions: list[dict]):
        stored = []
        for pos, q in enumerate(questions):
            stored.append(
                {
                    "id": q.get("id") or str(uuid.uuid4()),
                    "form_id": form_id,
                    "page_id": q.get("page_id"),
                    "position": pos,
                    "question_type": q["question_type"],
                    "label": q["label"],
                    "help_text": q.get("help_text"),
                    "is_required": q.get("is_required", False),
                    "options": q.get("options") or [],
                    "point_image_filename": q.get("point_image_filename"),
                    "is_active": True,
                }
            )
        self.questions[form_id] = stored
        return [dict(q) for q in stored]


class FakeQr:
    def __init__(self) -> None:
        self.deleted: list[str | None] = []

    def generate_form(self, *, token: str) -> str:
        return f"form-{token}.png"

    def delete(self, filename: str | None) -> None:
        self.deleted.append(filename)

    def read(self, filename: str):
        return b"png"


def _service():
    repo = FakeFormRepository()
    qr = FakeQr()
    return FormService(repository=repo, qr_service=qr), repo, qr


def _create(service):
    return service.create(
        FormInput(title="Pesquisa de visita", description="Conte sua experiência"),
        created_by="sub", created_by_name="Admin",
    )


def test_create_generates_token_qr_and_empty_questions():
    service, repo, qr = _service()
    view = _create(service)
    assert view["title"] == "Pesquisa de visita"
    assert view["questions"] == []
    assert view["isActive"] is True
    assert view["publicUrl"] and view["qrUrl"]


def test_create_blank_title_raises():
    service, _, _ = _service()
    with pytest.raises(FormValidationError):
        service.create(FormInput(title="   "), created_by=None, created_by_name=None)


def test_set_questions_valid_persists():
    service, _, _ = _service()
    fid = _create(service)["id"]
    view = service.set_questions(
        fid,
        [
            QuestionInput(label="Nota geral", question_type=QuestionType.RATING, is_required=True),
            QuestionInput(
                label="O que achou?",
                question_type=QuestionType.SINGLE_CHOICE,
                options=["Bom", "Ruim"],
            ),
        ],
    )
    assert len(view["questions"]) == 2
    assert view["questions"][0]["type"] == "rating"
    assert view["questions"][1]["options"] == ["Bom", "Ruim"]


def test_set_questions_choice_needs_two_options():
    service, _, _ = _service()
    fid = _create(service)["id"]
    with pytest.raises(FormValidationError):
        service.set_questions(
            fid,
            [QuestionInput(label="Escolha", question_type=QuestionType.MULTI_CHOICE, options=["Só uma"])],
        )


def test_set_questions_invalid_type_raises():
    service, _, _ = _service()
    fid = _create(service)["id"]
    with pytest.raises(FormValidationError):
        service.set_questions(fid, [QuestionInput(label="X", question_type="slider")])


def test_get_public_inactive_raises():
    service, repo, _ = _service()
    view = _create(service)
    service.deactivate(view["id"])
    token = repo.get_by_id(view["id"])["public_token"]
    with pytest.raises(FormNotFoundError):
        service.get_public(token)


def test_get_public_active_returns_questions():
    service, repo, _ = _service()
    view = _create(service)
    service.set_structure(
        view["id"], questions=[QuestionInput(label="Nota", question_type=QuestionType.RATING)]
    )
    token = repo.get_by_id(view["id"])["public_token"]
    public = service.get_public(token)
    assert public["title"] == "Pesquisa de visita"
    assert len(public["questions"]) == 1
    assert public["oneQuestionPerPage"] is False
    assert public["pages"] == []


def test_wizard_mode_creates_one_page_per_question():
    service, repo, _ = _service()
    view = _create(service)
    service.repository.update(view["id"], {"one_question_per_page": True})
    result = service.set_structure(
        view["id"],
        questions=[
            QuestionInput(label="P1", question_type=QuestionType.RATING),
            QuestionInput(label="P2", question_type=QuestionType.SHORT_TEXT),
        ],
    )
    assert result["oneQuestionPerPage"] is True
    assert len(result["pages"]) == 2
    assert len(result["questions"]) == 2
    assert result["questions"][0]["pageId"] == result["pages"][0]["id"]
    token = repo.get_by_id(view["id"])["public_token"]
    public = service.get_public(token)
    assert public["oneQuestionPerPage"] is True
    assert len(public["pages"]) == 2


def test_delete_removes_qr_and_row():
    service, repo, qr = _service()
    view = _create(service)
    service.delete(view["id"])
    assert repo.deleted == [view["id"]]
    assert qr.deleted  # qr removido


def test_delete_unknown_raises():
    service, _, _ = _service()
    with pytest.raises(FormNotFoundError):
        service.delete("nope")


class FakeImageStorage:
    def __init__(self) -> None:
        self.deleted: list[str | None] = []

    def save(self, *, content: bytes, mime_type: str | None) -> tuple[str, str]:
        return ("saved.jpg", mime_type or "image/jpeg")

    def delete(self, filename: str | None) -> None:
        self.deleted.append(filename)

    def read(self, filename: str) -> bytes:
        return b"img"


def test_remove_page_and_question_images():
    repo = FakeFormRepository()
    storage = FakeImageStorage()
    service = FormService(repository=repo, qr_service=FakeQr(), image_storage=storage)
    view = _create(service)
    fid = view["id"]
    page_id = str(uuid.uuid4())
    question_id = str(uuid.uuid4())
    repo.pages[fid] = [
        {
            "id": page_id,
            "form_id": fid,
            "position": 0,
            "title": "Etapa",
            "background_image_filename": "page-bg.jpg",
            "point_image_filename": "page-point.jpg",
        }
    ]
    repo.questions[fid] = [
        {
            "id": question_id,
            "form_id": fid,
            "page_id": page_id,
            "position": 0,
            "question_type": "rating",
            "label": "Nota",
            "help_text": None,
            "is_required": True,
            "options": [],
            "point_image_filename": "q-point.jpg",
            "is_active": True,
        }
    ]

    service.remove_page_background(fid, page_id)
    service.remove_page_point_image(fid, page_id)
    service.remove_question_point_image(fid, question_id)

    page = repo.pages[fid][0]
    question = repo.questions[fid][0]
    assert page["background_image_filename"] is None
    assert page["point_image_filename"] is None
    assert question["point_image_filename"] is None
    assert "page-bg.jpg" in storage.deleted
    assert "page-point.jpg" in storage.deleted
    assert "q-point.jpg" in storage.deleted
