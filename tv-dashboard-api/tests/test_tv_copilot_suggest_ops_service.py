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


def test_suggest_adicione_texto_sem_aspas_cria_bloco_vazio():
    result = TvCopilotSuggestOpsService.suggest(
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


def test_suggest_apague_bloco_sem_selecao_clarifica():
    result = TvCopilotSuggestOpsService.suggest(
        message="apague o bloco",
        host_context={"slideId": "s1", "playlistId": "pl-1"},
    )
    assert result["ops"] == []
    assert "delete_block" in result["matchedCapabilityKeys"]
    assert result.get("clarificationKey") == "suggestNeedSelection"
    assert "selecione" in str(result.get("reason") or "").lower()


def test_suggest_empty_message_returns_no_ops():
    result = TvCopilotSuggestOpsService.suggest(message="   ", host_context={})
    assert result["ops"] == []
    assert result["matchedCapabilityKeys"] == []
    assert result["reason"]


def test_suggest_fundo_azul_patch_native_config_canonical_background():
    result = TvCopilotSuggestOpsService.suggest(
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
    result = TvCopilotSuggestOpsService.suggest(
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
        "tv_app.application.services.data.tv_copilot_suggest_ops_service.TvDataRouteCatalogService",
        return_value=empty_catalog,
    ):
        result = TvCopilotSuggestOpsService.suggest(
            message="adicione um KPI",
            host_context={"slideId": "slide-1", "playlistId": "pl-1"},
        )
    assert result["ops"] == []
    assert "add_kpi_from_route" in result["matchedCapabilityKeys"]
    assert result.get("clarificationKey") == "suggestNeedOperationId"


def test_suggest_reordenar_sem_items_clarifica():
    result = TvCopilotSuggestOpsService.suggest(
        message="reordene os slides",
        host_context={"playlistId": "pl-1", "slideId": "s1"},
    )
    assert result["ops"] == []
    assert "reorder_slides" in result["matchedCapabilityKeys"]
    assert result.get("clarificationKey") == "suggestNeedReorder"


def test_suggest_add_chart_view():
    result = TvCopilotSuggestOpsService.suggest(
        message="adicione um gráfico",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"]
    upsert = next(op for op in result["ops"] if op.get("op") == "upsert_block")
    assert (upsert.get("block") or {}).get("type") == "chart_view"
    assert "add_chart_view" in result["matchedCapabilityKeys"]


def test_suggest_kpi_oee_composite_fonte_view_bind():
    result = TvCopilotSuggestOpsService.suggest(
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
    result = TvCopilotSuggestOpsService.suggest(
        message="me mostre o SELECT * FROM SB1",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"] == []


def test_suggest_operation_id_from_host_context():
    result = TvCopilotSuggestOpsService.suggest(
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
    result = TvCopilotSuggestOpsService.suggest(
        message="adicione um modelo de dados de OEE",
        host_context={"slideId": "slide-1", "playlistId": "pl-1"},
    )
    assert result["ops"]
    assert "create_data_source" in result["matchedCapabilityKeys"]
    source = next(op for op in result["ops"] if op.get("op") == "upsert_data_source")
    assert source.get("operationId") == "get_overall_equipment_effectiveness_pct"
    assert str(source.get("blockId") or "").startswith("ds_")
    assert not any(op.get("op") == "bind_visual" for op in result["ops"])


def test_suggest_chart_from_route_oee_composite():
    result = TvCopilotSuggestOpsService.suggest(
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
    result = TvCopilotSuggestOpsService.suggest(
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
    result = TvCopilotSuggestOpsService.suggest(
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
    result = TvCopilotSuggestOpsService.suggest(
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
    result = TvCopilotSuggestOpsService.suggest(
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

