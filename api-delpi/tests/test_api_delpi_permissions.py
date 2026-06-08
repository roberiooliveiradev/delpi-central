from app.application.security import api_delpi_permissions as perms


def test_core_permissions_are_stable_strings() -> None:
    assert perms.API_DELPI_ACCESS == "api-delpi.access"
    assert perms.QUALITY_NC_MANAGE == "quality-nc.manage"


def test_kpi_access_lists_include_api_delpi_access() -> None:
    for group in (
        perms.KPI_FINANCIAL_ACCESS,
        perms.KPI_COMMERCIAL_ACCESS,
        perms.KPI_PRODUCTION_ACCESS,
        perms.KPI_SUPPLIES_ACCESS,
        perms.KPI_HR_ACCESS,
    ):
        assert perms.API_DELPI_ACCESS in group


def test_scheduling_branch_maps_use_central_constants() -> None:
    assert perms.SCHEDULING_BRANCH_VIEW_PERMS["ES"] == perms.CENTRAL_AGENDAMENTO_VIEW_FILIAL_ES
    assert perms.SCHEDULING_BRANCH_MANAGE_PERMS["SC"] == perms.CENTRAL_AGENDAMENTO_MANAGE_FILIAL_SC
