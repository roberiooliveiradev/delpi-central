from app.domain.services.chat_entity_tracker_service import ChatEntityTrackerService


def test_tracks_product_and_supplier_hint():
    snapshot = ChatEntityTrackerService.apply_to_snapshot(
        {"lastEntities": {"productCode": "10080001"}},
        message="agora fornecedores",
    )

    assert snapshot["referenceHints"].get("fornecedores", "").startswith("fornecedores do produto")


def test_previous_product_codes_on_switch():
    snapshot = ChatEntityTrackerService.apply_to_snapshot(
        {"lastEntities": {"productCode": "10080001"}, "previousProductCodes": []},
        message="consulte produto 10080002",
    )

    assert snapshot["lastEntities"]["productCode"] == "10080002"
    assert "10080001" in snapshot.get("previousProductCodes", [])
