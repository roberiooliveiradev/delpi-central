"""Resolução transversal de papel de identificadores (slots tipados)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_identifier_resolution_models import (
    IdentifierAmbiguity,
    IdentifierResolution,
    IdentifierResolutionSet,
    IdentifierRole,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

_BUNDLE = "product_query_intent"
_TOKEN_RE = re.compile(
    r"\b(?:[A-Za-z][A-Za-z0-9.\-/]{2,}|\d[\d.\-/]{2,}\d|\d{4,})\b"
)


class ChatOperationalIdentifierResolutionService:
    @classmethod
    def resolve(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None = None,
        memory_snapshot: dict | None = None,
        preferred_role: IdentifierRole | None = None,
    ) -> IdentifierResolutionSet:
        raw = str(message or "")
        normalized = ChatMessageNormalizationService.normalize_for_matching(raw) or raw.lower()

        if cls._matches_supplier_part_number_lookup(normalized):
            return cls._resolve_supplier_part_number(
                raw,
                normalized,
                preferred_role=preferred_role,
            )

        return cls._resolve_delpi_or_unknown(
            raw,
            normalized,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
            preferred_role=preferred_role,
        )

    @classmethod
    def _matches_supplier_part_number_lookup(cls, normalized: str) -> bool:
        from app.domain.services.operational_route_matcher_service import (
            OperationalRouteMatcherService,
        )

        return OperationalRouteMatcherService.matches_custom_predicate(
            "supplierPartNumberLookup",
            normalized,
        )

    @classmethod
    def supplier_part_number_hint_terms(cls) -> tuple[str, ...]:
        return tuple(
            ChatAssistantContentService.list(
                _BUNDLE,
                "identifierRoles",
                "supplier_part_number",
                "hintTerms",
            )
        )

    @classmethod
    def clarification_text(cls, kind: str) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "identifierRoles",
                "clarifications",
                kind,
                default="",
            )
            or ""
        ).strip()

    @classmethod
    def _resolve_supplier_part_number(
        cls,
        raw: str,
        normalized: str,
        *,
        preferred_role: IdentifierRole | None,
    ) -> IdentifierResolutionSet:
        tokens = cls._extract_candidate_tokens(raw)
        if not tokens:
            return IdentifierResolutionSet(ambiguity="unknown_role")

        items = tuple(
            IdentifierResolution(
                value=value,
                role="supplier_part_number",
                confidence=0.9,
                source="message_hint",
                span=span,
            )
            for value, span in tokens
        )
        ambiguity: IdentifierAmbiguity = (
            "multiple_same_role" if len(items) > 1 else "none"
        )
        primary = items[0] if items else None
        if preferred_role == "supplier_part_number" and items:
            primary = items[0]
        return IdentifierResolutionSet(
            items=items,
            primary=primary if ambiguity == "none" else None,
            ambiguity=ambiguity,
        )

    @classmethod
    def _resolve_delpi_or_unknown(
        cls,
        raw: str,
        normalized: str,
        *,
        previous_messages: list[Any] | None,
        memory_snapshot: dict | None,
        preferred_role: IdentifierRole | None,
    ) -> IdentifierResolutionSet:
        code = ChatProductQueryIntentService.extract_product_code(raw)
        if code:
            item = IdentifierResolution(
                value=code,
                role="delpi_product_code",
                confidence=0.85,
                source="message_hint",
            )
            return IdentifierResolutionSet(
                items=(item,),
                primary=item,
                ambiguity="none",
            )

        inherited = ChatProductQueryIntentService.resolve_product_code(
            raw,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )
        if inherited and ChatProductQueryIntentService.should_inherit_product_code(raw):
            item = IdentifierResolution(
                value=inherited,
                role="delpi_product_code",
                confidence=0.7,
                source="session_focus",
            )
            return IdentifierResolutionSet(
                items=(item,),
                primary=item,
                ambiguity="none",
            )

        tokens = cls._extract_candidate_tokens(raw)
        if not tokens:
            return IdentifierResolutionSet(ambiguity="none")

        items = tuple(
            IdentifierResolution(
                value=value,
                role="unknown",
                confidence=0.4,
                source="none",
                span=span,
            )
            for value, span in tokens
        )
        return IdentifierResolutionSet(
            items=items,
            primary=None,
            ambiguity="unknown_role",
        )

    @classmethod
    def _extract_candidate_tokens(cls, text: str) -> list[tuple[str, tuple[int, int]]]:
        found: list[tuple[str, tuple[int, int]]] = []
        seen: set[str] = set()
        for match in _TOKEN_RE.finditer(str(text or "")):
            token = str(match.group(0) or "").strip()
            if not token or not re.search(r"\d", token):
                continue
            # Prefer raw token for supplier part numbers (keep leading zeros / letters).
            normalized_digits = ChatProductQueryIntentService.normalize_product_code(token)
            value = token if re.search(r"[A-Za-z]", token) else (normalized_digits or token)
            value = str(value or "").strip()
            if len(re.sub(r"\D", "", value)) < 4 and not re.search(r"[A-Za-z].*\d|\d.*[A-Za-z]", value):
                continue
            key = value.upper()
            if key in seen:
                continue
            seen.add(key)
            found.append((value, (match.start(), match.end())))
        return found

    @classmethod
    def primary_supplier_part_number(cls, message: str) -> str | None:
        resolved = cls.resolve(message, preferred_role="supplier_part_number")
        if resolved.primary and resolved.primary.role == "supplier_part_number":
            return resolved.primary.value
        if resolved.ambiguity == "multiple_same_role":
            values = resolved.role_values("supplier_part_number")
            return values[0] if len(values) == 1 else None
        # Predicate matched but ambiguity cleared primary — still allow single token.
        values = resolved.role_values("supplier_part_number")
        if len(values) == 1:
            return values[0]
        return None
