"""Contrato SelectionPending — candidatos + resume estruturado."""

from __future__ import annotations

from app.application.services.chat_catalog_selection_pending_service import (
    ChatCatalogSelectionPendingService,
)


def test_build_from_route_candidates_multi_select():
    pending = ChatCatalogSelectionPendingService.build_from_route_candidates(
        candidates=[
            {
                "operationId": "get_overall_equipment_effectiveness_pct",
                "label": "OEE geral",
                "score": 12.0,
                "reason": "match oee",
            },
            {
                "operationId": "get_oee_by_line",
                "label": "OEE por linha",
                "score": 10.5,
            },
        ],
        multi_select=True,
    )
    assert pending is not None
    assert pending["kind"] == "catalog_route"
    assert pending["multiSelect"] is True
    assert len(pending["candidates"]) == 2
    assert pending["resume"]["mode"] == "structured_action"
    assert "fontes:" in pending["candidates"][0]["query"]


def test_build_from_score_gap_clarification():
    pending = ChatCatalogSelectionPendingService.build_from_score_gap_clarification(
        {
            "scoreGap": 0.02,
            "suggestions": [
                {"operationId": "op_a", "label": "Rota A", "query": "consultar A"},
                {"operationId": "op_b", "label": "Rota B", "query": "consultar B"},
            ],
        }
    )
    assert pending is not None
    assert pending["multiSelect"] is False
    assert pending["scoreGap"] == 0.02
    assert pending["candidates"][0]["id"] == "op_a"


def test_attach_to_assistant_metadata_and_follow_ups():
    metadata: dict = {}
    ChatCatalogSelectionPendingService.attach_to_assistant_metadata(
        metadata,
        tool_context={
            "selectionPending": ChatCatalogSelectionPendingService.build_from_route_candidates(
                candidates=[
                    {"operationId": "route_1", "label": "Fonte 1"},
                    {"operationId": "route_2", "label": "Fonte 2"},
                ]
            )
        },
    )
    assert "selectionPending" in metadata
    assert len(metadata["selectionFollowUpSuggestions"]) == 2
    assert metadata["selectionFollowUpSuggestions"][0]["label"] == "Fonte 1"


def test_resume_message_joins_ids():
    msg = ChatCatalogSelectionPendingService.build_resume_message(
        ["op_a", "op_b"]
    )
    assert "op_a" in msg and "op_b" in msg
    assert msg.lower().startswith("adicione") or "fontes:" in msg


def test_evidence_preserved_in_candidates():
    pending = ChatCatalogSelectionPendingService.build_from_route_candidates(
        candidates=[
            {
                "operationId": "op_x",
                "label": "X",
                "evidence": {
                    "shape": "table",
                    "columns": ["a"],
                    "rows": [[1]],
                    "truncated": False,
                },
            }
        ]
    )
    assert pending["candidates"][0]["evidence"]["columns"] == ["a"]
