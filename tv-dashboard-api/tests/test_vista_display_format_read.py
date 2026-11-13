"""display_format read-only catalog — INT-1 P3 owner extension.

Governed TV_READ projection over the canonical format services:
``DisplayFormatService.format_catalog_entries()`` (value display
formats), ``PresentationOpsContentService.block_type_vocabulary()``
(canonical block vocabulary) and the display-mode catalog
(``tv_data_presentation_modes_service``). Never a second registry —
the projection derives entirely from owner canonical sources, and it
never exposes the TV_WRITE administrative ``get_catalog()`` document.

Positive/sibling/negative coverage only.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tv_app.application.gpt_actions.capability_surface import (
    READ_ENTITY_ACTIONS,
    READ_ENTITY_STATUS,
    build_capability_surface,
)
from tv_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
)
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.services.data.display_format_service import (
    DisplayFormatService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
)


def _admin():
    return SimpleNamespace(
        is_superadmin=True, permissions=[], id="actor-1",
        principal_type="user",
    )


def _viewer():
    return SimpleNamespace(
        is_superadmin=False, permissions=["tv-dashboard.read"],
        id="viewer-1", principal_type="user",
    )


def _no_perms():
    return SimpleNamespace(
        is_superadmin=False, permissions=[], id="noperm-1",
        principal_type="user",
    )


def _dispatch() -> GptActionsDispatchService:
    return GptActionsDispatchService(
        repo=MagicMock(), writes=MagicMock(), commit=MagicMock()
    )


def test_read_vocab_declares_display_format_list():
    assert READ_ENTITY_ACTIONS["display_format"] == ("list",)
    assert READ_ENTITY_STATUS["display_format"] == "proven"


def test_read_display_format_list_returns_canonical_projection():
    out = _dispatch().semantic_read(
        user=_viewer(), entity="display_format", action="list"
    )
    # Canonical value-display formats — same source as the admin
    # displayFormatCatalog, projected without admin-only fields.
    expected = DisplayFormatService.format_catalog_entries()
    formats = out["displayFormats"]
    assert len(formats) == len(expected)
    for projected, entry in zip(formats, expected):
        assert projected["formatId"] == entry["formatId"]
        assert projected["category"] == entry["category"]
        assert projected["compatibleTypes"] == list(
            entry["compatibleTypes"]
        )
    # Canonical block-type vocabulary — projected, not duplicated.
    assert out["blockTypeVocabulary"] == (
        PresentationOpsContentService.block_type_vocabulary()
    )
    # Display modes with their declared data-block bindings.
    modes = out["displayModes"]
    for mode in ("kpi", "line_chart", "bar_chart", "table", "auto"):
        assert mode in modes["modes"]
    assert modes["blockTypeByMode"]["kpi"] == "data_kpi"
    assert modes["blockTypeByMode"]["table"] == "data_table"
    # Data block categories from the canonical route catalog service.
    for t in ("data_kpi", "data_chart", "data_table"):
        assert t in out["dataBlockTypes"]
    for t in ("chart_view", "table_view", "kpi_view"):
        assert t in out["dataViewBlockTypes"]


def test_read_display_format_list_denied_without_read():
    with pytest.raises(PermissionError):
        _dispatch().semantic_read(
            user=_no_perms(), entity="display_format", action="list"
        )


def test_read_display_format_unknown_action_typed():
    with pytest.raises(GptActionsError) as exc:
        _dispatch().semantic_read(
            user=_viewer(), entity="display_format", action="mutate"
        )
    assert exc.value.code == "UNKNOWN_ACTION"


def test_read_display_format_rejects_undeclared_filters():
    with pytest.raises(GptActionsError) as exc:
        _dispatch().semantic_read(
            user=_viewer(), entity="display_format", action="list",
            filters={"secret": "x"},
        )
    assert exc.value.code == "VALIDATION_ERROR"


def test_read_display_format_never_persists():
    writes = MagicMock()
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    dispatch.semantic_read(
        user=_viewer(), entity="display_format", action="list"
    )
    writes.assert_not_called()


def test_display_format_list_does_not_expose_admin_catalog():
    """The READ projection must not leak the TV_WRITE admin document:
    no operations surface, no capability_surface, no product guide —
    only the read-scoped format vocabulary."""
    out = _dispatch().semantic_read(
        user=_admin(), entity="display_format", action="list"
    )
    for admin_key in (
        "operations", "capability_surface", "productGuide",
        "confirmationModel",
    ):
        assert admin_key not in out


def test_admin_catalog_still_requires_write_after_read_extension():
    """Sibling guard: extending the READ surface must not weaken the
    existing TV_WRITE gate on the administrative catalog."""
    with pytest.raises(PermissionError):
        _dispatch().semantic_get_context(
            user=_viewer(), action="catalog"
        )
    out = _dispatch().semantic_get_context(user=_admin(), action="catalog")
    assert "displayFormatCatalog" in out


def test_get_context_reports_display_format_capability_per_authz():
    out = _dispatch().semantic_get_context(user=_viewer())
    caps = {c["capability"]: c for c in out["effectiveCapabilities"]}
    assert caps["read.display_format.list"]["authorized"] is True
    assert caps["read.display_format.list"]["status"] == "proven"
    # No implicit grant: write capabilities stay denied for a reader.
    assert caps["execute.presentation.apply_mutation"]["authorized"] is False


def test_surface_read_entities_include_display_format():
    verbs = build_capability_surface(transport="mcp")["semantic_verbs"]
    entities = verbs["tools"]["read"]["entities"]
    assert entities["display_format"]["actions"] == ["list"]
    assert entities["display_format"]["status"] == "proven"
