from app.domain.services.envelope_contract_service import (
    load_envelope_contract_golden,
    validate_envelope_contract_golden,
)


def test_envelope_contract_golden_loads_routes() -> None:
    payload = load_envelope_contract_golden()
    routes = payload.get("routes")
    assert isinstance(routes, list)
    assert len(routes) >= 5
    assert routes[0].get("operationId")


def test_envelope_contract_golden_matches_registry() -> None:
    errors = validate_envelope_contract_golden()
    assert errors == []
