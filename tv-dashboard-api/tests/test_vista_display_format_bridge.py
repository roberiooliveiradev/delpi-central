"""Typed VISTA format mutation and compact READ."""
from copy import deepcopy

import pytest

from tv_app.application.gpt_actions.response_compact import (
    GPT_ACTIONS_RESPONSE_MAX_BYTES, actions_response_sizes, project_block_index,
    project_block_index_item, project_editor_focus_context,
)
from tv_app.application.services.data.display_format_service import DisplayFormatService
from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchError, PresentationPatchService,
)
from tv_app.application.services.data.presentation_nested_contract import validate_operation_payload


def block():
    return {"id": "weg-es", "type": "text", "frame": {"x": 1, "y": 2, "w": 30, "h": 4},
            "style": {"fontSize": 28, "color": "red"}, "resolved": {"displayText": "stale"},
            "contentRuns": [{"text": "de "}, {"dataRef": {"field": "filter.start_date"}},
                            {"text": " até "}, {"dataRef": {"field": "filter.end_date", "format": "raw"}},
                            {"text": "!"}]}


def op(occurrence=None):
    target = {"owner": "contentRunDataRef", "field": "filter.end_date"}
    if occurrence is not None:
        target["occurrence"] = occurrence
    return {"op": "set_display_format", "blockId": "weg-es", "target": target,
            "displayFormat": {"category": "date", "presetId": "date-year", "locale": "pt-BR"}}


def test_mutation_preserves_other_properties():
    b = block()
    before = deepcopy(b)
    request = op()
    validate_operation_payload("set_display_format", request)
    PresentationPatchService.__new__(PresentationPatchService)._op_set_display_format({"blocks": [b]}, request)
    before.pop("resolved")
    before["contentRuns"][3]["dataRef"]["displayFormat"] = request["displayFormat"]
    assert b == before
    assert project_block_index_item(b)["formatBindings"][1]["displayFormat"] == request["displayFormat"]


def test_ambiguous_target_fails_closed():
    b = block()
    b["contentRuns"].insert(4, {"dataRef": {"field": "filter.end_date"}})
    svc = PresentationPatchService.__new__(PresentationPatchService)
    with pytest.raises(PresentationPatchError) as caught:
        svc._op_set_display_format({"blocks": [b]}, op())
    assert caught.value.code == "DISPLAY_FORMAT_TARGET_AMBIGUOUS"
    assert "displayFormat" not in b["contentRuns"][3]["dataRef"]
    svc._op_set_display_format({"blocks": [b]}, op(1))
    assert "displayFormat" not in b["contentRuns"][3]["dataRef"]
    assert b["contentRuns"][4]["dataRef"]["displayFormat"]["presetId"] == "date-year"


def test_text_projection_and_invalid_preset():
    b = {"id": "weg-es", "type": "text", "textProjection": {"field": "filter.end_date"}}
    request = op()
    request["target"]["owner"] = "textProjection"
    svc = PresentationPatchService.__new__(PresentationPatchService)
    svc._op_set_display_format({"blocks": [b]}, request)
    assert b["textProjection"]["displayFormat"] == request["displayFormat"]
    request["displayFormat"]["presetId"] = "bogus"
    with pytest.raises(PresentationPatchError) as caught:
        svc._op_set_display_format({"blocks": [b]}, request)
    assert caught.value.code == "DISPLAY_FORMAT_INVALID"


@pytest.mark.parametrize("preset,expected", [
    ("date-short", "24/09/2026"), ("date-short-yy", "24/09/26"),
    ("date-month-year", "09/2026"), ("date-month-year-yy", "09/26"),
    ("date-month-abbrev-year", "set./2026"), ("date-month-full-year", "setembro/2026"),
    ("date-year", "2026"), ("date-iso", "2026-09-24"),
])
def test_date_matrix(preset, expected):
    spec = DisplayFormatService.validate_write_spec(DisplayFormatService.spec_from_preset_id(preset))
    assert DisplayFormatService.format_value("2026-09-24", spec) == expected


@pytest.mark.parametrize("preset", ["number-2", "currency-brl", "percent", "scientific"])
def test_numeric_matrix(preset):
    spec = DisplayFormatService.validate_write_spec(DisplayFormatService.spec_from_preset_id(preset))
    assert DisplayFormatService.format_value(1234.5, spec)


