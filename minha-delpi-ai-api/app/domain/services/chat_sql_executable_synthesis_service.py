"""Síntese de SELECT executável a partir da mensagem (authoring e one-shot execute)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatSqlExecutableSynthesisService:
    """Uma fonte para montar SELECT…FROM a partir de slots inferidos da mensagem."""

    @classmethod
    def build_context(
        cls,
        message: str | None,
        *,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        from app.domain.services.chat_sql_semantic_schema_mapper_service import (
            ChatSqlSemanticSchemaMapperService,
        )

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        mapping = ChatSqlSemanticSchemaMapperService.map_message(message)
        logical_table: str | None = None
        domain_explicit = False
        code_col = "A1_COD"
        name_col = "A1_NOME"
        group_col: str | None = None

        for item in mapping.get("matches") or []:
            table_hints = item.get("tableHints") or []

            if table_hints:
                logical_table = str(table_hints[0]).upper()
                domain_explicit = True
                break

        explicit = re.search(
            r"\b(?:sa|sb|sc|sd|se|sf|sg|sh|si|sj|sk|sl|sm|sn|so|sp)[a-z]?\d{1,4}\b",
            normalized,
            flags=re.IGNORECASE,
        )

        if explicit:
            logical_table = explicit.group(0).upper()
            domain_explicit = True

        if not logical_table:
            logical_table = ""
            code_col = ""
            name_col = ""
            group_col = None
        elif logical_table.startswith("SB"):
            code_col = "B1_COD"
            name_col = "B1_DESC"
            group_col = "B1_GRUPO"
        elif logical_table.startswith("SH"):
            code_col = "H6_OP"
            name_col = "H6_PRODUTO"
            group_col = None
        elif logical_table.startswith("SA"):
            code_col = "A1_COD"
            name_col = "A1_NOME"

        column_list = list(columns or [])

        if column_list:
            code_col = next(
                (c for c in column_list if "cod" in c.lower()),
                code_col,
            )
            name_col = next(
                (
                    c
                    for c in column_list
                    if (
                        "nome" in c.lower()
                        or "desc" in c.lower()
                        or "name" in c.lower()
                    )
                    and "cod" not in c.lower()
                ),
                name_col,
            )
            group_col = next(
                (c for c in column_list if "grupo" in c.lower()),
                group_col,
            )

        physical = ""
        if logical_table:
            physical = (
                logical_table
                if re.search(r"\d{3}$", logical_table)
                else f"{logical_table}010"
            )

        top_limit: int | None = None
        top_match = re.search(r"\btop\s+(\d+)\b", normalized, flags=re.IGNORECASE)

        if top_match:
            top_limit = int(top_match.group(1))
        else:
            count_match = re.search(
                r"\b(?:liste|listar|list|traga|mostre|retorne|busque|buscar|busca)"
                r"(?:\s+(?:os|as|me|a))?\s+(\d+)\s+",
                normalized,
                flags=re.IGNORECASE,
            )

            if count_match:
                top_limit = int(count_match.group(1))
            else:
                recent_count = re.search(
                    r"\b(\d{1,3})\s+(?:ultim|primeir|recent)",
                    normalized,
                    flags=re.IGNORECASE,
                )

                if recent_count:
                    top_limit = int(recent_count.group(1))
                else:
                    trazer_top = re.search(
                        r"\b(?:trazer|traga|ajuste|ajustar).*?\btop\s*(\d+)\b",
                        normalized,
                        flags=re.IGNORECASE,
                    )
                    if trazer_top:
                        top_limit = int(trazer_top.group(1))
                    else:
                        top_n = re.search(r"\btop\s*(\d+)\b", normalized, flags=re.IGNORECASE)
                        if top_n:
                            top_limit = int(top_n.group(1))

        return {
            "logicalTable": logical_table,
            "physicalTable": physical,
            "codeColumn": code_col,
            "nameColumn": name_col,
            "groupColumn": group_col,
            "groupValue": (
                group_match.group(1)
                if (
                    group_match := re.search(
                        r"\bgrupo\s+(\d+)\b",
                        normalized,
                        flags=re.IGNORECASE,
                    )
                )
                else None
            ),
            "topLimit": top_limit,
            "domainExplicit": domain_explicit,
        }

    @classmethod
    def synthesize_select(
        cls,
        message: str | None,
        *,
        columns: list[str] | None = None,
        invent_default_table: bool = False,
    ) -> str | None:
        """Monta SELECT…FROM. Execute one-shot: invent_default_table=False (exige domínio)."""
        ctx = cls.build_context(message, columns=columns)
        logical = str(ctx.get("logicalTable") or "").upper()

        if not logical:
            if not invent_default_table:
                return None

            logical = "SA1"
            ctx = {
                **ctx,
                "logicalTable": "SA1",
                "physicalTable": "SA1010",
                "codeColumn": ctx.get("codeColumn") or "A1_COD",
                "nameColumn": ctx.get("nameColumn") or "A1_NOME",
            }
        elif not ctx.get("domainExplicit") and not invent_default_table:
            return None

        select_prefix = (
            f"SELECT TOP {ctx['topLimit']} "
            if ctx.get("topLimit")
            else "SELECT "
        )

        if logical.startswith("SH"):
            select_cols = ["H6_OP", "H6_PRODUTO", "H6_DATA", "H6_HORA", "H6_QTDPROD"]
            lines = [
                f"{select_prefix}{', '.join(select_cols)}",
                f"FROM {ctx['physicalTable']}",
                "WHERE D_E_L_E_T_ = ''",
                "  AND H6_TIPO = 'P'",
            ]

            if cls._wants_recent_order(message):
                lines.append("ORDER BY H6_DATA DESC, H6_HORA DESC")

            return "\n".join(lines)

        select_cols = [str(ctx["codeColumn"])]

        if ctx.get("nameColumn") and ctx["nameColumn"] not in select_cols:
            select_cols.append(str(ctx["nameColumn"]))

        # Prefer explicit column tokens from the message when listed (T3 style).
        for token in ("B1_COD", "B1_DESC", "B1_GRUPO", "A1_COD", "A1_NOME"):
            if token.lower() in ChatMessageNormalizationService.normalize_for_matching(
                message
            ):
                if token not in select_cols:
                    select_cols.append(token)

        lines = [
            f"{select_prefix}{', '.join(select_cols)}",
            f"FROM {ctx['physicalTable']}",
            "WHERE D_E_L_E_T_ = ''",
        ]

        if ctx.get("groupColumn") and ctx.get("groupValue"):
            lines.append(f"  AND {ctx['groupColumn']} = '{ctx['groupValue']}'")

        return "\n".join(lines)

    @classmethod
    def _wants_recent_order(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        return any(
            marker in normalized
            for marker in (
                "ultimo",
                "ultimos",
                "recente",
                "recentes",
            )
        )
