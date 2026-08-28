"""Política de leitura no fallback semântico — filtra write/destructive."""

from __future__ import annotations

from typing import Any

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionSelectionReadPolicyService:
    """Aplica `actionSelection.readPolicy` sobre ranked do semantic fallback."""

    @classmethod
    def policy(cls) -> dict[str, Any]:
        node = ExternalActionResponseContentService.get_node(
            "actionSelection",
            "readPolicy",
        )
        return dict(node) if isinstance(node, dict) else {}

    @classmethod
    def is_safe_action(cls, action: dict[str, Any] | None, *, policy: dict[str, Any] | None = None) -> bool:
        if not isinstance(action, dict):
            return False

        cfg = policy if isinstance(policy, dict) else cls.policy()
        if not cfg.get("blockDestructive", True):
            return True

        blocked = {
            str(item).strip().lower()
            for item in (cfg.get("blockedSensitivities") or [])
            if str(item).strip()
        }
        sensitivity = str(action.get("sensitivity") or "").strip().lower()
        if sensitivity and sensitivity in blocked:
            return False

        prefer_method = str(cfg.get("preferSafeMethod") or "GET").strip().upper() or "GET"
        method = str(action.get("method") or "GET").strip().upper() or "GET"
        if prefer_method and method not in {prefer_method, "HEAD", "OPTIONS"}:
            return False

        return True

    @classmethod
    def apply(
        cls,
        ranked: list[dict] | None,
    ) -> tuple[dict | None, list[dict], str | None]:
        """
        Retorna (action_escolhida, ranked_ajustado, reason_key|None).

        reason_key=`readPolicyClarification` quando não há rival seguro.
        """
        items = [item for item in (ranked or []) if isinstance(item, dict)]
        if not items:
            return None, [], None

        cfg = cls.policy()
        if not cfg:
            return items[0], items, None

        if not cfg.get("blockDestructive", True):
            return items[0], items, None

        safe_items = [item for item in items if cls.is_safe_action(item, policy=cfg)]
        if not safe_items:
            if cfg.get("clarifyOnNoSafeRival", True):
                return None, items, "readPolicyClarification"
            return None, items, "readPolicyBlocked"

        preferred = safe_items[0]
        reason = None
        if preferred is not items[0]:
            reason = "readPolicyPreferSafe"

        # Downstream (score-gap) só vê candidatas seguras de leitura.
        return preferred, safe_items, reason
