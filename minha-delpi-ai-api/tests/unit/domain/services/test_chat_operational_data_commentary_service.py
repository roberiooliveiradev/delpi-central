from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)


def test_structure_exclusivity_commentary_uses_verdict_not_row_count():
    root = {
        "product": {"product_code": "90260255", "description": "CHICOTE EPR SINGELO 300MM"},
        "summary": {
            "total_components": 12,
            "total_intermediates": 4,
            "total_raw_materials": 8,
            "total_exclusive_raw_materials": 0,
        },
        "items": [{"component_type": "MP", "component_code": "10080098"}],
    }

    commentary = ChatOperationalDataCommentaryService.build("structure_exclusivity", root)

    assert commentary
    combined = "\n".join(commentary.get("highlights") or [])

    assert "Resposta" in combined
    assert "Não" in combined or "nenhuma MP exclusiva" in combined.lower()
    assert "12 componente" in combined or "Composição" in combined
    assert "4 registros" not in combined
    assert commentary.get("profileKey") == "structure_exclusivity"


def test_factory_commentary_includes_humanized_contract_fields():
    root = {
        "factory_status": "PA FINALIZADO / LIBERADO PARA EXPEDIÇÃO",
        "structure": {"items": []},
        "raw_material_stock": {"items": [], "summary": {"total_without_stock_for_one_pa": 0}},
        "shipping": {"summary": {"total_shipped_quantity": 0}},
    }

    commentary = ChatOperationalDataCommentaryService.build("factory_status", root)

    assert commentary
    assert commentary.get("summary")
    assert commentary.get("alertLevel") in {"ok", "attention", "critical", "unknown"}
    assert commentary.get("nextAction")


def test_factory_commentary_warns_low_mp_coverage():
    root = {
        "factory_status": "PA FINALIZADO / LIBERADO PARA EXPEDIÇÃO",
        "structure": {"items": [{"exclusive_raw_material": False}]},
        "raw_material_stock": {
            "items": [
                {
                    "raw_material_code": "10160002",
                    "unit": "PC",
                    "quantity_required_for_one_pa": "3000",
                    "available_quantity": "4638",
                    "has_stock_for_one_pa_label": "Sim",
                }
            ],
            "summary": {"total_without_stock_for_one_pa": 0},
        },
        "shipping": {"summary": {"total_shipped_quantity": 0}},
    }

    commentary = ChatOperationalDataCommentaryService.build("factory_status", root)

    assert commentary
    combined = "\n".join(commentary.get("highlights") or [])

    assert "10160002" in combined
    assert "cobertura baixa" in combined.lower()
    assert commentary.get("narrativeInsight")


def test_resolve_profile_key_from_factory_path():
    profile = ChatOperationalDataCommentaryService.resolve_profile_key(
        path="/products/90262404/factory-status",
        metadata={"apiDelpiResponseMeta": {"entity": "product_factory_status"}},
    )

    assert profile == "factory_status"


def test_stock_commentary_aggregates_available_total():
    root = {
        "items": [
            {
                "product_code": "90269001",
                "branch": "01",
                "warehouse": "01",
                "available_quantity": 105.0,
                "current_quantity": 120.0,
                "committed_quantity": 10.0,
            },
            {
                "product_code": "90269001",
                "branch": "02",
                "warehouse": "01",
                "available_quantity": 45.0,
                "current_quantity": 45.0,
                "committed_quantity": 0.0,
            },
        ],
        "total": 2,
    }

    commentary = ChatOperationalDataCommentaryService.build("stock", root)

    assert commentary
    assert commentary.get("summary")
    combined = "\n".join(commentary.get("highlights") or [])

    assert "150" in combined


def test_production_commentary_flags_open_op_without_start():
    root = {
        "reference_date": "20260604",
        "summary": {
            "total_pa_orders": 1,
            "total_pi_orders": 0,
            "pa_production_started": "NAO",
            "pi_production_started": "NAO",
            "total_pa_reported_quantity": 0,
            "total_pi_reported_quantity": 0,
        },
        "items": [{"total_reports": 0}],
    }

    commentary = ChatOperationalDataCommentaryService.build("production_status", root)

    assert commentary
    assert commentary.get("alertLevel") == "attention"
    combined = "\n".join((commentary.get("highlights") or []) + (commentary.get("attention") or []))

    assert "apontamento" in combined.lower()


def test_shipping_commentary_reports_shipped_quantity():
    root = {
        "date_start": "20260604",
        "date_end_exclusive": "20260605",
        "summary": {
            "total_shipped_quantity": 10,
            "total_inspection_loss_quantity": 1,
        },
        "items": [],
    }

    commentary = ChatOperationalDataCommentaryService.build("shipping_status", root)

    assert commentary
    combined = "\n".join(commentary.get("highlights") or [])

    assert "10" in combined


def test_render_markdown_sections_includes_highlights_header():
    commentary = {
        "profileKey": "factory_status",
        "highlights": ["Situação fabril: **PA PRODUZIDO**"],
        "attention": [],
    }

    rendered = ChatOperationalDataCommentaryService.render_markdown_sections(
        ChatOperationalDataCommentaryService.build(
            "factory_status",
            {
                "factory_status": "PA PRODUZIDO",
                "structure": {"items": []},
                "raw_material_stock": {"items": [], "summary": {}},
                "shipping": {"summary": {"total_shipped_quantity": 0}},
            },
        )
    )

    assert "<!-- section:summary -->" in rendered
    assert "Destaques" in rendered
    assert "PA PRODUZIDO" in rendered
