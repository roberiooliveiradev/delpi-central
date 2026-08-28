"""Interpretador determinístico de follow-up grounded (revise / challenge / clarify / narrate)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.services.chat_follow_up_turn_content_service import (
    ChatFollowUpTurnContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_turn_grounding_content_service import (
    ChatTurnGroundingContentService,
)


@dataclass(frozen=True)
class ChatFollowUpTurnInterpretation:
    decision: str
    reason: str
    continuity_mode: str = "allow_discovery"
    slot_delta: dict[str, str] = field(default_factory=dict)
    clarify_slot: str | None = None
    suppress_broad_narrate: bool = False

    def allows_parallel_discovery(self) -> bool:
        return self.continuity_mode == "allow_discovery"

    def requires_last_action_reexec(self) -> bool:
        return self.continuity_mode == "consume_last_action"

    def to_metadata(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "decision": self.decision,
            "reason": self.reason,
            "continuityMode": self.continuity_mode,
            "suppressBroadNarrate": self.suppress_broad_narrate,
            "allowsParallelDiscovery": self.allows_parallel_discovery(),
            "requiresLastActionReexec": self.requires_last_action_reexec(),
        }
        if self.slot_delta:
            payload["slotDelta"] = dict(self.slot_delta)
        if self.clarify_slot:
            payload["clarifySlot"] = self.clarify_slot
        return payload


class ChatFollowUpTurnInterpretationService:
    """Ordem canônica: switch → revise → clarify → challenge → narrate → new_intent."""

    @classmethod
    def interpret(
        cls,
        *,
        message: str,
        last_action: dict[str, Any] | None = None,
        last_result_excerpt: dict[str, Any] | None = None,
        operational_focus: dict[str, Any] | None = None,
    ) -> ChatFollowUpTurnInterpretation:
        del operational_focus  # reservado para slots futuros (produto/foco)

        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""
        typo_fixed = ChatFollowUpTurnContentService.normalize_branch_typos(message)
        typo_normalized = (
            ChatMessageNormalizationService.normalize_for_matching(typo_fixed) or normalized
        )

        excerpt = last_result_excerpt if isinstance(last_result_excerpt, dict) else None
        has_excerpt = bool(excerpt)
        action = last_action if isinstance(last_action, dict) else None
        action_useful = cls._is_useful_last_action(action)

        if action_useful and cls._is_topic_switch(typo_normalized, action):
            return cls._build(
                decision="new_intent",
                reason="topic_switch",
                suppress_broad_narrate=True,
            )

        slot_delta = cls._extract_slot_delta(typo_fixed, typo_normalized, action)
        has_revise_trigger = cls._has_revise_slot_trigger(typo_normalized)
        has_challenge = ChatFollowUpTurnContentService.message_has_any_trigger(
            typo_normalized,
            ChatFollowUpTurnContentService.challenge_triggers(),
        )

        if slot_delta:
            if action_useful:
                return cls._build(
                    decision="revise_last_query",
                    reason="slot_delta",
                    slot_delta=slot_delta,
                    suppress_broad_narrate=True,
                )
            return cls._build(
                decision="new_intent",
                reason="slot_delta_without_last_action",
                slot_delta=slot_delta,
                suppress_broad_narrate=True,
            )

        if has_revise_trigger and ChatFollowUpTurnContentService.has_branch_trigger_without_code(
            typo_fixed
        ):
            if (action_useful or has_excerpt) and not has_challenge:
                return cls._build(
                    decision="clarify_slot",
                    reason="branch_ambiguous",
                    clarify_slot="branch",
                    suppress_broad_narrate=True,
                )

        if has_challenge and has_excerpt:
            return cls._build(
                decision="challenge_last_result",
                reason="challenge_triggers",
                suppress_broad_narrate=True,
            )

        if cls._is_explicit_insight_enrich(typo_normalized):
            return cls._build(
                decision="new_intent",
                reason="defer_enrich_insight",
            )

        if cls._is_explicit_insight_narrate(typo_normalized) and has_excerpt:
            return cls._build(
                decision="narrate_recap",
                reason="insight_narrate_trigger",
                suppress_broad_narrate=False,
            )

        if (
            has_excerpt
            and ChatFollowUpTurnContentService.message_has_any_trigger(
                typo_normalized,
                ChatFollowUpTurnContentService.narrate_reference_triggers(),
            )
        ):
            return cls._build(
                decision="narrate_recap",
                reason="explicit_reference",
                suppress_broad_narrate=False,
            )

        return cls._build(
            decision="new_intent",
            reason="no_follow_up_match",
        )

    @classmethod
    def _build(
        cls,
        *,
        decision: str,
        reason: str,
        slot_delta: dict[str, str] | None = None,
        clarify_slot: str | None = None,
        suppress_broad_narrate: bool = False,
        continuity_mode: str | None = None,
    ) -> ChatFollowUpTurnInterpretation:
        mode = continuity_mode or ChatFollowUpTurnContentService.continuity_mode_for_decision(
            decision
        )
        return ChatFollowUpTurnInterpretation(
            decision=decision,
            reason=reason,
            continuity_mode=mode,
            slot_delta=dict(slot_delta or {}),
            clarify_slot=clarify_slot,
            suppress_broad_narrate=suppress_broad_narrate,
        )

    @classmethod
    def grounded_stage_for(
        cls,
        interpretation: ChatFollowUpTurnInterpretation,
    ) -> str | None:
        if interpretation.decision == "narrate_recap":
            if interpretation.reason == "insight_narrate_trigger":
                return "grounded_narrate_insight"
            return ChatFollowUpTurnContentService.stage_for_decision("narrate_recap")
        return ChatFollowUpTurnContentService.stage_for_decision(interpretation.decision)

    @classmethod
    def _is_useful_last_action(cls, last_action: dict[str, Any] | None) -> bool:
        if not isinstance(last_action, dict) or not last_action:
            return False
        path = str(last_action.get("path") or "").strip()
        name = str(last_action.get("name") or "").strip()
        operation_id = str(last_action.get("operationId") or last_action.get("operation_id") or "").strip()
        return bool(path or name or operation_id)

    @classmethod
    def _extract_slot_delta(
        cls,
        message: str,
        normalized: str,
        last_action: dict[str, Any] | None,
    ) -> dict[str, str]:
        delta: dict[str, str] = {}
        branch = ChatFollowUpTurnContentService.extract_branch_code(message)
        if branch and cls._has_revise_slot_trigger(normalized):
            delta["branch"] = branch
        elif branch and ChatFollowUpTurnContentService.compile_pattern("branchWithCode").search(
            ChatFollowUpTurnContentService.normalize_branch_typos(message)
        ):
            # «rol filail 01 deste mês» — branch explícito mesmo sem «somente»
            if "filial" in normalized or "filail" in normalized or "unidade" in normalized:
                delta["branch"] = branch

        period_kind = ChatFollowUpTurnContentService.period_slot_kind_for_message(normalized)
        if period_kind:
            delta["period"] = period_kind
            params = (
                last_action.get("params")
                if isinstance(last_action, dict) and isinstance(last_action.get("params"), dict)
                else {}
            )
            from app.domain.services.chat_date_range_intent_service import (
                ChatDateRangeIntentService,
            )

            shifted = ChatDateRangeIntentService.apply_period_slot(
                period_kind,
                start_date=str(params.get("start_date") or "") or None,
                end_date=str(params.get("end_date") or "") or None,
            )
            if shifted is not None:
                delta["start_date"] = shifted.start_date
                delta["end_date"] = shifted.end_date

        return delta

    @classmethod
    def _has_revise_slot_trigger(cls, normalized: str) -> bool:
        return ChatFollowUpTurnContentService.message_has_any_trigger(
            normalized,
            ChatFollowUpTurnContentService.revise_slot_triggers(),
        )

    @classmethod
    def _is_topic_switch(cls, normalized: str, last_action: dict[str, Any]) -> bool:
        action_blob = " ".join(
            str(last_action.get(key) or "")
            for key in ("path", "name", "operationId", "operation_id", "apiRouteDomain")
        ).lower()
        params = last_action.get("params")
        if isinstance(params, dict):
            action_blob = f"{action_blob} {' '.join(str(v) for v in params.values())}"

        markers = ChatFollowUpTurnContentService.topic_switch_markers()
        excludes = ChatFollowUpTurnContentService.topic_switch_exclude_markers()

        for domain, domain_markers in markers.items():
            if not any(marker in normalized for marker in domain_markers):
                continue
            exclude = excludes.get(domain) or ()
            if any(token in action_blob for token in exclude):
                continue
            # Pivot: mensagem traz domínio novo e ainda parece pergunta (não só refine de filial)
            if cls._has_revise_slot_trigger(normalized) and ChatFollowUpTurnContentService.extract_branch_code(
                normalized
            ):
                continue
            return True
        return False

    @classmethod
    def _is_explicit_insight_enrich(cls, normalized: str) -> bool:
        return any(
            ChatMessageNormalizationService.normalize_for_matching(token) in normalized
            for token in ChatTurnGroundingContentService.insight_enrich_triggers()
            if ChatMessageNormalizationService.normalize_for_matching(token)
        )

    @classmethod
    def _is_explicit_insight_narrate(cls, normalized: str) -> bool:
        return any(
            ChatMessageNormalizationService.normalize_for_matching(token) in normalized
            for token in ChatTurnGroundingContentService.insight_narrate_triggers()
            if ChatMessageNormalizationService.normalize_for_matching(token)
        )
