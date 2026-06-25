"""Acesso PAC no chat — leitura vs escrita (Onda 5.7)."""

from __future__ import annotations

from app.domain.ports.external_action_repository_port import ExternalActionRepositoryPort

QUALITY_ACTION_PLANS_PATH_TOKEN = "/quality/action-plans"

_PAC_WRITE_OPERATION_MARKERS = (
    "create_quality_action_plan",
    "update_quality_action_plan",
    "upsert_quality_action_plan",
    "reopen_quality_action_plan",
    "submit_quality_action_plan_effectiveness",
    "approve_quality_action_plan_effectiveness",
    "reject_quality_action_plan_effectiveness",
    "record_quality_action_plan_effectiveness",
    "attach_quality_action_plan_evidence",
    "delete_quality_action_plan_evidence",
    "promote_quality_action_plan_solution_pattern",
    "dispatch_quality_action_plan_notifications",
)

_WRITE_SENSITIVITIES = frozenset({"write", "destructive", "admin"})


class ChatQualityActionPlansAccessService:
    """Deriva modo só consulta a partir das actions PAC permitidas ao agente."""

    _external_action_repository: ExternalActionRepositoryPort | None = None

    @classmethod
    def configure_external_action_repository(
        cls,
        repository: ExternalActionRepositoryPort | None,
    ) -> None:
        cls._external_action_repository = repository

    @classmethod
    def resolve_read_only_mode(cls, allowed_action_ids: list[str] | None) -> bool:
        """True quando há leitura PAC mas nenhuma escrita PAC no catálogo permitido."""
        if not allowed_action_ids:
            return False

        allowed_set = {
            str(item).strip() for item in allowed_action_ids if str(item).strip()
        }

        if not allowed_set:
            return False

        pac_actions = cls._list_allowed_pac_actions(allowed_set)

        if not pac_actions:
            return cls._read_only_from_action_id_markers(allowed_set)

        return not any(cls._is_write_action(action) for action in pac_actions)

    @classmethod
    def _list_allowed_pac_actions(cls, allowed_set: set[str]) -> list[dict]:
        repository = cls._external_action_repository

        if repository is None:
            return []

        try:
            return [
                action
                for action in repository.list_actions()
                if str(action.get("actionId") or "").strip() in allowed_set
                and QUALITY_ACTION_PLANS_PATH_TOKEN
                in str(action.get("path") or "").lower()
            ]
        except Exception:
            return []

    @classmethod
    def _is_write_action(cls, action: dict) -> bool:
        sensitivity = str(action.get("sensitivity") or "").lower().strip()

        if sensitivity in _WRITE_SENSITIVITIES:
            return True

        method = str(action.get("method") or "").upper().strip()

        return method not in {"", "GET", "HEAD"}

    @classmethod
    def _read_only_from_action_id_markers(cls, allowed_set: set[str]) -> bool:
        has_read_marker = any(
            marker in action_id
            for action_id in allowed_set
            for marker in (
                "list_quality_action_plans",
                "get_quality_action_plans_dashboard",
                "get_quality_action_plan_detail",
            )
        )
        has_write_marker = any(
            marker in action_id
            for action_id in allowed_set
            for marker in _PAC_WRITE_OPERATION_MARKERS
        )

        return has_read_marker and not has_write_marker
