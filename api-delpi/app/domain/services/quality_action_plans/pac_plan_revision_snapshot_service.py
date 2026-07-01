from __future__ import annotations

from copy import deepcopy
from typing import Any

SNAPSHOT_SCHEMA_VERSION = 1

REVISION_SCOPE_CREATED = "created"
REVISION_SCOPE_IDENTIFICATION = "identification"
REVISION_SCOPE_STATUS = "status"
REVISION_SCOPE_ISHIKAWA = "ishikawa"
REVISION_SCOPE_FIVE_WHYS = "five_whys"
REVISION_SCOPE_RNC_8D = "rnc_8d"
REVISION_SCOPE_ACTIONS = "actions"
REVISION_SCOPE_EFFECTIVENESS = "effectiveness"
REVISION_SCOPE_RESTORE = "restore"

VALID_REVISION_SCOPES = frozenset(
    {
        REVISION_SCOPE_CREATED,
        REVISION_SCOPE_IDENTIFICATION,
        REVISION_SCOPE_STATUS,
        REVISION_SCOPE_ISHIKAWA,
        REVISION_SCOPE_FIVE_WHYS,
        REVISION_SCOPE_RNC_8D,
        REVISION_SCOPE_ACTIONS,
        REVISION_SCOPE_EFFECTIVENESS,
        REVISION_SCOPE_RESTORE,
    }
)

_PLAN_DERIVED_KEYS = frozenset(
    {
        "was_ever_completed",
        "contact_roles",
        "sla_level",
        "days_without_update",
        "sla_warning_days",
        "sla_breach_days",
        "incomplete_actions_count",
    }
)

_ACTION_VOLATILE_KEYS = frozenset({"created_at", "updated_at", "completed_at"})

_EVIDENCE_METADATA_KEYS = frozenset(
    {
        "id",
        "type",
        "section",
        "description",
        "knowledge_visible",
        "action_id",
        "file_name",
    }
)

_DEFAULT_SUMMARIES: dict[str, str] = {
    REVISION_SCOPE_CREATED: "Plano criado.",
    REVISION_SCOPE_IDENTIFICATION: "Identificação do plano atualizada.",
    REVISION_SCOPE_STATUS: "Status do plano alterado.",
    REVISION_SCOPE_ISHIKAWA: "Análise Ishikawa atualizada.",
    REVISION_SCOPE_FIVE_WHYS: "Análise 5 Porquês atualizada.",
    REVISION_SCOPE_RNC_8D: "Relatório 8D atualizado.",
    REVISION_SCOPE_ACTIONS: "Ações do plano atualizadas.",
    REVISION_SCOPE_EFFECTIVENESS: "Eficácia do plano atualizada.",
    REVISION_SCOPE_RESTORE: "Plano restaurado de revisão anterior.",
}


def default_revision_summary(scope: str) -> str:
    return _DEFAULT_SUMMARIES.get(scope, "Plano atualizado.")


def build_snapshot_from_detail(detail: dict[str, Any]) -> dict[str, Any]:
    plan = {
        key: value
        for key, value in (detail.get("plan") or {}).items()
        if key not in _PLAN_DERIVED_KEYS
    }
    actions: list[dict[str, Any]] = []
    for action in detail.get("actions") or []:
        if not isinstance(action, dict):
            continue
        trimmed = {
            key: value
            for key, value in action.items()
            if key not in _ACTION_VOLATILE_KEYS
        }
        if trimmed.get("id"):
            actions.append(trimmed)

    team_members: list[dict[str, Any]] = []
    for member in detail.get("team_members") or []:
        if not isinstance(member, dict):
            continue
        team_members.append(
            {
                "member_name": member.get("member_name"),
                "member_user_id": member.get("member_user_id"),
                "department": member.get("department"),
                "is_leader": bool(member.get("is_leader")),
                "sort_order": member.get("sort_order", 0),
            }
        )

    evidences: list[dict[str, Any]] = []
    for evidence in detail.get("evidences") or []:
        if not isinstance(evidence, dict) or not evidence.get("id"):
            continue
        evidences.append(
            {key: evidence.get(key) for key in _EVIDENCE_METADATA_KEYS if key in evidence}
        )

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "plan": plan,
        "ishikawa": deepcopy(detail.get("ishikawa")),
        "five_whys": deepcopy(detail.get("five_whys")),
        "actions": actions,
        "team_members": team_members,
        "evidences": evidences,
    }


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    if not isinstance(snapshot, dict):
        raise ValueError("Snapshot inválido.")
    if int(snapshot.get("schema_version") or 0) != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError("Versão de snapshot não suportada.")
    if not isinstance(snapshot.get("plan"), dict):
        raise ValueError("Snapshot sem bloco plan.")


def plan_fields_for_restore(snapshot: dict[str, Any]) -> dict[str, Any]:
    validate_snapshot(snapshot)
    plan = snapshot.get("plan") or {}
    allowed = {
        key: value
        for key, value in plan.items()
        if key not in {"id", "code", "created_at", "created_by_user_id", "deleted_at"}
        and key not in _PLAN_DERIVED_KEYS
    }
    return allowed
