from app.domain.services.chat_presentation_text_first_policy_service import (
    ChatPresentationTextFirstPolicyService,
)


def test_stock_simple_question_keeps_table_primary_without_views():
    assert not ChatPresentationTextFirstPolicyService.should_default_to_text_only(
        path="/products/10080001/stock",
        entity="product_stock",
        user_message="estoque do produto 10080001",
    )
    assert not ChatPresentationTextFirstPolicyService.should_build_views(
        path="/products/10080001/stock",
        entity="product_stock",
        user_message="estoque do produto 10080001",
    )


def test_sql_result_does_not_force_text_only_hiding_table():
    """Resultado /data/sql tem linhas — Automático deve mostrar tabela, não só o resumo."""
    assert not ChatPresentationTextFirstPolicyService.should_default_to_text_only(
        path="/data/sql",
        entity="sql_result",
        user_message="execute o sql",
        metadata={"presentationProfileKey": "sql", "tablePresentation": {"type": "table"}},
    )


def test_generic_on_demand_with_table_evidence_does_not_force_text_only():
    """Família generic+on_demand (ex.: system) com tabela montada não pode ocultar evidência."""
    assert not ChatPresentationTextFirstPolicyService.should_default_to_text_only(
        path="/system/tables",
        entity="system_metadata",
        user_message="liste as colunas",
        metadata={
            "presentationProfileKey": "system",
            "tablePresentation": {
                "type": "table",
                "rows": [{"coluna": "A1_COD"}],
            },
        },
    )


def test_generic_on_demand_without_evidence_does_not_imply_text_only():
    """Catch-all antigo: generic+on_demand ⇒ text-only — quebrava Automático em listagens."""
    assert not ChatPresentationTextFirstPolicyService.should_default_to_text_only(
        path="/data/sql",
        entity="sql_result",
        user_message="execute o sql",
        metadata={"presentationProfileKey": "system"},
    )


def test_declared_text_when_available_still_defaults_to_text_only():
    assert ChatPresentationTextFirstPolicyService.should_default_to_text_only(
        path="/products/10080001/pricing",
        entity="product_pricing",
        user_message="preço de venda",
    )


def test_text_when_available_yields_to_materialized_table_evidence():
    """Mesmo perfil text_when_available: se a tabela já veio no metadata, não ocultar."""
    assert not ChatPresentationTextFirstPolicyService.should_default_to_text_only(
        path="/products/10080001/pricing",
        entity="product_pricing",
        user_message="preço de venda",
        metadata={"tablePresentation": {"type": "table", "rows": [{"preco": 1}]}},
    )


def test_openapi_list_entity_does_not_force_text_only_without_metadata():
    """Anti-padrão: listagem OpenAPI não pode ocultar tabela por cair em generic."""
    assert not ChatPresentationTextFirstPolicyService.should_default_to_text_only(
        path="/production/schedule/today",
        entity="production_schedule_today",
        user_message="produtos programados para produzir hoje",
    )


def test_explicit_chart_request_builds_views():
    assert ChatPresentationTextFirstPolicyService.should_build_views(
        path="/products/10080001/stock",
        entity="product_stock",
        explicit_format="chart",
    )


def test_integrated_stack_request_builds_views():
    assert ChatPresentationTextFirstPolicyService.should_build_views(
        path="/products/10080001/stock",
        entity="product_stock",
        user_message="estoque completo do produto 10080001",
    )
    assert ChatPresentationTextFirstPolicyService.looks_like_integrated_stack_request(
        "mostre a visão integrada do estoque",
    )


def test_view_build_policy_defaults_to_on_demand_for_stock():
    assert (
        ChatPresentationTextFirstPolicyService.view_build_policy(
            "/products/10080001/stock",
            "product_stock",
        )
        == "on_demand"
    )


def test_apply_text_primary_keeps_tree_for_structure_text_outline():
    from app.domain.services.chat_presentation_primary_view_service import (
        ChatPresentationPrimaryViewService,
    )

    metadata = {
        "path": "/products/90260149/structure",
        "textPresentation": {"type": "markdown", "markdown": "### Estrutura\n\nResumo."},
        "presentation": {
            "type": "tree",
            "title": "Estrutura",
            "root": {"id": "90260149", "label": "90260149", "children": []},
        },
        "chartPresentation": {"type": "chart", "data": []},
        "availableFormats": ["text", "tree", "chart"],
    }

    applied = ChatPresentationPrimaryViewService.apply_session_preference(metadata, "text")

    assert applied is True
    assert metadata.get("presentation") is None
    assert metadata.get("treePresentation", {}).get("type") == "tree"


def test_apply_text_primary_skips_stock_when_table_is_primary():
    metadata = {
        "textPresentation": {"type": "markdown", "markdown": "### Estoque\n\n- Filial 01"},
        "presentation": {"type": "table", "rows": [{"branch": "01"}]},
        "chartPresentation": {"type": "chart", "data": []},
        "treePresentation": {"type": "tree", "nodes": []},
        "availableFormats": ["text", "table", "chart", "tree"],
    }

    applied = ChatPresentationTextFirstPolicyService.apply_text_primary_metadata(
        metadata,
        path="/products/10080001/stock",
        entity="product_stock",
        user_message="estoque do produto 10080001",
    )

    assert applied is False
    assert metadata.get("presentation", {}).get("type") == "table"
    assert metadata.get("chartPresentation", {}).get("type") == "chart"
