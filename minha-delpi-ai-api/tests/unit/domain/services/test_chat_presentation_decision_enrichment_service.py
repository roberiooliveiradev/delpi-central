from app.domain.services.chat_presentation_decision_enrichment_service import (
    ChatPresentationDecisionEnrichmentService,
)


def test_enrich_attaches_presentation_decision():
    metadata = {
        "path": "/products/90269001/stock",
        "apiDelpiResponseMeta": {"entity": "product_stock"},
        "tablePresentation": {
            "type": "table",
            "rows": [{"filial": "01", "saldo": 10}],
        },
        "availableFormats": ["table", "text"],
    }

    result = ChatPresentationDecisionEnrichmentService.enrich(
        metadata,
        user_message="estoque do produto",
    )

    assert result.get("presentationDecision")
    assert result["presentationDecision"].get("selected") in {"table", "text", "kpi"}


def test_enrich_sql_result_selects_table_not_text_only_summary():
    """Regressão: execute SQL listava N registros no texto e omitia a tabela na bolha."""
    from app.domain.services.chat_presentation_render_plan_service import (
        ChatPresentationRenderPlanService,
    )
    from app.domain.services.chat_presentation_payload_pruning_service import (
        ChatPresentationPayloadPruningService,
    )

    metadata = {
        "path": "/data/sql",
        "apiDelpiResponseMeta": {"entity": "sql_result", "shape": "paged_list"},
        "presentationProfileKey": "sql",
        "tablePresentation": {
            "type": "table",
            "title": "Resultado da consulta",
            "columns": [
                {"key": "CODIGO", "label": "Código"},
                {"key": "DESCRICAO", "label": "Descrição"},
            ],
            "rows": [
                {"CODIGO": "10080001", "DESCRICAO": "Produto A"},
                {"CODIGO": "10080002", "DESCRICAO": "Produto B"},
            ],
        },
        "textPresentation": {
            "type": "markdown",
            "markdown": "Foram retornados **2** registros.",
        },
        "availableFormats": ["text", "canvas", "table"],
    }

    result = ChatPresentationDecisionEnrichmentService.enrich(
        metadata,
        user_message="execute o sql",
    )
    decision = result.get("presentationDecision") or {}

    assert decision.get("selected") == "table"
    assert decision.get("presentationProfileKey") == "sql"

    ChatPresentationPayloadPruningService.prune(result)
    plan = ChatPresentationRenderPlanService.build(result) or result.get("renderPlan")
    if not plan:
        from app.domain.services.chat_presentation_render_pipeline_service import (
            ChatPresentationRenderPipelineService,
        )

        ChatPresentationRenderPipelineService.finalize(result)
        plan = result.get("renderPlan")

    assert isinstance(plan, dict)
    kinds = [seg.get("kind") for seg in (plan.get("segments") or []) if isinstance(seg, dict)]
    assert "table" in kinds


def test_enrich_generic_system_profile_with_table_selects_table():
    """Mesmo bug em perfil generic (não só sql): evidência tabular permanece no Automático."""
    metadata = {
        "path": "/system/tables/SA1010/columns",
        "apiDelpiResponseMeta": {"entity": "system_table_columns", "shape": "paged_list"},
        "presentationProfileKey": "system",
        "tablePresentation": {
            "type": "table",
            "title": "Colunas",
            "columns": [{"key": "name", "label": "Nome"}],
            "rows": [{"name": "A1_COD"}, {"name": "A1_NOME"}],
        },
        "textPresentation": {
            "type": "markdown",
            "markdown": "Foram retornados **2** registros.",
        },
        "availableFormats": ["text", "table"],
    }

    result = ChatPresentationDecisionEnrichmentService.enrich(
        metadata,
        user_message="mostre as colunas da SA1010",
    )

    assert (result.get("presentationDecision") or {}).get("selected") == "table"
