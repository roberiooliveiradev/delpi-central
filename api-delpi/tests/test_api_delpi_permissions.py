from app.application.security import api_delpi_permissions as perms


def test_core_permissions_are_stable_strings() -> None:
    assert perms.API_DELPI_ACCESS == "api-delpi.access"
    assert perms.API_DELPI_QUALITY_ACCESS == "api-delpi.quality.access"
    assert perms.AUDITORIA_5S_AUDIT_FILIAL_01 == "auditoria-5s.audit.filial-01"


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
    assert perms.SCHEDULING_BRANCH_APPROVE_PERMS["ES"] == perms.CENTRAL_AGENDAMENTO_APPROVE_FILIAL_ES
    assert perms.CENTRAL_AGENDAMENTO_APPROVE_FILIAL_SC in perms.SCHEDULING_APPROVE_PERMISSIONS


def test_retrabalho_branch_maps_use_filial_constants() -> None:
    assert perms.CONTROLE_RETRABALHO_BRANCH_VIEW_PERMS["01"] == (
        perms.CONTROLE_RETRABALHO_VIEW_FILIAL_SC
    )
    assert perms.CONTROLE_RETRABALHO_BRANCH_VIEW_PERMS["02"] == (
        perms.CONTROLE_RETRABALHO_VIEW_FILIAL_ES
    )


def test_financeiro_centro_custo_permissions_are_stable_strings() -> None:
    assert perms.FINANCEIRO_CENTRO_CUSTO_ACCESS == "financeiro-centro-custo.access"
    assert perms.FINANCEIRO_CENTRO_CUSTO_VIEW == "financeiro-centro-custo.view"
    assert perms.FINANCEIRO_CENTRO_CUSTO_EXPORT == "financeiro-centro-custo.export"


def test_financeiro_centro_custo_read_permissions_include_access_and_view() -> None:
    assert perms.FINANCEIRO_CENTRO_CUSTO_ACCESS in perms.FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS
    assert perms.FINANCEIRO_CENTRO_CUSTO_VIEW in perms.FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS
    assert perms.API_DELPI_ACCESS in perms.FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS


def test_financeiro_centro_custo_export_permissions_include_export() -> None:
    assert perms.FINANCEIRO_CENTRO_CUSTO_EXPORT in (
        perms.FINANCEIRO_CENTRO_CUSTO_EXPORT_PERMISSIONS
    )
