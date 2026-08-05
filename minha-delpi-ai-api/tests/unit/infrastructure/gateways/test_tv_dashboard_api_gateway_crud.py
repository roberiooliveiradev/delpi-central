"""Testes do allowlist e If-Match em execute_crud_command."""

from __future__ import annotations

import pytest

from app.infrastructure.gateways.tv_dashboard_api_gateway import TvDashboardApiGateway


class _FakeResponse:
    def __init__(
        self,
        payload,
        *,
        status_code: int = 200,
        headers: dict | None = None,
        ok: bool | None = None,
    ):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}
        self.ok = (status_code < 400) if ok is None else ok
        self.text = ""

    def json(self):
        return self._payload


def test_execute_crud_rejects_path_outside_playlists():
    gateway = TvDashboardApiGateway(base_url="http://tv.test")
    with pytest.raises(ValueError, match="outside /playlists"):
        gateway.execute_crud_command(
            {"method": "GET", "path": "/evil"},
            access_token="tok",
        )


def test_execute_crud_rejects_absolute_url():
    gateway = TvDashboardApiGateway(base_url="http://tv.test")
    with pytest.raises(ValueError, match="relative"):
        gateway.execute_crud_command(
            {"method": "PATCH", "path": "http://evil.example/playlists/x"},
            access_token="tok",
        )


def test_execute_crud_rejects_path_traversal():
    gateway = TvDashboardApiGateway(base_url="http://tv.test")
    with pytest.raises(ValueError, match="traversal"):
        gateway.execute_crud_command(
            {"method": "GET", "path": "/playlists/../admin"},
            access_token="tok",
        )


def test_execute_crud_rejects_disallowed_method():
    gateway = TvDashboardApiGateway(base_url="http://tv.test")
    with pytest.raises(ValueError, match="not allowlisted"):
        gateway.execute_crud_command(
            {"method": "PUT", "path": "/playlists/p1"},
            access_token="tok",
        )


def test_execute_crud_patch_sends_if_match(monkeypatch):
    gateway = TvDashboardApiGateway(base_url="http://tv.test", timeout=1.0)
    captured: dict = {}

    def fake_request(method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = kwargs.get("headers") or {}
        captured["json"] = kwargs.get("json")
        return _FakeResponse(
            {"ok": True, "data": {"id": "s1", "playlistRevision": 13}},
            status_code=200,
            headers={"X-Playlist-Revision": "13"},
        )

    monkeypatch.setattr(
        "app.infrastructure.gateways.tv_dashboard_api_gateway.requests.request",
        fake_request,
    )

    result = gateway.execute_crud_command(
        {
            "method": "PATCH",
            "path": "/playlists/p1/slides/s1",
            "body": {"title": "Hi"},
            "op": "update_slide",
            "requiresIfMatch": True,
            "expectedRevision": 12,
        },
        access_token="user-jwt",
        expected_revision=12,
    )

    assert captured["method"] == "PATCH"
    assert captured["url"] == "http://tv.test/playlists/p1/slides/s1"
    assert captured["headers"]["Authorization"] == "Bearer user-jwt"
    assert captured["headers"]["If-Match"] == '"12"'
    assert captured["json"] == {"title": "Hi"}
    assert result["_ok"] is True
    assert result["_httpStatus"] == 200
    assert result["playlistRevision"] == 13


def test_execute_crud_skips_if_match_when_not_required(monkeypatch):
    gateway = TvDashboardApiGateway(base_url="http://tv.test")
    captured: dict = {}

    def fake_request(method, url, **kwargs):
        captured["headers"] = kwargs.get("headers") or {}
        return _FakeResponse({"ok": True, "data": {"id": "p-new"}}, status_code=201)

    monkeypatch.setattr(
        "app.infrastructure.gateways.tv_dashboard_api_gateway.requests.request",
        fake_request,
    )

    gateway.execute_crud_command(
        {
            "method": "POST",
            "path": "/playlists",
            "body": {"name": "Nova"},
            "op": "create_playlist",
            "requiresIfMatch": False,
        },
        access_token="tok",
        expected_revision=5,
    )

    assert "If-Match" not in captured["headers"]


def test_execute_crud_reads_revision_from_header(monkeypatch):
    gateway = TvDashboardApiGateway(base_url="http://tv.test")

    def fake_request(method, url, **kwargs):
        return _FakeResponse(
            {"ok": True, "data": {"id": "s1"}},
            status_code=200,
            headers={"X-Playlist-Revision": "42"},
        )

    monkeypatch.setattr(
        "app.infrastructure.gateways.tv_dashboard_api_gateway.requests.request",
        fake_request,
    )

    result = gateway.execute_crud_command(
        {
            "method": "DELETE",
            "path": "/playlists/p1/slides/s1",
            "op": "delete_slide",
            "requiresIfMatch": True,
        },
        access_token="tok",
        expected_revision=41,
    )

    assert result["playlistRevision"] == 42
