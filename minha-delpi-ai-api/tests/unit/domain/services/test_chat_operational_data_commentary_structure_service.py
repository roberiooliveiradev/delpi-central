"""Commentary de estrutura (BOM) — highlights para prosa e insight."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

configure_domain_infrastructure_ports()


def _nested_structure_payload():
    return {
        "root": {
            "code": "90260149",
            "description": "CHICOTE DE LIGACAO",
            "type": "PA",
            "unit": "MI",
            "quantity": 1,
        },
        "items": [
            {
                "code": "50231850",
                "description": "CB18BRAN-00368",
                "type": "PI",
                "unit": "MI",
                "quantity": 1.0,
                "components": [
                    {
                        "code": "10030015",
                        "description": "CABO EPR 18AWG BN",
                        "type": "MP",
                        "unit": "MT",
                        "quantity": 368.0,
                    },
                ],
            },
            {
                "code": "50231851",
                "description": "CB18AZUL-00368",
                "type": "PI",
                "unit": "MI",
                "quantity": 1.0,
                "components": [
                    {
                        "code": "10030015",
                        "description": "CABO EPR 18AWG AZ",
                        "type": "MP",
                        "unit": "MT",
                        "quantity": 368.0,
                    },
                ],
            },
        ],
        "total": 2,
    }


def test_structure_commentary_nested_payload_mentions_pi_and_mp():
    commentary = ChatOperationalDataCommentaryService.build(
        "structure",
        _nested_structure_payload(),
    )

    assert commentary is not None
    highlights = commentary.get("highlights") or []
    joined = " ".join(highlights).upper()

    assert "90260149" in joined
    assert "PI" in joined
    assert "MP" in joined or "MATÉRIA" in joined or "MATERIA" in joined
    assert "Código:" not in joined
    assert "Tipo:" not in joined


def test_structure_commentary_detects_shared_mp_and_color_variants():
    commentary = ChatOperationalDataCommentaryService.build(
        "structure",
        _nested_structure_payload(),
    )

    assert commentary is not None
    joined = " ".join(commentary.get("highlights") or [])

    assert "reutilizada" in joined.lower() or "mais de um intermediário" in joined.lower()
    assert "variação" in joined.lower() or "cor/cabo" in joined.lower()


def test_structure_commentary_from_api_fixture():
    envelope = load_api_delpi_fixture_with_meta("product_structure_90269001.json")
    data = envelope.get("data") if isinstance(envelope, dict) else envelope

    commentary = ChatOperationalDataCommentaryService.build("structure", data)

    assert commentary is not None
    highlights = commentary.get("highlights") or []

    assert highlights
    assert any("PI" in line or "intermediário" in line.lower() for line in highlights)
    assert any("MP" in line or "matéria" in line.lower() for line in highlights)
