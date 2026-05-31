"""Desambiguação de consulta operacional (Playbook 02 §20–21, §25)."""

from __future__ import annotations

from typing import Any


class ChatIntentDisambiguationService:
    _SCOPE_OPTIONS: tuple[tuple[str, str, str], ...] = (
        ("Cadastro", "product_lookup", "me fale do produto {productCode}"),
        ("Estoque", "stock_lookup", "qual o estoque do produto {productCode}?"),
        ("Fornecedores", "supplier_lookup", "quais os fornecedores do produto {productCode}?"),
        ("Estrutura", "structure_lookup", "mostre a estrutura do produto {productCode}"),
        ("Vendas", "sales_lookup", "mostre as vendas do produto {productCode}"),
        ("Compras", "purchase_lookup", "mostre as compras do produto {productCode}"),
    )

    @classmethod
    def try_build(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None = None,
        workspace_context: dict | None = None,
        allowed_action_ids: list[str] | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_intent_router_service import ChatIntentRouterService

        route = ChatIntentRouterService.classify(
            message,
            previous_messages=previous_messages,
            workspace_context=workspace_context,
            allowed_action_ids=allowed_action_ids,
        )

        if not route.ambiguous or route.intent != "operational_query":
            return None

        product_code = str((route.resolved_params or {}).get("productCode") or "").strip()

        if not product_code:
            return None

        suggestions = cls.build_suggestions(product_code)
        direct_answer = (
            f"O que você quer ver sobre o produto **{product_code}**? "
            "Escolha uma opção abaixo ou descreva com suas palavras."
        )

        return {
            "directAnswer": direct_answer,
            "suggestions": suggestions,
            "productCode": product_code,
            "intentRoute": route.to_dict(),
        }

    @classmethod
    def build_suggestions(cls, product_code: str) -> list[dict[str, str]]:
        code = str(product_code or "").strip()
        suggestions: list[dict[str, str]] = []

        for label, _sub_intent, template in cls._SCOPE_OPTIONS:
            query = template.format(productCode=code)

            suggestions.append({"label": label, "query": query, "subIntent": _sub_intent})

        return suggestions
