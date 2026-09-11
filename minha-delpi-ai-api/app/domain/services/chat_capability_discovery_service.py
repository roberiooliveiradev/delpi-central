"""Discovery top-k de capabilities — Action Catalog (actions) + registry (não-OpenAPI)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_capability_registry_service import (
    ChatCapabilityRegistryService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


@dataclass(frozen=True)
class CapabilityDiscoveryResult:
    candidates: tuple[dict[str, Any], ...]
    discard_reasons: tuple[dict[str, str], ...]

    def as_admin_debug(self) -> dict[str, Any]:
        return {
            "capabilityCandidates": [dict(item) for item in self.candidates],
            "capabilityDiscardReasons": [dict(item) for item in self.discard_reasons],
        }


class ChatCapabilityDiscoveryService:
    """E4.S5: type=action vem do Action Catalog; rag/web/skill/transform do registry."""

    @classmethod
    def capabilities_from_actions(
        cls,
        action_catalog: list[dict[str, Any]] | None,
        *,
        allowed_action_ids: set[str] | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        allowed: set[str] | None = None
        if allowed_action_ids is not None:
            allowed = {str(item).strip() for item in allowed_action_ids if str(item).strip()}

        synthesized: list[dict[str, Any]] = []
        for action in action_catalog or []:
            if not isinstance(action, dict):
                continue
            action_id = str(action.get("actionId") or action.get("action_id") or "").strip()
            if not action_id:
                continue
            if allowed is not None and action_id not in allowed:
                continue
            if action.get("enabled") is False:
                continue

            metadata = action.get("delpi_metadata") or action.get("delpiMetadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}
            when_to_use = metadata.get("whenToUse") or action.get("whenToUse") or []
            if isinstance(when_to_use, str):
                when_to_use = [when_to_use]
            when_not = metadata.get("whenNotToUse") or action.get("whenNotToUse") or []
            if isinstance(when_not, str):
                when_not = [when_not]

            summary = str(
                action.get("summary") or action.get("description") or action_id
            ).strip()
            ux = metadata.get("uxCapability") if isinstance(metadata.get("uxCapability"), dict) else {}
            category = str(ux.get("category") or "").strip()

            contract = cls._capability_contract_from_action(action)

            synthesized.append(
                {
                    "capabilityId": f"action:{action_id}",
                    "type": "action",
                    "actionId": action_id,
                    "descriptionForModel": summary
                    + (f" ({category})" if category else ""),
                    "whenToUse": [str(item).strip() for item in when_to_use if str(item).strip()],
                    "whenNot": [str(item).strip() for item in when_not if str(item).strip()],
                    "readWrite": contract["readWrite"],
                    "parallelSafe": contract["parallelSafe"],
                    "risk": contract["risk"],
                    "requiresConfirmation": contract["requiresConfirmation"],
                    "source": "action_catalog",
                    "contractSource": "method+sensitivity",
                }
            )
        return synthesized

    @classmethod
    def _capability_contract_from_action(cls, action: dict[str, Any]) -> dict[str, Any]:
        """E11.S7 — derive capability metadata from OpenAPI method/sensitivity.

        Reuses ChatWriteConfirmationService (same authority as execution/parallel).
        """
        from app.domain.services.chat_write_confirmation_service import (
            ChatWriteConfirmationService,
        )

        sensitivity = str(action.get("sensitivity") or "").strip().lower()
        method = str(action.get("method") or "").strip().upper()

        if sensitivity in {"admin", "destructive"}:
            risk = "high"
            read_write = "write"
        elif sensitivity == "write" or method in {"POST", "PUT", "PATCH", "DELETE"}:
            risk = "medium"
            read_write = "write"
        else:
            risk = "low"
            read_write = "read"

        explicit = action.get("requiresConfirmation")
        if explicit is None:
            requires_confirmation = ChatWriteConfirmationService.action_requires_confirmation(
                action
            )
        else:
            requires_confirmation = bool(explicit)

        return {
            "readWrite": read_write,
            "parallelSafe": ChatWriteConfirmationService.is_parallel_safe_read(action),
            "risk": risk,
            "requiresConfirmation": requires_confirmation,
        }

    @classmethod
    def discover(
        cls,
        message: str,
        *,
        top_k: int | None = None,
        allowed_types: set[str] | None = None,
        action_catalog: list[dict[str, Any]] | None = None,
        allowed_action_ids: set[str] | list[str] | None = None,
    ) -> CapabilityDiscoveryResult:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or (
            message or ""
        ).lower()
        limit = top_k or ChatCapabilityRegistryService.limit_int("discoveryTopK", 8)
        scored: list[tuple[float, dict[str, Any]]] = []
        discards: list[dict[str, str]] = []

        pool: list[dict[str, Any]] = []
        # Non-OpenAPI from registry (skip legacy type=action mini-catalog).
        for capability in ChatCapabilityRegistryService.all_capabilities():
            cap_type = str(capability.get("type") or "").strip().lower()
            if cap_type == "action":
                continue
            pool.append(capability)

        pool.extend(
            cls.capabilities_from_actions(
                action_catalog,
                allowed_action_ids=allowed_action_ids,
            )
        )

        for capability in pool:
            cap_type = str(capability.get("type") or "").strip().lower()
            if allowed_types and cap_type not in allowed_types:
                discards.append(
                    {
                        "capabilityId": str(capability.get("capabilityId") or ""),
                        "reason": ChatCapabilityRegistryService.discard_reason(
                            "typeFiltered",
                            "type_filtered",
                        ),
                    }
                )
                continue

            score = cls._score(normalized, capability)
            if score <= 0:
                discards.append(
                    {
                        "capabilityId": str(capability.get("capabilityId") or ""),
                        "reason": ChatCapabilityRegistryService.discard_reason(
                            "lowRelevance",
                            "low_relevance",
                        ),
                    }
                )
                continue

            decimals = ChatCapabilityRegistryService.scoring_int("scoreDecimals", 3)
            scored.append((score, {**capability, "score": round(score, decimals)}))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = tuple(item for _, item in scored[: max(1, limit)])
        return CapabilityDiscoveryResult(candidates=selected, discard_reasons=tuple(discards))

    @classmethod
    def _score(cls, normalized: str, capability: dict[str, Any]) -> float:
        hit_weight = ChatCapabilityRegistryService.scoring_float("whenToUseWeight", 1.0)
        penalty = ChatCapabilityRegistryService.scoring_float("whenNotPenalty", 1.5)
        word_weight = ChatCapabilityRegistryService.scoring_float(
            "descriptionWordWeight",
            0.15,
        )
        min_word_chars = ChatCapabilityRegistryService.scoring_int(
            "minDescriptionWordChars",
            4,
        )
        score = 0.0

        for term in capability.get("whenToUse") or []:
            token = str(term or "").strip().lower()
            if token and token in normalized:
                score += hit_weight

        for term in capability.get("whenNot") or []:
            token = str(term or "").strip().lower()
            if token and token in normalized:
                score -= penalty

        description = str(capability.get("descriptionForModel") or "").lower()

        for word in normalized.split():
            if len(word) >= min_word_chars and word in description:
                score += word_weight

        return score
