"""Editor commits resolve operational data only when an op can change it."""

from unittest.mock import patch
from uuid import uuid4

from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_mutation_commit_service import (
    PresentationMutationCommitService,
)


def test_geometry_ops_do_not_require_data_fingerprint():
    ops = [
        {"op": "align_blocks", "blockIds": ["a", "b"], "command": "align-center-h"},
        {"op": "align_blocks", "blockIds": ["a", "b", "c"], "command": "distribute-h"},
        {"op": "reorder_block_z", "blockIds": ["a"], "command": "bring-to-front"},
    ]
    for op in ops:
        assert PresentationPatchService.mutation_ops_require_data_fingerprint([op]) is False


def test_data_ops_still_require_data_fingerprint():
    for name in (
        "patch_data_source_params",
        "upsert_block",
        "delete_block",
        "upsert_data_source",
    ):
        assert PresentationPatchService.mutation_ops_require_data_fingerprint(
            [{"op": name}]
        ) is True


def test_mixed_batch_keeps_fingerprint_when_any_op_touches_data():
    ops = [
        {"op": "align_blocks", "command": "align-center-h"},
        {"op": "upsert_block"},
    ]
    assert PresentationPatchService.mutation_ops_require_data_fingerprint(ops) is True


def test_geometry_commit_does_not_ask_preview_for_fingerprint():
    captured: dict[str, bool] = {}

    class _Patch:
        def preview(self, envelope, **kwargs):
            del envelope
            captured["include_fingerprint"] = kwargs["include_fingerprint"]
            return {
                "nativeConfig": {"version": 5, "blocks": []},
                "appliedOps": ["align_blocks"],
                "fingerprint": None,
                "sideEffectHints": [],
                "message": "ok",
            }

    class _Writes:
        def update_slide(self, *args, **kwargs):
            del args, kwargs
            return {"nativeConfig": {"version": 5, "blocks": []}}

    playlist_id = uuid4()
    slide_id = uuid4()
    result = PresentationMutationCommitService(patch=_Patch(), writes=_Writes()).commit(
        playlist_id=playlist_id,
        slide_id=slide_id,
        ops=[{"op": "align_blocks", "blockIds": ["a", "b"], "command": "align-center-h"}],
        user=object(),
        actor_user_id="editor",
    )

    assert captured["include_fingerprint"] is False
    assert result["persisted"] is True
    assert result["nativeConfig"]["version"] == 5
    assert result["appliedOps"] == ["align_blocks"]


def test_data_commit_still_asks_preview_for_fingerprint():
    captured: dict[str, bool] = {}

    class _Patch:
        def preview(self, envelope, **kwargs):
            del envelope
            captured["include_fingerprint"] = kwargs["include_fingerprint"]
            return {
                "nativeConfig": {"version": 5, "blocks": []},
                "appliedOps": ["patch_data_source_params"],
                "fingerprint": [{"blockId": "src"}],
                "sideEffectHints": [],
                "message": "ok",
            }

    class _Writes:
        def update_slide(self, *args, **kwargs):
            del args, kwargs
            return {"nativeConfig": {"version": 5, "blocks": []}}

    result = PresentationMutationCommitService(patch=_Patch(), writes=_Writes()).commit(
        playlist_id=uuid4(),
        slide_id=uuid4(),
        ops=[{"op": "patch_data_source_params", "blockId": "src"}],
        user=object(),
        actor_user_id="editor",
    )

    assert captured["include_fingerprint"] is True
    assert result["fingerprint"] == [{"blockId": "src"}]


PLAYLIST_ID = "00000000-0000-0000-0000-0000000000aa"
SLIDE_ID = "11111111-1111-1111-1111-1111111111aa"


def _bound_text_block(**projection_patch: object) -> dict:
    projection = {
        "field": "amount",
        "aggregation": "sum",
        "format": "currency",
        "decimalPlaces": 2,
        "displayFormat": {
            "category": "currency",
            "presetId": "currency-brl",
            "useThousandsSeparator": True,
        },
        "prefix": "R$ ",
        "suffix": "",
    }
    projection.update(projection_patch)
    return {
        "id": "value-1",
        "type": "text",
        "content": "0",
        "dataSourceId": "src-a",
        "modelId": "model-1",
        "frame": {"x": 1, "y": 2, "w": 10, "h": 4},
        "style": {"color": "#111111", "fontFamily": "Arial", "fontSize": 14},
        "textProjection": projection,
    }


class _CountingResolution:
    def __init__(self) -> None:
        self.resolve_calls = 0
        self.enrich_calls = 0

    def resolve_blocks(self, blocks, **kwargs):
        del kwargs
        self.resolve_calls += 1
        resolved = []
        for block in blocks:
            copied = dict(block)
            copied["resolved"] = {"rows": [{"amount": 1}]}
            resolved.append(copied)
        return resolved

    def enrich_data_models(self, models, **kwargs):
        del kwargs
        self.enrich_calls += 1
        return {}


