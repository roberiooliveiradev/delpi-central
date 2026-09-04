from app.domain.services.chat_reference_resolution_service import (
    ChatReferenceResolutionService,
)


def test_pronoun_coref_resolves_product_from_focus():
    snapshot = {
        "operationalFocus": {"productCode": "10080047"},
        "resultSets": [
            {
                "id": "rs-1",
                "items": [
                    {"ordinal": 1, "code": "10080047", "label": "A"},
                    {"ordinal": 2, "code": "10080099", "label": "B"},
                ],
            }
        ],
    }

    resolved, keys = ChatReferenceResolutionService.resolve_from_snapshot(
        "e o estoque dele?",
        snapshot,
    )

    values = {str(item.get("value") or "") for item in resolved}
    assert "10080047" in values
    assert "productCode" in keys


def test_ordinal_coref_resolves_second_from_result_sets():
    snapshot = {
        "resultSets": [
            {
                "id": "rs-1",
                "items": [
                    {"ordinal": 1, "code": "10080047", "label": "A"},
                    {"ordinal": 2, "code": "10080099", "label": "B"},
                ],
            }
        ],
    }

    resolved, keys = ChatReferenceResolutionService.resolve_from_snapshot(
        "estoque do segundo",
        snapshot,
    )

    values = {str(item.get("value") or "") for item in resolved}
    assert "10080099" in values
    assert "resultSets" in keys
