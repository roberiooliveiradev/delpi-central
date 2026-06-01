from app.application.services.chat_interactivity_suggestion_service import (
    ChatInteractivitySuggestionService,
)
from app.application.services.chat_operational_refinement_interactivity_service import (
    ChatOperationalRefinementInteractivityService,
)


def test_build_refinement_chips_for_paginated_stock():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/10080077/stock",
                "dataCoverageNotice": {
                    "kind": "pagination",
                    "details": {"pagination": {"page": 1, "totalPages": 3}},
                },
            },
        }
    ]

    chips = ChatOperationalRefinementInteractivityService.build_from_tool_calls(tool_calls)

    labels = [chip["label"] for chip in chips]

    assert "Traga tudo" in labels
    assert "Continue buscando" in labels
    assert "Só com saldo" in labels


def test_refinement_merged_into_interactivity():
    metadata = {
        "toolCalls": [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/10080077/stock",
                    "paginationConsolidation": {"completed": False},
                    "dataCoverageNotice": {"kind": "pagination"},
                },
            }
        ],
    }

    ChatInteractivitySuggestionService.attach_to_assistant_metadata(
        metadata,
        tool_calls=metadata["toolCalls"],
    )

    interactivity = metadata["interactivity"]
    all_queries = " ".join(
        item["query"]
        for item in interactivity["suggestions"]
        + sum(interactivity.get("moreSuggestions", {}).values(), [])
    )

    assert "traga tudo" in all_queries or "sim, continue" in all_queries
