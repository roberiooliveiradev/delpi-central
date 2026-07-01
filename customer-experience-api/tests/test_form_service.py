from __future__ import annotations

import uuid

import pytest

from cx_app.application.services.form_service import (
    FormNotFoundError,
    FormService,
    FormValidationError,
)
from cx_app.domain.form import FormInput, FormUpdate, QuestionInput, QuestionType


class FakeFormRepository:
    def __init__(self) -> None:
        self.forms: dict[str, dict] = {}
        self.questions: dict[str, list[dict]] = {}
        self.deleted: list[str] = []

    def create(self, data: dict) -> dict:
        fid = str(uuid.uuid4())
        row = {
            "id": fid,
            "is_active": True,
            "response_count": 0,
            "created_at": "2026-07-01T12:00:00Z",
            "updated_at": "2026-07-01T12:00:00Z",
            **data,
        }
        self.forms[fid] = row
        self.questions[fid] = []
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

    def replace_questions(self, form_id: str, questions: list[dict]):
        stored = []
        for pos, q in enumerate(questions):
            stored.append(
                {
                    "id": q.get("id") or str(uuid.uuid4()),
                    "form_id": form_id,
                    "position": pos,
                    "question_type": q["question_type"],
                    "label": q["label"],
                    "help_text": q.get("help_text"),
                    "is_required": q.get("is_required", False),
                    "options": q.get("options") or [],
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
    service.set_questions(
        view["id"], [QuestionInput(label="Nota", question_type=QuestionType.RATING)]
    )
    token = repo.get_by_id(view["id"])["public_token"]
    public = service.get_public(token)
    assert public["title"] == "Pesquisa de visita"
    assert len(public["questions"]) == 1


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
