"""OCC If-Match / X-Playlist-Revision."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import logging

from fastapi.responses import JSONResponse

from tv_app.application.errors.playlist_persistence import (
    PlaylistRevisionConflictError,
)
from tv_app.interface.http.playlist_revision_http import (
    assert_playlist_revision_or_conflict,
    parse_if_match_revision,
    playlist_revision_conflict_response,
    revision_response_headers,
    with_revision,
)

PLAYLIST_ID = UUID("00000000-0000-0000-0000-000000000001")


class _Repo:
    def __init__(self, revision: int = 5) -> None:
        self._revision = revision

    def get_revision(self, playlist_id):
        assert playlist_id == PLAYLIST_ID
        return self._revision


def test_parse_if_match_variants():
    def _req(value: str | None):
        headers = {}
        if value is not None:
            headers["If-Match"] = value
        return SimpleNamespace(headers=headers)

    assert parse_if_match_revision(_req(None)) is None
    assert parse_if_match_revision(_req("")) is None
    assert parse_if_match_revision(_req("12")) == 12
    assert parse_if_match_revision(_req('"12"')) == 12
    assert parse_if_match_revision(_req('W/"12"')) == 12
    assert parse_if_match_revision(_req("abc")) is None


def test_assert_allows_when_expected_matches_or_omitted():
    repo = _Repo(5)
    assert assert_playlist_revision_or_conflict(repo, PLAYLIST_ID, expected=None) == 5
    assert assert_playlist_revision_or_conflict(repo, PLAYLIST_ID, expected=5) == 5


def test_assert_returns_409_on_conflict():
    repo = _Repo(8)
    conflict = assert_playlist_revision_or_conflict(repo, PLAYLIST_ID, expected=5)
    assert isinstance(conflict, JSONResponse)
    assert conflict.status_code == 409


def test_revision_headers_and_payload():
    assert revision_response_headers(4) == {"X-Playlist-Revision": "4"}
    assert with_revision({"id": "s"}, 4)["playlistRevision"] == 4
    assert with_revision(None, 4) is None


def test_conflict_response_logs_rejection_with_context(caplog):
    """409 CAS deve registrar correlação segura (playlist/actor/client/op)."""
    exc = PlaylistRevisionConflictError(9, expected_revision=7)
    with caplog.at_level(logging.WARNING):
        response = playlist_revision_conflict_response(
            exc,
            expected=7,
            log_context={
                "playlistId": PLAYLIST_ID,
                "slideId": "slide-x",
                "requestId": "req-42",
                "actor": "actor-9",
                "clientId": "sess:ctx",
                "operation": "slide_duplicate",
            },
        )
    assert response.status_code == 409
    record = next(
        (entry for entry in caplog.records if "playlist_write_rejected" in entry.message),
        None,
    )
    assert record is not None
    message = record.getMessage()
    assert str(PLAYLIST_ID) in message
    assert "slide-x" in message
    assert "req-42" in message
    assert "actor-9" in message
    assert "sess:ctx" in message
    assert "slide_duplicate" in message
    assert "expected_revision=7" in message
    assert "current_revision=9" in message
    assert "result=revision_conflict" in message


def test_conflict_response_logs_without_context(caplog):
    """Sem contexto adicional o 409 ainda registra revisões (observabilidade base)."""
    exc = PlaylistRevisionConflictError(4, expected_revision=None)
    with caplog.at_level(logging.WARNING):
        playlist_revision_conflict_response(exc, expected=None)
    assert any("playlist_write_rejected" in entry.getMessage() for entry in caplog.records)
