from __future__ import annotations

from unittest.mock import MagicMock

from tv_app.infrastructure.gateways.delpi_operational_gateway import DelpiOperationalGateway


def test_gateway_preserves_meta_fields_dict_from_api_delpi():
    """Regressão: dict meta.fields não pode virar [] e cair em paramSchema."""
    catalog = MagicMock()
    catalog.get_route.return_value = {
        "operationId": "get_ppm_internal_summary",
        "path": "/quality/ppm/internal/summary",
        "httpMethod": "GET",
        "metaShape": "scalar",
        "paramSchema": {
            "branch": {"type": "string", "label": "Filial"},
            "start_date": {"type": "string"},
        },
        "valueFields": ["value", "ppm"],
        "valueFieldLabels": {"ppm": "PPM"},
    }
    client = MagicMock()
    client.get_path.return_value = {
        "success": True,
        "data": {
            "ppm": 1081.99,
            "target": 1400.0,
            "total_devolvido_un": 139.0,
            "value": 1081.99,
        },
        "meta": {
            "operationId": "get_ppm_internal_summary",
            "shape": "scalar",
            "fields": {
                "ppm": "PPM",
                "target": "Meta PPM",
                "total_devolvido_un": "Total devolvido (un.)",
                "value": "Valor",
            },
        },
    }
    gateway = DelpiOperationalGateway(client=client, catalog=catalog)
    result = gateway.fetch_by_operation_id("get_ppm_internal_summary", params={"branch": "01"})
    assert result["meta"]["fields"] == {
        "ppm": "PPM",
        "target": "Meta PPM",
        "total_devolvido_un": "Total devolvido (un.)",
        "value": "Valor",
    }
    assert "branch" not in result["meta"]["fields"]
    client.get_path.assert_called_once()
    assert client.get_path.call_args.kwargs["extra_headers"] == {}


class _Token:
    def get_token(self) -> str:
        return "svc-token"


def test_helpdesk_summary_attaches_service_authorization_only_for_that_operation():
    catalog = MagicMock()
    catalog.get_route.return_value = {
        "operationId": "get_helpdesk_dashboard_summary",
        "path": "/helpdesk/dashboard-summary",
        "httpMethod": "GET",
        "metaShape": "scalar",
        "paramSchema": {},
    }
    client = MagicMock()
    client.get_path.return_value = {"data": {"open": 0}, "meta": {}}
    gateway = DelpiOperationalGateway(
        client=client,
        catalog=catalog,
        helpdesk_token_provider_factory=lambda: _Token(),
    )
    gateway.fetch_by_operation_id("get_helpdesk_dashboard_summary", params={})
    headers = client.get_path.call_args.kwargs["extra_headers"]
    assert headers["X-Delpi-Service-Authorization"] == "Bearer svc-token"
    assert "Authorization" not in headers
