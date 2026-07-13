from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_drawing_intermediate_semantics_service import (
    ChatDrawingIntermediateSemanticsService,
)


def test_parse_intermediate_description_length_and_decapes():
    parsed = ChatDrawingIntermediateSemanticsService.parse_description(
        "CT26VERM-00036/04/06-0000-0000"
    )

    assert parsed["lengthMm"] == 36.0
    assert parsed["leftDecapeMm"] == 4.0
    assert parsed["rightDecapeMm"] == 6.0


def test_collect_structure_intermediates_skips_false_consumable_50xx():
    root = {
        "structure": {
            "items": [
                {
                    "code": "50250279",
                    "description": "LUVATERMOENCOLHVEL 6MM",
                    "components": [{"code": "10130001", "quantity": 6.0}],
                },
                {
                    "code": "50215433",
                    "description": "CT26PRET-00050/2,5/06-0000-0000",
                    "components": [{"code": "10440134", "quantity": 50.0}],
                },
            ]
        }
    }

    rows = ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(root)

    assert [row["code"] for row in rows] == ["50215433"]


def test_collect_structure_intermediates_uses_child_quantity():
    root = {
        "structure": {
            "items": [
                {
                    "code": "50215433",
                    "description": "CT26PRET-00050/2,5/06-0000-0000",
                    "components": [{"code": "10440134", "quantity": 50.0}],
                }
            ]
        }
    }

    rows = ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(root)

    assert len(rows) == 1
    assert rows[0]["code"] == "50215433"
    assert rows[0]["lengthMm"] == 50.0
    assert rows[0]["cableQuantityMm"] == 50.0


def test_collect_structure_intermediates_prefers_cable_child_over_terminal_pc():
    root = {
        "structure": {
            "items": [
                {
                    "code": "50233301",
                    "description": "CB20AZUL-00240/11/06",
                    "components": [
                        {"code": "10080063", "quantity": 1000.0, "unit": "PC"},
                        {"code": "10380013", "quantity": 240.0, "unit": "MT"},
                    ],
                }
            ]
        }
    }

    rows = ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(root)

    assert len(rows) == 1
    assert rows[0]["cableCode"] == "10380013"
    assert rows[0]["cableQuantityMm"] == 240.0
    assert rows[0]["cableUnit"] == "MT"


def test_collect_structure_intermediates_walks_nested_pi_under_pa():
    root = {
        "product": {
            "code": "90260027",
            "description": "CHICOTE PVC SINGELO 660MM",
        },
        "structure": {
            "items": [
                {
                    "code": "90260027",
                    "description": "CHICOTE PVC SINGELO 660MM",
                    "type": "PA",
                    "components": [
                        {
                            "code": "50220010",
                            "description": "CA18VDAR-00653/07/06-0000-2100",
                            "quantity": 1.0,
                            "components": [
                                {"code": "10020018", "quantity": 653.0, "unit": "MT"},
                            ],
                        }
                    ],
                }
            ]
        },
    }

    rows = ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(root)

    assert len(rows) == 1
    assert rows[0]["code"] == "50220010"
    assert rows[0]["lengthMm"] == 660.0
