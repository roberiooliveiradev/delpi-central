from __future__ import annotations

import io
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cx_app.interface.http.routes import participant_routes


class _User:
    is_superadmin = True


class _FakeService:
    """Captura os argumentos recebidos pelo service no PATCH."""

    def __init__(self) -> None:
        self.kwargs: dict = {}

    def update(self, participant_id, data, **kwargs):
        self.kwargs = {"id": participant_id, "data": data, **kwargs}
        return {"id": participant_id, "photoUrl": None}


@pytest.fixture()
def client(monkeypatch):
    service = _FakeService()
    monkeypatch.setattr(participant_routes, "resolve_user", lambda req: _User())
    monkeypatch.setattr(participant_routes, "assert_permission", lambda u, p: None)
    monkeypatch.setattr(
        participant_routes, "build_participant_service", lambda: service
    )
    app = FastAPI()
    app.include_router(participant_routes.router)
    return TestClient(app), service


def test_patch_omitted_fields_are_not_sent(client):
    tc, service = client
    r = tc.patch("/participants/p1", data={"full_name": "Ana"})
    assert r.status_code == 200
    data = service.kwargs["data"]
    assert data.full_name == "Ana"
    assert data.participant_info is None  # omitido = manter
    assert data.thank_you_message is None
    assert service.kwargs["remove_photo"] is False


def test_patch_empty_fields_mean_clear(client):
    tc, service = client
    r = tc.patch(
        "/participants/p1",
        data={"participant_info": "", "thank_you_message": ""},
    )
    assert r.status_code == 200
    data = service.kwargs["data"]
    assert data.participant_info == ""
    assert data.thank_you_message == ""


def test_patch_remove_photo_flag(client):
    tc, service = client
    r = tc.patch("/participants/p1", data={"remove_photo": "true"})
    assert r.status_code == 200
    assert service.kwargs["remove_photo"] is True
    assert service.kwargs["photo_bytes"] is None


def test_patch_photo_and_remove_photo_conflict(client):
    tc, _ = client
    r = tc.patch(
        "/participants/p1",
        data={"remove_photo": "true"},
        files={"photo": ("f.jpg", io.BytesIO(b"img"), "image/jpeg")},
    )
    assert r.status_code == 422


def test_patch_blank_required_field_rejected(client):
    tc, _ = client
    r = tc.patch("/participants/p1", data={"full_name": "   "})
    assert r.status_code == 422
    r = tc.patch("/participants/p1", data={"company_name": ""})
    assert r.status_code == 422


def test_patch_invalid_date_rejected(client):
    tc, _ = client
    r = tc.patch("/participants/p1", data={"visit_date": "28/10/2026"})
    assert r.status_code == 422


def test_patch_new_photo_passes_bytes_and_mime(client):
    tc, service = client
    r = tc.patch(
        "/participants/p1",
        files={"photo": ("f.png", io.BytesIO(b"png-bytes"), "image/png")},
    )
    assert r.status_code == 200
    assert service.kwargs["photo_bytes"] == b"png-bytes"
    assert service.kwargs["photo_mime"] == "image/png"
    assert service.kwargs["remove_photo"] is False
