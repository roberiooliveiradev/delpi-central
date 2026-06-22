from app.domain.services.operational_route_query_defaults_service import (
    OperationalRouteQueryDefaultsService,
)


def test_apply_injects_defaults_when_missing() -> None:
    merged = OperationalRouteQueryDefaultsService.apply(
        {
            "parametersSchema": [
                {"name": "reference_date"},
                {"name": "limit"},
            ],
        },
        {"reference_date": "22-06-2026"},
        route={
            "parameters": {
                "strategy": "date_branch",
                "queryDefaults": {"limit": 500},
            },
        },
    )

    assert merged["reference_date"] == "22-06-2026"
    assert merged["limit"] == 500


def test_apply_overrides_existing_when_key_listed() -> None:
    merged = OperationalRouteQueryDefaultsService.apply(
        {
            "parametersSchema": [{"name": "limit"}],
        },
        {"limit": 50},
        route={
            "parameters": {
                "queryDefaults": {"limit": 500},
                "overrideKeys": ["limit"],
            },
        },
    )

    assert merged["limit"] == 500


def test_apply_skips_unknown_schema_fields() -> None:
    merged = OperationalRouteQueryDefaultsService.apply(
        {"parametersSchema": [{"name": "reference_date"}]},
        {},
        route={
            "parameters": {
                "queryDefaults": {"limit": 500},
            },
        },
    )

    assert merged == {}


def test_apply_without_route_spec_returns_copy() -> None:
    merged = OperationalRouteQueryDefaultsService.apply(
        {"parametersSchema": [{"name": "limit"}]},
        {"limit": 10},
    )

    assert merged == {"limit": 10}
