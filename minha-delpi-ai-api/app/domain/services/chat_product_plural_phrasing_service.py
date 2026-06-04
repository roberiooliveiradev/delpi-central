"""Reconhecimento de perguntas operacionais no plural (vários produtos/itens)."""

from __future__ import annotations

import re

from app.domain.services.chat_product_operational_content_service import (
    ChatProductOperationalContentService,
)


class ChatProductPluralPhrasingService:
    _PRODUCT_NOUN = r"(?:produto|produtos|item|itens|material|materiais)"

    @classmethod
    def mentions_plural_products(cls, normalized: str) -> bool:
        if not normalized:
            return False

        return any(
            term in normalized
            for term in ChatProductOperationalContentService.list(
                "pluralPhrasing",
                "productReferenceTerms",
            )
        )

    @classmethod
    def _contains_whole_term(cls, normalized: str, term: str) -> bool:
        if not term:
            return False

        return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized) is not None

    @classmethod
    def _matches_linked_scope_phrase(
        cls,
        normalized: str,
        linked_stems: tuple[str, ...],
    ) -> bool:
        for stem in linked_stems:
            pattern = (
                rf"(?<!\w){re.escape(stem)}s?\s+(?:dos?|das?|de)\s+{cls._PRODUCT_NOUN}\b"
            )

            if re.search(pattern, normalized):
                return True

        return False

    @classmethod
    def matches_scope_linked_to_products(
        cls,
        normalized: str,
        *,
        scope: str | None = None,
        scope_terms: tuple[str, ...] = (),
        scope_plural_terms: tuple[str, ...] = (),
        linked_stems: tuple[str, ...] = (),
    ) -> bool:
        if not normalized:
            return False

        if scope:
            loaded_terms, loaded_plural = ChatProductOperationalContentService.scope_term_groups(
                scope
            )
            scope_terms = scope_terms or loaded_terms
            scope_plural_terms = scope_plural_terms or loaded_plural
            linked_stems = linked_stems or ChatProductOperationalContentService.linked_scope_stems(
                scope
            )

        if any(cls._contains_whole_term(normalized, term) for term in scope_terms):
            return True

        if scope_plural_terms and any(
            cls._contains_whole_term(normalized, term) for term in scope_plural_terms
        ):
            return True

        if linked_stems and cls._matches_linked_scope_phrase(normalized, linked_stems):
            return True

        return False

    @classmethod
    def has_product_entity_reference(cls, normalized: str) -> bool:
        return any(
            term in normalized
            for term in ChatProductOperationalContentService.list(
                "pluralPhrasing",
                "productEntityTerms",
            )
        )

    @classmethod
    def scope_labels_from_api_path(cls, path: str) -> list[str]:
        return ChatProductOperationalContentService.scope_labels_from_api_path(path)

    @classmethod
    def join_scope_labels_pt(cls, labels: list[str]) -> str | None:
        if not labels:
            return None

        joined = ChatProductOperationalContentService.join_list_pt(labels)

        return joined or None
