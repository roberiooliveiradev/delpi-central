"""Códigos RBAC do Transformômetro.

Alvo: `transformometro.access` e `transformometro.manage`.
Os 21 códigos antigos permanecem no manifesto nesta fatia.
Códigos `branch.*`, `view.filial-*` e `manage.filial-*` são legado.
Eles não concedem acesso ao portal.
`view.consolidated` também não concede acesso: consolidado é filtro.
`meeting-minutes.sign` e `atas.sign` autorizam a ação de assinar e o detalhe
pendente. Não abrem a lista de processos.
"""

from __future__ import annotations

TRANSFORMOMETRO_ACCESS = "transformometro.access"
TRANSFORMOMETRO_MANAGE = "transformometro.manage"
TRANSFORMOMETRO_VIEW = "transformometro.view"
TRANSFORMOMETRO_VIEW_CONSOLIDATED = "transformometro.view.consolidated"
TRANSFORMOMETRO_VIEW_FILIAL_01 = "transformometro.view.filial-01"
TRANSFORMOMETRO_VIEW_FILIAL_02 = "transformometro.view.filial-02"
TRANSFORMOMETRO_MANAGE_FILIAL_01 = "transformometro.manage.filial-01"
TRANSFORMOMETRO_MANAGE_FILIAL_02 = "transformometro.manage.filial-02"

# Segregadores de filial (capacidade × escopo)
TRANSFORMOMETRO_BRANCH_FILIAL_01 = "transformometro.branch.filial-01"
TRANSFORMOMETRO_BRANCH_FILIAL_02 = "transformometro.branch.filial-02"

TRANSFORMOMETRO_PROCESSES_MANAGE = "transformometro.processes.manage"
TRANSFORMOMETRO_REVISIONS_MANAGE = "transformometro.revisions.manage"
TRANSFORMOMETRO_MEASUREMENTS_MANAGE = "transformometro.measurements.manage"
TRANSFORMOMETRO_INVESTMENTS_MANAGE = "transformometro.investments.manage"
TRANSFORMOMETRO_SHARED_RESOURCES_MANAGE = "transformometro.shared-resources.manage"
TRANSFORMOMETRO_DASHBOARD_RECALCULATE = "transformometro.dashboard.recalculate"
TRANSFORMOMETRO_DATA_TRANSFER = "transformometro.data.transfer"

# Canônico EN
TRANSFORMOMETRO_MEETING_MINUTES_VIEW = "transformometro.meeting-minutes.view"
TRANSFORMOMETRO_MEETING_MINUTES_MANAGE = "transformometro.meeting-minutes.manage"
TRANSFORMOMETRO_MEETING_MINUTES_SIGN = "transformometro.meeting-minutes.sign"

# Alias legado PT (dual até migração RBAC)
TRANSFORMOMETRO_ATAS_VIEW = "transformometro.atas.view"
TRANSFORMOMETRO_ATAS_MANAGE = "transformometro.atas.manage"
TRANSFORMOMETRO_ATAS_SIGN = "transformometro.atas.sign"

MEETING_MINUTES_VIEW_PERMISSIONS: tuple[str, ...] = (
    TRANSFORMOMETRO_MEETING_MINUTES_VIEW,
    TRANSFORMOMETRO_ATAS_VIEW,
)
MEETING_MINUTES_MANAGE_PERMISSIONS: tuple[str, ...] = (
    TRANSFORMOMETRO_MEETING_MINUTES_MANAGE,
    TRANSFORMOMETRO_ATAS_MANAGE,
)
MEETING_MINUTES_SIGN_PERMISSIONS: tuple[str, ...] = (
    TRANSFORMOMETRO_MEETING_MINUTES_SIGN,
    TRANSFORMOMETRO_ATAS_SIGN,
)
MEETING_MINUTES_READ_PERMISSIONS: tuple[str, ...] = (
    *MEETING_MINUTES_VIEW_PERMISSIONS,
    *MEETING_MINUTES_MANAGE_PERMISSIONS,
    *MEETING_MINUTES_SIGN_PERMISSIONS,
)
MEETING_MINUTES_LIST_PERMISSIONS: tuple[str, ...] = (
    *MEETING_MINUTES_VIEW_PERMISSIONS,
    *MEETING_MINUTES_MANAGE_PERMISSIONS,
)
MEETING_MINUTES_PROFILE_PERMISSIONS: tuple[str, ...] = MEETING_MINUTES_READ_PERMISSIONS

BRANCH_SCOPE_PERMISSIONS: dict[str, str] = {
    "01": TRANSFORMOMETRO_BRANCH_FILIAL_01,
    "02": TRANSFORMOMETRO_BRANCH_FILIAL_02,
}

VIEW_FILIAL_PERMISSIONS: dict[str, str] = {
    "01": TRANSFORMOMETRO_VIEW_FILIAL_01,
    "02": TRANSFORMOMETRO_VIEW_FILIAL_02,
}

MANAGE_FILIAL_PERMISSIONS: dict[str, str] = {
    "01": TRANSFORMOMETRO_MANAGE_FILIAL_01,
    "02": TRANSFORMOMETRO_MANAGE_FILIAL_02,
}

GLOBAL_MANAGE_PERMISSIONS: tuple[str, ...] = (
    TRANSFORMOMETRO_PROCESSES_MANAGE,
    TRANSFORMOMETRO_REVISIONS_MANAGE,
    TRANSFORMOMETRO_MEASUREMENTS_MANAGE,
    TRANSFORMOMETRO_INVESTMENTS_MANAGE,
    TRANSFORMOMETRO_SHARED_RESOURCES_MANAGE,
    TRANSFORMOMETRO_MEETING_MINUTES_MANAGE,
    TRANSFORMOMETRO_ATAS_MANAGE,
)

BRANCH_VIEW_PERMISSIONS: tuple[str, ...] = tuple(VIEW_FILIAL_PERMISSIONS.values())
BRANCH_MANAGE_PERMISSIONS: tuple[str, ...] = tuple(MANAGE_FILIAL_PERMISSIONS.values())
BRANCH_SCOPE_PERMISSION_CODES: tuple[str, ...] = tuple(BRANCH_SCOPE_PERMISSIONS.values())

# Uso normal legado. Inclui o CRUD do domínio que o alvo absorve em access.
# Não inclui filial nem consolidado. Sign não abre o portal: só a ação de assinar.
LEGACY_NORMAL_USE_PERMISSIONS: tuple[str, ...] = (
    TRANSFORMOMETRO_VIEW,
    TRANSFORMOMETRO_PROCESSES_MANAGE,
    TRANSFORMOMETRO_REVISIONS_MANAGE,
    TRANSFORMOMETRO_MEASUREMENTS_MANAGE,
    TRANSFORMOMETRO_INVESTMENTS_MANAGE,
    TRANSFORMOMETRO_SHARED_RESOURCES_MANAGE,
    TRANSFORMOMETRO_DASHBOARD_RECALCULATE,
    TRANSFORMOMETRO_DATA_TRANSFER,
    *MEETING_MINUTES_VIEW_PERMISSIONS,
    *MEETING_MINUTES_MANAGE_PERMISSIONS,
)

# Estes códigos não são access. Ficam nomeados para o teste negativo.
LEGACY_SCOPE_CODES_THAT_DO_NOT_GRANT_ACCESS: tuple[str, ...] = (
    *BRANCH_SCOPE_PERMISSION_CODES,
    *BRANCH_VIEW_PERMISSIONS,
    *BRANCH_MANAGE_PERMISSIONS,
    TRANSFORMOMETRO_VIEW_CONSOLIDATED,
)
