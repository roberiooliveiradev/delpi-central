"""Mapeamento semântico de termos do usuário para colunas/tabelas — Playbook §15."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

# (termos na mensagem, padrões de coluna, dicas de tabela Protheus/ANSI)
_SEMANTIC_MAPPINGS: tuple[tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]], ...] = (
    (("cliente", "clientes", "customer"), ("A1_COD", "A1_NOME", "CLIENTE", "COD_CLIENTE", "CUSTOMER_ID", "CLIENT_ID"), ("SA1",)),
    (("nome do cliente", "razao social", "razão social"), ("A1_NOME", "A1_NREDUZ", "CUSTOMER_NAME", "NOME_CLIENTE"), ("SA1",)),
    (("venda", "vendas", "faturamento", "receita"), ("C6_VALOR", "D2_TOTAL", "VALOR_TOTAL", "SALES_VALUE", "TOTAL_AMOUNT"), ("SC6", "SD2", "SF2")),
    (("pedido", "pedidos", "order"), ("C5_NUM", "C5_CLIENTE", "ORDER_ID", "PEDIDO_ID"), ("SC5",)),
    (
        ("apontamento", "apontamentos"),
        ("H6_OP", "H6_PRODUTO", "H6_DATA", "H6_HORA", "H6_QTDPROD", "H6_TIPO"),
        ("SH6",),
    ),
    (("produto", "produtos", "item", "sku"), ("B1_COD", "D2_COD", "PRODUCT_ID", "ITEM_CODE", "SKU"), ("SB1", "SD2")),
    (("estoque", "saldo", "inventory"), ("B2_QATU", "B2_QEMP", "SALDO", "QTY", "QUANTIDADE"), ("SB2",)),
    (("filial", "branch"), ("FILIAL", "BRANCH", "A1_FILIAL", "C5_FILIAL", "D2_FILIAL"), ()),
    (("data", "emissao", "emissão", "periodo", "período"), ("DATA", "EMISSAO", "DT_EMISSAO", "SALE_DATE", "C5_EMISSAO", "D2_EMISSAO"), ()),
    (("vendedor", "representante"), ("A3_COD", "SELLER_ID", "SALES_REP_ID", "VENDEDOR"), ("SA3",)),
    (("quantidade", "qtd", "qty"), ("QUANTIDADE", "QTD", "QUANTITY", "D2_QUANT"), ()),
    (("margem", "lucro"), ("MARGEM", "MARGIN", "PROFIT_MARGIN", "LUCRO"), ()),
    (("cidade", "municipio", "município"), ("A1_MUN", "CIDADE", "CITY", "MUNICIPIO"), ("SA1",)),
    (("status", "situacao", "situação"), ("STATUS", "SITUACAO", "STATE", "C5_STATUS"), ()),
)


class ChatSqlSemanticSchemaMapperService:
    @classmethod
    def map_message(cls, message: str | None) -> dict[str, Any]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        matches: list[dict[str, Any]] = []
        seen_terms: set[str] = set()

        if not normalized:
            return {"matches": matches, "hasMatches": False}

        for terms, column_patterns, table_hints in _SEMANTIC_MAPPINGS:
            for term in terms:
                if term in seen_terms:
                    continue

                if term not in normalized:
                    continue

                seen_terms.add(term)
                matches.append(
                    {
                        "term": term,
                        "columnPatterns": list(column_patterns),
                        "tableHints": list(table_hints),
                    }
                )
                break

        return {"matches": matches, "hasMatches": bool(matches)}

    @classmethod
    def resolve_primary_table(cls, message: str | None) -> str | None:
        mapping = cls.map_message(message)

        for item in mapping.get("matches") or []:
            table_hints = item.get("tableHints") or []

            if table_hints:
                return str(table_hints[0]).upper()

        return None

    @classmethod
    def format_hints(cls, mapping: dict[str, Any] | None) -> list[str]:
        if not isinstance(mapping, dict):
            return []

        lines: list[str] = []

        for item in mapping.get("matches") or []:
            if not isinstance(item, dict):
                continue

            term = str(item.get("term") or "").strip()
            columns = item.get("columnPatterns") or []
            tables = item.get("tableHints") or []

            if not term:
                continue

            column_text = ", ".join(str(c) for c in columns[:5])
            table_text = ", ".join(str(t) for t in tables[:3])
            hint = f"«{term}» → colunas candidatas: {column_text}"

            if table_text:
                hint = f"{hint}; tabelas: {table_text}"

            lines.append(hint)

        return lines
