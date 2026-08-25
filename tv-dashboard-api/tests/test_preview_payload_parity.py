"""preview-payload ?parity=tv usa enrich como /present (sem JWT no build_by_id)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import Request

from tv_app.interface.http.routes import playlist_routes


def test_preview_payload_parity_tv_clears_auth_for_enrich():
    playlist_id = uuid4()
    user = object()
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer editor-token"}
    request.query_params = MagicMock()
    request.query_params.multi_items.return_value = []

    with (
        patch.object(
            playlist_routes,
            "require_playlist_access",
            return_value=(user, MagicMock()),
        ),
        patch.object(playlist_routes, "is_access_error", return_value=False),
        patch.object(playlist_routes, "parse_filter_overrides_query", return_value=None),
        patch.object(playlist_routes, "_present") as present,
        patch.object(playlist_routes, "ok", side_effect=lambda payload: payload),
    ):
        present.build_by_id.return_value = {"playlist": {"id": str(playlist_id)}}
        result = playlist_routes.preview_payload(
            request,
            playlist_id,
            filters=None,
            parity="tv",
        )

    present.build_by_id.assert_called_once_with(
        playlist_id,
        authorization=None,
        user=None,
        filter_overrides=None,
    )
    assert result["playlist"]["id"] == str(playlist_id)


def test_preview_payload_without_parity_keeps_jwt_user():
    playlist_id = uuid4()
    user = object()
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer editor-token"}
    request.query_params = MagicMock()
    request.query_params.multi_items.return_value = []

    with (
        patch.object(
            playlist_routes,
            "require_playlist_access",
            return_value=(user, MagicMock()),
        ),
        patch.object(playlist_routes, "is_access_error", return_value=False),
        patch.object(playlist_routes, "parse_filter_overrides_query", return_value=None),
        patch.object(playlist_routes, "_present") as present,
        patch.object(playlist_routes, "ok", side_effect=lambda payload: payload),
    ):
        present.build_by_id.return_value = {"ok": True}
        playlist_routes.preview_payload(request, playlist_id, filters=None, parity=None)

    present.build_by_id.assert_called_once_with(
        playlist_id,
        authorization="Bearer editor-token",
        user=user,
        filter_overrides=None,
    )
