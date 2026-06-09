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
    # Pares "Rótulo: valor" / "Rótulo = valor" vindos do drill-down de linha
    # (ex.: "A1 cod: 000167; A1 nome: CARLOS ..."). O em dash separa o verbo do
    # conteúdo e fica fora da classe de caracteres do rótulo.
    _VALUE_FILTER_PAIR_RE = re.compile(
        r"([0-9A-Za-zÀ-ÿ][0-9A-Za-zÀ-ÿ _.]*?)\s*[:=]\s*([^;]+?)(?:\s*;|\s*$)"
    )
    _CODE_LIKE_COLUMN_RE = re.compile(
        r"(COD|CODIGO|^ID$|_ID$|NUM|SKU|PRODUTO|PRODUCT|CHAVE)",
    )
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
    _SA1_AUTHORING_COLUMN_DEFINITIONS: dict[str, dict[str, Any]] = {
        "cidade": {
            "aliases": ("cidade", "municipio", "município", "mun"),
            "select": "A1_MUN AS CIDADE",
            "group_by": "A1_MUN",
            "result_alias": "CIDADE",
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
        if cls.resolve(message, previous_messages=previous_messages) is not None:
            return True

        return cls._looks_like_incremental_authoring(
            message,
            previous_messages=previous_messages,
        )

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

        from app.domain.services.chat_sql_memory_workspace_service import (
            ChatSqlMemoryWorkspaceService,
        )

        stored_sql = ChatSqlMemoryWorkspaceService.resolve_current_sql(
            message=message,
            previous_messages=previous_messages,
        )

        recent = cls.collect_recent_sql_execution(previous_messages)
        active_sql = stored_sql or (recent.sql if recent else None)

        if not active_sql:
            return None

        title = recent.title if recent else "Consulta SQL (elaboração)"
        mode = cls._resolve_refinement_mode(
            normalized,
            has_recent_execution=bool(recent),
        )

        if cls._looks_like_remove_branch_filter(normalized):
            updated = cls.remove_branch_filter(active_sql)

            if updated != active_sql:
                return SqlQueryRefinement(
                    mode=mode,
                    sql=updated,
                    title=title,
                    reason="Refinamento SQL: filtro de filial removido da consulta anterior.",
                )

        top_limit = cls._extract_top_limit(normalized)

        if top_limit is not None and cls._looks_like_limit_adjustment(normalized):
            updated = cls.apply_top_limit(active_sql, top_limit)

            if updated != active_sql:
                return SqlQueryRefinement(
                    mode=mode,
                    sql=updated,
                    title=title,
                    reason="Refinamento SQL: limite TOP ajustado na consulta anterior.",
                )

        column_key = cls._extract_column_key(normalized, sql=active_sql)

        if column_key and cls._looks_like_add_column(normalized):
            updated = cls.add_column(active_sql, column_key)

            if updated != active_sql:
                return SqlQueryRefinement(
                    mode=mode,
                    sql=updated,
                    title=title,
                    reason="Refinamento SQL: inclusão de coluna solicitada na consulta anterior.",
                )

        if column_key and cls._looks_like_remove_column(normalized):
            updated = cls.remove_column(active_sql, column_key)

            if updated != active_sql:
                return SqlQueryRefinement(
                    mode=mode,
                    sql=updated,
                    title=title,
                    reason="Refinamento SQL: remoção de coluna solicitada na consulta anterior.",
                )

        if cls._looks_like_filter_adjustment(normalized):
            value_filters = cls._extract_value_filters(message, active_sql)

            if value_filters:
                predicates = [
                    f"RTRIM({expr}) = '{cls._escape_sql_literal(value)}'"
                    for expr, value in value_filters
                ]
                updated = cls.apply_value_filters(active_sql, predicates)

                if updated != active_sql:
                    return SqlQueryRefinement(
                        mode=mode,
                        sql=updated,
                        title=title,
                        reason=(
                            "Refinamento SQL: filtro por valor da linha aplicado "
                            "na consulta anterior."
                        ),
                    )

        branches = cls._extract_branch_codes(normalized)

        if branches and cls._looks_like_filter_adjustment(normalized, branches=branches):
            updated = cls.apply_branch_filter(active_sql, branches)

            if updated != active_sql:
                return SqlQueryRefinement(
                    mode=mode,
                    sql=updated,
                    title=title,
                    reason="Refinamento SQL: filtro de filial aplicado na consulta anterior.",
                )

        if cls._looks_like_show_query(normalized):
            return SqlQueryRefinement(
                mode="show_sql",
                sql=active_sql,
                title=title,
                reason="A mensagem solicita exibir a consulta SQL da conversa.",
            )

        if cls._looks_like_branch_breakdown_request(normalized):
            from app.domain.services.chat_sql_production_query_service import (
                ChatSqlProductionQueryService,
            )

            updated = ChatSqlProductionQueryService.expand_production_sql_by_branch(
                active_sql
            )

            if updated != active_sql:
                return SqlQueryRefinement(
                    mode=mode,
                    sql=updated,
                    title=title,
                    reason=(
                        "Refinamento SQL: consulta de programação expandida "
                        "para todas as filiais com coluna FILIAL."
                    ),
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

        if re.search(r"\n\s*FROM\b", sql, flags=re.I):
            updated = re.sub(
                r"(\nFROM\b)",
                f",\n    {select_expr}\n\\1",
                sql,
                count=1,
                flags=re.I,
            )
        elif re.search(r"\bFROM\b", sql, flags=re.I):
            updated = re.sub(
                r"(\bSELECT\s+(?:DISTINCT\s+)?)(.+?)(\s+FROM\b)",
                rf"\1\2, {select_expr}\3",
                sql,
                count=1,
                flags=re.I | re.S,
            )
        else:
            return sql

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
    def apply_value_filters(cls, sql: str, predicates: list[str]) -> str:
        """Acrescenta predicados de igualdade à consulta anterior (WHERE/AND)."""
        clean = [str(predicate).strip() for predicate in predicates if str(predicate).strip()]

        if not clean:
            return sql

        combined = " AND ".join(f"({predicate})" for predicate in clean)

        boundary = re.search(r"\b(GROUP\s+BY|ORDER\s+BY|HAVING)\b", sql, flags=re.I)
        insert_at = boundary.start() if boundary else len(sql)
        head = sql[:insert_at].rstrip()
        tail = sql[insert_at:]

        connector = "AND" if re.search(r"\bWHERE\b", head, flags=re.I) else "WHERE"
        snippet = f"\n  {connector} {combined}"

        if tail.strip():
            return f"{head}{snippet}\n{tail.lstrip(chr(10))}"

        return f"{head}{snippet}"

    @classmethod
    def _extract_value_filters(
        cls,
        message: str | None,
        sql: str,
    ) -> list[tuple[str, str]]:
        """Mapeia pares "rótulo: valor" da linha para colunas reais da consulta."""
        raw = str(message or "")
        columns = cls._sql_selected_columns(sql)

        if not raw or not columns:
            return []

        matched: list[tuple[str, str, str]] = []
        seen: set[str] = set()

        for pair in cls._VALUE_FILTER_PAIR_RE.finditer(raw):
            label = pair.group(1).strip()
            value = pair.group(2).strip().strip("'\"").strip()

            if not value:
                continue

            resolved = cls._match_column_from_label(label, columns)

            if not resolved:
                continue

            key, expr = resolved

            if key in seen:
                continue

            seen.add(key)
            matched.append((key, expr, value))

        if not matched:
            return []

        # Prioriza colunas identificadoras (código/id) para não filtrar por nome,
        # que costuma ter espaços/acentos e zera o resultado.
        code_like = [
            (expr, value)
            for key, expr, value in matched
            if cls._is_code_like_column(key)
        ]

        if code_like:
            return code_like

        return [(expr, value) for _key, expr, value in matched]

    @classmethod
    def _sql_selected_columns(cls, sql: str) -> dict[str, str]:
        """Colunas simples do SELECT mapeadas para a expressão usável no WHERE."""
        match = re.search(r"\bSELECT\b(.*?)\bFROM\b", str(sql or ""), flags=re.I | re.S)

        if not match:
            return {}

        body = re.sub(
            r"^\s*(?:DISTINCT\s+)?(?:TOP\s+\d+\s+)?",
            "",
            match.group(1),
            flags=re.I,
        )

        columns: dict[str, str] = {}

        for item in cls._split_select_items(body):
            expr = item.strip()

            if not expr:
                continue

            alias_match = re.search(
                r"\bAS\b\s+([A-Za-z_][A-Za-z0-9_]*)\s*$",
                expr,
                flags=re.I,
            )
            alias = alias_match.group(1) if alias_match else None

            if alias_match:
                expr = expr[: alias_match.start()].strip()

            simple = re.fullmatch(
                r"([A-Za-z_][A-Za-z0-9_]*\.)?([A-Za-z_][A-Za-z0-9_]*)",
                expr,
            )

            if simple:
                columns[simple.group(2).upper()] = expr

                if alias:
                    columns[alias.upper()] = expr

        return columns

    @staticmethod
    def _split_select_items(body: str) -> list[str]:
        items: list[str] = []
        depth = 0
        current: list[str] = []

        for char in body:
            if char == "(":
                depth += 1
            elif char == ")":
                depth = max(0, depth - 1)

            if char == "," and depth == 0:
                items.append("".join(current))
                current = []
            else:
                current.append(char)

        if current:
            items.append("".join(current))

        return items

    @classmethod
    def _match_column_from_label(
        cls,
        label: str,
        columns: dict[str, str],
    ) -> tuple[str, str] | None:
        words = re.findall(r"[0-9A-Za-zÀ-ÿ]+", str(label or ""))

        if not words:
            return None

        for size in range(min(4, len(words)), 0, -1):
            candidate = "_".join(words[-size:]).upper()

            if candidate in columns:
                return candidate, columns[candidate]

        return None

    @classmethod
    def _is_code_like_column(cls, column_key: str) -> bool:
        return bool(cls._CODE_LIKE_COLUMN_RE.search(str(column_key or "").upper()))

    @staticmethod
    def _escape_sql_literal(value: str) -> str:
        return str(value or "").replace("'", "''")

    @classmethod
    def apply_top_limit(cls, sql: str, limit: int) -> str:
        bounded = max(1, min(int(limit), 500))

        if re.search(r"\bSELECT\s+TOP\s+\d+\b", sql, flags=re.I):
            return re.sub(
                r"(\bSELECT\s+TOP\s+)\d+",
                rf"\g<1>{bounded}",
                sql,
                count=1,
                flags=re.I,
            )

        return re.sub(
            r"(\bSELECT\s+)(?:DISTINCT\s+)?",
            rf"\1TOP {bounded} ",
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

        definitions = dict(cls._COLUMN_DEFINITIONS)

        if re.search(r"\bSA1\b", str(sql or ""), flags=re.I):
            definitions.update(cls._SA1_AUTHORING_COLUMN_DEFINITIONS)

        return definitions

    @classmethod
    def _resolve_refinement_mode(
        cls,
        normalized: str,
        *,
        has_recent_execution: bool,
    ) -> SqlRefinementMode:
        if cls._is_authoring_only(normalized) or not has_recent_execution:
            return "show_sql"

        return "execute"

    @classmethod
    def _is_authoring_only(cls, normalized: str) -> bool:
        return any(
            term in normalized
            for term in (
                "sem executar",
                "sem rodar",
                "nao execute",
                "não execute",
                "somente a query",
                "so a query",
                "só a query",
                "apenas a query",
                "nao rodar",
                "não rodar",
            )
        )

    @classmethod
    def _looks_like_incremental_authoring(
        cls,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        from app.domain.services.chat_sql_memory_workspace_service import (
            ChatSqlMemoryWorkspaceService,
        )

        if not ChatSqlMemoryWorkspaceService.resolve_current_sql(
            message=message,
            previous_messages=previous_messages,
        ):
            return False

        incremental_terms = (
            *cls._ADD_TERMS,
            *cls._ALTER_TERMS,
            *cls._FILTER_TERMS,
            "consulta anterior",
            "query anterior",
            "sql anterior",
            "primeiros",
            "primeiras",
        )

        if cls._extract_top_limit(normalized) is not None:
            return True

        return any(term in normalized for term in incremental_terms)

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
    def _looks_like_branch_breakdown_request(cls, normalized: str) -> bool:
        from app.domain.services.chat_sql_production_query_service import (
            ChatSqlProductionQueryService,
        )

        if not ChatSqlProductionQueryService.wants_branch_breakdown(normalized):
            return False

        return not cls._extract_branch_codes(normalized)

    @classmethod
    def _looks_like_limit_adjustment(cls, normalized: str) -> bool:
        return cls._extract_top_limit(normalized) is not None and (
            "top" in normalized
            or any(term in normalized for term in cls._ALTER_TERMS + cls._FILTER_TERMS)
            or re.search(r"\b\d{1,3}\s+produtos?\b", normalized)
            or re.search(r"\b\d{1,3}\s+registros?\b", normalized)
            or re.search(r"\b\d{1,3}\s+primeir[oa]s?\b", normalized)
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

        match = re.search(r"\b(\d{1,3})\s+primeir[oa]s?\b", normalized)

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
