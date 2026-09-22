"""Compound plan compiler + synthetic preview chaining."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tv_app.application.gpt_actions.commit_service import TvGptCommitService
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.proposal_store import reset_proposal_store_for_tests
from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
    clear_tv_copilot_content_cache,
)
from tv_app.application.services.data.presentation_mutation import (
    PlanCompileError,
    compile_presentation_plan,
)
from tv_app.infrastructure.persistence.repositories.idempotency_repository import (
    InMemoryIdempotencyRepository,
)


@pytest.fixture(autouse=True)
def _reset():
    clear_tv_copilot_content_cache()
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()
    clear_tv_copilot_content_cache()


def _superadmin():
    return SimpleNamespace(is_superadmin=True, permissions=[], id="actor-1")


def _compound_ops():
    return [
        {
            "op": "upsert_block",
            "block": {"id": "blk_hello", "type": "text", "content": "Olá mundo"},
        },
        {"op": "add_blank_slide", "title": "Slide 1", "as": "s1"},
        {"op": "create_playlist", "name": "Vista - Testes", "as": "pl1"},
    ]


def test_all_ops_declare_produces_and_consumes():
    for name, spec in TvCopilotContentService.operations().items():
        assert isinstance(spec.get("produces"), list), name
        assert isinstance(spec.get("consumes"), list), name


def test_plan_resource_requirements_satisfiable_after_create_chain():
    ordered = [
        {"op": "create_playlist", "name": "A"},
        {"op": "add_blank_slide", "title": "B"},
        {
            "op": "upsert_block",
            "block": {"id": "b1", "type": "text", "content": "x"},
        },
    ]
    req = TvCopilotContentService.plan_resource_requirements(ordered, {})
    assert req["satisfiable"] is True
    assert req["requiresPlaylist"] is False
    assert req["requiresSlide"] is False


def test_compiler_reorders_shuffled_compound_ops():
    compiled = compile_presentation_plan(ops=_compound_ops(), target={})
    assert compiled.dependency_order == [
        "create_playlist",
        "add_blank_slide",
        "upsert_block",
    ]
    assert compiled.alias_producers["pl1"] == "playlist"
    assert compiled.alias_producers["s1"] == "slide"


def test_compiler_rejects_unsatisfiable_upsert_without_slide():
    with pytest.raises(PlanCompileError) as caught:
        compile_presentation_plan(
            ops=[
                {
                    "op": "upsert_block",
                    "block": {"id": "b1", "type": "text", "content": "x"},
                }
            ],
            target={},
        )
    assert caught.value.code == "DEPENDENCY_UNSATISFIABLE"


def test_compiler_rejects_unknown_ref():
    with pytest.raises(PlanCompileError) as caught:
        compile_presentation_plan(
            ops=[
                {"op": "create_playlist", "name": "A", "as": "pl1"},
                {
                    "op": "add_blank_slide",
                    "title": "B",
                    "playlistRef": "missing_alias",
                },
            ],
            target={},
        )
    assert caught.value.code == "INVALID_REF"


def test_preview_compound_mints_synthetic_ids_and_native_text():
    from tv_app.application.services.data.presentation_mutation import (
        PresentationPatchService,
    )

    svc = PresentationPatchService()
    result = svc.preview(
        {
            "target": {},
            "ops": _compound_ops(),
            "catalogVersion": TvCopilotContentService.catalog_version(),
        },
        user=_superadmin(),
    )
    assert result["dependencyOrder"] == [
        "create_playlist",
        "add_blank_slide",
        "upsert_block",
    ]
    assert str(result["target"]["playlistId"]).startswith("syn:")
    assert str(result["target"]["slideId"]).startswith("syn:")
    blocks = (result.get("nativeConfig") or {}).get("blocks") or []
    assert any(
        isinstance(b, dict) and b.get("content") == "Olá mundo" for b in blocks
    )


def test_dispatch_commit_now_compound_verified():
    writes = MagicMock()
    new_pl = uuid4()
    new_slide = uuid4()
    writes.create_playlist.return_value = {"id": str(new_pl), "name": "Vista - Testes"}
    writes.get_revision.return_value = 1
    writes.add_slide.return_value = {"id": str(new_slide), "title": "Slide 1"}
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": str(new_pl), "name": "Vista - Testes"}

    persisted: dict = {}

    def _update_slide(playlist_id, slide_id, body, **kwargs):
        if isinstance(body, dict) and "nativeConfig" in body:
            persisted["nativeConfig"] = body["nativeConfig"]
        return {"id": str(slide_id)}

    def _list_slides(playlist_id):
        return [
            {
                "id": str(new_slide),
                "title": "Slide 1",
                "nativeConfig": persisted.get(
                    "nativeConfig",
                    {
                        "version": 5,
                        "blocks": [
                            {"id": "blk_hello", "type": "text", "content": "Olá mundo"}
                        ],
                    },
                ),
            }
        ]

    writes.update_slide.side_effect = _update_slide
    writes.list_slides.side_effect = _list_slides

    commit = TvGptCommitService(writes=writes, idempotency=InMemoryIdempotencyRepository())
    dispatch = GptActionsDispatchService(repo=MagicMock(), writes=writes, commit=commit)
    dispatch._access.actor_id = MagicMock(return_value="actor-1")

    result = dispatch.preview_change(
        user=_superadmin(),
        target={},
        ops=_compound_ops(),
        catalog_version=TvCopilotContentService.catalog_version(),
        authorization=None,
        commit_now=True,
        confirmation={"confirmed": True},
        idempotency_key="compound-p0-1",
    )
    assert result.get("commit_now_applied") is True
    assert result.get("status") == "VERIFIED"
    writes.create_playlist.assert_called_once()
    writes.add_slide.assert_called_once()
    assert writes.update_slide.called
    assert persisted.get("nativeConfig")


def test_dispatch_compound_reorder_metamorphic_same_order():
    from tv_app.application.services.data.presentation_mutation import (
        PresentationPatchService,
    )

    svc = PresentationPatchService()
    a = svc.preview(
        {"target": {}, "ops": _compound_ops()},
        user=_superadmin(),
    )
    b = svc.preview(
        {
            "target": {},
            "ops": list(reversed(_compound_ops())),
        },
        user=_superadmin(),
    )
    assert a["dependencyOrder"] == b["dependencyOrder"]
