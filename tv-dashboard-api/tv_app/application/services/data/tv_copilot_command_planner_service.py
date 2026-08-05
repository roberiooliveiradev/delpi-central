"""Planner canônico do Copiloto TV — capability → ops tipadas + política de execução."""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)
from tv_app.application.services.data.tv_copilot_suggest_ops_service import (
    TvCopilotSuggestOpsService,
)


class TvCopilotCommandPlannerService:
    """Produz um plano discriminado a partir de NL + hostContext.

    Status:
    - ``ready`` — ops tipadas válidas; ``confirmationPolicy`` diz se aplica direto
    - ``clarification`` — faltam dados/contexto; ``reason`` é a mensagem ao usuário
    - ``unsupported`` — nenhuma capability casou
    - ``error`` — mensagem vazia / envelope inválido
    """

    @classmethod
    def plan(cls, *, message: str, host_context: dict | None) -> dict[str, Any]:
        suggestion = TvCopilotSuggestOpsService.materialize(
            message=message,
            host_context=host_context,
        )
        catalog_version = str(suggestion.get("catalogVersion") or "").strip()
        matched = suggestion.get("matchedCapabilityKeys") or []
        if not isinstance(matched, list):
            matched = []
        ops = suggestion.get("ops")
        if not isinstance(ops, list):
            ops = []

        host = host_context if isinstance(host_context, dict) else {}
        playlist_id = str(host.get("playlistId") or "").strip()
        slide_id = str(host.get("slideId") or "").strip()
        has_local_draft = bool(host.get("hasLocalDraft") or host.get("localDraftDirty"))

        # Mensagem vazia / sem match / clarificação já resolvida no suggest.
        if not ops:
            clarification_key = suggestion.get("clarificationKey")
            reason = str(suggestion.get("reason") or "").strip()
            if not str(message or "").strip():
                return cls._result(
                    status="error",
                    catalog_version=catalog_version,
                    matched=matched,
                    reason=reason,
                    clarification_key=clarification_key,
                )
            if matched:
                return cls._result(
                    status="clarification",
                    catalog_version=catalog_version,
                    matched=matched,
                    reason=reason,
                    clarification_key=clarification_key,
                )
            return cls._result(
                status="unsupported",
                catalog_version=catalog_version,
                matched=matched,
                reason=reason,
                clarification_key=clarification_key,
            )

        policy = TvCopilotContentService.aggregate_ops_policy(ops)

        if policy["requiresPlaylist"] and not playlist_id:
            return cls._result(
                status="clarification",
                catalog_version=catalog_version,
                matched=matched,
                reason=TvCopilotContentService.message("suggestNeedPlaylist"),
                clarification_key="suggestNeedPlaylist",
                policy=policy,
            )

        if policy["requiresSlide"] and not slide_id:
            return cls._result(
                status="clarification",
                catalog_version=catalog_version,
                matched=matched,
                reason=TvCopilotContentService.message("suggestNeedSlideOrCreate"),
                clarification_key="suggestNeedSlideOrCreate",
                policy=policy,
            )

        if policy["requiresSlide"] and has_local_draft:
            return cls._result(
                status="clarification",
                catalog_version=catalog_version,
                matched=matched,
                reason=TvCopilotContentService.message("suggestLocalDraftConflict"),
                clarification_key="suggestLocalDraftConflict",
                policy=policy,
            )

        confirmation = str(policy.get("confirmationPolicy") or "direct")
        if confirmation == "confirm":
            reason = TvCopilotContentService.message(
                "planReadyConfirm", count=len(ops)
            )
        else:
            reason = TvCopilotContentService.message(
                "planReadyDirect", count=len(ops)
            )

        return cls._result(
            status="ready",
            catalog_version=catalog_version,
            matched=matched,
            reason=reason,
            ops=ops,
            policy=policy,
        )

    @classmethod
    def to_suggest_payload(cls, plan: dict[str, Any]) -> dict[str, Any]:
        """Fachada compatível com o contrato histórico de suggest-ops."""
        status = str(plan.get("status") or "")
        ops = plan.get("ops") if isinstance(plan.get("ops"), list) else []
        ready = status == "ready"
        return {
            "catalogVersion": plan.get("catalogVersion"),
            "ops": list(ops) if ready else [],
            "matchedCapabilityKeys": plan.get("matchedCapabilityKeys") or [],
            "clarificationKey": plan.get("clarificationKey"),
            "reason": plan.get("reason"),
            "status": status,
            "confirmationPolicy": plan.get("confirmationPolicy"),
            "risk": plan.get("risk"),
            "sideEffectHints": plan.get("sideEffectHints") or [],
            "requiresPlaylist": bool(plan.get("requiresPlaylist")),
            "requiresSlide": bool(plan.get("requiresSlide")),
        }

    @classmethod
    def _result(
        cls,
        *,
        status: str,
        catalog_version: str,
        matched: list[Any],
        reason: str,
        clarification_key: str | None = None,
        ops: list[dict[str, Any]] | None = None,
        policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        policy = policy or {}
        return {
            "status": status,
            "catalogVersion": catalog_version,
            "ops": list(ops or []),
            "matchedCapabilityKeys": list(matched),
            "clarificationKey": clarification_key,
            "reason": reason,
            "confirmationPolicy": str(policy.get("confirmationPolicy") or "direct"),
            "risk": str(policy.get("risk") or "additive"),
            "sideEffectHints": list(policy.get("sideEffectHints") or []),
            "requiresPlaylist": bool(policy.get("requiresPlaylist")),
            "requiresSlide": bool(policy.get("requiresSlide")),
        }
