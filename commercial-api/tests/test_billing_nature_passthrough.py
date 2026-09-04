"""Pass-through de nature no enrichment / billing-series (structural)."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_enrichment_and_billing_series_bodies_accept_nature() -> None:
    schemas = (ROOT / "commercial_app/interface/http/schemas/portfolio_schemas.py").read_text(
        encoding="utf-8"
    )
    assert 'pattern=r"^(gross|net)$"' in schemas
    assert 'pattern=r"^(value|quantity)$"' in schemas
    routes = (ROOT / "commercial_app/interface/http/routes/customer_routes.py").read_text(
        encoding="utf-8"
    )
    assert 'payload["nature"] = body.nature' in routes
    assert 'payload["metric"] = body.metric' in routes
