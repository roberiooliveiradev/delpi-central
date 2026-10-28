from __future__ import annotations

from datetime import date

import pytest

from cx_app.application.services.participant_service import (
    ParticipantNotFoundError,
    ParticipantService,
)
from cx_app.domain.participant import ParticipantInput, ParticipantUpdate


class FakeRepository:
    def __init__(self, rows: dict | None = None) -> None:
        self.rows: dict[str, dict] = rows or {}
        self.deleted: list[str] = []

    def create(self, data: dict) -> dict:
        row = {
            "id": "p1",
            "view_count": 0,
            "is_active": True,
            "created_at": "2026-07-01T12:00:00Z",
            "updated_at": "2026-07-01T12:00:00Z",
            **data,
        }
        self.rows[row["id"]] = row
        return row

    def get_by_id(self, participant_id: str):
        row = self.rows.get(participant_id)
        # espelha o repositório real: cada leitura é um snapshot independente
        return dict(row) if row is not None else None

    def update(self, participant_id: str, fields: dict):
        row = self.rows.get(participant_id)
        if not row:
            return None
        row.update(fields)
        return dict(row)

    def set_active(self, participant_id: str, is_active: bool):
        return self.update(participant_id, {"is_active": is_active})

    def delete(self, participant_id: str) -> bool:
        if participant_id in self.rows:
            del self.rows[participant_id]
            self.deleted.append(participant_id)
            return True
        return False


class FakePhotoStorage:
    def __init__(self) -> None:
        self.saved: list[bytes] = []
        self.deleted: list[str | None] = []

    def save(self, *, content: bytes, mime_type: str | None):
        self.saved.append(content)
        return f"photo-{len(self.saved)}.jpg", "image/jpeg"

    def delete(self, filename: str | None) -> None:
        self.deleted.append(filename)


class FakeQrService:
    def __init__(self) -> None:
        self.deleted: list[str | None] = []

    def generate(self, *, token: str) -> str:
        return f"{token}.png"

    def delete(self, filename: str | None) -> None:
        self.deleted.append(filename)


def _service(rows: dict | None = None):
    repo = FakeRepository(rows)
    photo = FakePhotoStorage()
    qr = FakeQrService()
    service = ParticipantService(repository=repo, photo_storage=photo, qr_service=qr)
    return service, repo, photo, qr


def _existing_row() -> dict:
    return {
        "p1": {
            "id": "p1",
            "public_token": "tok",
            "full_name": "Ana Souza",
            "company_name": "Transforma+",
            "visit_date": date(2026, 7, 1),
            "participant_info": None,
            "thank_you_message": None,
            "photo_filename": "old-photo.jpg",
            "photo_mime": "image/jpeg",
            "qr_filename": "tok.png",
            "is_active": True,
            "view_count": 3,
            "created_at": "2026-07-01T12:00:00Z",
            "updated_at": "2026-07-01T12:00:00Z",
        }
    }


def test_create_generates_qr_code_and_saves_photo():
    service, repo, photo, _ = _service()
    view = service.create(
        ParticipantInput(
            full_name="Ana Souza",
            company_name="Transforma+",
            visit_date=date(2026, 7, 1),
            participant_info=None,
            thank_you_message=None,
        ),
        photo_bytes=b"img",
        photo_mime="image/jpeg",
        created_by="sub-1",
        created_by_name="Admin",
    )
    assert view["fullName"] == "Ana Souza"
    assert view["isActive"] is True
    assert len(photo.saved) == 1
    stored = repo.rows["p1"]
    assert stored["qr_filename"].endswith(".png")


def test_update_changes_fields_and_replaces_photo():
    service, _, photo, _ = _service(_existing_row())
    view = service.update(
        "p1",
        ParticipantUpdate(
            full_name="Ana Paula Souza",
            company_name=None,
            visit_date=None,
            participant_info="Engenharia",
            thank_you_message=None,
        ),
        photo_bytes=b"new-img",
        photo_mime="image/png",
    )
    assert view["fullName"] == "Ana Paula Souza"
    assert view["participantInfo"] == "Engenharia"
    # foto antiga removida após persistir a nova
    assert "old-photo.jpg" in photo.deleted


def test_update_unknown_raises_not_found():
    service, _, _, _ = _service()
    with pytest.raises(ParticipantNotFoundError):
        service.update("nope", ParticipantUpdate(full_name="X"))


