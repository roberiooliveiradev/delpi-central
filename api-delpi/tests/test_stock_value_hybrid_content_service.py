from app.application.services.supplies.stock_value_hybrid_content_service import (
    note,
    process_warehouse_locations,
)


def test_process_warehouse_locations_loaded() -> None:
    locations = process_warehouse_locations()
    assert "99" in locations


def test_note_register_snapshot_not_empty() -> None:
    text = note("registerSnapshot")
    assert "SB2" in text
