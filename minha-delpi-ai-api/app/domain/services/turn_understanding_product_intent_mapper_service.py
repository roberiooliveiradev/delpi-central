"""E2.S4 — map Turn Understanding goals → product intent enum.

Does not call OpenAPI selection. Used when productFamilyAuthorityShadow.cutoverEnabled.
Requires product grounding (code / “produto”) to avoid RAG/policy false positives.
"""

from __future__ import annotations

import re

from app.domain.entities.turn_understanding import TurnUnderstanding
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class TurnUnderstandingProductIntentMapperService:
    """Derives ChatProductQueryIntent-compatible tokens from TU prose goals."""

    # Ordered: first match wins per goal. Prefer specific facets before catch-alls.
    _TOKEN_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("structure", ("estrutura", "lista de materiais")),
        ("parents", ("onde e usado", "onde é usado", "pais do produto", "parents")),
        ("stock", ("estoque", "saldo", "stock")),
        ("sales", ("venda", "vendas", "fatur")),
        ("suppliers", ("fornecedor", "fornecedore", "supplier")),
        ("purchases", ("compra", "compras", "purchase")),
        ("pricing", ("preco", "preço", "pricing", "quanto custa")),
        ("guide", ("roteiro", "guide", "rota de fabric")),
        ("customers", ("cliente", "clientes", "customer")),
        ("inspection", ("inspecao", "inspeção", "inspection")),
        ("analyser", ("analisador", "analyser", "analise completa", "análise completa")),
        ("summary", ("resumo do produto", "ficha do produto")),
        ("description", ("descricao", "descrição", "o que e o produto", "o que é o produto")),
    )

    _NON_PRODUCT_DOC_MARKERS: tuple[str, ...] = (
        "politica",
        "política",
        "norma",
        "procedimento",
        "regulamento",
        "documento",
        "manual da",
        "o que diz",
    )

    _PRODUCT_LEXICAL_MARKERS: tuple[str, ...] = (
        "produto",
        "produtos",
        "peca",
        "peça",
        "pa ",
        "mp ",
    )

    _CODE_RE = re.compile(r"\b\d{5,}\b")

    @classmethod
    def from_understanding(cls, contract: TurnUnderstanding | None) -> str | None:
        if contract is None or not contract.goals:
            return None

        user_goal = ChatMessageNormalizationService.normalize_for_matching(
            str(contract.user_goal or "")
        )
        if cls._looks_like_non_product_document(user_goal) and not cls._has_product_code(
            contract
        ):
            return None

        if not cls._is_product_grounded(contract, user_goal):
            return None

        mapped: list[str] = []
        for goal in contract.goals:
            intent = cls.from_goal_prose(str(goal.intent or ""))
            if intent:
                mapped.append(intent)

        unique = list(dict.fromkeys(mapped))
        if not unique:
            return None
        if len(unique) >= 2:
            return "multi_scope"
        return unique[0]

    @classmethod
    def from_goal_prose(cls, prose: str) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(prose)
        if not normalized:
            return None

        for intent, tokens in cls._TOKEN_RULES:
            if any(token in normalized for token in tokens):
                return intent
        return None

    @classmethod
    def from_message(cls, message: str) -> str | None:
        from app.domain.services.chat_turn_understanding_service import (
            ChatTurnUnderstandingService,
        )

        contract = ChatTurnUnderstandingService.analyze(message)
        return cls.from_understanding(contract)

    @classmethod
    def _has_product_code(cls, contract: TurnUnderstanding) -> bool:
        for goal in contract.goals:
            if str(goal.entities.get("productCode") or "").strip():
                return True
        return bool(cls._CODE_RE.search(str(contract.user_goal or "")))

    @classmethod
    def _is_product_grounded(cls, contract: TurnUnderstanding, user_goal: str) -> bool:
        if cls._has_product_code(contract):
            return True
        return any(marker in user_goal for marker in cls._PRODUCT_LEXICAL_MARKERS)

    @classmethod
    def _looks_like_non_product_document(cls, normalized: str) -> bool:
        return any(marker in normalized for marker in cls._NON_PRODUCT_DOC_MARKERS)
