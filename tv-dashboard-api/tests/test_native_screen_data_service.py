from tv_app.application.services.native_screen_data_service import NativeScreenDataService


def test_custom_message_screen():
    service = NativeScreenDataService()
    data = service.resolve(
        screen_key="custom_message",
        config={"headline": "Bem-vindos", "subtitle": "Turno A"},
    )
    assert data["headline"] == "Bem-vindos"
    assert data["subtitle"] == "Turno A"


def test_native_catalog_has_oee():
    catalog = NativeScreenDataService.catalog()
    keys = {item["key"] for item in catalog}
    assert "production_oee_overview" in keys
