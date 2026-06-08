from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from si_app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from si_app.infrastructure.gateways.delpi_quality_gateway import (
    DelpiAudit5SGateway,
    DelpiKaizenGateway,
)


def test_kaizen_gateway_maps_api_payload() -> None:
    client = MagicMock()
    client.get_kaizen_summary.return_value = {
        "date_start": "01-04-2026",
        "date_end": "30-04-2026",
        "total_kaizens": 1,
        "total_savings": 7.0,
        "list_kaizen": [
            {
                "id": "k1",
                "title": "Abril",
                "date_implemented": "24/04/2026",
                "status": "implantado",
                "daily_savings": 1.0,
                "branch": "01",
            }
        ],
    }

    gateway = DelpiKaizenGateway(client)
    summary = gateway.get_kaizen_summary(
        KaizenSummaryRequest(
            date_start="01-04-2026",
            date_end="30-04-2026",
            branch="01",
        )
    )

    assert summary.total_kaizens == 1
    assert summary.total_savings == 7.0
    assert summary.list_kaizen[0].title == "Abril"
    client.get_kaizen_summary.assert_called_once()


def test_kaizen_gateway_caches_repeated_requests() -> None:
    client = MagicMock()
    client.get_kaizen_summary.return_value = {
        "total_kaizens": 0,
        "total_savings": 0.0,
        "list_kaizen": [],
    }

    gateway = DelpiKaizenGateway(client)
    request = KaizenSummaryRequest(date_start="01-04-2026", date_end="30-04-2026")

    gateway.get_kaizen_summary(request)
    gateway.get_kaizen_summary(request)

    client.get_kaizen_summary.assert_called_once()


def test_audit_5s_gateway_maps_api_payload() -> None:
    client = MagicMock()
    client.get_audit_5s_summary.return_value = {
        "start_date": "01-04-2026",
        "end_date": "30-04-2026",
        "average_score": 4.5,
        "list_audits": [
            {
                "id": "a1",
                "date": "15/04/2026",
                "average_line_score": 4.5,
                "branch": "01",
            }
        ],
    }

    gateway = DelpiAudit5SGateway(client)
    summary = gateway.get_audit_summary(
        Audit5SSummaryRequest(
            start_date="01-04-2026",
            end_date="30-04-2026",
            branch="01",
        )
    )

    assert summary.average_score == 4.5
    assert summary.list_audits[0].branch == "01"
    client.get_audit_5s_summary.assert_called_once()
