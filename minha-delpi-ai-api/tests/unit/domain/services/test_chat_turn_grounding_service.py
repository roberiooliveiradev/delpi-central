from app.domain.services.chat_turn_grounding_service import (
    ChatTurnGroundingService,
    ChatTurnGroundingStatus,
)


def test_grounded_with_last_result_excerpt():
    result = ChatTurnGroundingService.evaluate(
        message="o que me diz sobre os itens?",
        snapshot={
            "lastResultExcerpt": {
                "title": "Estrutura 90260149",
                "rowCount": 6,
                "topKeys": ["10380044"],
            }
        },
    )

    assert result.status == ChatTurnGroundingStatus.GROUNDED
    assert result.reason == "last_result_excerpt"
    assert result.referring_label
    assert "90260149" in result.referring_label


def test_ungrounded_without_history():
    result = ChatTurnGroundingService.evaluate(
        message="isso",
        snapshot={},
        previous_messages=[],
    )

    assert result.status == ChatTurnGroundingStatus.UNGROUNDED


def test_grounded_operational_focus_follow_up():
    result = ChatTurnGroundingService.evaluate(
        message="e o estoque dele?",
        snapshot={"operationalFocus": {"productCode": "10080001"}},
    )

    assert result.status == ChatTurnGroundingStatus.GROUNDED
    assert result.reason == "operational_focus_follow_up"


def test_grounded_recent_tool_success():
    result = ChatTurnGroundingService.evaluate(
        message="os itens",
        snapshot={},
        previous_messages=[
            {
                "role": "assistant",
                "metadata": {
                    "toolCalls": [
                        {
                            "name": "execute_external_action",
                            "metadata": {"ok": True, "path": "/products/1/structure"},
                        }
                    ]
                },
            }
        ],
    )

    assert result.status == ChatTurnGroundingStatus.GROUNDED
    assert result.reason == "recent_tool_success"


def test_should_enrich_before_insight_for_items_question():
    excerpt = {
        "title": "Estrutura 90260149",
        "rowCount": 6,
        "topKeys": ["10380044"],
    }

    message = "o que me diz sobre os itens?"

    assert ChatTurnGroundingService.should_enrich_before_insight(message, excerpt)
    assert not ChatTurnGroundingService.should_narrate_excerpt(message, excerpt)
    assert (
        ChatTurnGroundingService.resolve_grounded_stage(message=message, excerpt=excerpt)
        == "grounded_enrich_insight"
    )


def test_resolve_grounded_stage_recap_for_list_codes():
    excerpt = {
        "title": "Estrutura 90260149",
        "rowCount": 6,
        "topKeys": ["10380044"],
    }

    assert (
        ChatTurnGroundingService.resolve_grounded_stage(
            message="lista os códigos",
            excerpt=excerpt,
        )
        == "grounded_narrate_recap"
    )


def test_resolve_grounded_stage_count_total_is_new_intent_not_recap():
    """«quantidade total» não pode recapitular o TOP N — precisa tools/SQL."""
    excerpt = {
        "title": "Resultado da consulta",
        "rowCount": 2,
        "topKeys": ["10080001", "10080002"],
        "preview": "10080001 …",
    }

    assert (
        ChatTurnGroundingService.resolve_grounded_stage(
            message="traga a quantidade total de intens no grupo 1008",
            excerpt=excerpt,
            last_action={
                "name": "external_action",
                "path": "/data/sql",
                "operationId": "execute_readonly_sql",
            },
        )
        is None
    )
    assert not ChatTurnGroundingService.should_narrate_excerpt(
        "traga a quantidade total de intens no grupo 1008",
        excerpt,
    )


def test_isso_substring_in_disso_does_not_force_recap():
    """«disso»/«nisso» não podem casar o token «isso» por substring."""
    excerpt = {
        "title": "Resultado da consulta",
        "rowCount": 2,
        "topKeys": ["10080001"],
        "preview": "10080001 …",
    }
    last_action = {
        "name": "external_action",
        "path": "/data/sql",
        "operationId": "execute_readonly_sql",
    }

    assert (
        ChatTurnGroundingService.resolve_grounded_stage(
            message="preciso disso amanha com o total do grupo",
            excerpt=excerpt,
            last_action=last_action,
        )
        is None
    )
    assert not ChatTurnGroundingService.should_narrate_excerpt(
        "nao quero isso agora, quero o total",
        excerpt,
    )


def test_bare_isso_with_excerpt_still_recaps():
    excerpt = {
        "title": "Resultado da consulta",
        "rowCount": 2,
        "topKeys": ["10080001"],
        "preview": "10080001 …",
    }

    assert (
        ChatTurnGroundingService.resolve_grounded_stage(
            message="isso",
            excerpt=excerpt,
            last_action={"path": "/data/sql"},
        )
        == "grounded_narrate_recap"
    )


def test_resolve_grounded_stage_narrate_insight_only():
    excerpt = {
        "title": "Estrutura 90260149",
        "rowCount": 6,
        "topKeys": ["10380044"],
    }

    assert (
        ChatTurnGroundingService.resolve_grounded_stage(
            message="o que isso implica?",
            excerpt=excerpt,
        )
        == "grounded_narrate_insight"
    )


def test_resolve_grounded_stage_interprete_resultado_is_insight_not_recap():
    excerpt = {
        "title": "Resultado da consulta",
        "rowCount": 2,
        "topKeys": ["10080001", "10080002"],
    }

    assert (
        ChatTurnGroundingService.resolve_grounded_stage(
            message="interprete o resultado da última consulta SQL",
            excerpt=excerpt,
            last_action={
                "name": "external_action",
                "path": "/data/sql",
                "operationId": "execute_readonly_sql",
            },
        )
        == "grounded_narrate_insight"
    )


def test_should_not_narrate_when_stock_expansion_requested():
    excerpt = {
        "title": "Estrutura 90260149",
        "rowCount": 6,
        "topKeys": ["10380044", "10380045"],
    }

    assert not ChatTurnGroundingService.should_narrate_excerpt(
        "e o estoque desses itens?",
        excerpt,
    )
    assert ChatTurnGroundingService.should_expand_from_excerpt(
        "e o estoque desses itens?",
        excerpt,
    )


def test_resolve_referent_component_type_for_raw_materials():
    assert ChatTurnGroundingService.resolve_referent_component_type(
        "estoque das matérias-primas",
    ) == "MP"


def test_resolve_referent_component_type_for_intermediates():
    assert ChatTurnGroundingService.resolve_referent_component_type(
        "detalhe dos produtos intermediários",
    ) == "PI"
