"""B4 — MDD export/import via the six semantic verbs.

read.*.export_mdd (bounded inline JSON artifact) and
execute.*.import_preview/import_apply (canonical services;
playlist apply consumes the preview's single-use importToken).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from test_vista_mcp_write_surface import (
    _ctx,
    _editor,
    _governed_dispatch,
    _viewer,
)
from tv_app.interface.mcp import tool_bridge
from tv_app.interface.mcp.constants import MCP_TOOL_NAMES

DECK = (
    "tv_app.application.services.tv_deck_package_service."
    "TvDeckPackageService"
)
TPL = (
    "tv_app.application.services.slide_template_library_service."
    "SlideTemplateLibraryService"
)


def test_surface_still_six_tools():
    assert MCP_TOOL_NAMES == (
        "get_context", "read", "analyze", "knowledge", "execute", "delete")


# ---------------------------------------------------------------------------
# export_mdd
# ---------------------------------------------------------------------------


def test_export_playlist_mdd():
    dispatch, _, _ = _governed_dispatch()
    pid = str(uuid4())
    svc = MagicMock()
    svc.export_package.return_value = (
        b'{"format":"mdd","stats":{}}', "deck.mdd")
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(DECK, return_value=svc):
        r = tool_bridge.tool_read(
            entity="playlist", action="export_mdd", ref=pid)
    assert r.is_error is False
    data = r.structured_content["data"]
    assert data["filename"] == "deck.mdd"
    assert data["mdd"]["format"] == "mdd"


def test_export_template_mdd():
    dispatch, _, _ = _governed_dispatch()
    tid = str(uuid4())
    svc = MagicMock()
    svc.export_mdd.return_value = (
        b'{"format":"mdd-tpl","key":"t"}', "tpl.mdd")
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(TPL, return_value=svc):
        r = tool_bridge.tool_read(
            entity="slide_template", action="export_mdd", ref=tid)
    assert r.is_error is False
    assert r.structured_content["data"]["filename"] == "tpl.mdd"


def test_export_requires_ref():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_read(entity="playlist", action="export_mdd")
    assert r.is_error is True
    assert r.structured_content["code"] == "ARGUMENT_VALIDATION"


# ---------------------------------------------------------------------------
# playlist import
# ---------------------------------------------------------------------------


def test_playlist_import_preview_no_persist():
    dispatch, _, _ = _governed_dispatch()
    svc = MagicMock()
    svc.preview_import.return_value = {
        "valid": True, "importToken": "tok-1", "stats": {}}
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(DECK, return_value=svc):
        r = tool_bridge.tool_execute(
            entity="playlist", action="import_preview",
            operations=[{"mdd": {"format": "mdd"}}])
    assert r.is_error is False
    data = r.structured_content["data"]
    assert data["status"] == "PREVIEW_ONLY"
    assert data["persisted"] is False
    assert data["summary"]["importToken"] == "tok-1"
    assert not svc.apply_import.called


def test_playlist_import_apply_uses_token():
    dispatch, _, _ = _governed_dispatch()
    svc = MagicMock()
    svc.apply_import.return_value = {"id": "p1", "name": "Importada"}
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(DECK, return_value=svc):
        r = tool_bridge.tool_execute(
            entity="playlist", action="import_apply",
            operations=[{"importToken": "tok-1",
                         "nameOverride": "Novo nome"}])
    assert r.is_error is False
    assert r.structured_content["data"]["status"] == "VERIFIED"
    kw = svc.apply_import.call_args.kwargs
    assert kw["import_token"] == "tok-1"
    assert kw["name_override"] == "Novo nome"
    assert kw["created_by"]


def test_playlist_import_apply_requires_token():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_execute(
            entity="playlist", action="import_apply",
            operations=[{}])
    assert r.is_error is True
    assert r.structured_content["code"] == "ARGUMENT_VALIDATION"


def test_playlist_import_denied_for_viewer():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_execute(
            entity="playlist", action="import_preview",
            operations=[{"mdd": {}}])
    assert r.is_error is True
    assert r.structured_content["httpStatus"] == 403


def test_import_oversized_mdd_rejected():
    dispatch, _, _ = _governed_dispatch()
    big = {"pad": "x" * (600 * 1024)}
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_execute(
            entity="playlist", action="import_preview",
            operations=[{"mdd": big}])
    assert r.is_error is True
    assert r.structured_content["code"] == "ARGUMENT_VALIDATION"


# ---------------------------------------------------------------------------
# template import
# ---------------------------------------------------------------------------


def _manager():
    u = _editor()
    u.permissions = [
        "tv-dashboard.read", "tv-dashboard.write",
        "tv-dashboard.templates.manage",
    ]
    return u


def test_template_import_preview():
    dispatch, _, _ = _governed_dispatch()
    svc = MagicMock()
    svc.import_preview.return_value = {"label": "T", "nativeConfig": {}}
    with _ctx(_manager()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(TPL, return_value=svc):
        r = tool_bridge.tool_execute(
            entity="slide_template", action="import_preview",
            operations=[{"mdd": {"label": "T"}}])
    assert r.is_error is False
    assert r.structured_content["data"]["status"] == "PREVIEW_ONLY"


def test_template_import_apply():
    dispatch, _, _ = _governed_dispatch()
    svc = MagicMock()
    svc.import_apply.return_value = {"id": "t1", "status": "draft"}
    with _ctx(_manager()), patch.object(tool_bridge, "_dispatch", dispatch), \
            patch(TPL, return_value=svc):
        r = tool_bridge.tool_execute(
            entity="slide_template", action="import_apply",
            operations=[{"mdd": {"label": "T"}, "publishNow": False}])
    assert r.is_error is False
    assert r.structured_content["data"]["status"] == "VERIFIED"
    kw = svc.import_apply.call_args.kwargs
    assert kw["publish_now"] is False


def test_template_import_denied_without_manage():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        r = tool_bridge.tool_execute(
            entity="slide_template", action="import_preview",
            operations=[{"mdd": {}}])
    assert r.is_error is True
    assert r.structured_content["httpStatus"] == 403
