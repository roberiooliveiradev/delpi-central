"""Editor commits resolve operational data only when an op can change it."""

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
