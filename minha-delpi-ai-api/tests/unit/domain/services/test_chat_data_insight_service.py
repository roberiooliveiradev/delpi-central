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
