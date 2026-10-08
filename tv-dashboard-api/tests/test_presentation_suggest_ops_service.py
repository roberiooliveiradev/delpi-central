"""Testes PresentationSuggestOpsService — NL → ops tipadas (sem LLM)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tv_app.application.services.data.presentation_ops_content_service import (
    clear_presentation_ops_content_cache,
)
from tv_app.application.services.data.presentation_suggest_ops_service import (
    PresentationSuggestOpsService,
)


@pytest.fixture(autouse=True)
def _skip_ai_route_rank_in_unit_tests():
    """Unitários usam ranking local; S2S AI é coberto em testes dedicados."""
    clear_presentation_ops_content_cache()
    with patch.object(
        PresentationSuggestOpsService,
        "_rank_via_ai_suggest",
        return_value=[],
    ):
        yield
    clear_presentation_ops_content_cache()


def test_suggest_adicione_texto_sem_aspas_cria_bloco_vazio():
    result = PresentationSuggestOpsService.suggest(
        message="adicione um texto no slide",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"]
    upsert = next(op for op in result["ops"] if op.get("op") == "upsert_block")
    block = upsert.get("block") or {}
    assert block.get("type") == "text"
    assert block.get("content") == ""
    assert str(block.get("id") or "").startswith("txt_")
    assert "upsert_block" in result["matchedCapabilityKeys"]


def test_suggest_escreva_texto_upsert_block_with_quoted_content():
    result = PresentationSuggestOpsService.suggest(
        message='escreva um texto no slide atual "ola sou uma ia"',
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"]
    upsert = next(op for op in result["ops"] if op.get("op") == "upsert_block")
    block = upsert.get("block") or {}
    assert block.get("type") == "text"
    assert "ola" in str(block.get("content") or "").lower()
    assert "upsert_block" in result["matchedCapabilityKeys"]


@pytest.mark.parametrize(
    "message",
    [
        "adicione um texto 'X' neste slide",
        "coloque um texto 'X' neste slide",
        "insira um texto 'X' neste slide",
        "crie um texto 'X' neste slide",
    ],
)
def test_suggest_text_creation_verbs_same_intent_family(message):
    """NL sibling corpus — every canonical creation verb must materialize the
    same create semantics (live defect: «coloque um texto» was unsupported)."""
    result = PresentationSuggestOpsService.suggest(
        message=message,
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["status"] == "ready"
    upsert = next(op for op in result["ops"] if op.get("op") == "upsert_block")
    block = upsert.get("block") or {}
    assert block.get("type") == "text"
    assert str(block.get("id") or "").startswith("txt_")
    # Canonical create intent — text blocks are not create-friendly types and
    # the template has no authored frame, so createIfMissing is required for
    # the op to enter PREPARE at all.
    assert upsert.get("createIfMissing") is True


def test_suggest_crie_um_slide_add_blank_or_preset():
    result = PresentationSuggestOpsService.suggest(
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
    result = PresentationSuggestOpsService.suggest(
        message="apague o bloco",
        host_context={
            "selectedBlockIds": ["blk-42"],
            "slideId": "s1",
            "playlistId": "pl-1",
        },
    )
    assert result["ops"]
    delete = next(op for op in result["ops"] if op.get("op") == "delete_block")
    assert delete.get("blockId") == "blk-42"
    assert "delete_block" in result["matchedCapabilityKeys"]


def test_suggest_apague_bloco_sem_selecao_clarifica():
    result = PresentationSuggestOpsService.suggest(
        message="apague o bloco",
        host_context={"slideId": "s1", "playlistId": "pl-1"},
    )
    assert result["ops"] == []
    assert "delete_block" in result["matchedCapabilityKeys"]
    assert result.get("clarificationKey") == "suggestNeedSelection"
    assert "selecione" in str(result.get("reason") or "").lower()


def test_suggest_apague_caixa_de_texto_selecionada_delete_block():
    """Regressão: «apague a caixa de texto» não pode virar upsert_block vazio."""
    result = PresentationSuggestOpsService.suggest(
        message="apague a caixa de texto selecionada",
        host_context={
            "selectedBlockIds": ["txt_de88186807"],
            "slideId": "s1",
            "playlistId": "pl-1",
        },
    )
    assert result["ops"] == [
        {"op": "delete_block", "blockId": "txt_de88186807"}
    ]
    assert result["matchedCapabilityKeys"] == ["delete_block"]
    assert all(op.get("op") != "upsert_block" for op in result["ops"])


def test_suggest_exclua_kpi_usa_focus_block_id():
    result = PresentationSuggestOpsService.suggest(
        message="exclua o kpi selecionado",
        host_context={
            "focusBlockId": "kpi-1",
            "slideId": "s1",
            "playlistId": "pl-1",
        },
    )
    assert result["ops"] == [{"op": "delete_block", "blockId": "kpi-1"}]


def test_suggest_apague_caixa_sem_selecao_clarifica_nao_cria_texto():
    result = PresentationSuggestOpsService.suggest(
        message="apague a caixa de texto",
        host_context={"slideId": "s1", "playlistId": "pl-1"},
    )
    assert result["ops"] == []
    assert "delete_block" in result["matchedCapabilityKeys"]
    assert "upsert_block" not in result["matchedCapabilityKeys"]
    assert result.get("clarificationKey") == "suggestNeedSelection"


def test_suggest_empty_message_returns_no_ops():
    result = PresentationSuggestOpsService.suggest(message="   ", host_context={})
    assert result["ops"] == []
    assert result["matchedCapabilityKeys"] == []
    assert result["reason"]


def test_suggest_fundo_azul_patch_native_config_canonical_background():
    result = PresentationSuggestOpsService.suggest(
        message="mude a cor do fundo do slide para azul",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"]
    patch_op = next(op for op in result["ops"] if op.get("op") == "patch_native_config")
    background = (patch_op.get("patch") or {}).get("background") or {}
    assert background.get("type") == "color"
    assert str(background.get("value") or "").startswith("#")
    assert "patch_native_config" in result["matchedCapabilityKeys"]


def test_suggest_fundo_sem_cor_nao_emite_background_vazio():
    result = PresentationSuggestOpsService.suggest(
        message="mude a cor do fundo do slide",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"] == []
    assert "patch_native_config" in result["matchedCapabilityKeys"]
    assert result.get("clarificationKey") == "suggestNeedColor"
    assert "cor" in str(result.get("reason") or "").lower()


def test_suggest_kpi_sem_rota_clarifica_operation_id():
    from unittest.mock import MagicMock, patch

    empty_catalog = MagicMock()
    empty_catalog.get_route.return_value = None
    empty_catalog.list_routes.return_value = []
    with patch(
        "tv_app.application.services.data.presentation_suggest_ops_service.TvDataRouteCatalogService",
        return_value=empty_catalog,
    ):
        result = PresentationSuggestOpsService.suggest(
            message="adicione um KPI",
            host_context={"slideId": "slide-1", "playlistId": "pl-1"},
        )
    assert result["ops"] == []
    assert "add_kpi_from_route" in result["matchedCapabilityKeys"]
    assert result.get("clarificationKey") == "suggestNeedOperationId"


def test_suggest_reordenar_sem_items_clarifica():
    result = PresentationSuggestOpsService.suggest(
        message="reordene os slides",
        host_context={"playlistId": "pl-1", "slideId": "s1"},
    )
    assert result["ops"] == []
    assert "reorder_slides" in result["matchedCapabilityKeys"]
    assert result.get("clarificationKey") == "suggestNeedReorder"


def test_suggest_add_chart_view():
    result = PresentationSuggestOpsService.suggest(
        message="adicione um gráfico",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"]
    upsert = next(op for op in result["ops"] if op.get("op") == "upsert_block")
    assert (upsert.get("block") or {}).get("type") == "chart_view"
    assert "add_chart_view" in result["matchedCapabilityKeys"]


def test_suggest_kpi_oee_composite_fonte_view_bind():
    result = PresentationSuggestOpsService.suggest(
        message="adicione um KPI de OEE",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    ops = result["ops"]
    assert len(ops) == 3
    assert {op.get("op") for op in ops} == {
        "upsert_data_source",
        "upsert_block",
        "bind_visual",
    }
    source = next(op for op in ops if op.get("op") == "upsert_data_source")
    assert source.get("operationId") == "get_overall_equipment_effectiveness_pct"
    assert source.get("displayMode") == "kpi"
    visual = next(op for op in ops if op.get("op") == "upsert_block")
    block = visual.get("block") or {}
    assert block.get("type") == "kpi_view"
    bind = next(op for op in ops if op.get("op") == "bind_visual")
    assert bind.get("visualId") == block.get("id")
    assert bind.get("dataSourceId") == source.get("blockId")
    assert "add_kpi_from_route" in result["matchedCapabilityKeys"]


def test_suggest_sql_trap_returns_no_ops():
    result = PresentationSuggestOpsService.suggest(
        message="me mostre o SELECT * FROM SB1",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"] == []


def test_suggest_operation_id_from_host_context():
    result = PresentationSuggestOpsService.suggest(
        message="adicione um KPI",
        host_context={
            "slideId": "slide-1",
            "playlistId": "pl-1",
            "operationId": "get_overall_equipment_effectiveness_pct",
        },
    )
    source = next(op for op in result["ops"] if op.get("op") == "upsert_data_source")
    assert source.get("operationId") == "get_overall_equipment_effectiveness_pct"


def test_suggest_create_modelo_de_dados_oee():
    result = PresentationSuggestOpsService.suggest(
        message="adicione um modelo de dados de OEE",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"]
    assert "create_data_source" in result["matchedCapabilityKeys"]
    source = next(op for op in result["ops"] if op.get("op") == "upsert_data_source")
    assert source.get("operationId") == "get_overall_equipment_effectiveness_pct"
    assert str(source.get("blockId") or "").startswith("ds_")
    assert not any(op.get("op") == "bind_visual" for op in result["ops"])


def test_suggest_modelo_oee_sem_slide_clarifica_antes_do_patch():
    result = PresentationSuggestOpsService.suggest(
        message="adicione o modelo de dados oee",
        host_context={"playlistId": "pl-1"},
    )

    assert result["status"] == "clarification"
    assert result["ops"] == []
    assert result["clarificationKey"] == "suggestNeedSlideOrCreate"
    assert result["requiresSlide"] is True
    assert "slide" in str(result["reason"]).lower()


def test_suggest_criar_slide_sem_slide_aberto_executa_direto():
    result = PresentationSuggestOpsService.suggest(
        message="crie um slide",
        host_context={"playlistId": "pl-1"},
    )

    assert result["status"] == "ready"
    assert result["confirmationPolicy"] == "direct"
    assert result["risk"] == "additive"
    assert result["requiresSlide"] is False
    assert any(op.get("op") == "add_blank_slide" for op in result["ops"])


def test_suggest_excluir_bloco_exige_confirmacao():
    result = PresentationSuggestOpsService.suggest(
        message="apague o bloco",
        host_context={
            "playlistId": "pl-1",
            "slideId": "slide-1",
            "selectedBlockIds": ["block-1"],
        },
    )

    assert result["status"] == "ready"
    assert result["confirmationPolicy"] == "confirm"
    assert result["risk"] == "destructive"
    assert result["ops"] == [{"op": "delete_block", "blockId": "block-1"}]


def test_suggest_mutacao_com_draft_local_nao_emite_ops():
    result = PresentationSuggestOpsService.suggest(
        message="adicione o modelo de dados oee",
        host_context={
            "playlistId": "pl-1",
            "slideId": "slide-1",
            "hasLocalDraft": True,
        },
    )

    assert result["status"] == "clarification"
    assert result["clarificationKey"] == "suggestLocalDraftConflict"
    assert result["ops"] == []
    assert "locais" in str(result["reason"]).lower()


def test_suggest_chart_from_route_oee_composite():
    result = PresentationSuggestOpsService.suggest(
        message="adicione um gráfico de OEE",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    ops = result["ops"]
    assert len(ops) == 3
    assert "add_chart_from_route" in result["matchedCapabilityKeys"]
    source = next(op for op in ops if op.get("op") == "upsert_data_source")
    visual = next(op for op in ops if op.get("op") == "upsert_block")
    assert source.get("operationId") == "get_overall_equipment_effectiveness_pct"
    assert (visual.get("block") or {}).get("type") == "chart_view"


def test_suggest_update_filial_on_selected_source():
    result = PresentationSuggestOpsService.suggest(
        message="mude a filial para 02",
        host_context={
            "slideId": "slide-1",
            "playlistId": "pl-1",
            "dataSourceId": "ds-keep",
            "selectedDataSourceId": "ds-keep",
            "operationId": "get_overall_equipment_effectiveness_pct",
            "dataSources": [
                {
                    "id": "ds-keep",
                    "operationId": "get_overall_equipment_effectiveness_pct",
                    "label": "OEE",
                }
            ],
        },
    )
    assert result["ops"]
    assert "update_data_source" in result["matchedCapabilityKeys"]
    source = next(op for op in result["ops"] if op.get("op") == "upsert_data_source")
    assert source.get("blockId") == "ds-keep"
    assert (source.get("params") or {}).get("branch") == "02"


def test_suggest_bind_visual_with_selection_and_source_list():
    result = PresentationSuggestOpsService.suggest(
        message="ligue à fonte de OEE",
        host_context={
            "slideId": "slide-1",
            "playlistId": "pl-1",
            "selectedVisualId": "viz-1",
            "focusBlockType": "chart_view",
            "dataSources": [
                {
                    "id": "ds-oee",
                    "operationId": "get_overall_equipment_effectiveness_pct",
                    "label": "OEE",
                }
            ],
        },
    )
    assert result["ops"]
    bind = next(op for op in result["ops"] if op.get("op") == "bind_visual")
    assert bind.get("visualId") == "viz-1"
    assert bind.get("dataSourceId") == "ds-oee"


def test_suggest_transform_top_10():
    result = PresentationSuggestOpsService.suggest(
        message="manter top 10 na fonte",
        host_context={
            "slideId": "slide-1",
            "playlistId": "pl-1",
            "dataSourceId": "ds-1",
            "selectedDataSourceId": "ds-1",
            "operationId": "get_supplies_stock_value",
            "dataSources": [
                {
                    "id": "ds-1",
                    "operationId": "get_supplies_stock_value",
                    "label": "Estoque",
                }
            ],
        },
    )
    assert result["ops"]
    transform = next(op for op in result["ops"] if op.get("op") == "set_data_transform")
    assert transform.get("blockId") == "ds-1"
    steps = transform.get("steps") or []
    assert steps and steps[0].get("op") == "keepRows"
    assert steps[0].get("count") == 10


def test_suggest_field_labels_rename():
    result = PresentationSuggestOpsService.suggest(
        message='renomeie o campo "value" para "OEE"',
        host_context={
            "slideId": "slide-1",
            "playlistId": "pl-1",
            "dataSourceId": "ds-1",
            "selectedDataSourceId": "ds-1",
            "operationId": "get_overall_equipment_effectiveness_pct",
            "dataSources": [
                {
                    "id": "ds-1",
                    "operationId": "get_overall_equipment_effectiveness_pct",
                    "label": "OEE",
                }
            ],
        },
    )
    assert result["ops"]
    source = next(op for op in result["ops"] if op.get("op") == "upsert_data_source")
    assert source.get("blockId") == "ds-1"
    assert (source.get("fieldLabels") or {}).get("value") == "OEE"


def test_suggest_modelo_de_dados_generico_selection_pending():
    """Pedido genérico de modelo sem vencedor claro → candidatos, sem inventar rota."""
    result = PresentationSuggestOpsService.suggest(
        message="adicione o modelo de dados",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["status"] == "selection_pending"
    assert result["ops"] == []
    assert result["clarificationKey"] == "suggestNeedRouteSelection"
    assert isinstance(result.get("candidates"), list)
    assert len(result["candidates"]) >= 2
    assert all(c.get("operationId") for c in result["candidates"])


def test_suggest_resume_explicit_operation_ids_creates_sources():
    result = PresentationSuggestOpsService.suggest(
        message=(
            "adicione no slide as fontes: get_overall_equipment_effectiveness_pct, "
            "get_product_detail"
        ),
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["status"] == "ready"
    sources = [op for op in result["ops"] if op.get("op") == "upsert_data_source"]
    ids = {op.get("operationId") for op in sources}
    assert "get_overall_equipment_effectiveness_pct" in ids
    assert "get_product_detail" in ids


def test_selection_evidence_failure_keeps_candidates():
    from tv_app.application.services.data.tv_catalog_selection_evidence_service import (
        TvCatalogSelectionEvidenceService,
    )

    def _boom(*_args, **_kwargs):
        raise RuntimeError("preview down")

    enriched = TvCatalogSelectionEvidenceService.enrich(
        [
            {
                "operationId": "get_overall_equipment_effectiveness_pct",
                "label": "OEE",
                "score": 9.0,
            }
        ],
        preview_fn=_boom,
    )
    assert len(enriched) == 1
    assert enriched[0]["operationId"] == "get_overall_equipment_effectiveness_pct"
    assert "evidence" not in enriched[0]


def test_selection_evidence_from_preview_payload():
    from tv_app.application.services.data.tv_catalog_selection_evidence_service import (
        TvCatalogSelectionEvidenceService,
    )

    def _ok(*_args, **_kwargs):
        return {
            "resolved": {
                "data": {
                    "items": [
                        {"filial": "01", "oee": 0.82},
                        {"filial": "02", "oee": 0.77},
                    ]
                }
            }
        }

    enriched = TvCatalogSelectionEvidenceService.enrich(
        [{"operationId": "get_oee", "label": "OEE", "score": 8.0}],
        preview_fn=_ok,
    )
    evidence = enriched[0].get("evidence")
    assert evidence["shape"] == "table"
    assert "filial" in evidence["columns"]
    assert len(evidence["rows"]) == 2


def test_suggest_rename_data_source_label_only():
    result = PresentationSuggestOpsService.suggest(
        message=(
            'Renomeie a fonte "WEG SC · setembro 2025" para '
            '"WEG SC · setembro ano passado", preservando toda a configuração da fonte.'
        ),
        host_context={
            "slideId": "slide-1",
            "playlistId": "pl-1",
            "selectedDataSourceId": "ds-weg-sep-2025",
            "dataSources": [
                {
                    "id": "ds-weg-sep-2025",
                    "operationId": "get_sales_order_otd_series",
                    "label": "WEG SC · setembro 2025",
                }
            ],
        },
    )
    assert result["status"] == "ready"
    assert "rename_data_source_label" in result["matchedCapabilityKeys"]
    ops = [op for op in result["ops"] if op.get("op") == "upsert_data_source"]
    assert len(ops) == 1
    source = ops[0]
    assert source.get("blockId") == "ds-weg-sep-2025"
    assert source.get("label") == "WEG SC · setembro ano passado"
    assert "operationId" not in source or not source.get("operationId")
    assert not source.get("params")
    assert not source.get("dataTransform")


# ---------------------------------------------------------------------------
# TV-DM-MUT-002 — DataModel vs legacy routing (fail-closed, no legacy ops on models)
# ---------------------------------------------------------------------------

_MODEL_HOST = {
    "slideId": "s1",
    "playlistId": "pl-1",
    "dataSources": [
        {"id": "ds-1", "operationId": "get_vendas", "label": "Vendas"}
    ],
    "dataModels": [
        {
            "id": "mdl_1",
            "label": "Mensal",
            "inputs": [
                {"id": "in_a", "label": "Atual", "operationId": "get_vendas"}
            ],
        }
    ],
}


def test_suggest_model_intent_routes_patch_data_model():
    result = PresentationSuggestOpsService.suggest(
        message="defina o transform do modelo com top 10",
        host_context=dict(_MODEL_HOST),
    )
    ops = [op for op in result["ops"] if op.get("op") == "patch_data_model"]
    assert len(ops) == 1
    assert ops[0]["modelId"] == "mdl_1"
    assert ops[0]["modelPatch"]["transform"]["steps"][0]["op"] == "keepRows"
    assert not any(
        op.get("op") in ("set_data_transform", "patch_data_source_params")
        for op in result["ops"]
    )


def test_suggest_model_rename_routes_patch_not_legacy_rename():
    result = PresentationSuggestOpsService.suggest(
        message='renomeie o modelo para "Anual"',
        host_context=dict(_MODEL_HOST),
    )
    ops = result["ops"]
    assert len(ops) == 1
    assert ops[0]["op"] == "patch_data_model"
    assert ops[0]["modelPatch"]["label"] == "Anual"
    assert not any(op.get("op") == "upsert_data_source" for op in ops)


def test_suggest_model_input_transform_targets_input():
    result = PresentationSuggestOpsService.suggest(
        message="defina o transform do input Atual do modelo com top 5",
        host_context=dict(_MODEL_HOST),
    )
    ops = [op for op in result["ops"] if op.get("op") == "patch_data_model"]
    assert len(ops) == 1
    patch = ops[0]["inputPatches"][0]
    assert patch["inputId"] == "in_a"
    assert patch["transform"]["steps"][0]["count"] == 5


def test_suggest_legacy_source_intent_stays_on_source_ops():
    result = PresentationSuggestOpsService.suggest(
        message="troque o transform da fonte para top 5",
        host_context=dict(_MODEL_HOST),
    )
    ops = [op for op in result["ops"] if op.get("op") == "set_data_transform"]
    assert len(ops) == 1
    assert ops[0]["blockId"] == "ds-1"
    assert not any(op.get("op") == "patch_data_model" for op in result["ops"])


def test_suggest_model_intent_without_model_fails_closed():
    """Vocabulário de modelo sem modelo resolvível → clarificação, nunca op
    com modelId vazio nem fallback para op legacy."""
    result = PresentationSuggestOpsService.suggest(
        message="mude o período do modelo",
        host_context={
            "slideId": "s1",
            "playlistId": "pl-1",
            "dataSources": _MODEL_HOST["dataSources"],
        },
    )
    assert not result["ops"]
    assert result.get("clarificationKey")
    assert "patch_data_model" in result["matchedCapabilityKeys"]


def test_suggest_ambiguous_multi_model_fails_closed():
    host = dict(_MODEL_HOST)
    host["dataModels"] = [
        {"id": "mdl_1", "label": "Mensal"},
        {"id": "mdl_2", "label": "Anual"},
    ]
    result = PresentationSuggestOpsService.suggest(
        message="defina o transform do modelo com top 10",
        host_context=host,
    )
    assert not result["ops"]
    assert result.get("clarificationKey")


def test_suggest_model_param_patch_uses_explicit_params_only():
    """Sem param explícito a op não inventa dateRangePreset — clarifica."""
    result = PresentationSuggestOpsService.suggest(
        message="atualize o modelo",
        host_context=dict(_MODEL_HOST),
    )
    assert not result["ops"]
    assert result.get("clarificationKey")


# ---------------------------------------------------------------------------
# VISTA-SUGGEST-CHANGE-EXISTING-BLOCK-GROUNDING-FIX
# Pedido de alteração num bloco existente selecionado deve materializar
# ALTER_EXISTING canônico (upsert_block com blockId + delta parcial),
# nunca um novo bloco txt_* com createIfMissing:true.
# ---------------------------------------------------------------------------

_SELECTED_BLOCK_HOST = {
    "slideId": "slide-1",
    "playlistId": "pl-1",
    "selectedBlockId": "vista_knowledge_title",
    "selectedBlockIds": ["vista_knowledge_title"],
    "selectedBlockTypes": ["heading"],
    "focusBlockId": "vista_knowledge_title",
    "focusBlockType": "heading",
}


def test_suggest_absolute_font_size_targets_selected_block_alter_existing():
    """Regressão central: «de 48 para 56» no bloco selecionado emite patch
    parcial canônico (blockId + style.fontSize), nunca ghost txt_*."""
    result = PresentationSuggestOpsService.suggest(
        message=(
            "Aumente o tamanho da fonte do título principal "
            "de 48 para 56, mantendo o mesmo bloco."
        ),
        host_context=dict(_SELECTED_BLOCK_HOST),
    )
    assert result["status"] == "ready"
    assert result["ops"] == [
        {
            "op": "upsert_block",
            "blockId": "vista_knowledge_title",
            "block": {
                "id": "vista_knowledge_title",
                "type": "heading",
                "style": {"fontSize": 56},
            },
        }
    ]
    upsert = result["ops"][0]
    assert upsert.get("createIfMissing") is not True
    block = upsert["block"]
    assert not str(block.get("id") or "").startswith("txt_")
    assert "content" not in block
    assert block.get("type") == "heading"
    assert "update_block" in result["matchedCapabilityKeys"]


def test_suggest_alter_existing_font_size_patch_preserves_block_on_apply():
    """O candidato materializado, aplicado via merge canônico, preserva
    type/content/frame e demais style do bloco existente."""
    from types import SimpleNamespace
    from uuid import uuid4

    from tv_app.application.services.data.presentation_mutation import (
        PresentationPatchService,
    )
    from tv_app.application.services.data.presentation_ops_content_service import (
        PresentationOpsContentService,
    )

    result = PresentationSuggestOpsService.suggest(
        message=(
            "Aumente o tamanho da fonte do título principal "
            "de 48 para 56, mantendo o mesmo bloco."
        ),
        host_context=dict(_SELECTED_BLOCK_HOST),
    )
    assert len(result["ops"]) == 1
    candidate = result["ops"][0]

    playlist_id = str(uuid4())
    slide_id = str(uuid4())

    class _Repo:
        def get_by_id(self, pid):
            return {"id": str(pid), "revision": 3, "dataDefaults": {}}

        def get_slide(self, sid, playlist_id=None):
            return {
                "id": str(sid),
                "nativeConfig": {
                    "version": 5,
                    "blocks": [
                        {
                            "id": "vista_knowledge_title",
                            "type": "heading",
                            "content": "O que a VISTA conhece",
                            "frame": {"x": 5, "y": 12, "w": 90, "h": 18},
                            "style": {
                                "fontSize": 48,
                                "color": "#ffffff",
                                "fontWeight": "bold",
                            },
                        }
                    ],
                },
            }

    svc = PresentationPatchService(repo=_Repo())
    applied = svc.preview(
        {
            "target": {"playlistId": playlist_id, "slideId": slide_id},
            "ops": [candidate],
            "catalogVersion": PresentationOpsContentService.catalog_version(),
        },
        user=SimpleNamespace(is_superadmin=True, permissions=[], id="u1"),
    )
    blocks = applied["nativeConfig"]["blocks"]
    assert len(blocks) == 1
    block = blocks[0]
    assert block["id"] == "vista_knowledge_title"
    assert block["type"] == "heading"
    assert block["content"] == "O que a VISTA conhece"
    assert block["frame"] == {"x": 5, "y": 12, "w": 90, "h": 18}
    assert block["style"]["fontSize"] == 56
    assert block["style"]["color"] == "#ffffff"
    assert block["style"]["fontWeight"] == "bold"


def test_suggest_relative_font_size_bumps_selected_block_no_ghost():
    """«Aumente a fonte do título» → bump_font_size relativo no alvo —
    sem upsert_block de criação parasita."""
    result = PresentationSuggestOpsService.suggest(
        message="Aumente a fonte do título",
        host_context=dict(_SELECTED_BLOCK_HOST),
    )
    assert result["ops"] == [
        {
            "op": "bump_font_size",
            "blockId": "vista_knowledge_title",
            "deltaSteps": 1,
        }
    ]
    assert all(op.get("op") != "upsert_block" for op in result["ops"])


def test_suggest_muda_texto_do_titulo_altera_bloco_selecionado():
    """«Mude o texto do título para "Novo título"» → patch de content no
    bloco existente; o literal entre aspas não pode disparar criação."""
    result = PresentationSuggestOpsService.suggest(
        message='Mude o texto do título para "Novo título"',
        host_context=dict(_SELECTED_BLOCK_HOST),
    )
    assert result["ops"] == [
        {
            "op": "upsert_block",
            "blockId": "vista_knowledge_title",
            "block": {
                "id": "vista_knowledge_title",
                "type": "heading",
                "content": "Novo título",
            },
        }
    ]
    assert result["ops"][0].get("createIfMissing") is not True


def test_suggest_cor_do_titulo_altera_bloco_selecionado_style():
    """«Altere a cor do título para azul» → style.color no bloco existente;
    nunca patch de fundo do slide nem ghost."""
    result = PresentationSuggestOpsService.suggest(
        message="Altere a cor do título para azul",
        host_context=dict(_SELECTED_BLOCK_HOST),
    )
    assert result["ops"] == [
        {
            "op": "upsert_block",
            "blockId": "vista_knowledge_title",
            "block": {
                "id": "vista_knowledge_title",
                "type": "heading",
                "style": {"color": "#2563eb"},
            },
        }
    ]
    assert result["ops"][0].get("createIfMissing") is not True


def test_suggest_deixe_fonte_maior_bump_sem_ghost():
    """«Deixe a fonte do título maior» → bump relativo no alvo selecionado."""
    result = PresentationSuggestOpsService.suggest(
        message="Deixe a fonte do título maior",
        host_context=dict(_SELECTED_BLOCK_HOST),
    )
    assert result["ops"] == [
        {
            "op": "bump_font_size",
            "blockId": "vista_knowledge_title",
            "deltaSteps": 1,
        }
    ]


def test_suggest_aumente_fonte_para_absoluto_gera_patch_nao_bump():
    """«para 56» é alvo absoluto — patch exato vence o bump relativo."""
    result = PresentationSuggestOpsService.suggest(
        message="Aumente a fonte do título para 56",
        host_context=dict(_SELECTED_BLOCK_HOST),
    )
    assert result["ops"] == [
        {
            "op": "upsert_block",
            "blockId": "vista_knowledge_title",
            "block": {
                "id": "vista_knowledge_title",
                "type": "heading",
                "style": {"fontSize": 56},
            },
        }
    ]
    assert all(op.get("op") != "bump_font_size" for op in result["ops"])


def test_suggest_crie_novo_bloco_de_texto_single_typed_create():
    """«Crie um novo bloco de texto» → exatamente UMA criação canônica:
    create_block tipado (typed create), nunca upsert_block txt_* +
    create_block para a mesma intenção."""
    result = PresentationSuggestOpsService.suggest(
        message="Crie um novo bloco de texto",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"] == [{"op": "create_block", "type": "text"}]
    assert result["matchedCapabilityKeys"] == ["create_block"]


def test_suggest_crie_novo_bloco_de_titulo_single_typed_create():
    """«Crie um novo bloco de título» → uma única criação tipada heading."""
    result = PresentationSuggestOpsService.suggest(
        message="Crie um novo bloco de título",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"] == [{"op": "create_block", "type": "heading"}]


def test_suggest_adicione_um_bloco_de_texto_single_typed_create():
    """«Adicione um bloco de texto» → typed create único (path existente)."""
    result = PresentationSuggestOpsService.suggest(
        message="Adicione um bloco de texto",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"] == [{"op": "create_block", "type": "text"}]


def test_suggest_crie_novo_bloco_sem_tipo_clarifica():
    """«Crie um novo bloco» sem tipo resolvível → clarificação de tipo;
    nunca default silencioso para text."""
    result = PresentationSuggestOpsService.suggest(
        message="Crie um novo bloco",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"] == []
    assert result.get("clarificationKey")


def test_suggest_crie_novo_bloco_de_texto_continua_criando():
    """«Crie um novo bloco de texto» aplicado no write layer cria
    exatamente UM bloco novo (regressão do duplo-create persistido)."""
    from types import SimpleNamespace
    from uuid import uuid4

    from tv_app.application.services.data.presentation_mutation import (
        PresentationPatchService,
    )
    from tv_app.application.services.data.presentation_ops_content_service import (
        PresentationOpsContentService,
    )

    result = PresentationSuggestOpsService.suggest(
        message="Crie um novo bloco de texto",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert len(result["ops"]) == 1

    playlist_id = str(uuid4())
    slide_id = str(uuid4())

    class _Repo:
        def get_by_id(self, pid):
            return {"id": str(pid), "revision": 3, "dataDefaults": {}}

        def get_slide(self, sid, playlist_id=None):
            return {
                "id": str(sid),
                "nativeConfig": {
                    "version": 5,
                    "blocks": [
                        {
                            "id": "vista_knowledge_title",
                            "type": "heading",
                            "content": "O que a VISTA conhece",
                            "frame": {"x": 5, "y": 12, "w": 90, "h": 18},
                            "style": {"fontSize": 48},
                        }
                    ],
                },
            }

    svc = PresentationPatchService(repo=_Repo())
    applied = svc.preview(
        {
            "target": {"playlistId": playlist_id, "slideId": slide_id},
            "ops": result["ops"],
            "catalogVersion": PresentationOpsContentService.catalog_version(),
        },
        user=SimpleNamespace(is_superadmin=True, permissions=[], id="u1"),
    )
    blocks = applied["nativeConfig"]["blocks"]
    assert len(blocks) == 2
    new_blocks = [b for b in blocks if b.get("id") != "vista_knowledge_title"]
    assert len(new_blocks) == 1
    assert new_blocks[0]["type"] == "text"


def test_suggest_criacao_com_bloco_selecionado_nao_vira_update():
    """«Crie um novo bloco de texto abaixo do título» com seleção → CREATE;
    a seleção sozinha não força ALTER_EXISTING."""
    result = PresentationSuggestOpsService.suggest(
        message="Crie um novo bloco de texto abaixo do título",
        host_context=dict(_SELECTED_BLOCK_HOST),
    )
    assert result["ops"] == [{"op": "create_block", "type": "text"}]
    assert not any(
        op.get("blockId") == "vista_knowledge_title" for op in result["ops"]
    )


def test_suggest_crie_novo_titulo_cria_heading():
    """«Crie um novo título» → criação tipada (heading), não text genérico."""
    result = PresentationSuggestOpsService.suggest(
        message="Crie um novo título",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    upsert = next(op for op in result["ops"] if op.get("op") == "upsert_block")
    block = upsert.get("block") or {}
    assert str(block.get("id") or "").startswith("txt_")
    assert block.get("type") == "heading"
    assert upsert.get("createIfMissing") is True


@pytest.mark.parametrize(
    ("message", "expected_content"),
    [
        ('Crie um bloco de texto com conteúdo "Teste"', "Teste"),
        ('Crie um bloco de texto escrito "Teste"', "Teste"),
        ('Crie um bloco de texto com conteúdo "Olá, mundo!"', "Olá, mundo!"),
        ('Crie um bloco de texto com conteúdo "123"', "123"),
    ],
)
def test_suggest_crie_bloco_de_texto_com_conteudo_preserva_content(
    message, expected_content
):
    """«Crie um bloco de texto com conteúdo "X"» → typed create único
    carregando o conteúdo citado verbatim no campo content do contrato."""
    result = PresentationSuggestOpsService.suggest(
        message=message,
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert len(result["ops"]) == 1
    op = result["ops"][0]
    assert op["op"] == "create_block"
    assert op["type"] == "text"
    assert op["content"] == expected_content
    assert "create_block" in result["matchedCapabilityKeys"]


def test_suggest_crie_bloco_de_titulo_com_texto_preserva_content():
    """Sibling heading: grammar «bloco de título» roteia para create_block
    e preserva o conteúdo citado."""
    result = PresentationSuggestOpsService.suggest(
        message='Crie um bloco de título com texto "Teste"',
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"] == [
        {"op": "create_block", "type": "heading", "content": "Teste"}
    ]


@pytest.mark.parametrize(
    ("message", "expected_type"),
    [
        ("Crie uma forma", "shape"),
        ("Adicione um ícone", "icon"),
        ("Crie um novo bloco de texto", "text"),
        ("Crie um novo bloco de título", "heading"),
    ],
)
def test_suggest_create_block_sem_conteudo_nao_inventa_content(
    message, expected_type
):
    """Sem conteúdo citado, o op create_block omite content — nunca
    injeta "" (neutro para text/heading, mas semântico para icon/shape)."""
    result = PresentationSuggestOpsService.suggest(
        message=message,
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"] == [{"op": "create_block", "type": expected_type}]
    assert "content" not in result["ops"][0]
    assert "iconName" not in result["ops"][0]


def test_suggest_create_block_com_content_aplica_no_write_layer():
    """«Crie um bloco de texto com conteúdo "Teste"» aplicado no write
    layer cria exatamente UM bloco cujo content é "Teste"."""
    from types import SimpleNamespace
    from uuid import uuid4

    from tv_app.application.services.data.presentation_mutation import (
        PresentationPatchService,
    )
    from tv_app.application.services.data.presentation_ops_content_service import (
        PresentationOpsContentService,
    )

    result = PresentationSuggestOpsService.suggest(
        message='Crie um bloco de texto com conteúdo "Teste"',
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert len(result["ops"]) == 1

    playlist_id = str(uuid4())
    slide_id = str(uuid4())

    class _Repo:
        def get_by_id(self, pid):
            return {"id": str(pid), "revision": 3, "dataDefaults": {}}

        def get_slide(self, sid, playlist_id=None):
            return {
                "id": str(sid),
                "nativeConfig": {
                    "version": 5,
                    "blocks": [
                        {
                            "id": "vista_knowledge_title",
                            "type": "heading",
                            "content": "O que a VISTA conhece",
                            "frame": {"x": 5, "y": 12, "w": 90, "h": 18},
                            "style": {"fontSize": 48},
                        }
                    ],
                },
            }

    svc = PresentationPatchService(repo=_Repo())
    applied = svc.preview(
        {
            "target": {"playlistId": playlist_id, "slideId": slide_id},
            "ops": result["ops"],
            "catalogVersion": PresentationOpsContentService.catalog_version(),
        },
        user=SimpleNamespace(is_superadmin=True, permissions=[], id="u1"),
    )
    blocks = applied["nativeConfig"]["blocks"]
    assert len(blocks) == 2
    new_blocks = [b for b in blocks if b.get("id") != "vista_knowledge_title"]
    assert len(new_blocks) == 1
    assert new_blocks[0]["type"] == "text"
    assert new_blocks[0]["content"] == "Teste"


def test_suggest_edit_sem_selecao_clarifica_nao_cria_ghost():
    """«Mude o título para "X"» sem alvo resolvível → clarificação canônica,
    nunca bloco fantasma criado a partir do substantivo."""
    result = PresentationSuggestOpsService.suggest(
        message='Mude o título para "Novo título"',
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"] == []
    assert result.get("clarificationKey") == "suggestNeedSelection"
    assert "update_block" in result["matchedCapabilityKeys"]
    assert "upsert_block" not in result["matchedCapabilityKeys"]


def test_suggest_edit_sem_delta_suportado_clarifica_nao_cria():
    """«Atualize o título» com seleção mas sem delta reconhecido → clarificação;
    nunca upsert vazio nem ghost."""
    result = PresentationSuggestOpsService.suggest(
        message="Atualize o título",
        host_context=dict(_SELECTED_BLOCK_HOST),
    )
    assert result["ops"] == []
    assert result.get("clarificationKey")
    assert "update_block" in result["matchedCapabilityKeys"]
