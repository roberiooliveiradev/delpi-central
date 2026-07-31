"""Permissões HTTP da biblioteca de templates."""

from __future__ import annotations

from types import SimpleNamespace

from tv_app.core.security import TV_READ, TV_TEMPLATES_MANAGE, TV_WRITE, can
from tv_app.interface.http.routes import template_routes


class FakeUser:
    def __init__(self, permissions: list[str], *, is_superadmin: bool = False):
        self.permissions = permissions
        self.is_superadmin = is_superadmin
        self.id = "user-1"


class FakeRequest:
    def __init__(self, user: FakeUser | None):
        self.state = SimpleNamespace(user=user)


def test_can_templates_manage():
    assert can(FakeUser([TV_TEMPLATES_MANAGE]), TV_TEMPLATES_MANAGE)
    assert not can(FakeUser([TV_WRITE]), TV_TEMPLATES_MANAGE)
    assert can(FakeUser([], is_superadmin=True), TV_TEMPLATES_MANAGE)


def test_list_published_allows_read(monkeypatch):
    monkeypatch.setattr(
        template_routes._service,
        "list_published",
        lambda: [{"id": "1", "status": "published", "label": "A"}],
    )
    response = template_routes.list_slide_templates(
        FakeRequest(FakeUser([TV_READ])),
        status="published",
    )
    body = response.body.decode("utf-8")
    assert '"success":true' in body.replace(" ", "")
    assert "published" in body


def test_list_library_requires_manage():
    response = template_routes.list_slide_templates(
        FakeRequest(FakeUser([TV_WRITE])),
        status=None,
    )
    assert response.status_code == 403


def test_create_requires_manage():
    response = template_routes.create_slide_template(
        FakeRequest(FakeUser([TV_WRITE])),
        template_routes.CreateTemplateBody(
            label="X",
            nativeConfig={"version": 4, "blocks": []},
        ),
    )
    assert response.status_code == 403
