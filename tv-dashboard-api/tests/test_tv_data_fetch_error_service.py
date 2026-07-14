from __future__ import annotations

from delpi_api_client.client import DelpiApiError

from tv_app.application.services.data.tv_data_fetch_error_service import resolve_data_fetch_error


def test_resolve_delpi_api_error_surfaces_status_and_detail() -> None:
    payload = resolve_data_fetch_error(DelpiApiError(403, "Filial não autorizada."))
    assert payload["statusCode"] == 403
    assert payload["error"] == "[403] Filial não autorizada."
    assert payload["detail"] == "Filial não autorizada."


def test_resolve_value_error_uses_message() -> None:
    payload = resolve_data_fetch_error(ValueError("Fonte de dados indisponível."))
    assert payload["error"] == "Fonte de dados indisponível."
    assert "statusCode" not in payload


def test_enrich_fetch_failure_exposes_api_error() -> None:
    from unittest.mock import MagicMock

    from tv_app.application.services.comunicado_data_enrichment_service import (
        ComunicadoDataEnrichmentService,
    )
    from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService

    gateway = MagicMock()
    gateway.fetch_by_operation_id.side_effect = DelpiApiError(
        422,
        "Parâmetro reference_date inválido.",
    )
    service = ComunicadoDataEnrichmentService(
        catalog=TvDataRouteCatalogService(),
        gateway=gateway,
    )
    enriched = service.enrich_blocks(
        [
            {
                "id": "ds1",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "get_overall_equipment_effectiveness_pct",
                    "params": {},
                },
            }
        ],
        cfg={},
        authorization="Bearer x",
    )
    resolved = enriched[0]["resolved"]
    assert resolved["error"] == "[422] Parâmetro reference_date inválido."
    assert resolved["statusCode"] == 422