def test_deactivate_and_activate_toggle_is_active():
    service, _, _, _ = _service(_existing_row())
    assert service.deactivate("p1")["isActive"] is False
    assert service.activate("p1")["isActive"] is True


def test_activate_unknown_raises_not_found():
    service, _, _, _ = _service()
    with pytest.raises(ParticipantNotFoundError):
        service.activate("nope")


def test_delete_removes_row_photo_and_qr_files():
    service, repo, photo, qr = _service(_existing_row())
    service.delete("p1")
    assert repo.deleted == ["p1"]
    assert "p1" not in repo.rows
    assert "old-photo.jpg" in photo.deleted
    assert "tok.png" in qr.deleted


def test_delete_unknown_raises_not_found():
    service, _, _, _ = _service()
    with pytest.raises(ParticipantNotFoundError):
        service.delete("nope")


def test_update_clears_optional_fields_with_empty_value():
    service, repo, _, _ = _service(_existing_row())
    repo.rows["p1"]["participant_info"] = "Engenharia"
    repo.rows["p1"]["thank_you_message"] = "Obrigado!"
    view = service.update(
        "p1",
        ParticipantUpdate(participant_info="", thank_you_message="  "),
    )
    assert view["participantInfo"] is None
    assert view["thankYouMessage"] is None
    # campos omitidos permanecem
    assert view["fullName"] == "Ana Souza"


def test_update_remove_photo_deletes_file_and_nulls_fields():
    service, repo, photo, _ = _service(_existing_row())
    view = service.update("p1", ParticipantUpdate(), remove_photo=True)
    assert view["photoUrl"] is None
    stored = repo.rows["p1"]
    assert stored["photo_filename"] is None
    assert stored["photo_mime"] is None
    assert "old-photo.jpg" in photo.deleted


def test_update_remove_photo_keeps_other_fields():
    service, repo, _, _ = _service(_existing_row())
    service.update(
        "p1",
        ParticipantUpdate(full_name="Ana Paula"),
        remove_photo=True,
    )
    stored = repo.rows["p1"]
    assert stored["full_name"] == "Ana Paula"
    assert stored["photo_filename"] is None


def test_update_replaces_photo_and_versions_photo_url():
    service, repo, photo, _ = _service(_existing_row())
    before = service.get_admin("p1")["photoUrl"]
    view = service.update(
        "p1", ParticipantUpdate(), photo_bytes=b"new", photo_mime="image/png"
    )
    after = view["photoUrl"]
    assert before != after
    assert "old-photo.jpg" in photo.deleted
    # nova URL carrega o nome do novo arquivo — cache antigo não colide
    stored = repo.rows["p1"]
    assert stored["photo_filename"] in after


def test_update_never_changes_public_token_or_qr():
    service, repo, _, _ = _service(_existing_row())
    token_before = repo.rows["p1"]["public_token"]
    qr_before = repo.rows["p1"]["qr_filename"]
    view = service.update(
        "p1",
        ParticipantUpdate(
            full_name="Novo Nome",
            company_name="Outra Empresa",
            visit_date=date(2026, 8, 15),
            participant_info="Nova info",
            thank_you_message="Nova msg",
        ),
        photo_bytes=b"img",
        photo_mime="image/jpeg",
    )
    assert view["publicToken"] == token_before
    assert repo.rows["p1"]["qr_filename"] == qr_before


def test_public_view_photo_url_none_without_photo():
    service, repo, _, _ = _service(_existing_row())
    repo.rows["p1"]["photo_filename"] = None

    class _Repo(repo.__class__):
        def get_by_token(self, token):
            return dict(self.rows["p1"])

        def increment_view_count(self, token):
            pass

    service2 = ParticipantService(
        repository=_Repo(repo.rows), photo_storage=service.photo_storage,
        qr_service=service.qr_service,
    )
    public = service2.get_public("tok")
    assert public["photoUrl"] is None


def test_remove_photo_flag_without_existing_photo_is_noop():
    service, repo, photo, _ = _service(_existing_row())
    repo.rows["p1"]["photo_filename"] = None
    view = service.update("p1", ParticipantUpdate(), remove_photo=True)
    assert view["photoUrl"] is None
    assert photo.deleted == []
