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

    summary = data_answer.get("summary")

    assert summary.get("answer")
    assert any(
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
    derived_metrics = data_answer.get("derivedMetrics") or []
    assert derived_metrics[0]["label"] == "Registros"
    assert derived_metrics[0]["value"] == "2"
    assert "não retornou registros" not in str(data_answer.get("summary") or "").lower()


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
