"""Códigos RBAC do Transformômetro — escopo por filial (Playbook 18 S10).

Meeting minutes: canônico `meeting-minutes.*`; `atas.*` permanece como alias legado.

Escopo de filial (canônico): `transformometro.branch.filial-*` — só segrega.
Combinar com capacidades (`*.view` / `*.manage` / `*.sign` / `processes.manage` …).
Legado: `view.filial-*` e `manage.filial-*` continuam como aliases de escopo
(`manage.filial-*` também implica manage naquela filial).
"""

from __future__ import annotations

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
