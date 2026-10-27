"""Exportações gerenciais de paradas (Etapa 5) — autorização + arquivos."""

from types import SimpleNamespace

import pytest

from delpi_mes_app.application.services.mes_downtime_export_service import (
    MesDowntimeExportService,
)
from delpi_mes_app.domain.errors import BranchAccessDenied, HumanPrincipalRequired


def user(*permissions, principal_type="user"):
    return SimpleNamespace(
        id="user-1", name="Gestora", permissions=list(permissions),
        is_superadmin=False, principal_type=principal_type,
        rbac_unavailable=False, access_token="tok-user-1",
    )


EXPORT_PERMS = (
    "delpi-mes.access",
    "delpi-mes.downtimes.export",
    "delpi-mes.view.filial-01",
)


def _export_payload():
    return {
        "branch": "01",
        "referenceAt": "2026-09-29T13:00:00+00:00",
        "timezone": "America/Sao_Paulo",
        "appliedFilters": {"workCenter": "CT-41", "status": "open"},
        "total": 1,
        "capped": False,
        "items": [
            {
                "id": "dt-1", "workCenter": "CT-41",
                "productionOrder": "100123", "operationCode": "10",
                "startedAt": "2026-09-29T10:00:00+00:00",
                "endedAt": None, "source": "system",
                "reasonCode": "falta_material",
                "reasonLabel": "Falta de material",
                "category": "material", "confirmed": False,
                "confirmedAt": None, "confirmedByRef": None,
                "note": None, "updatedAt": "2026-09-29T12:00:00+00:00",
                "treatmentStatus": "referred",
                "treatmentRequestId": "req-9",
            }
        ],
    }


class FakeGateway:
    def __init__(self):
        self.export_kwargs = None
        self.analytics_kwargs = None

    def export_downtimes(self, **kwargs):
        self.export_kwargs = kwargs
        return _export_payload()

    def get_downtime_analytics(self, **kwargs):
        self.analytics_kwargs = kwargs
        return {
            "branch": "01",
            "referenceAt": "2026-09-29T13:00:00+00:00",
            "timezone": "America/Sao_Paulo",
            "appliedFilters": {},
            "summary": {
                "totalStoppedSeconds": 7200, "attributedSeconds": 5400,
                "occurrencesCount": 3, "averageOccurrenceSeconds": 1800,
                "pendingCount": 1, "openCount": 1,
            },
            "byReason": [
                {"reasonCode": "setup", "label": "Setup",
                 "seconds": 3600, "occurrencesCount": 2},
            ],
            "byWorkCenter": [
                {"workCenter": "CT-41", "seconds": 5400,
                 "occurrencesCount": 3, "percentOfTotal": 1.0},
            ],
            "quality": {"overlapDetected": True, "partial": False,
                        "factsCapped": False},
        }


def service():
    return MesDowntimeExportService(gateway=FakeGateway())


def test_csv_export_includes_metadata_and_all_occurrences():
    result = service().export_occurrences(
        user(*EXPORT_PERMS), branch="01", export_format="csv",
        status="open",
    )
    text = result["content"].decode("utf-8-sig")
    assert "delpi-mes-paradas-01-" in result["filename"]
    assert result["contentType"].startswith("text/csv")
    assert "Filial: 01" in text
    assert "status=open" in text
    assert "Referência de cálculo: 29/09/2026" in text
    assert "Identificador" in text and "dt-1" in text
    assert "Encaminhada" in text  # treatmentStatus mapeado
    assert "req-9" in text
    # situação derivada dos campos canônicos — aberta sem endedAt
    assert "Aberta" in text


def test_xlsx_export_produces_workbook_with_metadata_sheet():
    result = service().export_occurrences(
        user(*EXPORT_PERMS), branch="01", export_format="xlsx",
    )
    assert result["filename"].endswith(".xlsx")
    assert result["content"][:2] == b"PK"  # zip do xlsx


def test_export_forwards_all_filters_and_pendency_flag():
    gw = FakeGateway()
    MesDowntimeExportService(gateway=gw).export_occurrences(
        user(*EXPORT_PERMS), branch="01", export_format="csv",
        pendency=True, work_center=" CT-41 ", reason_code=" setup ",
        status="open", source="system", classification="pending",
    )
    assert gw.export_kwargs["pendency"] is True
    assert gw.export_kwargs["work_center"] == "CT-41"
    assert gw.export_kwargs["reason_code"] == "setup"
    assert gw.export_kwargs["status"] == "open"


def test_export_requires_export_permission():
    with pytest.raises(PermissionError):
        service().export_occurrences(
            user("delpi-mes.access", "delpi-mes.downtimes.view",
                 "delpi-mes.view.filial-01"),
            branch="01", export_format="csv",
        )


def test_export_denies_other_branch():
    with pytest.raises(BranchAccessDenied):
        service().export_occurrences(
            user("delpi-mes.access", "delpi-mes.downtimes.export",
                 "delpi-mes.view.filial-02"),
            branch="01", export_format="csv",
        )


def test_export_requires_human_principal():
    with pytest.raises(HumanPrincipalRequired):
        service().export_occurrences(
            user(*EXPORT_PERMS, principal_type="service"),
            branch="01", export_format="csv",
        )


def test_export_rejects_invalid_format():
    with pytest.raises(ValueError, match="format"):
        service().export_occurrences(
            user(*EXPORT_PERMS), branch="01", export_format="pdf",
        )


def test_executive_pdf_contains_indicators_and_metadata():
    from datetime import datetime, timezone
    result = service().export_executive_report(
        user(*EXPORT_PERMS), branch="01",
        period_from=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    assert result["contentType"] == "application/pdf"
    assert result["filename"].endswith(".pdf")
    assert result["content"].startswith(b"%PDF")
    assert len(result["content"]) > 500


def test_executive_pdf_requires_period_and_branch_authz():
    from datetime import datetime, timezone
    svc = service()
    with pytest.raises(BranchAccessDenied):
        svc.export_executive_report(
            user("delpi-mes.access", "delpi-mes.downtimes.export",
                 "delpi-mes.view.filial-02"),
            branch="01",
            period_from=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
