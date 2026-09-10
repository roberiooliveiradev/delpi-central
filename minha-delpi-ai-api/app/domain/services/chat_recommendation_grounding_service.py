"""Contrato de grounding para recomendações contextuais (E6.S2) — input bounded, sem payload bruto."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)

_RECOMMENDATION_SOURCES = frozenset(
    {
        "llm_contextual",
        "profile_fallback",
        "deterministic",
    }
)


@dataclass(frozen=True)
class RecommendationGroundingContext:
    """Input mínimo para producer contextual (E6.S3+); nunca inclui data bruto ilimitado."""

    user_message: str
    user_goals: tuple[str, ...]
    facts: tuple[str, ...]
    limitations: tuple[str, ...]
    result_refs: tuple[dict[str, str], ...]
    allowed_action_ids: tuple[str, ...]
    already_executed_action_ids: tuple[str, ...]
    already_executed_goal_ids: tuple[str, ...]
    profile_key: str
    truncated: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "userMessage": self.user_message,
            "userGoals": list(self.user_goals),
            "facts": list(self.facts),
            "limitations": list(self.limitations),
            "resultRefs": [dict(item) for item in self.result_refs],
            "allowedActionIds": list(self.allowed_action_ids),
            "alreadyExecutedActionIds": list(self.already_executed_action_ids),
            "alreadyExecutedGoalIds": list(self.already_executed_goal_ids),
            "profileKey": self.profile_key,
            "truncated": self.truncated,
        }


@dataclass(frozen=True)
class StructuredRecommendationCandidate:
    """Shape alvo do plano 06 — validação de output (sem auto-execução)."""

    label: str
    query: str
    reason: str
    action_id: str | None
    source: str
    confidence: float | None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "label": self.label,
            "query": self.query,
            "reason": self.reason,
            "source": self.source,
        }
        if self.action_id:
            payload["actionId"] = self.action_id
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        return payload


class ChatRecommendationGroundingService:
    """Monta grounding bounded a partir do turno; policy de caps no content JSON."""

    @classmethod
    def build(
        cls,
        *,
        user_message: str | None = None,
        user_goals: list[Any] | tuple[Any, ...] | None = None,
        facts: list[Any] | tuple[Any, ...] | None = None,
        limitations: list[Any] | tuple[Any, ...] | None = None,
        result_refs: list[Any] | tuple[Any, ...] | None = None,
        allowed_action_ids: list[Any] | set[Any] | tuple[Any, ...] | None = None,
        already_executed_action_ids: list[Any] | set[Any] | tuple[Any, ...] | None = None,
        already_executed_goal_ids: list[Any] | set[Any] | tuple[Any, ...] | None = None,
        profile_key: str | None = None,
        metadata: dict[str, Any] | None = None,
        data_answer: dict[str, Any] | None = None,
        execution_results: list[dict[str, Any]] | None = None,
        raw_data: Any = None,
    ) -> RecommendationGroundingContext:
        # raw_data é aceito só para garantir que NÃO vaza no contexto (contrato).
        _ = raw_data

        meta = metadata if isinstance(metadata, dict) else {}
        answer = data_answer if isinstance(data_answer, dict) else {}

        caps = cls._caps()
        truncated = False

        message, msg_trunc = cls._clip_text(
            user_message if user_message is not None else meta.get("userMessage"),
            caps["maxMessageChars"],
        )
        truncated = truncated or msg_trunc

        goals_src = user_goals
        if goals_src is None:
            goals_src = meta.get("userGoals") or meta.get("goalIds") or []
        goals, goals_trunc = cls._clip_str_list(goals_src, caps["maxUserGoals"])
        truncated = truncated or goals_trunc

        facts_src = facts
        if facts_src is None:
            facts_src = answer.get("facts") or meta.get("facts") or []
        facts_out, facts_trunc = cls._clip_str_list(
            facts_src,
            caps["maxFacts"],
            max_item_chars=caps["maxFactChars"],
        )
        truncated = truncated or facts_trunc

        lim_src = limitations
        if lim_src is None:
            lim_src = answer.get("limitations") or meta.get("limitations") or []
        lims, lims_trunc = cls._clip_str_list(
            lim_src,
            caps["maxLimitations"],
            max_item_chars=caps["maxLimitationChars"],
        )
        truncated = truncated or lims_trunc

        refs_src = result_refs
        if refs_src is None:
            refs_src = cls._collect_result_refs(meta, execution_results)
        refs, refs_trunc = cls._clip_result_refs(refs_src, caps["maxResultRefs"])
        truncated = truncated or refs_trunc

        allowed_src = allowed_action_ids
        if allowed_src is None:
            allowed_src = (
                meta.get("allowedActionIds")
                or meta.get("allowedActions")
                or answer.get("allowedActionIds")
            )
        allowed, allowed_trunc = cls._clip_id_list(allowed_src, caps["maxAllowedActions"])
        truncated = truncated or allowed_trunc

        exec_actions_src = already_executed_action_ids
        if exec_actions_src is None:
            exec_actions_src = cls._collect_executed_action_ids(meta, execution_results)
        exec_actions, exec_a_trunc = cls._clip_id_list(
            exec_actions_src, caps["maxAlreadyExecuted"]
        )
        truncated = truncated or exec_a_trunc

        exec_goals_src = already_executed_goal_ids
        if exec_goals_src is None:
            exec_goals_src = cls._collect_executed_goal_ids(meta)
        exec_goals, exec_g_trunc = cls._clip_id_list(
            exec_goals_src, caps["maxAlreadyExecuted"]
        )
        truncated = truncated or exec_g_trunc

        profile = str(
            profile_key
            or answer.get("profileKey")
            or meta.get("presentationProfileKey")
            or (meta.get("stackPresentationPlan") or {}).get("presentationProfileKey")
            or ""
        ).strip()

        return RecommendationGroundingContext(
            user_message=message,
            user_goals=goals,
            facts=facts_out,
            limitations=lims,
            result_refs=refs,
            allowed_action_ids=allowed,
            already_executed_action_ids=exec_actions,
            already_executed_goal_ids=exec_goals,
            profile_key=profile,
            truncated=truncated,
        )

    @classmethod
    def parse_candidate(cls, item: Any) -> StructuredRecommendationCandidate | None:
        if not isinstance(item, dict):
            return None
        label = str(item.get("label") or item.get("text") or "").strip()
        if "query" not in item and "intent" not in item:
            return None
        query = str(item.get("query") or item.get("intent") or "").strip()
        if not label or not query:
            return None
        source = str(item.get("source") or "").strip() or "deterministic"
        if source not in _RECOMMENDATION_SOURCES:
            source = "deterministic"
        action_id = str(item.get("actionId") or item.get("action_id") or "").strip() or None
        confidence_raw = item.get("confidence")
        confidence: float | None
        try:
            confidence = float(confidence_raw) if confidence_raw is not None else None
        except (TypeError, ValueError):
            confidence = None
        if confidence is not None:
            confidence = max(0.0, min(1.0, confidence))
        return StructuredRecommendationCandidate(
            label=label,
            query=query,
            reason=str(item.get("reason") or "").strip(),
            action_id=action_id,
            source=source,
            confidence=confidence,
        )

    @classmethod
    def filter_candidates_against_grounding(
        cls,
        items: list[Any] | None,
        grounding: RecommendationGroundingContext,
    ) -> list[dict[str, Any]]:
        """Allowlist actionId + dropa actionId já executado; preserva source/confidence."""

        allowed = {token for token in grounding.allowed_action_ids if token}
        enforce = bool(allowed)
        executed = {
            token.casefold()
            for token in grounding.already_executed_action_ids
            if token
        }
        output: list[dict[str, Any]] = []
        for item in items or []:
            candidate = cls.parse_candidate(item)
            if candidate is None:
                continue
            if candidate.action_id and enforce and candidate.action_id not in allowed:
                continue
            if candidate.action_id and candidate.action_id.casefold() in executed:
                continue
            output.append(candidate.as_dict())
        return output

    @classmethod
    def _caps(cls) -> dict[str, int]:
        return ChatHumanizedDataResponseContentService.recommendation_grounding_caps()

    @classmethod
    def _clip_text(cls, value: Any, max_chars: int) -> tuple[str, bool]:
        text = str(value or "").strip()
        if max_chars <= 0:
            return "", bool(text)
        if len(text) <= max_chars:
            return text, False
        return text[:max_chars].rstrip(), True

    @classmethod
    def _clip_str_list(
        cls,
        values: Any,
        max_items: int,
        *,
        max_item_chars: int | None = None,
    ) -> tuple[tuple[str, ...], bool]:
        truncated = False
        items: list[str] = []
        if not isinstance(values, (list, tuple, set)):
            return (), False
        for raw in values:
            text = str(raw or "").strip()
            if not text:
                continue
            if max_item_chars is not None and len(text) > max_item_chars:
                text = text[:max_item_chars].rstrip()
                truncated = True
            items.append(text)
        if max_items >= 0 and len(items) > max_items:
            truncated = True
            items = items[:max_items]
        return tuple(items), truncated

    @classmethod
    def _clip_id_list(cls, values: Any, max_items: int) -> tuple[tuple[str, ...], bool]:
        truncated = False
        items: list[str] = []
        seen: set[str] = set()
        if values is None:
            return (), False
        iterable = values if isinstance(values, (list, tuple, set)) else []
        for raw in iterable:
            token = str(raw or "").strip()
            if not token or token in seen:
                continue
            seen.add(token)
            items.append(token)
        if max_items >= 0 and len(items) > max_items:
            truncated = True
            items = items[:max_items]
        return tuple(items), truncated

    @classmethod
    def _clip_result_refs(
        cls, values: Any, max_items: int
    ) -> tuple[tuple[dict[str, str], ...], bool]:
        truncated = False
        refs: list[dict[str, str]] = []
        if not isinstance(values, (list, tuple)):
            return (), False
        for raw in values:
            if not isinstance(raw, dict):
                continue
            action_id = str(raw.get("actionId") or raw.get("action_id") or "").strip()
            ref_id = str(raw.get("resultRef") or raw.get("ref") or "").strip()
            path = str(raw.get("path") or "").strip()
            status = str(raw.get("status") or raw.get("ok") or "").strip()
            entry: dict[str, str] = {}
            if action_id:
                entry["actionId"] = action_id
            if ref_id:
                entry["resultRef"] = ref_id
            if path:
                # path só como referência curta — não authority de routing
                entry["path"] = path[:120]
            if status:
                entry["status"] = status[:40]
            if not entry:
                continue
            # Nunca copiar data/payload
            refs.append(entry)
        if max_items >= 0 and len(refs) > max_items:
            truncated = True
            refs = refs[:max_items]
        return tuple(refs), truncated

    @classmethod
    def _collect_result_refs(
        cls,
        metadata: dict[str, Any],
        execution_results: list[dict[str, Any]] | None,
    ) -> list[dict[str, str]]:
        refs: list[dict[str, str]] = []
        for raw in execution_results or []:
            if not isinstance(raw, dict):
                continue
            action_id = str(raw.get("actionId") or "").strip()
            ok = raw.get("ok")
            status = "ok" if ok is True else ("failed" if ok is False else str(ok or ""))
            meta = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
            path = str(meta.get("path") or raw.get("path") or "").strip()
            entry: dict[str, str] = {}
            if action_id:
                entry["actionId"] = action_id
            if path:
                entry["path"] = path[:120]
            if status:
                entry["status"] = status
            if entry:
                refs.append(entry)
        existing = metadata.get("resultRefs")
        if isinstance(existing, list):
            for item in existing:
                if isinstance(item, dict):
                    refs.append(
                        {
                            k: str(v)
                            for k, v in item.items()
                            if k in {"actionId", "resultRef", "path", "status"} and v
                        }
                    )
        return refs

    @classmethod
    def _collect_executed_action_ids(
        cls,
        metadata: dict[str, Any],
        execution_results: list[dict[str, Any]] | None,
    ) -> list[str]:
        ids: list[str] = []
        for key in ("executedActionIds", "alreadyExecutedActionIds"):
            raw = metadata.get(key)
            if isinstance(raw, (list, tuple, set)):
                ids.extend(str(x).strip() for x in raw if str(x).strip())
        for raw in execution_results or []:
            if not isinstance(raw, dict):
                continue
            if raw.get("ok") is False:
                continue
            action_id = str(raw.get("actionId") or "").strip()
            if action_id:
                ids.append(action_id)
        return ids

    @classmethod
    def _collect_executed_goal_ids(cls, metadata: dict[str, Any]) -> list[str]:
        coverage = metadata.get("goalCoverage")
        if not isinstance(coverage, dict):
            return []
        fulfilled = coverage.get("results") or []
        ids: list[str] = []
        if isinstance(fulfilled, list):
            for item in fulfilled:
                if not isinstance(item, dict):
                    continue
                if str(item.get("status") or "").strip().lower() != "fulfilled":
                    continue
                goal_id = str(item.get("goalId") or "").strip()
                if goal_id:
                    ids.append(goal_id)
        return ids
