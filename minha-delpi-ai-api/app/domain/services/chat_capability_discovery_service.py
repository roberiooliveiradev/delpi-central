"""Discovery top-k de capabilities (E4.S2) — sem free-pick de operationId."""

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
    @classmethod
    def discover(
        cls,
        message: str,
        *,
        top_k: int | None = None,
        allowed_types: set[str] | None = None,
    ) -> CapabilityDiscoveryResult:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or (
            message or ""
        ).lower()
        limit = top_k or ChatCapabilityRegistryService.limit_int("discoveryTopK", 8)
        scored: list[tuple[float, dict[str, Any]]] = []
        discards: list[dict[str, str]] = []

        for capability in ChatCapabilityRegistryService.all_capabilities():
            cap_type = str(capability.get("type") or "").strip().lower()
            if allowed_types and cap_type not in allowed_types:
                discards.append(
                    {
                        "capabilityId": str(capability.get("capabilityId") or ""),
                        "reason": "type_filtered",
                    }
                )
                continue

            score = cls._score(normalized, capability)
            if score <= 0:
                discards.append(
                    {
                        "capabilityId": str(capability.get("capabilityId") or ""),
                        "reason": "low_relevance",
                    }
                )
                continue

            scored.append((score, {**capability, "score": round(score, 3)}))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = tuple(item for _, item in scored[: max(1, limit)])
        return CapabilityDiscoveryResult(candidates=selected, discard_reasons=tuple(discards))

    @classmethod
    def _score(cls, normalized: str, capability: dict[str, Any]) -> float:
        score = 0.0
        for term in capability.get("whenToUse") or []:
            token = str(term or "").strip().lower()
            if token and token in normalized:
                score += 1.0
        for term in capability.get("whenNot") or []:
            token = str(term or "").strip().lower()
            if token and token in normalized:
                score -= 1.5
        description = str(capability.get("descriptionForModel") or "").lower()
        for word in normalized.split():
            if len(word) >= 4 and word in description:
                score += 0.15
        return score
