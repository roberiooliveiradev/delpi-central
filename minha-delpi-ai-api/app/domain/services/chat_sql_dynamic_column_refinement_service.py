"""Motor canônico — agrupar/filtrar por colunas do SELECT da consulta ativa."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_sql_intent_vocabulary_service import (
    ChatSqlIntentVocabularyService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)

DynamicColumnRefinementKind = Literal["group_by", "filter"]


@dataclass(frozen=True)
class SqlDynamicColumnRefinement:
    kind: DynamicColumnRefinementKind
    sql: str
    reason: str
    column_key: str


class ChatSqlDynamicColumnRefinementService:
    _NUMERIC_COLUMN_RE = re.compile(
        r"(QUANT|QTD|VALOR|TOTAL|AMOUNT|NUM|PRECO|PRICE|CUSTO|COST|SALDO|"
        r"STOCK|QTY|_PC$|_PCT|PERCENT|PLANEJAD)",
        re.IGNORECASE,
    )
    _GROUP_BY_PHRASE_RE = re.compile(
        r"(?:agrup(?:ar|a|ado|ada)|group\s*by)\s+(?:por\s+)?(.+?)\??$",
        re.IGNORECASE,
    )
    _TABLE_COLUMN_EXPR: dict[str, dict[str, tuple[str, str]]] = {
        "SC2010": {
            "filial": ("FILIAL", "OP.C2_FILIAL"),
        },
        "SB2010": {
            "filial": ("branch", "SB2.B2_FILIAL"),
            "armazem": ("warehouse", "SB2.B2_LOCAL"),
        },
        "SA1010": {
            "cidade": ("CIDADE", "A1_MUN"),
            "municipio": ("CIDADE", "A1_MUN"),
        },
    }

    @classmethod
    def _group_by_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.group_by_terms()

    @classmethod
    def _filter_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "dynamicColumnRefinement",
            "filterTerms",
        )

    @classmethod
    def _group_by_markers(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "dynamicColumnRefinement",
            "groupByMarkers",
        )

    @classmethod
    def _filter_prefix_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.filter_prefix_terms()

    @classmethod
    def _column_synonyms(cls) -> dict[str, tuple[str, ...]]:
        return ChatSqlIntentVocabularyService.synonym_map(
            "dynamicColumnRefinement",
            "columnSynonyms",
        )

    @classmethod
    def resolve(cls, message: str | None, sql: str | None) -> SqlDynamicColumnRefinement | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        active_sql = str(sql or "").strip()

        if not normalized or not active_sql:
            return None

        group_phrase = cls._extract_group_by_phrase(normalized)

        if group_phrase:
            matched = cls.match_column(group_phrase, active_sql)

            if matched:
                column_key, column_expr = matched
                updated = cls.apply_group_by(active_sql, column_key, column_expr)

                if updated != active_sql:
                    return SqlDynamicColumnRefinement(
                        kind="group_by",
                        sql=updated,
                        column_key=column_key,
                        reason=ExternalActionResponseContentService.format(
                            "sqlColumnRefinement",
                            "groupByColumn",
                            column=cls._human_column_label(column_key),
                        ),
                    )

        filter_match = cls._extract_filter_phrase(message, normalized)

        if filter_match:
            label, value = filter_match
            matched = cls.match_column(label, active_sql)

            if matched and value:
                column_key, column_expr = matched
                updated = cls.apply_filter_equals(active_sql, column_expr, value)

                if updated != active_sql:
                    return SqlDynamicColumnRefinement(
                        kind="filter",
                        sql=updated,
                        column_key=column_key,
                        reason=ExternalActionResponseContentService.format(
                            "sqlColumnRefinement",
                            "filterByColumn",
                            column=cls._human_column_label(column_key),
                            value=value,
                        ),
                    )

        return None

    @classmethod
    def looks_like_dynamic_column_follow_up(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._group_by_terms()):
            return True

        if any(term in normalized for term in cls._filter_terms()):
            return True

        return bool(cls._GROUP_BY_PHRASE_RE.search(normalized))

    @classmethod
    def match_column(cls, phrase: str, sql: str) -> tuple[str, str] | None:
        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        columns = ChatSqlQueryRefinementService.selected_columns(sql)

        if not columns:
            return None

        resolved = ChatSqlQueryRefinementService.match_column_label(phrase, columns)

        if resolved:
            return resolved

        normalized_phrase = ChatMessageNormalizationService.normalize_for_matching(phrase)

        for synonym, keys in cls._column_synonyms().items():
            if synonym not in normalized_phrase:
                continue

            for key in keys:
                if key in columns:
                    return key, columns[key]

        words = re.findall(r"[0-9a-z]+", normalized_phrase)

        for size in range(min(4, len(words)), 0, -1):
            candidate = "_".join(words[-size:]).upper()

            if candidate in columns:
                return candidate, columns[candidate]

        for key, expr in columns.items():
            if normalized_phrase.replace(" ", "_") == key.lower().replace(" ", "_"):
                return key, expr

            key_tokens = re.findall(r"[A-Z0-9]+", key)

            if key_tokens and all(token.lower() in normalized_phrase for token in key_tokens[-2:]):
                return key, expr

        table_match = cls._match_table_expression(normalized_phrase, sql)

        if table_match:
            return table_match

        return None

    @classmethod
    def _match_table_expression(cls, phrase: str, sql: str) -> tuple[str, str] | None:
        normalized_phrase = ChatMessageNormalizationService.normalize_for_matching(phrase)
        sql_upper = str(sql or "").upper()

        for table, synonyms in cls._TABLE_COLUMN_EXPR.items():
            if table not in sql_upper:
                continue

            for synonym, (alias, expr) in synonyms.items():
                if synonym in normalized_phrase:
                    return alias, expr

        return None

    @classmethod
    def apply_group_by(cls, sql: str, column_key: str, column_expr: str) -> str:
        if re.search(rf"\bGROUP BY\b", sql, flags=re.I):
            return cls._append_group_by_existing(sql, column_key, column_expr)

        return cls._introduce_group_by(sql, column_key, column_expr)

    @classmethod
    def apply_filter_equals(cls, sql: str, column_expr: str, value: str) -> str:
        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        literal = ChatSqlQueryRefinementService.escape_sql_literal(value)
        predicate = f"RTRIM({column_expr}) = '{literal}'"

        return ChatSqlQueryRefinementService.apply_value_filters(sql, [predicate])

    @classmethod
    def _extract_group_by_phrase(cls, normalized: str) -> str | None:
        if not any(
            token in normalized
            for token in cls._group_by_markers()
        ):
            return None

        match = cls._GROUP_BY_PHRASE_RE.search(normalized)

        if match:
            return match.group(1).strip()

        for prefix in cls._group_by_terms():
            if prefix in normalized:
                tail = normalized.split(prefix, 1)[1].strip()
                return tail.strip(" ?")

        return None

    @classmethod
    def _extract_filter_phrase(
        cls,
        message: str | None,
        normalized: str,
    ) -> tuple[str, str] | None:
        if not any(term in normalized for term in cls._filter_terms()):
            return None

        tail = normalized

        for prefix in cls._filter_prefix_terms():
            if prefix in tail:
                tail = tail.split(prefix, 1)[1].strip()
                break
        else:
            return None

        if not tail:
            return None

        if "=" in tail or ":" in tail:
            label, value = re.split(r"[:=]", tail, maxsplit=1)
            label = label.strip()
            value = value.strip().strip("'\"").strip()

            if label and value:
                return label, value

            return None

        parts = tail.rsplit(maxsplit=1)

        if len(parts) != 2:
            return None

        label, value = parts[0].strip(), parts[1].strip().strip("'\"").strip()

        if not label or not value:
            return None

        return label, value

    @classmethod
    def _append_group_by_existing(cls, sql: str, column_key: str, column_expr: str) -> str:
        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        updated = sql

        if column_key not in ChatSqlQueryRefinementService.selected_columns(updated):
            updated = cls._append_select_expression(
                updated,
                f"{column_expr} AS {column_key}",
            )

        group_section = re.search(r"\bGROUP BY\b(.+?)(?:\nORDER BY\b|\Z)", updated, flags=re.I | re.S)

        if not group_section:
            return updated

        group_body = group_section.group(1)

        if column_expr in group_body or re.search(rf"\b{re.escape(column_key)}\b", group_body, flags=re.I):
            return updated

        return re.sub(
            r"(\bGROUP BY\s+)(.+?)(\nORDER BY\b|\Z)",
            lambda match: (
                f"{match.group(1)}{match.group(2).rstrip()},\n    {column_expr}{match.group(3)}"
            ),
            updated,
            count=1,
            flags=re.I | re.S,
        )

    @classmethod
    def _introduce_group_by(cls, sql: str, column_key: str, column_expr: str) -> str:
        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        select_match = re.search(r"\bSELECT\b(.*?)\bFROM\b", sql, flags=re.I | re.S)

        if not select_match:
            return sql

        body = re.sub(
            r"^\s*(?:DISTINCT\s+)?(?:TOP\s+\d+\s+)?",
            "",
            select_match.group(1),
            flags=re.I,
        )
        items = ChatSqlQueryRefinementService.split_select_items(body)

        if not items:
            return sql

        group_exprs = [column_expr]
        projected: list[str] = []
        group_expr_upper = column_expr.upper()

        for item in items:
            item = item.strip()
            alias_match = re.search(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", item, flags=re.I)
            alias = alias_match.group(1).upper() if alias_match else None
            bare_expr = item[: alias_match.start()].strip() if alias_match else item

            if bare_expr.upper() == group_expr_upper or alias == column_key.upper():
                projected.append(f"{bare_expr} AS {column_key}")
                continue

            if cls._looks_like_numeric_column(alias or bare_expr):
                projected.append(f"SUM({bare_expr}) AS {alias or column_key}")
                continue

            projected.append(item)
            group_exprs.append(bare_expr)

        select_head = sql[: select_match.start(1)]
        select_tail = sql[select_match.end(1) :]
        new_select_body = ",\n    ".join(projected)
        grouped_sql = f"{select_head}{new_select_body}{select_tail}"

        boundary = re.search(r"\b(ORDER BY|HAVING)\b", grouped_sql, flags=re.I)
        insert_at = boundary.start() if boundary else len(grouped_sql)
        head = grouped_sql[:insert_at].rstrip()
        tail = grouped_sql[insert_at:]
        group_clause = ",\n    ".join(dict.fromkeys(group_exprs))

        if tail.strip():
            return f"{head}\nGROUP BY\n    {group_clause}\n{tail.lstrip(chr(10))}"

        return f"{head}\nGROUP BY\n    {group_clause}"

    @classmethod
    def _append_select_expression(cls, sql: str, select_expr: str) -> str:
        alias_match = re.search(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", select_expr, flags=re.I)
        alias = alias_match.group(1) if alias_match else ""

        if alias and re.search(rf"\bAS\s+{re.escape(alias)}\b", sql, flags=re.I):
            return sql

        if re.search(r"\n\s*FROM\b", sql, flags=re.I):
            return re.sub(
                r"(\nFROM\b)",
                f",\n    {select_expr}\n\\1",
                sql,
                count=1,
                flags=re.I,
            )

        return re.sub(
            r"(\bSELECT\s+(?:DISTINCT\s+)?)(.+?)(\s+FROM\b)",
            rf"\1\2, {select_expr}\3",
            sql,
            count=1,
            flags=re.I | re.S,
        )

    @classmethod
    def _looks_like_numeric_column(cls, token: str | None) -> bool:
        return bool(cls._NUMERIC_COLUMN_RE.search(str(token or "")))

    @classmethod
    def _human_column_label(cls, column_key: str) -> str:
        from app.domain.services.external_actions.external_action_column_label_service import (
            ExternalActionColumnLabelService,
        )

        labels = ExternalActionColumnLabelService()
        return labels.label_for(column_key)