class _SlideRepo:
    def __init__(self, blocks: list[dict]) -> None:
        self.native = {
            "version": 5,
            "dataModels": [{"id": "model-1", "name": "Faturamento"}],
            "blocks": blocks,
        }

    def get_slide(self, slide_id, *, playlist_id=None):
        del slide_id, playlist_id
        return {"id": SLIDE_ID, "nativeConfig": self.native}

    def get_by_id(self, playlist_id):
        del playlist_id
        return {"id": PLAYLIST_ID, "revision": 4, "dataDefaults": {}}

    def get_revision(self, playlist_id):
        del playlist_id
        return 4


def _preview_upsert(block: dict, extra_ops: list[dict] | None = None):
    resolution = _CountingResolution()
    source = {
        "id": "src-a",
        "type": "data_source",
        "dataBinding": {
            "operationId": "op.demo",
            "params": {"branch": "01"},
            "displayMode": "auto",
            "label": "Amount",
        },
    }
    service = PresentationPatchService(
        repo=_SlideRepo([source, _bound_text_block()]),
        resolution=resolution,
        catalog=type(
            "Catalog",
            (),
            {"get_route": lambda self, operation_id: {
                "operationId": operation_id,
                "label": "Demo",
                "paramSchema": {"branch": {"type": "string"}},
            }},
        )(),
    )
    ops = [{"op": "upsert_block", "block": block, "createIfMissing": True}]
    if extra_ops:
        ops.extend(extra_ops)
    with (
        patch(
            "tv_app.application.services.data.presentation_mutation.patch_service.validate_comunicado_native_config",
            lambda cfg, user=None, catalog=None: None,
        ),
        patch(
            "tv_app.application.services.data.presentation_mutation.patch_service.sanitize_and_hydrate_comunicado_config",
            lambda cfg, catalog=None: cfg,
        ),
    ):
        result = service.preview(
            {
                "version": "TvPresentationPatchV1",
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": ops,
            },
            user={"sub": "editor"},
            authorization=None,
            include_fingerprint=True,
        )
    return result, resolution


def test_prefix_suffix_and_format_do_not_resolve_operational_data():
    cases = [
        {"prefix": "US$ "},
        {"suffix": " mil"},
        {"decimalPlaces": 0},
        {"displayFormat": {
            "category": "currency",
            "presetId": "currency-brl",
            "useThousandsSeparator": False,
        }},
    ]
    for patch in cases:
        result, resolution = _preview_upsert(_bound_text_block(**patch))
        assert result["appliedOps"] == ["upsert_block"]
        assert resolution.resolve_calls == 0
        assert resolution.enrich_calls == 0
        assert result.get("fingerprint") is None


def test_style_color_and_font_do_not_resolve_operational_data():
    block = _bound_text_block()
    block["style"] = {**block["style"], "color": "#ff0000", "fontFamily": "Georgia"}
    result, resolution = _preview_upsert(block)
    assert result["appliedOps"] == ["upsert_block"]
    assert resolution.resolve_calls == 0
    assert resolution.enrich_calls == 0


def test_field_binding_change_still_resolves_operational_data():
    _result, resolution = _preview_upsert(_bound_text_block(field="quantity"))
    assert resolution.resolve_calls > 0 or resolution.enrich_calls > 0


def test_source_param_patch_still_resolves_operational_data():
    _result, resolution = _preview_upsert(
        _bound_text_block(),
        extra_ops=[{
            "op": "patch_data_source_params",
            "blockId": "src-a",
            "set": {"branch": "02"},
        }],
    )
    assert resolution.resolve_calls > 0 or resolution.enrich_calls > 0


def test_mixed_visual_and_data_batch_keeps_resolution():
    _result, resolution = _preview_upsert(
        _bound_text_block(prefix="R$ "),
        extra_ops=[{
            "op": "patch_data_source_params",
            "blockId": "src-a",
            "set": {"branch": "02"},
        }],
    )
    assert resolution.resolve_calls > 0 or resolution.enrich_calls > 0


def test_unknown_block_key_stays_fail_closed():
    block = _bound_text_block()
    block["unclassifiedHint"] = "keep-validation"
    _result, resolution = _preview_upsert(block)
    assert resolution.resolve_calls > 0 or resolution.enrich_calls > 0


def test_transform_op_stays_in_the_operational_gate():
    ops = PresentationPatchService.ops_requiring_operational_resolution(
        [{"op": "set_data_transform", "blockId": "src-a", "steps": []}],
        [],
        [],
    )
    assert [op["op"] for op in ops] == ["set_data_transform"]


def test_new_block_upsert_stays_fail_closed():
    block = _bound_text_block()
    block["id"] = "value-new"
    _result, resolution = _preview_upsert(block)
    assert resolution.resolve_calls > 0 or resolution.enrich_calls > 0
