from app.domain.services.chat_operational_commentary_enrichment_service import (
    ChatOperationalCommentaryEnrichmentService,
)


def test_enrich_metadata_attaches_commentary_and_quick_reading():
    metadata = {
        "path": "/products/90262404/factory-status",
        "stackPresentationPlan": {"presentationProfileKey": "factory_status"},
        "textPresentation": {
            "markdown": "### Status fabril\n\nSituação consolidada.",
        },
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

    ChatOperationalCommentaryEnrichmentService.enrich_metadata(metadata, data=data)

    data_answer = metadata.get("dataAnswer")
    commentary = metadata.get("dataCommentary")

    assert isinstance(data_answer, dict)
    assert data_answer.get("summary", {}).get("answer")
    assert isinstance(commentary, dict)
    assert commentary.get("highlights")
    assert commentary.get("summary")
    assert commentary.get("alertLevel")
    assert commentary.get("nextAction")

    markdown = str(metadata["textPresentation"]["markdown"])

    assert "<!-- section:summary -->" in markdown
    assert "Destaques" in markdown
    assert "Próxima ação" in markdown
