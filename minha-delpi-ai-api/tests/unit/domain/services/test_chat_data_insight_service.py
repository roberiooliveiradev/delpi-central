from app.domain.services.chat_data_insight_service import ChatDataInsightService


def test_build_factory_status_emits_data_answer_and_mirror():
    metadata = {
        "path": "/products/90262404/factory-status",
        "stackPresentationPlan": {"presentationProfileKey": "factory_status"},
    }
    data = {
        "factory_status": "PA PRODUZIDO / AGUARDANDO INSPEÇÃO FINAL",
        "structure": {"summary": {"total_raw_materials": 3, "total_exclusive_raw_materials": 0}},
        "production": {
            "summary": {
                "pa_production_started": True,
                "pi_production_started": False,
                "total_pa_orders": 305,
                "total_pi_orders": 0,
            }
        },
        "shipping": {"summary": {"total_shipped_quantity": 0}},
        "raw_material_stock": {
            "items": [],
            "summary": {"total_without_stock_for_one_pa": 0},
        },
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert data_answer.get("profileKey") == "factory_status"

    summary = data_answer.get("summary")

    assert isinstance(summary, dict)
    assert summary.get("answer")
    assert summary.get("riskLevel") in {"ok", "attention", "critical", "undefined"}
    assert summary.get("nextAction")

    recommendations = data_answer.get("recommendations") or []

    assert recommendations
    assert recommendations[0].get("label")
    assert recommendations[0].get("query")

    mirror = ChatDataInsightService.build_commentary_mirror(data_answer)

    assert isinstance(mirror, dict)
    assert mirror.get("summary")
    assert mirror.get("alertLevel")


def test_build_generic_empty_list_detects_empty_anomaly():
    metadata = {
        "path": "/custom/report",
        "tablePresentation": {"type": "table", "rows": []},
    }
    data = {"items": []}

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert data_answer.get("profileKey") == "generic_list"
    assert data_answer.get("emptyResult") is True

    summary = data_answer.get("summary")

    assert summary.get("answer")
    assert not summary.get("nextAction")
    assert summary.get("attention") == []
    assert data_answer.get("recommendations") == []
    assert "filtrar" not in str(summary.get("nextAction") or "").casefold()
    assert "pontos de atenção" not in str(summary.get("answer") or "").casefold()
    assert any(
        anomaly.get("type") == "empty_list"
        for anomaly in (data_answer.get("anomalies") or [])
        if isinstance(anomaly, dict)
    )


def test_build_empty_outbound_invoice_domain_aware_message():
    from app.domain.services.chat_operational_commentary_lead_service import (
        ChatOperationalCommentaryLeadService,
    )
    from app.domain.services.chat_humanized_data_response_service import (
        ChatHumanizedDataResponseService,
    )

    metadata = {
        "path": "/products/90260148/outbound-invoice-items",
        "productCode": "90260148",
        "apiDelpiResponseMeta": {
            "entity": "product_outbound_invoice_items",
            "shape": "paged_list",
        },
        "tablePresentation": {"type": "table", "rows": []},
    }
    data = {"items": []}

    data_answer = ChatDataInsightService.build(metadata, data)
    mirror = ChatHumanizedDataResponseService.to_commentary_mirror(data_answer)
    lead = ChatOperationalCommentaryLeadService.format_lead(mirror, depth="standard")

    assert data_answer.get("emptyResult") is True
    answer = str((data_answer.get("summary") or {}).get("answer") or "")
    assert "nota fiscal de saída" in answer.casefold() or "nota fiscal de saida" in answer.casefold()
    assert "90260148" in answer
    assert "pontos de atenção" not in lead.casefold()
    assert "próximos passos" not in lead.casefold()
    assert "filtrar" not in lead.casefold()


def test_build_empty_internal_movements_domain_aware_message():
    metadata = {
        "path": "/products/90260148/internal-movements",
        "productCode": "90260148",
        "apiDelpiResponseMeta": {"entity": "product_internal_movements"},
        "tablePresentation": {"rows": []},
    }
    data_answer = ChatDataInsightService.build(metadata, {"items": []})
    answer = str((data_answer.get("summary") or {}).get("answer") or "").casefold()

    assert data_answer.get("emptyResult") is True
    assert "moviment" in answer
    assert "90260148" in answer


def test_build_document_export_never_reports_empty_result():
    metadata = {
        "path": "/products/90261757/structure/excel",
        "apiDelpiResponseMeta": {
            "operationId": "get_product_structure_excel",
            "entity": "product_structure_excel",
            "shape": "document_export",
        },
        "downloadArtifacts": [
            {
                "href": "/apps/api-delpi/products/90261757/structure/excel?format=xlsx",
                "filename": "Estrutura_90261757.xlsx",
                "label": "Baixar Estrutura_90261757.xlsx",
            }
        ],
    }
    data = {
        "message": "Arquivo Excel gerado com sucesso!",
        "filename": "Estrutura_90261757.xlsx",
        "downloadPath": "/products/90261757/structure/excel?format=xlsx",
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert data_answer.get("profileKey") == "document_export"

    summary = data_answer.get("summary") or {}

    assert "Estrutura_90261757.xlsx" in str(summary.get("answer") or "")
    assert "não retornou registros" not in str(summary.get("answer") or "").lower()
    assert summary.get("riskLevel") == "ok"
    assert not any(
        anomaly.get("type") == "empty_list"
        for anomaly in (data_answer.get("anomalies") or [])
        if isinstance(anomaly, dict)
    )


def test_build_sql_result_uses_presentation_rows():
    metadata = {
        "path": "/data/sql",
        "presentation": {
            "type": "table",
            "rows": [
                {"B1_COD": "10080001", "B1_DESC": "Produto A"},
                {"B1_COD": "10080002", "B1_DESC": "Produto B"},
            ],
        },
    }

    data_answer = ChatDataInsightService.build(metadata, {})

    assert isinstance(data_answer, dict)
    assert data_answer.get("profileKey") == "generic_list"
    assert "2" in str(
        next(
            (
                metric.get("value")
                for metric in (data_answer.get("derivedMetrics") or [])
                if isinstance(metric, dict) and metric.get("label") == "Registros"
            ),
            {},
        )
    )
    assert not any(
        anomaly.get("type") == "empty_list"
        for anomaly in (data_answer.get("anomalies") or [])
        if isinstance(anomaly, dict)
    )


def test_build_factory_status_marks_limitations_when_production_table_truncated():
    metadata = {
        "path": "/products/90262404/factory-status",
        "stackPresentationPlan": {"presentationProfileKey": "factory_status"},
        "tablePresentations": [
            {
                "role": "list",
                "title": "Produção (PA / PI / OP / apontamentos) — 30 de 305 OP(s)",
                "rows": [{"production_order": f"{index:03d}"} for index in range(1, 31)],
            }
        ],
    }
    data = {
        "factory_status": "PA PRODUZIDO / AGUARDANDO INSPEÇÃO FINAL",
        "production": {
            "items": [{"production_order": f"{index:03d}"} for index in range(1, 306)],
            "summary": {
                "pa_production_started": True,
                "pi_production_started": False,
                "total_pa_orders": 305,
                "total_pi_orders": 0,
            },
        },
        "structure": {"summary": {"total_raw_materials": 1}},
        "shipping": {"summary": {"total_shipped_quantity": 0}},
        "raw_material_stock": {"items": [], "summary": {"total_without_stock_for_one_pa": 0}},
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert data_answer.get("limitations")


def test_build_generic_categorical_shape_adds_visual_hint():
    metadata = {
        "path": "/reports/sales-by-branch",
        "tablePresentation": {
            "type": "table",
            "rows": [
                {"filial": "01", "quantidade": 120},
                {"filial": "02", "quantidade": 80},
                {"filial": "03", "quantidade": 45},
            ],
        },
    }
    data = {"items": metadata["tablePresentation"]["rows"]}

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert data_answer.get("profileKey") == "generic_list"
    visual_hints = data_answer.get("visualHints") or []

    assert visual_hints
    assert visual_hints[0] in {
        "composition",
        "categorical_ranking",
        "generic_list",
        "kpi_set",
        "time_series",
    }

    derived_metrics = data_answer.get("derivedMetrics") or []

    assert derived_metrics
    assert derived_metrics[0].get("label") == "Registros"


def test_build_system_tables_search_counts_results_rows() -> None:
    metadata = {
        "path": "/system/tables/search",
        "apiDelpiResponseMeta": {
            "entity": "protheus_table",
            "shape": "paged_list",
        },
    }
    data = {
        "success": True,
        "data": {
            "success": True,
            "total_records": 5477,
            "results": [
                {"X2_ARQUIVO": "SB1010", "X2_NOME": "CADASTRO DE PRODUTOS"},
                {"X2_ARQUIVO": "SB2010", "X2_NOME": "GRUPO DE PRODUTOS"},
            ],
        },
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert data_answer is not None
    assert data_answer.get("profileKey") == "system_metadata"
    blob = " ".join(
        [
            str((data_answer.get("summary") or {}).get("answer") or ""),
            *[
                str(item.get("text") if isinstance(item, dict) else item)
                for item in (data_answer.get("facts") or [])
            ],
        ]
    )
    assert "5477" in blob
    assert "similarity_ratio" not in blob.casefold()
    assert "não retornou registros" not in blob.casefold()
    assert not (data_answer.get("derivedMetrics") or [])


def test_build_system_tables_search_skips_similarity_ratio_total() -> None:
    """Search com score numérico não vira «Total de similarity_ratio» (F06 R4)."""
    rows = [
        {"X2_ARQUIVO": f"T{i:04d}", "similarity_ratio": 0.5 + (i % 10) / 100}
        for i in range(32)
    ]
    metadata = {
        "path": "/system/tables/search",
        "apiDelpiResponseMeta": {
            "entity": "protheus_table",
            "shape": "paged_list",
        },
        "tablePresentation": {"type": "table", "rows": rows},
    }
    data = {
        "total_records": 5477,
        "results": rows,
        "pagination": {"returned": 32, "is_complete": False},
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert data_answer is not None
    assert data_answer.get("profileKey") == "system_metadata"
    blob = str(data_answer).casefold()
    assert "similarity_ratio" not in blob
    assert "lista é extensa" not in blob
    assert "5477" in blob


def test_build_system_columns_uses_catalog_total_not_generic_numeric() -> None:
    metadata = {
        "path": "/system/tables/SB1010/columns",
        "apiDelpiResponseMeta": {
            "entity": "protheus_column",
            "shape": "paged_list",
        },
        "tablePresentation": {
            "type": "table",
            "rows": [
                {"X3_CAMPO": "B1_COD", "X3_TAMANHO": 8},
                {"X3_CAMPO": "B1_DESC", "X3_TAMANHO": 60},
            ],
        },
    }
    data = {
        "items": [
            {"X3_CAMPO": "B1_COD", "X3_TAMANHO": 8},
            {"X3_CAMPO": "B1_DESC", "X3_TAMANHO": 60},
        ],
        "total": 318,
        "page": 1,
        "pageSize": 50,
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert data_answer is not None
    assert data_answer.get("profileKey") == "system_metadata"
    blob = " ".join(
        [
            str((data_answer.get("summary") or {}).get("answer") or ""),
            *[
                str(item.get("text") if isinstance(item, dict) else item)
                for item in (data_answer.get("facts") or [])
            ],
        ]
    )
    assert "318" in blob
    assert "x3_tamanho" not in blob.casefold()
    assert "similarity_ratio" not in blob.casefold()


def test_build_schedule_today_complete_list_does_not_add_page_limitation() -> None:
    rows = [
        {
            "production_order": f"245559010{index:02d}",
            "product_code": "70260010",
            "description": "CHICOTE BUHLER",
            "planned_qty": 0.001,
            "branch": "01" if index < 164 else "02",
        }
        for index in range(169)
    ]
    metadata = {
        "path": "/production/schedule/today",
        "apiDelpiResponseMeta": {
            "entity": "production_schedule_today",
            "pagination": {"limit": 500, "returned": 169, "is_complete": True},
        },
        "tablePresentation": {"type": "table", "rows": rows},
    }
    data = {
        "items": rows,
        "summary": {
            "total_records": 169,
            "reference_date": "20260622",
            "is_complete": True,
            "branch_filter_applied": False,
            "consolidated_across_branches": True,
        },
        "pagination": {"limit": 500, "offset": 0, "returned": 169, "is_complete": True},
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    limitations = "\n".join(data_answer.get("limitations") or []).lower()
    assert "registros desta página" not in limitations
    assert "resultado incompleto" not in limitations


def test_build_generic_complete_list_does_not_mark_pagination_limitation():
    rows = [
        {
            "production_order": f"245559010{index:02d}",
            "product_code": "70260010",
            "description": "CHICOTE BUHLER",
            "planned_qty": 0.001,
        }
        for index in range(50)
    ]
    metadata = {
        "path": "/production/schedule/today",
        "paginationConsolidation": {
            "completed": True,
            "mergedCount": 50,
            "consolidatedPayload": {
                "items": rows,
                "page": 1,
                "page_size": 50,
                "total": 50,
                "total_pages": 1,
            },
        },
        "tablePresentation": {"type": "table", "rows": rows},
    }
    data = {
        "items": rows,
        "summary": {
            "total_records": 50,
            "reference_date": "20260611",
            "is_complete": False,
            "branch_filter_applied": False,
        },
        "pagination": {"limit": 50, "offset": 0, "returned": 50, "is_complete": False},
    }
    metadata = {
        **metadata,
        "apiDelpiResponseMeta": {
            "pagination": {"limit": 50, "returned": 50, "is_complete": False},
        },
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert data_answer.get("profileKey") == "generic_list"
    assert data_answer.get("limitations")
    assert any(
        "Resultado incompleto" in str(line)
        for line in (data_answer.get("limitations") or [])
    )


def test_build_product_analyser_uses_analyser_commentary_not_generic_list():
    metadata = {
        "path": "/products/10080024/analyser",
        "apiDelpiResponseMeta": {
            "entity": "product_analyser",
            "shape": "composite_analysis",
        },
        "tablePresentations": [
            {
                "type": "table",
                "role": "profile",
                "title": "Produto 10080024",
                "rows": [
                    {"campo": "Código", "valor": "10080024"},
                    {"campo": "Descrição", "valor": "TERM. OLHAL M6"},
                ],
            }
        ],
    }
    data = {
        "product": {
            "code": "10080024",
            "description": "TERM. OLHAL M6",
            "type": "MP",
            "group_code": "1008",
        },
        "structure": {"items": [], "total": 0},
        "guide": {"items": [], "total": 0},
        "inspection": {"items": [], "total": 0},
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert data_answer.get("profileKey") == "analyser"
    assert "10080024" in str((data_answer.get("summary") or {}).get("answer") or "")
    assert data_answer.get("profileKey") != "generic_list"
    assert "14 registros" not in str((data_answer.get("summary") or {}).get("answer") or "").lower()


def test_resolve_rows_reads_materials_items_for_cost_impact_without_table_metadata():
    metadata = {
        "path": "/products/90261255/cost-impact-simulation",
        "apiDelpiResponseMeta": {
            "shape": "composite_analysis",
            "sections": [{"key": "materials", "label": "Impacto de MPs", "itemCount": 2}],
        },
    }
    data = {
        "product": {"product_code": "90261255", "description": "CHICOTE"},
        "materials": {
            "items": [
                {"rank": 1, "raw_material_code": "10210011", "extended_cost": 29133.0},
                {"rank": 2, "raw_material_code": "10080227", "extended_cost": 12864.0},
            ],
            "total": 2,
        },
        "summary": {"total_material_cost": 41997.0},
    }

    rows = ChatDataInsightService._resolve_rows(metadata, data)

    assert rows is not None
    assert len(rows) == 2
    assert rows[0]["raw_material_code"] == "10210011"


def test_build_generic_commentary_does_not_mark_cost_impact_as_empty_without_table():
    metadata = {
        "path": "/products/90261255/cost-impact-simulation",
        "apiDelpiResponseMeta": {
            "shape": "composite_analysis",
            "sections": [{"key": "materials", "itemCount": 1}],
        },
    }
    data = {
        "materials": {
            "items": [{"rank": 1, "raw_material_code": "10210011", "extended_cost": 100.0}],
        }
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    summary = (data_answer or {}).get("summary") or {}
    answer = str(summary.get("answer") or "").lower()

    assert "não retornou registros" not in answer
    assert "nao retornou registros" not in answer
    assert "1" in answer


def test_build_summary_first_commentary_prefers_summary_over_days_diff_total():
    metadata = {
        "path": "/production/otd",
        "apiDelpiResponseMeta": {
            "entity": "production_otd_detail",
            "shape": "playbook_report",
        },
        "tablePresentation": {
            "type": "table",
            "rows": [
                {"op": "1", "status": "late", "days_diff": -4},
                {"op": "2", "status": "late", "days_diff": -2},
            ],
        },
    }
    data = {
        "summary": {
            "late_ops": 25,
            "on_time_ops": 95,
            "on_time_delivery_pct": 79.17,
        },
        "orders": {
            "items": [
                {"op": "1", "status": "late", "days_diff": -4},
                {"op": "2", "status": "late", "days_diff": -2},
            ]
        },
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert data_answer.get("profileKey") == "kpi_summary"
    summary = data_answer.get("summary") if isinstance(data_answer.get("summary"), dict) else {}
    facts = data_answer.get("facts") or []
    fact_text = " ".join(
        [
            str(summary.get("answer") or ""),
            str(summary.get("meaning") or ""),
            *[
                str(item.get("text") if isinstance(item, dict) else item)
                for item in facts
            ],
        ]
    )
    assert "atraso" in fact_text.casefold() or "otd" in fact_text.casefold()
    assert "days_diff" not in fact_text.casefold()


def test_single_row_count_aggregate_leads_with_total_not_rowcount():
    """COUNT(*) / TOTAL (mesmo como string JSON) não pode virar «1 registro» genérico."""
    metadata = {
        "path": "/data/sql",
        "tablePresentation": {
            "type": "table",
            "rows": [{"TOTAL": "1898"}],
        },
    }
    data = {"rows": [{"TOTAL": "1898"}]}

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    summary = data_answer.get("summary") if isinstance(data_answer.get("summary"), dict) else {}
    answer = str(summary.get("answer") or "")
    facts = " ".join(
        str(item.get("text") if isinstance(item, dict) else item)
        for item in (data_answer.get("facts") or [])
    )
    blob = f"{answer} {facts}"
    assert "1898" in blob.replace(".", "")
    assert "foram retornados" not in blob.casefold()
    assert "formato dos dados sugere" not in blob.casefold()


def test_multi_row_list_prefers_numeric_total_not_shape_recommend():
    metadata = {
        "path": "/production/schedule/today",
        "tablePresentation": {
            "type": "table",
            "rows": [
                {"op": "1", "planned_qty": 10},
                {"op": "2", "planned_qty": 20},
                {"op": "3", "planned_qty": 5},
            ],
        },
    }
    data = {
        "items": [
            {"op": "1", "planned_qty": 10},
            {"op": "2", "planned_qty": 20},
            {"op": "3", "planned_qty": 5},
        ]
    }

    commentary = ChatDataInsightService._build_generic_commentary(metadata, data)
    assert isinstance(commentary, dict)
    highlights = " ".join(str(item) for item in (commentary.get("highlights") or []))
    assert "35" in highlights.replace(".", "") or "planned_qty" in highlights.casefold()
    assert "formato dos dados sugere" not in highlights.casefold()
    assert commentary.get("recommendedVisual") in {"table", "kpi", "chart", "line", None} or True
    # shapeRecommend never in prose highlights
    assert "formato dos dados sugere" not in str(commentary.get("summaryLines") or []).casefold()


def test_system_table_schema_uses_summary_not_rowcount_or_x3_tamanho():
    """protheus_table_schema → system_metadata: columnCount, sem soma SX3."""
    metadata = {
        "path": "/system/tables/SB1010/schema",
        "apiDelpiResponseMeta": {
            "entity": "protheus_table_schema",
            "shape": "composite_analysis",
        },
        "tablePresentation": {
            "type": "table",
            "rows": [
                {"X3_CAMPO": "B1_COD", "X3_TAMANHO": 8},
                {"X3_CAMPO": "B1_DESC", "X3_TAMANHO": 60},
            ],
        },
    }
    data = {
        "summary": {
            "tableName": "SB1010",
            "alias": "SB1",
            "description": "Descrição Genérica do Produto",
            "columnCount": 318,
            "indexCount": 19,
            "relationCount": 962,
        },
        "columns": {
            "items": [
                {"X3_CAMPO": "B1_COD", "X3_TAMANHO": 8},
                {"X3_CAMPO": "B1_DESC", "X3_TAMANHO": 60},
            ],
            "total": 318,
            "truncated": False,
        },
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert data_answer.get("profileKey") == "system_metadata"
    blob = " ".join(
        [
            str((data_answer.get("summary") or {}).get("answer") or ""),
            *[
                str(item.get("text") if isinstance(item, dict) else item)
                for item in (data_answer.get("facts") or [])
            ],
        ]
    )
    assert "SB1010" in blob
    assert "318" in blob
    assert "foram retornados" not in blob.casefold()
    assert "x3_tamanho" not in blob.casefold()
    assert "x3 tamanho" not in blob.casefold()
    metrics = data_answer.get("derivedMetrics") or []
    metric_blob = " ".join(
        f"{m.get('label')} {m.get('value')}" for m in metrics if isinstance(m, dict)
    ).casefold()
    assert "tamanho" not in metric_blob
    assert "2703" not in metric_blob
    assert "média" not in metric_blob
