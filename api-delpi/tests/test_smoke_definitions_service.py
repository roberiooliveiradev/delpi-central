from app.domain.services.smoke_definitions_service import load_smoke_definitions


def test_load_smoke_definitions_has_suites() -> None:
    payload = load_smoke_definitions()

    assert payload.get("version")
    suites = payload.get("suites")
    assert isinstance(suites, list)
    assert len(suites) >= 1
    assert suites[0].get("id")
    assert isinstance(suites[0].get("cases"), list)
