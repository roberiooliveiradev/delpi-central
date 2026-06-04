"""Reconhecimento de perguntas operacionais no plural (vários produtos/itens)."""

from __future__ import annotations

import re


class ChatProductPluralPhrasingService:
    _PRODUCT_NOUN = r"(?:produto|produtos|item|itens|material|materiais)"

    _PLURAL_PRODUCT_REFERENCE_TERMS = (
        "produtos",
        "itens",
        "materiais",
        "desses produtos",
        "destes produtos",
        "esses produtos",
        "estes produtos",
        "os produtos citados",
        "os itens citados",
        "os produtos acima",
        "os itens acima",
        "produtos acima",
        "itens acima",
        "mesmos produtos",
        "mesmos itens",
    )

    _SCOPE_LABEL_BY_PATH_FRAGMENT: tuple[tuple[str, str], ...] = (
        ("/parents", "onde o item é usado"),
        ("/stock", "estoque"),
        ("/structure", "estrutura (BOM)"),
        ("/guide", "roteiro de produção"),
        ("/inspection", "plano de inspeção"),
        ("/sales", "vendas"),
        ("/profile", "cadastro"),
    )

    @classmethod
    def mentions_plural_products(cls, normalized: str) -> bool:
        if not normalized:
            return False

        return any(term in normalized for term in cls._PLURAL_PRODUCT_REFERENCE_TERMS)

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
        scope_terms: tuple[str, ...],
        scope_plural_terms: tuple[str, ...] = (),
        linked_stems: tuple[str, ...] = (),
    ) -> bool:
        if not normalized:
            return False

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
            for term in (
                "produto",
                "produtos",
                "item",
                "itens",
                "material",
                "materiais",
                "codigo",
                "código",
            )
        )

    @classmethod
    def scope_labels_from_api_path(cls, path: str) -> list[str]:
        lowered = str(path or "").lower()
        labels: list[str] = []

        for fragment, label in cls._SCOPE_LABEL_BY_PATH_FRAGMENT:
            if fragment in lowered and label not in labels:
                labels.append(label)

        return labels

    @classmethod
    def join_scope_labels_pt(cls, labels: list[str]) -> str | None:
        if not labels:
            return None

        if len(labels) == 1:
            return labels[0]

        if len(labels) == 2:
            return f"{labels[0]} e {labels[1]}"

        return ", ".join(labels[:-1]) + f" e {labels[-1]}"
