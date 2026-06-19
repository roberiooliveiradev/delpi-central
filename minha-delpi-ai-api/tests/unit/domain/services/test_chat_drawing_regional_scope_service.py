from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_regional_scope_service import (
    ChatDrawingRegionalScopeService,
)

configure_domain_infrastructure_ports()


def test_resolve_bom_scope_from_stamp_table_not_full_stamp():
    stamp_text = (
        "10056570 DC:Z-855 REV: 15\n"
        "90261757\n"
        "QTD.| CÓDIGO DESCRIÇÃO\n"
        "01 [10020194] CABO PVC\n"
        "01 |10080021 | TERM. OLHAL\n"
    )

    scopes = ChatDrawingRegionalScopeService.resolve(
        metadata={
            "stampText": stamp_text,
            "regionTexts": {"stamp": stamp_text},
        }
    )

    bom = scopes["bom"]

    assert bom["available"] is True
    assert bom["sourceKey"] == "stamp_bom_table"
    assert "10056570" not in bom["text"]
    assert "10020194" in bom["text"]


def test_build_bom_sources_exclude_raw_stamp_region():
    scopes = ChatDrawingRegionalScopeService.resolve(
        metadata={
            "bomText": 'VISTA "A"',
            "stampText": "1 10080591 TERM. PINO",
            "regionTexts": {
                "bom": 'VISTA "A"',
                "stamp": "1 10080591 TERM. PINO",
            },
        }
    )

    sources = ChatDrawingRegionalScopeService.build_bom_sources(scopes)

    assert [name for name, _ in sources] == ["stamp_bom_table"]
    assert "10080591" in sources[0][1]


def test_scope_label_from_json():
    label = ChatDrawingRegionalScopeService.scope_label("stamp_bom_table")

    assert "carimbo" in label.lower()


def test_resolve_bom_scope_rejects_stamp_layout_as_bom_region():
    stamp_like_bom = (
        "1 | 2 | 3 | 4\n"
        "MEDIDAS EM MILÍMETRO\n"
        "REV. | DATA | LMP | RESUMO DAS MODIFICAÇÕES\n"
        "CLIENTE: | WEG INDUSTRIA S.A.\n"
        "CHICOTE DE LIGAÇÃO | 90263396"
    )

    scopes = ChatDrawingRegionalScopeService.resolve(
        metadata={
            "filename": "90263396.pdf",
            "regionTexts": {"bom": stamp_like_bom},
        },
        product_code="90263396",
    )

    assert scopes["bom"]["available"] is False
    assert scopes["bom"]["sourceKey"] is None
