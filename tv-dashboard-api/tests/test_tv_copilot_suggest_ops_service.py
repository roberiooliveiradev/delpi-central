"""Testes TvCopilotSuggestOpsService — NL → ops tipadas (sem LLM)."""

from __future__ import annotations

from tv_app.application.services.data.tv_copilot_content_service import (
    clear_tv_copilot_content_cache,
)
from tv_app.application.services.data.tv_copilot_suggest_ops_service import (
    TvCopilotSuggestOpsService,
)


def setup_function() -> None:
    clear_tv_copilot_content_cache()


def test_suggest_escreva_texto_upsert_block_with_quoted_content():
    result = TvCopilotSuggestOpsService.suggest(
        message='escreva um texto no slide atual "ola sou uma ia"',
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"]
    upsert = next(op for op in result["ops"] if op.get("op") == "upsert_block")
    block = upsert.get("block") or {}
    assert block.get("type") == "text"
    assert "ola" in str(block.get("content") or "").lower()
    assert "upsert_block" in result["matchedCapabilityKeys"]


def test_suggest_crie_um_slide_add_blank_or_preset():
    result = TvCopilotSuggestOpsService.suggest(
        message="crie um slide",
        host_context={"playlistId": "pl-1"},
    )
    ops_names = {str(op.get("op") or "") for op in result["ops"]}
    assert ops_names & {"add_blank_slide", "add_slide_from_preset"}
    assert any(
        key in result["matchedCapabilityKeys"]
        for key in ("add_blank_slide", "add_slide_from_preset")
    )


def test_suggest_apague_bloco_with_selection():
    result = TvCopilotSuggestOpsService.suggest(
        message="apague o bloco",
        host_context={"selectedBlockIds": ["blk-42"], "slideId": "s1"},
    )
    assert result["ops"]
    delete = next(op for op in result["ops"] if op.get("op") == "delete_block")
    assert delete.get("blockId") == "blk-42"
    assert "delete_block" in result["matchedCapabilityKeys"]


def test_suggest_empty_message_returns_no_ops():
    result = TvCopilotSuggestOpsService.suggest(message="   ", host_context={})
    assert result["ops"] == []
    assert result["matchedCapabilityKeys"] == []
    assert result["reason"]
