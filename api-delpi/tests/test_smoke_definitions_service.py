from app.domain.services.smoke_definitions_service import load_smoke_definitions


def test_load_smoke_definitions_has_suites() -> None:
    payload = load_smoke_definitions()

    assert payload.get("version")
    suites = payload.get("suites")
    assert isinstance(suites, list)
    assert len(suites) >= 1
    assert suites[0].get("id")
    assert isinstance(suites[0].get("cases"), list)


def test_produced_quantity_smoke_case_has_required_query() -> None:
    payload = load_smoke_definitions()
    ppm_suite = next(s for s in payload["suites"] if s["id"] == "qualidade-ppm")
    produced = next(c for c in ppm_suite["cases"] if c["id"] == "produced-quantity")
    query = produced.get("query") or {}

    assert query.get("product")
    assert query.get("date_start")
    assert query.get("date_end")
