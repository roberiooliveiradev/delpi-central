"""Priorização declarativa de candidatos OpenAPI — siblingDisambiguation JSON."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


class ExternalActionCandidatePrioritizationService:
    """Reordena/filtra candidatos por regras declarativas em actionSelection.siblingDisambiguation."""

    @classmethod
    def apply(
        cls,
        message: str,
        candidates: list[dict],
        *,
        supplies_otd: bool = False,
    ) -> list[dict]:
        ordered = list(candidates)
        if not ordered:
            return ordered

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        flags = {"supplies_otd": bool(supplies_otd)}
        rules = ExternalActionResponseContentService.object_list(
            "actionSelection",
            "siblingDisambiguation",
        )

        for rule in rules:
            required_flag = str(rule.get("requiresFlag") or "").strip()
            if required_flag and not flags.get(required_flag):
                continue

            mode = str(rule.get("mode") or "").strip()
            if mode == "domainPathChains":
                ordered = cls._apply_domain_path_chains(normalized, ordered, rule)
            elif mode == "filterPreferredSort":
                ordered = cls._apply_filter_preferred_sort(normalized, ordered, rule)
            elif mode == "preferMatch":
                ordered = cls._apply_prefer_match(normalized, ordered, rule)
            elif mode == "preferBranches":
                ordered = cls._apply_prefer_branches(normalized, ordered, rule)

        return ordered

    @classmethod
    def _terms_from_key(cls, key: str) -> list[str]:
        token = str(key or "").strip()
        if not token:
            return []
        parts = tuple(part for part in token.split(".") if part)
        return ExternalActionResponseContentService.list("actionSelection", *parts)

    @classmethod
    def _scalar_from_key(cls, key: str, default: str = "") -> str:
        token = str(key or "").strip()
        if not token:
            return default
        parts = tuple(part for part in token.split(".") if part)
        return ExternalActionResponseContentService.get(
            "actionSelection",
            *parts,
            default=default,
        )

    @classmethod
    def _message_has_any(cls, normalized: str, term_keys: list[Any]) -> bool:
        for key in term_keys:
            terms = cls._terms_from_key(str(key))
            if any(term in normalized for term in terms):
                return True
        return False

    @classmethod
    def _message_has_all_groups(cls, normalized: str, term_keys: list[Any]) -> bool:
        for key in term_keys:
            terms = cls._terms_from_key(str(key))
            if not any(term in normalized for term in terms):
                return False
        return True

    @classmethod
    def _rule_matches_message(cls, normalized: str, rule: dict) -> bool:
        block_keys = rule.get("blockAnyOfTermKeys") or []
        if isinstance(block_keys, list) and cls._message_has_any(normalized, block_keys):
            return False

        any_keys = rule.get("anyOfTermKeys") or []
        if isinstance(any_keys, list) and any_keys:
            if not cls._message_has_any(normalized, any_keys):
                return False

        all_keys = rule.get("allOfAnyTermKeys") or []
        if isinstance(all_keys, list) and all_keys:
            if not cls._message_has_all_groups(normalized, all_keys):
                return False

        also_keys = rule.get("alsoAnyOfTermKeys") or []
        if isinstance(also_keys, list) and also_keys:
            if not cls._message_has_any(normalized, also_keys):
                return False

        gate_keys = rule.get("gateAnyOfTermKeys") or []
        if isinstance(gate_keys, list) and gate_keys:
            if not cls._message_has_any(normalized, gate_keys):
                return False

        return True

    @classmethod
    def _path_operation_matches(
        cls,
        action: dict,
        *,
        path_value: str,
        operation_value: str,
        path_match: str,
    ) -> bool:
        path = str(action.get("path") or "").lower()
        operation_id = str(action.get("operationId") or "").lower()
        path_token = str(path_value or "").lower().strip()
        op_token = str(operation_value or "").lower().strip()

        if op_token and op_token in operation_id:
            return True

        if not path_token:
            return False

        if path_match == "contains":
            return path_token.rstrip("/") in path.rstrip("/")

        return path.rstrip("/") == path_token.rstrip("/")

    @classmethod
    def _matched_actions(
        cls,
        candidates: list[dict],
        selector: dict,
    ) -> list[dict]:
        path_match = str(selector.get("pathMatch") or "equals").strip() or "equals"
        path_value = ""
        if selector.get("pathEqualsFromKey"):
            path_value = cls._scalar_from_key(str(selector["pathEqualsFromKey"]))
        elif selector.get("pathContainsFromKey"):
            path_value = cls._scalar_from_key(str(selector["pathContainsFromKey"]))
        elif selector.get("pathContains"):
            path_value = str(selector.get("pathContains") or "")
        elif selector.get("pathEquals"):
            path_value = str(selector.get("pathEquals") or "")

        operation_value = ""
        if selector.get("operationIdContainsFromKey"):
            operation_value = cls._scalar_from_key(
                str(selector["operationIdContainsFromKey"])
            )
        elif selector.get("operationIdContains"):
            operation_value = str(selector.get("operationIdContains") or "")

        return [
            action
            for action in candidates
            if cls._path_operation_matches(
                action,
                path_value=path_value,
                operation_value=operation_value,
                path_match=path_match,
            )
        ]

    @classmethod
    def _prefer_actions(
        cls,
        candidates: list[dict],
        selector: dict,
    ) -> list[dict]:
        return cls._matched_actions(candidates, selector) or candidates

    @classmethod
    def _apply_domain_path_chains(
        cls,
        normalized: str,
        candidates: list[dict],
        rule: dict,
    ) -> list[dict]:
        chains = rule.get("chains") or []
        if not isinstance(chains, list):
            return candidates

        for chain in chains:
            if not isinstance(chain, dict):
                continue
            any_keys = chain.get("anyOfTermKeys") or []
            if not isinstance(any_keys, list) or not cls._message_has_any(
                normalized, any_keys
            ):
                continue

            marker = ""
            if chain.get("pathContainsFromKey"):
                marker = cls._scalar_from_key(str(chain["pathContainsFromKey"])).lower()
            else:
                marker = str(chain.get("pathContains") or "").lower()

            if not marker:
                continue

            filtered = [
                action
                for action in candidates
                if marker in str(action.get("path") or "").lower()
            ]
            if filtered:
                return filtered

        return candidates

    @classmethod
    def _apply_filter_preferred_sort(
        cls,
        normalized: str,
        candidates: list[dict],
        rule: dict,
    ) -> list[dict]:
        if not cls._rule_matches_message(normalized, rule):
            return candidates

        path_markers = [
            str(item).lower()
            for item in cls._terms_from_key(str(rule.get("pathMarkersKey") or ""))
            if str(item).strip()
        ]
        preferred_list = [
            str(item).lower()
            for item in cls._terms_from_key(
                str(rule.get("preferredOperationIdsKey") or "")
            )
            if str(item).strip()
        ]
        preferred_ids = set(preferred_list)
        preferred_order = {op_id: index for index, op_id in enumerate(preferred_list)}

        def _is_match(action: dict) -> bool:
            path = str(action.get("path") or "").lower()
            operation_id = str(action.get("operationId") or "").lower()
            if operation_id in preferred_ids:
                return True
            return any(
                marker in path or marker in operation_id for marker in path_markers
            )

        matched = [action for action in candidates if _is_match(action)]
        if not matched:
            return candidates

        def _sort_key(action: dict) -> tuple:
            operation_id = str(action.get("operationId") or "").lower()
            return (
                preferred_order.get(operation_id, 99),
                str(action.get("path") or ""),
            )

        return sorted(matched, key=_sort_key)

    @classmethod
    def _apply_prefer_match(
        cls,
        normalized: str,
        candidates: list[dict],
        rule: dict,
    ) -> list[dict]:
        if not cls._rule_matches_message(normalized, rule):
            return candidates
        return cls._prefer_actions(candidates, rule)

    @classmethod
    def _apply_prefer_branches(
        cls,
        normalized: str,
        candidates: list[dict],
        rule: dict,
    ) -> list[dict]:
        if not cls._rule_matches_message(normalized, rule):
            return candidates

        branches = rule.get("branches") or []
        if not isinstance(branches, list):
            return candidates

        for branch in branches:
            if not isinstance(branch, dict):
                continue
            any_keys = branch.get("anyOfTermKeys") or []
            if isinstance(any_keys, list) and any_keys:
                if not cls._message_has_any(normalized, any_keys):
                    continue
                matched = cls._matched_actions(candidates, branch)
                if matched:
                    return matched
                continue

            return cls._prefer_actions(candidates, branch)

        return candidates
