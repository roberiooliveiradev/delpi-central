from app.domain.services.chat_prior_turn_facts_packing_service import (
    ChatPriorTurnFactsPackingService,
)


def test_packing_includes_code_and_description():
    snapshot = {
        "lastResultExcerpt": {
            "identityFields": {
                "code": "10080047",
                "description": "TERMINAL PINO 6,3MM",
            },
            "title": "Produto 10080047",
        },
        "resultSets": [
            {
                "id": "rs-1",
                "kind": "product",
                "totalCount": 2,
                "items": [
                    {"ordinal": 1, "code": "10080047", "label": "TERMINAL PINO"},
                    {"ordinal": 2, "code": "10080099", "label": "TERMINAL OLHAL"},
                ],
            }
        ],
        "sessionCapabilities": {
            "skills": ["f11_technical_description"],
            "tools": ["execute_external_action"],
        },
    }

    packed = ChatPriorTurnFactsPackingService.build(snapshot)

    assert packed.chars > 0
    assert "10080047" in packed.text
    assert "TERMINAL PINO" in packed.text
    assert "identity" in packed.sections
    assert "resultSets" in packed.sections
    assert "capabilities" in packed.sections
    assert "f11_technical_description" in packed.text


def test_packing_respects_max_chars():
    snapshot = {
        "lastResultExcerpt": {
            "identityFields": {
                "code": "10080047",
                "description": "TERMINAL " + ("X" * 200),
            }
        }
    }

    packed = ChatPriorTurnFactsPackingService.build(snapshot, max_chars=80)

    assert packed.truncated is True
    assert packed.chars <= 80