def test_compact_70_block_budget():
    base = block()
    base.pop("resolved")
    cfg = {"blocks": [{**deepcopy(base), "id": f"weg-{i}"} for i in range(70)]}
    index = project_block_index(cfg, slide_id="s1", revision=1)
    assert index["total"] == 70
    assert all(len(row["formatBindings"]) == 2 for row in index["items"])
    payload = project_editor_focus_context(
        playlist={"id": "p1", "name": "WEG"}, slides_index=[{"id": "s1", "title": "WEG"}],
        detail_slide={"id": "s1", "title": "WEG", "nativeConfig": cfg},
        data_sources=[], selected_data_source_id=None, sections=[],
        access_role="owner", revision=1, block_index=index,
    )
    assert payload["blockIndex"]["returned"] == 70
    assert max(actions_response_sizes(payload).values()) < GPT_ACTIONS_RESPONSE_MAX_BYTES


def test_commit_postcondition_requires_persisted_and_materialized_format():
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch
    from uuid import uuid4
    from tv_app.application.gpt_actions.commit_service import TvGptCommitService

    b = block()
    request = op()
    PresentationPatchService.__new__(PresentationPatchService)._op_set_display_format({"blocks": [b]}, request)
    persisted = {"version": 5, "blocks": [b]}
    pid, sid = uuid4(), uuid4()
    writes = MagicMock()
    writes.list_slides.return_value = [{"id": str(sid), "nativeConfig": persisted}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": str(pid), "dataDefaults": {}}
    service = TvGptCommitService(writes=writes, idempotency=MagicMock())
    applied = [{"op": "native_config_batch", "slideId": str(sid), "expected": {"nativeConfig": persisted}}]

    def enriched(display):
        item = deepcopy(b)
        item["resolved"] = {"contextValues": {"filter.end_date": "2026-09-24"},
                            "displayRuns": [{"text": "de "}, {"text": "2026"},
                                            {"text": " até "}, {"text": display}, {"text": "!"}],
                            "displayText": f"de 2026 até {display}!"}
        return [item]

    with (patch("tv_app.application.services.data.slide_data_resolution_service.SlideDataResolutionService.resolve_blocks", return_value=enriched("2026")),
          patch("tv_app.application.services.data.ready_slide_quality_service.ReadySlideQualityService.collect_native_quality_issues", return_value=[]),
          patch("tv_app.application.services.data.slide_layout_quality_service.SlideLayoutQualityService.collect_native_layout_issues", return_value=[])):
        ok, details = service._verify_postcondition(current_playlist=pid, applied=applied,
                                                    expected_native=persisted, ops=[request], user=SimpleNamespace(id="u1"))
    assert ok
    assert any(c.get("reason") == "materialized_display" for c in details["checks"])

    with (patch("tv_app.application.services.data.slide_data_resolution_service.SlideDataResolutionService.resolve_blocks", return_value=enriched("2026-09-24")),
          patch("tv_app.application.services.data.ready_slide_quality_service.ReadySlideQualityService.collect_native_quality_issues", return_value=[]),
          patch("tv_app.application.services.data.slide_layout_quality_service.SlideLayoutQualityService.collect_native_layout_issues", return_value=[])):
        ok, details = service._verify_postcondition(current_playlist=pid, applied=applied,
                                                    expected_native=persisted, ops=[request], user=SimpleNamespace(id="u1"))
    assert not ok
    assert details["reason"] == "DISPLAY_FORMAT_NOT_MATERIALIZED"


def test_presentation_mutation_preview_uses_existing_block_and_typed_catalog():
    from types import SimpleNamespace
    from uuid import uuid4
    from tv_app.application.services.data.presentation_ops_content_service import PresentationOpsContentService

    pid, sid = str(uuid4()), str(uuid4())
    original = block()
    original.pop("resolved")

    class Repo:
        def get_by_id(self, playlist_id):
            return {"id": str(playlist_id), "revision": 1, "dataDefaults": {}}

        def get_slide(self, slide_id, playlist_id=None):
            return {"id": str(slide_id), "nativeConfig": {"version": 5, "blocks": [deepcopy(original)]}}

    result = PresentationPatchService(repo=Repo()).preview(
        {"target": {"playlistId": pid, "slideId": sid}, "ops": [op()],
         "catalogVersion": PresentationOpsContentService.catalog_version()},
        user=SimpleNamespace(is_superadmin=True, permissions=[], id="u1"),
        include_fingerprint=False,
    )
    blocks = result["nativeConfig"]["blocks"]
    assert len(blocks) == 1
    assert blocks[0]["id"] == "weg-es"
    assert blocks[0]["contentRuns"][3]["dataRef"]["displayFormat"]["presetId"] == "date-year"


@pytest.mark.parametrize("preset,raw_value,expected", [
    ("date-year", "2026-09-24", "2026"),
    ("date-month-year", "2026-09-24", "09/2026"),
    ("date-month-abbrev-year", "2026-09-24", "set./2026"),
    ("number-2", 1234.5, "1234,50"),
    ("currency-brl", 1234.5, "R$\u00a01.234,50"),
    ("percent", 12.5, "12,5%"),
])
def test_gpt_actions_preview_commit_read_enrich(preset, raw_value, expected):
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch
    from uuid import UUID, uuid4
    from tv_app.application.gpt_actions.commit_service import TvGptCommitService
    from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
    from tv_app.application.services.data.presentation_ops_content_service import PresentationOpsContentService
    from tv_app.infrastructure.persistence.repositories.idempotency_repository import InMemoryIdempotencyRepository

    pid, sid = str(uuid4()), str(uuid4())
    sc = block()
    sc["id"] = "weg-sc"
    sc["contentRuns"][3]["dataRef"]["displayFormat"] = DisplayFormatService.spec_from_preset_id(preset)
    es = block()
    field = "Metric" if isinstance(raw_value, (int, float)) else "filter.end_date"
    for b in (sc, es):
        b.pop("resolved")
        b["contentRuns"][3]["dataRef"]["field"] = field
    state = {"nativeConfig": {"version": 5, "blocks": [sc, es]}, "revision": 1}

    class Repo:
        def get_by_id(self, playlist_id):
            return {"id": str(playlist_id), "revision": state["revision"], "dataDefaults": {}}

        def get_slide(self, slide_id, playlist_id=None):
            return {"id": str(slide_id), "nativeConfig": deepcopy(state["nativeConfig"])}

    repo = Repo()
    writes = MagicMock(unsafe=True)
    writes.get_revision.side_effect = lambda playlist_id: state["revision"]
    writes.get_playlist.return_value = {"id": pid, "name": "WEG", "dataDefaults": {}}
    writes.list_sections.return_value = []
    writes.list_slides.side_effect = lambda playlist_id: [{"id": sid, "title": "WEG", "sortOrder": 0,
                                                             "nativeConfig": deepcopy(state["nativeConfig"])}]

    def update_slide(playlist_id, slide_id, payload, **kwargs):
        state["nativeConfig"] = deepcopy(payload["nativeConfig"])
        state["revision"] += 1
        return {"id": sid, "nativeConfig": deepcopy(state["nativeConfig"])}
    writes.update_slide.side_effect = update_slide

    def resolve_blocks(blocks, **kwargs):
        out = deepcopy(blocks)
        for b in out:
            resolved = {"contextValues": {"filter.start_date": "2025-09-24",
                                          "filter.end_date": raw_value if field.startswith("filter.") else None},
                        "table": {"rows": [{field: raw_value}]},
                        "serverDisplayApplied": True}
            DisplayFormatService._apply_text_display(resolved, b)
            b["resolved"] = resolved
        return out

    patch_svc = PresentationPatchService(repo=repo)
    commit = TvGptCommitService(writes=writes, idempotency=InMemoryIdempotencyRepository(), patch=patch_svc)
    dispatch = GptActionsDispatchService(repo=repo, writes=writes, commit=commit, patch=patch_svc)
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="actor-1")
    access = SimpleNamespace(can_edit=True, can_read=True, level="owner",
                             playlist={"id": pid, "name": "WEG", "dataDefaults": {}})
    with (patch.object(dispatch._access, "resolve", return_value=access),
          patch.object(dispatch._access, "actor_id", return_value="actor-1"),
          patch.object(commit._access, "resolve", return_value=access),
          patch("tv_app.application.gpt_actions.dispatch_service.assert_permission", return_value=None),
          patch("tv_app.application.services.data.slide_data_resolution_service.SlideDataResolutionService.resolve_blocks", side_effect=resolve_blocks),
          patch("tv_app.application.services.data.ready_slide_quality_service.ReadySlideQualityService.collect_native_quality_issues", return_value=[]),
          patch("tv_app.application.services.data.slide_layout_quality_service.SlideLayoutQualityService.collect_native_layout_issues", return_value=[])):
        before = project_block_index(state["nativeConfig"], slide_id=sid, revision=1)
        source = next(row for row in before["items"] if row["id"] == "weg-sc")
        copied = deepcopy(source["formatBindings"][1]["displayFormat"])
        request = op()
        request["target"]["field"] = field
        request["displayFormat"] = copied
        prepared = dispatch.preview_change(user=user, target={"playlistId": pid, "slideId": sid},
                                           ops=[request], catalog_version=PresentationOpsContentService.catalog_version(),
                                           authorization=None)
        assert prepared["proposal_handle"]
        committed = commit.commit(user=user, actor_id="actor-1", proposal_handle=prepared["proposal_handle"],
                                  confirmation={"confirmed": True}, idempotency_key=f"weg-format-{preset}")
        reread = dispatch.get_playlist_context(user=user, playlist_id=pid, scope="editorFocus",
                                                preview_slide_id=sid, object_query="weg-es")
    assert committed["status"] == "VERIFIED"
    assert reread["scope"] == "editorFocus"
    assert "nativeConfig" not in reread["focusedSlide"]
    assert reread["objectMatches"][0]["formatBindings"][1]["displayFormat"] == copied
    after = project_block_index(state["nativeConfig"], slide_id=sid, revision=state["revision"])
    target = next(row for row in after["items"] if row["id"] == "weg-es")
    assert target["formatBindings"][1]["displayFormat"] == copied
    assert len(state["nativeConfig"]["blocks"]) == 2
    enriched = resolve_blocks(state["nativeConfig"]["blocks"])
    assert enriched[1]["resolved"]["displayRuns"][3]["text"] == expected


