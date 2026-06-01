"""Refinamentos multi-turn em consultas SQL já executadas na sessão."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_sql_capability_service import (
    ExternalActionSqlCapabilityService,
)

SqlRefinementMode = Literal["execute", "show_sql"]


@dataclass(frozen=True)
class SqlQueryRefinement:
    mode: SqlRefinementMode
    sql: str
    title: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class RecentSqlExecution:
    sql: str
    title: str | None = None
    path: str | None = None


class ChatSqlQueryRefinementService:
    _ADD_TERMS = (
        "acrescente",
        "acrescenta",
        "adicione",
        "adiciona",
        "inclua",
        "incluir",
        "add ",
        "insira",
        "insere",
        "coloque a coluna",
        "coloca a coluna",
    )
    _REMOVE_TERMS = (
        "remova",
        "remove",
        "retire",
        "retira",
        "tire",
        "exclua",
        "excluir",
        "elimine",
        "elimina",
    )
    _ALTER_TERMS = (
        "altere",
        "altera",
        "ajuste",
        "ajusta",
        "atualize",
        "atualiza",
        "modifique",
        "modifica",
        "mude",
        "muda",
        "refine",
        "refina",
        "troque",
        "troca",
    )
    _SHOW_QUERY_TERMS = (
        "mostre a query",
        "mostra a query",
        "exiba a query",
        "exibe a query",
        "qual query",
        "qual e a query",
        "qual é a query",
        "query usada",
        "query utilizada",
        "sql usado",
        "sql utilizado",
        "mostre o sql",
        "mostra o sql",
        "exiba o sql",
        "exibe o sql",
        "qual sql",
        "query executada",
        "consulta executada",
        "consulta usada",
        "me mostre o sql",
        "me mostra o sql",
        "ver sql",
        "ver a query",
        "ver o sql",
        "ver consulta",
        "codigo sql",
        "código sql",
        "codigo da query",
        "código da query",
        "mostre o codigo",
        "mostra o codigo",
        "mostre o código",
        "mostra o código",
        "somente a query",
        "so a query",
        "só a query",
        "apenas a query",
        "sem executar",
        "sem rodar",
    )
    _FILTER_TERMS = (
        "filtre",
        "filtro",
        "filtrar",
        "filtra ",
        "somente",
        "apenas",
        "restrinja",
        "restringe",
        "limitar",
        "limita ",
    )
    _REMOVE_BRANCH_TERMS = (
        "todas as filiais",
        "todas filiais",
        "remover filtro de filial",
        "remova filtro de filial",
        "retire filtro de filial",
        "sem filtro de filial",
        "sem filial",
    )
    _BRANCH_RE = re.compile(
        r"\b(?:filial|fil\.?)\s*[_-]?\s*(\d{1,2})\b",
        re.IGNORECASE,
    )
    _TOP_RE = re.compile(r"\btop\s*(\d{1,3})\b", re.IGNORECASE)
    _COLUMN_DEFINITIONS: dict[str, dict[str, Any]] = {
        "filial": {
            "aliases": ("filial", "cod filial", "codigo filial", "branch"),
            "select": "OP.C2_FILIAL AS FILIAL",
            "group_by": "OP.C2_FILIAL",
            "result_alias": "FILIAL",
        },
        "descricao produto": {
            "aliases": (
                "descricao produto",
                "descrição produto",
                "descricao do produto",
                "descrição do produto",
                "descricao",
                "descrição",
            ),
            "select": "P.B1_DESC AS DESCRICAO_PRODUTO",
            "group_by": "P.B1_DESC",
            "result_alias": "DESCRICAO_PRODUTO",
        },
        "cod produto": {
            "aliases": ("cod produto", "codigo produto", "código produto", "produto"),
            "select": "OP.C2_PRODUTO AS COD_PRODUTO",
            "group_by": "OP.C2_PRODUTO",
            "result_alias": "COD_PRODUTO",
        },
        "quantidade": {
            "aliases": (
                "quantidade",
                "qtd planejada",
                "qtd",
                "quantidade planejada",
            ),
            "select": "OP.C2_QUANT AS QTD_PLANEJADA",
            "group_by": "OP.C2_QUANT",
            "result_alias": "QTD_PLANEJADA",
        },
        "unidade": {
            "aliases": ("unidade", "um"),
            "select": "OP.C2_UM AS UNIDADE",
            "group_by": "OP.C2_UM",
            "result_alias": "UNIDADE",
        },
        "data inicio": {
            "aliases": (
                "data inicio",
                "data início",
                "data inicio operacao",
                "data início operação",
                "inicio operacao",
                "início operação",
            ),
            "select": "OA.H8_DTINI AS DATA_INICIO_OPERACAO",
            "group_by": "OA.H8_DTINI",
            "result_alias": "DATA_INICIO_OPERACAO",
        },
    }
    _INVENTORY_COLUMN_DEFINITIONS: dict[str, dict[str, Any]] = {
        "filial": {
            "aliases": ("filial", "cod filial", "codigo filial", "branch"),
            "select": "SB2.B2_FILIAL AS branch",
            "group_by": "SB2.B2_FILIAL",
            "result_alias": "branch",
        },
        "armazem": {
            "aliases": ("armazem", "armazém", "local", "warehouse"),
            "select": "RTRIM(SB2.B2_LOCAL) AS warehouse",
            "group_by": "SB2.B2_LOCAL",
            "result_alias": "warehouse",
        },
        "descricao produto": {
            "aliases": (
                "descricao produto",
                "descrição produto",
                "descricao do produto",
                "descrição do produto",
                "descricao",
                "descrição",
            ),
            "select": "RTRIM(SB1.B1_DESC) AS product_description",
            "group_by": "SB1.B1_DESC",
            "result_alias": "product_description",
        },
        "cod produto": {
            "aliases": ("cod produto", "codigo produto", "código produto", "produto"),
            "select": "SB2.B2_COD AS product_code",
            "group_by": "SB2.B2_COD",
            "result_alias": "product_code",
        },
        "estoque minimo": {
            "aliases": (
                "estoque minimo",
                "estoque mínimo",
                "minimo",
                "mínimo",
                "minimum stock",
            ),
            "select": (
                "COALESCE(NULLIF(SBZ.BZ_ESTSEG, 0), NULLIF(SB1.B1_EMIN, 0)) "
                "AS minimum_stock"
            ),
            "group_by": "",
            "result_alias": "minimum_stock",
        },
    }

    @classmethod
    def is_sql_follow_up(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        return cls.resolve(message, previous_messages=previous_messages) is not None

    @classmethod
    def resolve(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> SqlQueryRefinement | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        recent = cls.collect_recent_sql_execution(previous_messages)

        if not recent:
            return None

        if cls._looks_like_show_query(normalized):
            return SqlQueryRefinement(
                mode="show_sql",
                sql=recent.sql,
                title=recent.title,
                reason="A mensagem solicita exibir a consulta SQL da pesquisa anterior.",
            )

        if cls._looks_like_remove_branch_filter(normalized):
            updated = cls.remove_branch_filter(recent.sql)

            if updated != recent.sql:
                return SqlQueryRefinement(
                    mode="execute",
                    sql=updated,
                    title=recent.title,
                    reason="Refinamento SQL: filtro de filial removido da consulta anterior.",
                )

        top_limit = cls._extract_top_limit(normalized)

        if top_limit is not None and cls._looks_like_limit_adjustment(normalized):
            updated = cls.apply_top_limit(recent.sql, top_limit)

            if updated != recent.sql:
                return SqlQueryRefinement(
                    mode="execute",
                    sql=updated,
                    title=recent.title,
                    reason="Refinamento SQL: limite TOP ajustado na consulta anterior.",
                )

        column_key = cls._extract_column_key(normalized, sql=recent.sql)

        if column_key and cls._looks_like_add_column(normalized):
            updated = cls.add_column(recent.sql, column_key)

            if updated == recent.sql:
                return None

            return SqlQueryRefinement(
                mode="execute",
                sql=updated,
                title=recent.title,
                reason="Refinamento SQL: inclusão de coluna solicitada na consulta anterior.",
            )

        if column_key and cls._looks_like_remove_column(normalized):
            updated = cls.remove_column(recent.sql, column_key)

            if updated == recent.sql:
                return None

            return SqlQueryRefinement(
                mode="execute",
                sql=updated,
                title=recent.title,
                reason="Refinamento SQL: remoção de coluna solicitada na consulta anterior.",
            )

        branches = cls._extract_branch_codes(normalized)

        if branches and cls._looks_like_filter_adjustment(normalized, branches=branches):
            updated = cls.apply_branch_filter(recent.sql, branches)

            if updated == recent.sql:
                return None

            return SqlQueryRefinement(
                mode="execute",
                sql=updated,
                title=recent.title,
                reason="Refinamento SQL: filtro de filial aplicado na consulta anterior.",
            )

        return None

    @classmethod
    def collect_recent_sql_execution(
        cls,
        previous_messages: list[Any] | None,
    ) -> RecentSqlExecution | None:
        for item in reversed((previous_messages or [])[-12:]):
            metadata = cls._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if tool_meta.get("ok") is False:
                    continue

                path = str(tool_meta.get("path") or "").lower()
                action_id = str(tool_meta.get("actionId") or "").lower()
                sensitivity = str(tool_meta.get("sensitivity") or "").lower()

                if path != "/data/sql" and "sql" not in action_id and sensitivity != "sql":
                    continue

                sql = ExternalActionSqlCapabilityService.extract_sql_from_metadata(tool_meta)

                if not sql:
                    arguments = tool_call.get("arguments") or {}
                    body = arguments.get("body") or {}
                    sql = ExternalActionSqlCapabilityService.extract_sql_from_arguments(
                        {"body": body, **arguments}
                    )

                if not sql:
                    continue

                title = cls._extract_title(tool_meta)

                return RecentSqlExecution(sql=sql, title=title, path=path or None)

        return None

    @classmethod
    def add_column(cls, sql: str, column_key: str) -> str:
        definition = cls._column_definitions_for_sql(sql).get(column_key)

        if not definition:
            return sql

        alias = str(definition["result_alias"])
        select_expr = str(definition["select"])
        group_expr = str(definition.get("group_by") or "")

        if re.search(rf"\bAS\s+{re.escape(alias)}\b", sql, flags=re.I):
            return sql

        updated = re.sub(
            r"(\nFROM\b)",
            f",\n    {select_expr}\n\\1",
            sql,
            count=1,
            flags=re.I,
        )

        if group_expr and re.search(r"\bGROUP BY\b", updated, flags=re.I):
            updated = re.sub(
                r"(GROUP BY\s+)(.+?)(\nORDER BY\b|\Z)",
                lambda match: (
                    f"{match.group(1)}{match.group(2).rstrip()},\n    {group_expr}"
                    f"{match.group(3)}"
                ),
                updated,
                count=1,
                flags=re.I | re.S,
            )

        return updated

    @classmethod
    def remove_column(cls, sql: str, column_key: str) -> str:
        definition = cls._column_definitions_for_sql(sql).get(column_key)

        if not definition:
            return sql

        alias = str(definition["result_alias"])
        group_expr = str(definition.get("group_by") or "")

        updated = re.sub(
            rf",?\s*\n\s*[^\n]*\bAS\s+{re.escape(alias)}\b",
            "",
            sql,
            count=1,
            flags=re.I,
        )

        if group_expr:
            updated = re.sub(
                rf",?\s*\n\s*{re.escape(group_expr)}\s*",
                "",
                updated,
                count=1,
                flags=re.I,
            )

        return updated

    @classmethod
    def apply_branch_filter(cls, sql: str, branch_codes: list[str]) -> str:
        branches = [
            str(code).zfill(2)[:2]
            for code in branch_codes
            if str(code or "").strip()
        ]

        if not branches:
            return sql

        if re.search(r"DECLARE\s+@FILIAL\s+CHAR\(2\)\s*=", sql, flags=re.I):
            return re.sub(
                r"(DECLARE\s+@FILIAL\s+CHAR\(2\)\s*=\s*')(\d{2})(';\s*)",
                rf"\g<1>{branches[0]}\3",
                sql,
                count=1,
                flags=re.I,
            )

        predicate = cls._branch_predicate("SB2.B2_FILIAL", branches)

        replaced = re.sub(
            r"\n\s*AND\s+SB2\.B2_FILIAL\s+(?:=\s*'\d{2}'|IN\s*\([^)]+\))",
            f"\n  AND {predicate}",
            sql,
            count=1,
            flags=re.I,
        )

        if replaced != sql:
            return replaced

        if re.search(r"\bSB2010\b", sql, flags=re.I):
            return re.sub(
                r"(\nORDER BY\b)",
                f"\n  AND {predicate}\\1",
                sql,
                count=1,
                flags=re.I,
            )

        return sql

    @classmethod
    def remove_branch_filter(cls, sql: str) -> str:
        updated = re.sub(
            r"\n\s*AND\s+SB2\.B2_FILIAL\s+(?:=\s*'\d{2}'|IN\s*\([^)]+\))",
            "",
            sql,
            count=1,
            flags=re.I,
        )

        return updated

    @classmethod
    def apply_top_limit(cls, sql: str, limit: int) -> str:
        bounded = max(1, min(int(limit), 500))

        if not re.search(r"\bSELECT\s+TOP\s+\d+\b", sql, flags=re.I):
            return sql

        return re.sub(
            r"(\bSELECT\s+TOP\s+)\d+",
            rf"\g<1>{bounded}",
            sql,
            count=1,
            flags=re.I,
        )

    @classmethod
    def format_show_sql_answer(cls, refinement: SqlQueryRefinement) -> str:
        title = refinement.title or "Consulta SQL"
        return (
            f"### {title}\n\n"
            "Consulta SQL utilizada na pesquisa anterior:\n\n"
            f"```sql\n{refinement.sql.strip()}\n```\n\n"
            "Peça alterações em linguagem natural — por exemplo: "
            "*filial 01 e 02*, *top 100* ou *acrescente a coluna de armazém*."
        )

    @classmethod
    def _column_definitions_for_sql(cls, sql: str) -> dict[str, dict[str, Any]]:
        if "SB2010" in str(sql or "").upper():
            return cls._INVENTORY_COLUMN_DEFINITIONS

        return cls._COLUMN_DEFINITIONS

    @classmethod
    def _branch_predicate(cls, column: str, branches: list[str]) -> str:
        if len(branches) == 1:
            return f"{column} = '{branches[0]}'"

        joined = ", ".join(f"'{branch}'" for branch in branches)

        return f"{column} IN ({joined})"

    @classmethod
    def _extract_column_key(cls, normalized: str, *, sql: str = "") -> str | None:
        match = re.search(
            r"\bcoluna(?:s)?\s+(?:de\s+|da\s+|do\s+)?(.+)$",
            normalized,
        )

        candidate = match.group(1).strip() if match else normalized

        for key, definition in cls._column_definitions_for_sql(sql).items():
            aliases = definition.get("aliases") or ()

            if any(alias in candidate for alias in aliases):
                return key

            if any(alias in normalized for alias in aliases):
                return key

        return None

    @classmethod
    def _looks_like_add_column(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._ADD_TERMS) or (
            "coluna" in normalized
            and not any(term in normalized for term in cls._REMOVE_TERMS)
            and not cls._looks_like_show_query(normalized)
        )

    @classmethod
    def _looks_like_remove_column(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._REMOVE_TERMS)

    @classmethod
    def _looks_like_show_query(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._SHOW_QUERY_TERMS):
            return True

        if "sql" in normalized and any(
            token in normalized for token in ("mostre", "mostra", "exiba", "exibe", "ver", "qual")
        ):
            return True

        return False

    @classmethod
    def _looks_like_filter_adjustment(
        cls,
        normalized: str,
        *,
        branches: list[str] | None = None,
    ) -> bool:
        if any(term in normalized for term in cls._FILTER_TERMS):
            return True

        if any(term in normalized for term in cls._ALTER_TERMS) and branches:
            return True

        return bool(branches)

    @classmethod
    def _looks_like_remove_branch_filter(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._REMOVE_BRANCH_TERMS)

    @classmethod
    def _looks_like_limit_adjustment(cls, normalized: str) -> bool:
        return cls._extract_top_limit(normalized) is not None and (
            "top" in normalized
            or any(term in normalized for term in cls._ALTER_TERMS + cls._FILTER_TERMS)
            or re.search(r"\b\d{1,3}\s+produtos?\b", normalized)
            or re.search(r"\b\d{1,3}\s+registros?\b", normalized)
        )

    @classmethod
    def _extract_branch_codes(cls, normalized: str) -> list[str]:
        match = re.search(r"\b(?:filial(?:is)?|fil\.?)\s*(.+)$", normalized)

        if match:
            tail = match.group(1)
            codes = re.findall(r"\d{1,2}", tail)

            if codes:
                return [str(code).zfill(2)[:2] for code in codes]

        single = cls._BRANCH_RE.search(normalized)

        if single:
            return [str(single.group(1)).zfill(2)]

        return []

    @classmethod
    def _extract_top_limit(cls, normalized: str) -> int | None:
        match = cls._TOP_RE.search(normalized)

        if match:
            return min(int(match.group(1)), 500)

        match = re.search(r"\b(\d{1,3})\s+produtos?\b", normalized)

        if match:
            return min(int(match.group(1)), 500)

        match = re.search(r"\b(\d{1,3})\s+registros?\b", normalized)

        if match:
            return min(int(match.group(1)), 500)

        return None

    @classmethod
    def _extract_title(cls, metadata: dict) -> str | None:
        presentation = metadata.get("presentation") or {}
        title = presentation.get("title")

        if title:
            return str(title)

        humanized = metadata.get("humanizedSummary") or {}

        if isinstance(humanized, dict) and humanized.get("titulo"):
            return str(humanized["titulo"])

        return None

    @classmethod
    def _message_metadata(cls, item: Any) -> dict:
        if isinstance(item, dict):
            return item.get("metadata") or {}

        return getattr(item, "metadata", None) or {}
