import pytest

from app.application.services.chat_interactivity_suggestion_service import (
    ChatInteractivitySuggestionService,
)
from app.application.services.chat_presentation_interactivity_service import (
    ChatPresentationInteractivityService,
)
from tests.fixtures.interactivity_cases import INTERACTIVITY_CASES


@pytest.mark.parametrize("case", INTERACTIVITY_CASES, ids=lambda c: c["id"])
def test_interactivity_cases(case):
    metadata = dict(case.get("metadata") or {})

    workspace = case.get("workspace_context") or {
        "capabilities": {"canvas": True},
        "userActivatedAgent": True,
    }

    ChatInteractivitySuggestionService.attach_to_assistant_metadata(
        metadata,
        workspace_context=workspace,
        tool_calls=case.get("tool_calls"),
    )

    interactivity = metadata.get("interactivity") or {}

    assert interactivity.get("consolidated") is True

    if not case.get("expect_disabled_label"):
        assert interactivity.get("suggestions")

    if case.get("expect_more"):
        assert interactivity.get("moreSuggestions")

    if case.get("expect_primary_labels"):
        labels = [item["label"] for item in interactivity["suggestions"]]

        for label in case["expect_primary_labels"]:
            assert label in labels

    if case.get("expect_group"):
        groups = {item.get("group") for item in interactivity["suggestions"]}
        overflow = interactivity.get("moreSuggestions") or {}
        all_groups = set(groups) | set(overflow.keys())

        assert case["expect_group"] in all_groups

    if case.get("expect_in_suggestions"):
        shown = interactivity.get("suggestionsShown") or []
        assert case["expect_in_suggestions"] in shown

    if case.get("expect_presentation"):
        assert metadata.get("presentationFollowUpSuggestions")

    if case.get("expect_presentation_label"):
        labels = [
            item.get("label")
            for item in metadata.get("presentationFollowUpSuggestions") or []
        ]
        assert case["expect_presentation_label"] in labels

    if case.get("expect_requires_confirmation"):
        all_items = list(interactivity["suggestions"]) + sum(
            (interactivity.get("moreSuggestions") or {}).values(),
            [],
        )
        assert any(item.get("requiresConfirmation") for item in all_items)

    if case.get("expect_disabled_label"):
        all_items = list(interactivity["suggestions"]) + sum(
            (interactivity.get("moreSuggestions") or {}).values(),
            [],
        )
        disabled = [
            item
            for item in all_items
            if item.get("label") == case["expect_disabled_label"]
        ]
        assert disabled and disabled[0].get("disabledReason")

    if case.get("expect_context_bar"):
        assert interactivity.get("contextBar")
        assert interactivity["contextBar"].get("items")

    if case.get("expect_resolved_query"):
        queries = " ".join(
            item.get("query", "")
            for item in interactivity["suggestions"]
            + sum((interactivity.get("moreSuggestions") or {}).values(), [])
        )
        assert case["expect_resolved_query"] in queries

    if case.get("expect_primary_label"):
        labels = [item["label"] for item in interactivity["suggestions"]]
        assert labels[0] == case["expect_primary_label"]


def test_presentation_table_chips():
    suggestions = ChatPresentationInteractivityService.build_from_tool_calls(
        [
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "presentation": {"type": "table"}},
            }
        ]
    )

    assert suggestions
    assert any("Exportar" in item["label"] or "Gráfico" in item["label"] for item in suggestions)


def test_presentation_decision_adds_view_switch_chips():
    suggestions = ChatPresentationInteractivityService.build_from_tool_calls(
        [
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "presentation": {"type": "table"},
                    "presentationDecision": {
                        "selected": "table",
                        "availableViews": ["table", "line_chart", "chart"],
                    },
                },
            }
        ]
    )

    labels = [item["label"] for item in suggestions]

    assert "Gerar gráfico" in labels


def test_presentation_chart_includes_explain_chip():
    suggestions = ChatPresentationInteractivityService.build_from_tool_calls(
        [
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "presentation": {"type": "chart"}},
            }
        ]
    )

    labels = [item["label"] for item in suggestions]

    assert "Explique esse gráfico" in labels

    explain = next(item for item in suggestions if item["label"] == "Explique esse gráfico")

    assert "insight" in explain["query"].lower()


def test_presentation_kpi_ver_em_tabela_query():
    suggestions = ChatPresentationInteractivityService.build_from_tool_calls(
        [
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "presentation": {"type": "kpi"}},
            }
        ]
    )

    table_chip = next(item for item in suggestions if item["label"] == "Ver em tabela")

    assert table_chip["query"] == "mostre o último resultado em tabela"


def test_max_primary_is_four():
    metadata = {
        "followUpSuggestions": [
            {"label": f"Ação {index}", "query": f"ação {index}"} for index in range(10)
        ],
    }

    ChatInteractivitySuggestionService.attach_to_assistant_metadata(metadata)

    assert len(metadata["interactivity"]["suggestions"]) <= 4