def test_batch_16_existing_labels_keeps_70_blocks():
    blocks = []
    for i in range(70):
        b = block()
        b["id"] = f"weg-{i}"
        b.pop("resolved")
        blocks.append(b)
    cfg = {"blocks": blocks}
    svc = PresentationPatchService.__new__(PresentationPatchService)
    for i in range(16):
        request = op()
        request["blockId"] = f"weg-{i}"
        request["displayFormat"]["presetId"] = (
            "date-year" if i % 2 == 0 else "date-month-abbrev-year"
        )
        svc._op_set_display_format(cfg, request)
    assert len(cfg["blocks"]) == 70
    assert [b["id"] for b in cfg["blocks"]] == [f"weg-{i}" for i in range(70)]
    for i in range(16):
        assert cfg["blocks"][i]["contentRuns"][3]["dataRef"]["displayFormat"]["presetId"] == (
            "date-year" if i % 2 == 0 else "date-month-abbrev-year"
        )


def test_invalid_or_null_runtime_value_never_proves_date_materialization():
    spec = DisplayFormatService.validate_write_spec({"category": "date", "presetId": "date-year"})
    for raw in (None, "not-a-date"):
        outcome = DisplayFormatService.try_format_value(raw, spec)
        assert outcome["convertible"] is False
        assert outcome["preview"] is None


