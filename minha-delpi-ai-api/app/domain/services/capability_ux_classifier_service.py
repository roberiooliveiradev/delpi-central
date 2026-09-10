"""Classificação UX de capabilities no import/reindex — nunca no hot path por request."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_DEFAULT_CATEGORY = "Outras consultas"
_DEFAULT_EXAMPLES = (
    "consulta conforme rota habilitada",
    "dados operacionais autorizados",
)


@lru_cache(maxsize=1)
def _rules() -> dict[str, Any]:
    return ChatAssistantContentService.load_bundle("capability_ux_classification")


class CapabilityUxClassifierService:
    """Deriva ``uxCapability`` a partir de sinais OpenAPI/Action Catalog (sem path authority)."""

    @classmethod
    def invalidate_cache(cls) -> None:
        _rules.cache_clear()

    @classmethod
    def classify_action(cls, action: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(action, dict):
            return cls._fallback(source="empty")

        metadata = action.get("delpi_metadata") or action.get("delpiMetadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        existing = metadata.get("uxCapability") or metadata.get("ux_capability")
        if isinstance(existing, dict) and str(existing.get("category") or "").strip():
            return {
                "category": str(existing["category"]).strip(),
                "examples": cls._examples(existing.get("examples")),
                "source": str(existing.get("source") or "persisted").strip() or "persisted",
                "confidence": str(existing.get("confidence") or "high").strip() or "high",
            }

        entity = str(metadata.get("entity") or "").strip().casefold()
        shape = str(metadata.get("shape") or "").strip().casefold()
        if entity or shape:
            for rule in _rules().get("entityRules") or []:
                if not isinstance(rule, dict):
                    continue
                if entity and str(rule.get("entity") or "").casefold() != entity:
                    continue
                if shape and str(rule.get("shape") or "").casefold() != shape:
                    continue
                category = str(rule.get("category") or "").strip()
                if category:
                    return {
                        "category": category,
                        "examples": cls._examples(rule.get("examples")),
                        "source": "entity_shape",
                        "confidence": "high",
                    }

        haystack = cls._haystack(action, metadata)
        best: dict[str, Any] | None = None
        best_hits = 0
        for rule in _rules().get("keywordRules") or []:
            if not isinstance(rule, dict):
                continue
            match_any = [
                str(token).casefold().strip()
                for token in (rule.get("matchAny") or [])
                if str(token).strip()
            ]
            if not match_any:
                continue
            hits = 0
            for token in match_any:
                if len(token) < 4:
                    # avoid accidental substring hits on short tokens
                    if f" {token} " in f" {haystack} ":
                        hits += 1
                elif token in haystack:
                    hits += 1
            if hits <= 0:
                continue
            if hits > best_hits:
                best_hits = hits
                best = rule

        if best is not None:
            category = str(best.get("category") or "").strip()
            if category:
                return {
                    "category": category,
                    "examples": cls._examples(best.get("examples")),
                    "source": "keyword",
                    "confidence": "high" if best_hits >= 2 else "medium",
                }

        return cls._fallback(source="default")

    @classmethod
    def attach_to_action(cls, action: dict[str, Any]) -> dict[str, Any]:
        """Mutates and returns action with ``delpi_metadata.uxCapability`` set."""

        classified = cls.classify_action(action)
        metadata = dict(action.get("delpi_metadata") or action.get("delpiMetadata") or {})
        metadata["uxCapability"] = classified
        action["delpi_metadata"] = metadata
        if "delpiMetadata" in action:
            action["delpiMetadata"] = metadata
        return action

    @classmethod
    def _haystack(cls, action: dict[str, Any], metadata: dict[str, Any]) -> str:
        tags = action.get("tags") or []
        tag_text = " ".join(str(tag) for tag in tags if str(tag).strip())
        parts = [
            str(action.get("summary") or ""),
            str(action.get("description") or ""),
            str(metadata.get("whenToUse") or action.get("when_to_use") or ""),
            str(metadata.get("whenNotToUse") or action.get("when_not_to_use") or ""),
            tag_text,
            str(metadata.get("entity") or ""),
            str(metadata.get("shape") or ""),
            str(action.get("operation_id") or action.get("operationId") or ""),
        ]
        # Explicitly exclude path from haystack — path must not be authority.
        return " ".join(parts).casefold()

    @classmethod
    def _examples(cls, value: object) -> list[str]:
        if not isinstance(value, (list, tuple)):
            return list(_DEFAULT_EXAMPLES)
        return [str(item).strip() for item in value if str(item).strip()][:6]

    @classmethod
    def _fallback(cls, *, source: str) -> dict[str, Any]:
        data = _rules()
        category = str(data.get("defaultCategory") or _DEFAULT_CATEGORY).strip() or _DEFAULT_CATEGORY
        examples = cls._examples(data.get("defaultExamples"))
        if not examples:
            examples = list(_DEFAULT_EXAMPLES)
        return {
            "category": category,
            "examples": examples,
            "source": source,
            "confidence": "low",
        }
