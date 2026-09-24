"""Op aliases: GPT synonyms must resolve to catalog ops (create_slide → add_blank_slide)."""

from __future__ import annotations

import pytest

from tv_app.application.services.data.presentation_mutation import (
    PlanCompileError,
    compile_presentation_plan,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
    clear_presentation_ops_content_cache,
)


@pytest.fixture(autouse=True)
def _reset_ops_cache():
    clear_presentation_ops_content_cache()
    yield
    clear_presentation_ops_content_cache()


def test_resolve_op_name_create_slide_alias() -> None:
    assert (
        PresentationOpsContentService.resolve_op_name("create_slide")
        == "add_blank_slide"
    )
    assert (
        PresentationOpsContentService.resolve_op_name("add_blank_slide")
        == "add_blank_slide"
    )


def test_resolve_op_name_negative_unknown_stays() -> None:
    assert PresentationOpsContentService.resolve_op_name("invented_op_xyz") == (
        "invented_op_xyz"
    )
    assert "create_slide" not in PresentationOpsContentService.allowed_ops()
    assert "add_blank_slide" in PresentationOpsContentService.allowed_ops()


def test_compile_plan_rewrites_create_slide_to_add_blank_slide() -> None:
    compiled = compile_presentation_plan(
        ops=[{"op": "create_slide", "title": "Carteira semanal", "as": "s1"}],
        target={"playlistId": "pl-1"},
    )
    assert compiled.ordered_ops[0]["op"] == "add_blank_slide"
    assert compiled.dependency_order == ["add_blank_slide"]


def test_compile_plan_sibling_add_blank_slide_unchanged() -> None:
    compiled = compile_presentation_plan(
        ops=[{"op": "add_blank_slide", "title": "OK"}],
        target={"playlistId": "pl-1"},
    )
    assert compiled.ordered_ops[0]["op"] == "add_blank_slide"


def test_compile_plan_negative_unknown_op_still_rejected() -> None:
    with pytest.raises(PlanCompileError) as exc_info:
        compile_presentation_plan(
            ops=[{"op": "totally_fake_op"}],
            target={},
        )
    assert exc_info.value.code == "UNSUPPORTED_CAPABILITY"
