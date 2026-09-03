"""Loader canônico — bundle ``follow_up_turn.json``."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "follow_up_turn"


class ChatFollowUpTurnContentService:
    @classmethod
    def decisions(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "followUpDecisions")
            if str(item).strip()
        )

    @classmethod
    def stage_for_decision(cls, decision: str) -> str | None:
        node = ChatAssistantContentService.get_node(_BUNDLE, "stages") or {}
        if not isinstance(node, dict):
            return None
        value = node.get(str(decision or "").strip())
        return str(value).strip() or None if value is not None else None

    @classmethod
    def revise_slot_triggers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "reviseSlotTriggers")
            if str(item).strip()
        )

    @classmethod
    def challenge_triggers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "challengeTriggers")
            if str(item).strip()
        )

    @classmethod
    def narrate_reference_triggers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "narrateReferenceTriggers")
            if str(item).strip()
        )

    @classmethod
    def narrate_reference_whole_messages(cls) -> frozenset[str]:
        return frozenset(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(
                _BUNDLE,
                "narrateReferenceWholeMessages",
            )
            if str(item).strip()
        )

    @classmethod
    def message_matches_narrate_reference(cls, message: str) -> bool:
        """Referência explícita ao resultado — token com fronteira de palavra, não substring."""
        haystack = str(message or "").strip().lower()

        if not haystack:
            return False

        whole = cls._normalize_whole_message(haystack)

        if whole in cls.narrate_reference_whole_messages():
            return True

        return any(
            cls.trigger_matches_with_word_boundary(haystack, trigger)
            for trigger in cls.narrate_reference_triggers()
        )

    @classmethod
    def _normalize_whole_message(cls, message: str) -> str:
        text = str(message or "").strip().lower()
        text = re.sub(r"[?!.,;:…]+$", "", text).strip()
        return text

    @classmethod
    def _is_word_char(cls, char: str) -> bool:
        if not char:
            return False
        return bool(re.match(r"[0-9A-Za-zÀ-ÿ_]", char))

    @classmethod
    def trigger_matches_with_word_boundary(cls, haystack: str, trigger: str) -> bool:
        needle = str(trigger or "").strip().lower()
        text = str(haystack or "").strip().lower()

        if not needle or not text:
            return False

        start = 0

        while True:
            idx = text.find(needle, start)

            if idx < 0:
                return False

            before_ok = idx == 0 or not cls._is_word_char(text[idx - 1])
            end = idx + len(needle)
            after_ok = end >= len(text) or not cls._is_word_char(text[end])

            if before_ok and after_ok:
                return True

            start = idx + 1

    @classmethod
    @lru_cache(maxsize=1)
    def branch_typos(cls) -> dict[str, str]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "branchTypos") or {}
        if not isinstance(node, dict):
            return {}
        return {
            str(src).strip().lower(): str(dst).strip().lower()
            for src, dst in node.items()
            if str(src).strip() and str(dst).strip()
        }

    @classmethod
    @lru_cache(maxsize=16)
    def compile_pattern(cls, key: str) -> re.Pattern[str]:
        source = ChatAssistantContentService.get(_BUNDLE, "patterns", key, default="")
        if not str(source or "").strip():
            raise KeyError(f"{_BUNDLE}.patterns.{key} ausente")
        return re.compile(str(source), re.IGNORECASE)

    @classmethod
    def normalize_branch_typos(cls, text: str) -> str:
        """Substitui typos de filial sem alterar o restante da mensagem."""
        raw = str(text or "")
        if not raw:
            return raw
        normalized = raw
        for typo, canonical in cls.branch_typos().items():
            if typo == canonical:
                continue
            normalized = re.sub(
                rf"\b{re.escape(typo)}\b",
                canonical,
                normalized,
                flags=re.IGNORECASE,
            )
        return normalized

    @classmethod
    def extract_branch_code(cls, text: str) -> str | None:
        codes = cls.extract_branch_codes(text)
        return codes[0] if codes else None

    @classmethod
    def extract_branch_codes(cls, text: str) -> list[str]:
        candidate = cls.normalize_branch_typos(text)
        pattern = cls.compile_pattern("branchWithCode")
        found: list[str] = []
        for match in pattern.finditer(candidate):
            code = str(match.group(1)).zfill(2)
            if code not in found:
                found.append(code)
        if len(found) >= 2:
            return found
        # «01 vs 02» / «01 e 02» sem palavra filial
        for match in re.finditer(r"\b(\d{1,2})\b", candidate):
            code = str(match.group(1)).zfill(2)
            if code not in found and code in {"01", "02", "03", "04"}:
                found.append(code)
        return found

    @classmethod
    def has_branch_trigger_without_code(cls, text: str) -> bool:
        candidate = cls.normalize_branch_typos(text)
        if cls.extract_branch_code(candidate):
            return False
        return bool(cls.compile_pattern("branchTriggerWithoutCode").search(candidate))

    @classmethod
    def topic_switch_markers(cls) -> dict[str, tuple[str, ...]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "topicSwitchMarkers") or {}
        if not isinstance(node, dict):
            return {}
        resolved: dict[str, tuple[str, ...]] = {}
        for domain, markers in node.items():
            if not isinstance(markers, list):
                continue
            cleaned = tuple(str(item).strip().lower() for item in markers if str(item).strip())
            if cleaned:
                resolved[str(domain).strip()] = cleaned
        return resolved

    @classmethod
    def topic_switch_exclude_markers(cls) -> dict[str, tuple[str, ...]]:
        node = (
            ChatAssistantContentService.get_node(
                _BUNDLE, "topicSwitchExcludeWhenLastActionMarkers"
            )
            or {}
        )
        if not isinstance(node, dict):
            return {}
        resolved: dict[str, tuple[str, ...]] = {}
        for domain, markers in node.items():
            if not isinstance(markers, list):
                continue
            cleaned = tuple(str(item).strip().lower() for item in markers if str(item).strip())
            if cleaned:
                resolved[str(domain).strip()] = cleaned
        return resolved

    @classmethod
    def api_route_domain_affinity(cls) -> dict[str, tuple[str, ...]]:
        """Mapa follow-up domain → apiRouteDomain(s) compatíveis com revise grounded."""
        node = ChatAssistantContentService.get_node(_BUNDLE, "apiRouteDomainAffinity") or {}
        if not isinstance(node, dict):
            return {}
        resolved: dict[str, tuple[str, ...]] = {}
        for domain, values in node.items():
            if not isinstance(values, list):
                continue
            cleaned = tuple(str(item).strip().lower() for item in values if str(item).strip())
            if cleaned:
                resolved[str(domain).strip().lower()] = cleaned
        return resolved

    @classmethod
    def branch_compare_markers(cls) -> tuple[str, ...]:
        return tuple(
            str(item)
            for item in ChatAssistantContentService.list(_BUNDLE, "branchCompareMarkers")
            if str(item or "").strip()
        )

    @classmethod
    def message_topic_domains(cls, normalized: str) -> tuple[str, ...]:
        """Domínios de topicSwitchMarkers presentes na mensagem normalizada."""
        text = f" {str(normalized or '').strip().lower()} "
        if not text.strip():
            return ()
        found: list[str] = []
        for domain, markers in cls.topic_switch_markers().items():
            if any(f" {marker} " in text or marker in text for marker in markers):
                found.append(str(domain).strip().lower())
        return tuple(found)

    @classmethod
    def last_action_route_domain(cls, last_action: dict[str, Any] | None) -> str:
        if not isinstance(last_action, dict):
            return ""
        explicit = str(
            last_action.get("apiRouteDomain") or last_action.get("api_route_domain") or ""
        ).strip().lower()
        if explicit:
            return explicit
        path = str(last_action.get("path") or "").strip()
        if not path:
            return ""
        from app.domain.services.chat_operational_api_domain_service import (
            ChatOperationalApiDomainService,
        )

        return str(ChatOperationalApiDomainService.classify_path(path) or "").strip().lower()

    @classmethod
    def domains_affine_to_last_action(
        cls,
        message_domains: tuple[str, ...] | list[str],
        last_action: dict[str, Any] | None,
    ) -> bool:
        """True se não há domínio na mensagem ou algum domínio é afim ao lastAction."""
        domains = [str(item).strip().lower() for item in (message_domains or []) if str(item).strip()]
        if not domains:
            return True
        route_domain = cls.last_action_route_domain(last_action)
        if not route_domain:
            return False
        affinity = cls.api_route_domain_affinity()
        for domain in domains:
            allowed = affinity.get(domain) or ()
            if route_domain in allowed:
                return True
            excludes = cls.topic_switch_exclude_markers().get(domain) or ()
            action_blob = " ".join(
                str(last_action.get(key) or "")
                for key in ("path", "name", "operationId", "operation_id", "apiRouteDomain")
            ).lower() if isinstance(last_action, dict) else ""
            if any(token in action_blob for token in excludes):
                return True
        return False

    @classmethod
    def clarify_slot_prompt(cls, slot: str) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE, "clarifySlotPrompts", slot, default=""
            )
            or ""
        ).strip()

    @classmethod
    def challenge_faithfulness_instruction(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE, "challengeFaithfulness", "instruction", default=""
            )
            or ""
        ).strip()

    @classmethod
    def challenge_suggestions(cls) -> list[dict[str, str]]:
        node = ChatAssistantContentService.get_node(
            _BUNDLE, "challengeFaithfulness", "suggestions"
        )
        suggestions: list[dict[str, str]] = []
        if not isinstance(node, list):
            return suggestions
        for item in node:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()
            if label and query:
                suggestions.append({"label": label, "query": query})
        return suggestions

    @classmethod
    def revise_ack_branch(cls, branch: str) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            "reviseAck",
            "branchTemplate",
            default="Consulta filtrada pela filial {branch}.",
            branch=str(branch or "").strip(),
        )

    @classmethod
    def revise_ack_period(
        cls,
        *,
        start: str,
        end: str,
        changed: bool = False,
    ) -> str:
        key = "periodChangedTemplate" if changed else "periodKeptTemplate"
        default = (
            "Período ajustado: {start} a {end}."
            if changed
            else "Período mantido: {start} a {end}."
        )
        # Compat: periodTemplate legado
        text = ChatAssistantContentService.format(
            _BUNDLE,
            "reviseAck",
            key,
            default="",
            start=str(start or "").strip(),
            end=str(end or "").strip(),
        )
        if text:
            return text
        return ChatAssistantContentService.format(
            _BUNDLE,
            "reviseAck",
            "periodTemplate",
            default=default,
            start=str(start or "").strip(),
            end=str(end or "").strip(),
        )

    @classmethod
    def period_compare_format(cls, key: str, **values: Any) -> str:
        return str(
            ChatAssistantContentService.format(
                _BUNDLE,
                "periodCompare",
                key,
                default="",
                **values,
            )
            or ""
        ).strip()

    @classmethod
    def period_compare_next_steps(cls) -> list[dict[str, str]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "periodCompare", "nextSteps")
        out: list[dict[str, str]] = []
        if not isinstance(node, list):
            return out
        for item in node:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or "").strip()
            query = str(item.get("query") or "").strip()
            if label and query:
                out.append({"label": label, "query": query})
        return out

    @classmethod
    def period_compare_preferred_metric_keys(cls) -> tuple[str, ...]:
        raw = ChatAssistantContentService.list(
            _BUNDLE,
            "periodCompare",
            "preferredMetricKeys",
        )
        keys = tuple(
            str(item).strip().lower()
            for item in raw
            if str(item).strip()
        )
        return keys or ("rol", "value", "total", "gross_revenue")

    @classmethod
    def period_compare_prior_label(cls, period_kind: str | None) -> str:
        kind = str(period_kind or "").strip()
        mapping = ChatAssistantContentService.get_mapping(
            _BUNDLE,
            "periodCompare",
            "priorPeriodLabelByKind",
        )
        if kind and isinstance(mapping, dict) and mapping.get(kind):
            template = str(mapping.get(kind)).strip()
            if "{branch}" not in template:
                return template
        return cls.period_compare_format("priorPeriodLabel") or "período de comparação"

    @classmethod
    def period_compare_slot_label(
        cls,
        period_kind: str | None,
        role: str,
        *,
        branch: str | None = None,
    ) -> str:
        kind = str(period_kind or "").strip()
        branch_code = str(branch or "").strip()

        if kind == "branch" and branch_code:
            labeled = cls.period_compare_format(
                "branchSlotLabelTemplate",
                branch=branch_code,
            )
            if labeled:
                return labeled

        if str(role or "").strip().lower() == "baseline":
            return cls.period_compare_format("baselinePeriodLabel") or "referência"

        return cls.period_compare_prior_label(kind)

    @classmethod
    def period_compare_branch_ack(
        cls,
        *,
        baseline_branch: str,
        compare_branch: str,
        start: str,
        end: str,
    ) -> str:
        return cls.period_compare_format(
            "branchCompareAckTemplate",
            baseline_branch=str(baseline_branch or "").strip(),
            compare_branch=str(compare_branch or "").strip(),
            start=str(start or "").strip(),
            end=str(end or "").strip(),
        )

    @classmethod
    def challenge_contrast_format(cls, key: str, **values: Any) -> str:
        return str(
            ChatAssistantContentService.format(
                _BUNDLE,
                "challengeContrast",
                key,
                default="",
                **values,
            )
            or ""
        ).strip()

    @classmethod
    def continuity_modes(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "continuityModes")
            if str(item).strip()
        )

    @classmethod
    def continuity_mode_for_decision(cls, decision: str) -> str:
        node = ChatAssistantContentService.get_node(_BUNDLE, "continuityModeByDecision") or {}
        if not isinstance(node, dict):
            return "allow_discovery"
        value = node.get(str(decision or "").strip())
        return str(value).strip() or "allow_discovery"

    @classmethod
    def period_revise_triggers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(_BUNDLE, "periodReviseTriggers")
            if str(item).strip()
        )

    @classmethod
    def period_slot_kinds(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "periodSlotKinds")
            if str(item).strip()
        )

    @classmethod
    def normalize_period_typos(cls, text: str) -> str:
        haystack = str(text or "")
        if not haystack:
            return haystack
        mapping = ChatAssistantContentService.get_mapping(
            _BUNDLE,
            "periodTypoReplacements",
        )
        if not isinstance(mapping, dict) or not mapping:
            return haystack
        out = haystack
        # Longer keys first to avoid partial clobber.
        for wrong, right in sorted(
            ((str(k), str(v)) for k, v in mapping.items() if str(k).strip() and str(v).strip()),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            out = out.replace(wrong, right)
            out = out.replace(wrong.upper(), right)
            # Accented / title variants are uncommon; lowercase path covers normalized haystacks.
            out = out.replace(wrong.capitalize(), right)
        return out

    @classmethod
    def period_slot_kind_for_message(cls, normalized: str) -> str | None:
        haystack = cls.normalize_period_typos(str(normalized or "").strip().lower())
        if not haystack:
            return None
        groups = ChatAssistantContentService.get_node(
            _BUNDLE, "periodSlotKindByTriggerGroup"
        ) or {}
        if not isinstance(groups, dict):
            return None
        # Prefer previous_year when both could match (YoY phrases include "comparar").
        preferred_order = ("previous_year_same_range", "previous_period", "message_resolved")
        for kind in preferred_order:
            triggers = groups.get(kind) or []
            if not isinstance(triggers, list):
                continue
            if any(str(item).strip().lower() in haystack for item in triggers if str(item).strip()):
                return kind
        for kind, triggers in groups.items():
            if kind in preferred_order or not isinstance(triggers, list):
                continue
            if any(str(item).strip().lower() in haystack for item in triggers if str(item).strip()):
                return str(kind).strip() or None
        if cls.message_has_any_trigger(haystack, cls.period_revise_triggers()):
            return "previous_year_same_range"
        return None

    @classmethod
    def classifier_labels(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip()
            for item in ChatAssistantContentService.list(_BUNDLE, "classifierLabels")
            if str(item).strip()
        )

    @classmethod
    def decision_for_classifier_label(cls, label: str) -> str:
        node = ChatAssistantContentService.get_node(_BUNDLE, "labelToDecision") or {}
        if not isinstance(node, dict):
            return "new_intent"
        value = node.get(str(label or "").strip())
        return str(value).strip() or "new_intent"

    @classmethod
    def classifier_prompt_system(cls) -> str:
        return str(
            ChatAssistantContentService.get(_BUNDLE, "classifierPrompt", "system") or ""
        ).strip()

    @classmethod
    def classifier_prompt_user(cls, *, message: str, last_action_summary: str) -> str:
        labels = ", ".join(cls.classifier_labels())
        return ChatAssistantContentService.format(
            _BUNDLE,
            "classifierPrompt",
            "userTemplate",
            labels=labels,
            message=str(message or "").strip(),
            lastActionSummary=str(last_action_summary or "").strip() or "{}",
        )

    @classmethod
    def entity_families(cls) -> dict[str, tuple[str, ...]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "entityFamilies") or {}
        if not isinstance(node, dict):
            return {}
        resolved: dict[str, tuple[str, ...]] = {}
        for family, markers in node.items():
            if not isinstance(markers, list):
                continue
            cleaned = tuple(str(item).strip().lower() for item in markers if str(item).strip())
            if cleaned:
                resolved[str(family).strip()] = cleaned
        return resolved

    @classmethod
    def entity_family_for_markers(cls, *candidates: str | None) -> str | None:
        families = cls.entity_families()
        haystack = " ".join(str(item or "").strip().lower() for item in candidates if item)
        if not haystack:
            return None
        for family, markers in families.items():
            if any(marker in haystack for marker in markers):
                return family
        return None

    @classmethod
    def message_has_any_trigger(cls, message: str, triggers: tuple[str, ...]) -> bool:
        haystack = str(message or "").strip().lower()
        if not haystack:
            return False
        return any(trigger in haystack for trigger in triggers if trigger)

    @classmethod
    def invalidate_cache(cls) -> None:
        cls.branch_typos.cache_clear()
        cls.compile_pattern.cache_clear()