def test_target_missing_and_wrong_owner_are_structured_errors():
    svc = PresentationPatchService.__new__(PresentationPatchService)
    with pytest.raises(PresentationPatchError) as missing:
        svc._op_set_display_format({"blocks": []}, op())
    assert missing.value.code == "DISPLAY_FORMAT_TARGET_NOT_FOUND"
    request = op()
    request["target"]["owner"] = "textProjection"
    with pytest.raises(PresentationPatchError) as unsupported:
        svc._op_set_display_format({"blocks": [block()]}, request)
    assert unsupported.value.code == "DISPLAY_FORMAT_TARGET_NOT_FOUND"


def test_custom_pattern_requires_nonempty_mask_and_uses_canonical_formatter():
    with pytest.raises(ValueError):
        DisplayFormatService.validate_write_spec({"category": "custom", "pattern": ""})
    spec = DisplayFormatService.validate_write_spec({"category": "custom", "pattern": "dd/mm/yyyy"})
    assert DisplayFormatService.format_value("2026-09-24", spec) == "24/09/2026"


def test_gpt_catalog_projects_exact_backend_format_presets_under_budget():
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch
    from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
    dispatch = GptActionsDispatchService(repo=MagicMock(), writes=MagicMock(), commit=MagicMock())
    with patch("tv_app.application.gpt_actions.dispatch_service.assert_permission", return_value=None):
        catalog = dispatch.get_catalog(user=SimpleNamespace(id="u1"))
    expected = {entry["formatId"]: entry["spec"] for entry in DisplayFormatService.format_catalog_entries()}
    actual = {entry["formatId"]: entry["spec"] for entry in catalog["displayFormatCatalog"]}
    assert actual == expected
    assert actual["date-year"]["presetId"] == "date-year"
    assert max(actions_response_sizes(catalog).values()) < GPT_ACTIONS_RESPONSE_MAX_BYTES
