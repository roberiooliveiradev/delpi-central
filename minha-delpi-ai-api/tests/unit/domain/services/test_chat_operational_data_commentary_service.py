from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)


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


def test_render_markdown_sections_includes_highlights_header():
    commentary = {
        "profileKey": "factory_status",
        "highlights": ["Situação fabril: **PA PRODUZIDO**"],
        "attention": [],
    }

    rendered = ChatOperationalDataCommentaryService.render_markdown_sections(commentary)

    assert "Destaques" in rendered
    assert "PA PRODUZIDO" in rendered
