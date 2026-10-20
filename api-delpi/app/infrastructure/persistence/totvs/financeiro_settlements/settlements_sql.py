"""Parameterized read-only SQL for Protheus settlement events.

Sources and joins audited in docs 46/47/48 (rounds L1.3–L1.6, 20/10/2026):

- Fact table: ``FK2010`` (payables) / ``FK1010`` (receivables) — one row per
  settlement event; ``FKx_VALOR`` is the event amount (never ``E1/E2_VALOR``);
  ``FKx_DATA`` is the temporal filter.
- Title bridge: ``FK7010`` via ``FK7_IDDOC = FKx_IDDOC`` with
  ``FK7_ALIAS = 'SE1'|'SE2'`` (SX9-declared, 8.911/5.578 coverage probes).
- Titles: ``SE2010``/``SE1010`` via the SX9 composite
  (prefix, num, parcela, tipo, clifor, loja, filial=FK7_FILTIT).
- Nature: ``SED010`` via ``ED_CODIGO = FKx_NATURE``.
- Every JOIN is LEFT so events without document/nature survive with
  ``linkStatus`` flags — never silently dropped.
- ``FK5``/``FKA`` stay out: identifier coincidence alone proves nothing.

All filters are bound parameters; ``sort_by`` reaches SQL only through the
whitelist below.
"""

from __future__ import annotations

SETTLEMENT_SELECT = """
    LTRIM(RTRIM(F.{id_field})) AS settlement_id,
    LTRIM(RTRIM(F.{date_field})) AS settlement_date,
    CAST(F.{amount_field} AS DECIMAL(18, 2)) AS settlement_amount,
    LTRIM(RTRIM(F.{currency_field})) AS currency_code,
    LTRIM(RTRIM(F.{nature_field})) AS nature_code,
    LTRIM(RTRIM(N.ED_DESCRIC)) AS nature_description,
    LTRIM(RTRIM(T.FK7_NUM)) AS document_number,
    LTRIM(RTRIM(T.FK7_PREFIX)) AS prefix,
    LTRIM(RTRIM(T.FK7_PARCEL)) AS installment,
    LTRIM(RTRIM(T.FK7_TIPO)) AS document_type,
    LTRIM(RTRIM(T.FK7_CLIFOR)) AS party_code,
    LTRIM(RTRIM(T.FK7_LOJA)) AS party_store,
    LTRIM(RTRIM(TITLE.{party_name_field})) AS party_name,
    LTRIM(RTRIM(TITLE.{issue_field})) AS issue_date,
    LTRIM(RTRIM(TITLE.{due_field})) AS due_date,
    LTRIM(RTRIM(F.{history_field})) AS history,
    LTRIM(RTRIM(F.{tpdoc_field})) AS movement_type,
    LTRIM(RTRIM(F.{recpag_field})) AS payment_direction,
    LTRIM(RTRIM(F.{filial_field})) AS source_branch,
    CASE WHEN T.FK7_IDDOC IS NULL THEN 1 ELSE 0 END AS missing_document,
    CASE WHEN N.ED_CODIGO IS NULL THEN 1 ELSE 0 END AS missing_nature
""".strip()

_SIDE_BINDINGS = {
    "payable": {
        "table": "FK2010",
        "title_alias": "SE2",
        "title_table": "SE2010",
        "id_field": "FK2_IDFK2",
        "date_field": "FK2_DATA",
        "amount_field": "FK2_VALOR",
        "currency_field": "FK2_MOEDA",
        "nature_field": "FK2_NATURE",
        "history_field": "FK2_HISTOR",
        "tpdoc_field": "FK2_TPDOC",
        "recpag_field": "FK2_RECPAG",
        "filial_field": "FK2_FILIAL",
        "party_name_field": "E2_NOMFOR",
        "issue_field": "E2_EMISSAO",
        "due_field": "E2_VENCTO",
        "title_prefix": "E2_PREFIXO",
        "title_num": "E2_NUM",
        "title_parcela": "E2_PARCELA",
        "title_tipo": "E2_TIPO",
        "title_clifor": "E2_FORNECE",
        "title_loja": "E2_LOJA",
        "title_filial": "E2_FILIAL",
    },
    "receivable": {
        "table": "FK1010",
        "title_alias": "SE1",
        "title_table": "SE1010",
        "id_field": "FK1_IDFK1",
        "date_field": "FK1_DATA",
        "amount_field": "FK1_VALOR",
        "currency_field": "FK1_MOEDA",
        "nature_field": "FK1_NATURE",
        "history_field": "FK1_HISTOR",
        "tpdoc_field": "FK1_TPDOC",
        "recpag_field": "FK1_RECPAG",
        "filial_field": "FK1_FILIAL",
        "party_name_field": "E1_NOMCLI",
        "issue_field": "E1_EMISSAO",
        "due_field": "E1_VENCTO",
        "title_prefix": "E1_PREFIXO",
        "title_num": "E1_NUM",
        "title_parcela": "E1_PARCELA",
        "title_tipo": "E1_TIPO",
        "title_clifor": "E1_CLIENTE",
        "title_loja": "E1_LOJA",
        "title_filial": "E1_FILIAL",
    },
}

_SORT_COLUMNS = {
    "settlement_date": "F.{date_field}",
    "nature": "F.{nature_field}",
}


def _bindings(side: str) -> dict:
    try:
        return _SIDE_BINDINGS[side]
    except KeyError:
        raise ValueError(f"side inválido: {side!r}")


def _from_clause(b: dict) -> str:
    # FK7 and SED lookups can match >1 row per event (multi-title links,
    # per-branch SED rows) — TOP 1 keeps one row per settlement event;
    # R_E_C_N_O_/ED_FILIAL make the choice deterministic (global SED first).
    return f"""
FROM {b["table"]} F WITH (NOLOCK)
OUTER APPLY (
    SELECT TOP 1 T2.FK7_IDDOC, T2.FK7_PREFIX, T2.FK7_NUM, T2.FK7_PARCEL,
        T2.FK7_TIPO, T2.FK7_CLIFOR, T2.FK7_LOJA, T2.FK7_FILTIT
    FROM FK7010 T2 WITH (NOLOCK)
    WHERE T2.D_E_L_E_T_ = ''
        AND T2.FK7_ALIAS = '{b["title_alias"]}'
        AND T2.FK7_IDDOC = F.FK_IDDOC_PLACEHOLDER
    ORDER BY T2.R_E_C_N_O_
) T
LEFT JOIN {b["title_table"]} TITLE WITH (NOLOCK)
    ON TITLE.D_E_L_E_T_ = ''
    AND TITLE.{b["title_filial"]} = T.FK7_FILTIT
    AND TITLE.{b["title_prefix"]} = T.FK7_PREFIX
    AND TITLE.{b["title_num"]} = T.FK7_NUM
    AND TITLE.{b["title_parcela"]} = T.FK7_PARCEL
    AND TITLE.{b["title_tipo"]} = T.FK7_TIPO
    AND TITLE.{b["title_clifor"]} = T.FK7_CLIFOR
    AND TITLE.{b["title_loja"]} = T.FK7_LOJA
OUTER APPLY (
    SELECT TOP 1 N2.ED_CODIGO, N2.ED_DESCRIC
    FROM SED010 N2 WITH (NOLOCK)
    WHERE N2.D_E_L_E_T_ = ''
        AND N2.ED_CODIGO = F.{b["nature_field"]}
    ORDER BY N2.ED_FILIAL
) N
""".strip()


def _where_and_params(
    b: dict,
    *,
    start_date: str,
    end_date: str,
    nature_code: str | None,
    movement_type: str | None,
) -> tuple[str, list]:
    clauses = [
        "F.D_E_L_E_T_ = ''",
        f"F.{b['date_field']} >= ?",
        f"F.{b['date_field']} <= ?",
    ]
    params: list = [start_date, end_date]
    if nature_code:
        clauses.append(f"F.{b['nature_field']} = ?")
        params.append(nature_code)
    if movement_type:
        clauses.append(f"F.{b['tpdoc_field']} = ?")
        params.append(movement_type)
    return " AND ".join(clauses), params


def _select_block(b: dict) -> str:
    id_doc_field = "FK2_IDDOC" if b["table"] == "FK2010" else "FK1_IDDOC"
    return (
        "SELECT\n"
        + SETTLEMENT_SELECT.format(**b)
        + "\n"
        + _from_clause(b).replace("F.FK_IDDOC_PLACEHOLDER", f"F.{id_doc_field}")
    )


def build_settlements_list_query(
    *,
    side: str,
    start_date: str,
    end_date: str,
    nature_code: str | None = None,
    movement_type: str | None = None,
    sort_by: str,
    sort_dir: str,
    page: int,
    page_size: int,
) -> tuple[str, tuple]:
    b = _bindings(side)
    where, params = _where_and_params(
        b,
        start_date=start_date,
        end_date=end_date,
        nature_code=nature_code,
        movement_type=movement_type,
    )
    order_column = _SORT_COLUMNS[sort_by].format(**b)
    direction = "ASC" if sort_dir == "asc" else "DESC"
    offset = (page - 1) * page_size
    query = f"""
{_select_block(b)}
WHERE {where}
ORDER BY {order_column} {direction}, F.{b["id_field"]} {direction}
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
""".strip()
    return query, tuple([*params, offset, page_size])


def build_settlements_count_query(
    *,
    side: str,
    start_date: str,
    end_date: str,
    nature_code: str | None = None,
    movement_type: str | None = None,
) -> tuple[str, tuple]:
    """Count on the fact table only — joins never multiply the total."""
    b = _bindings(side)
    where, params = _where_and_params(
        b,
        start_date=start_date,
        end_date=end_date,
        nature_code=nature_code,
        movement_type=movement_type,
    )
    query = f"""
SELECT COUNT(*) AS total_items
FROM {b["table"]} F WITH (NOLOCK)
WHERE {where}
""".strip()
    return query, tuple(params)


def build_settlements_quality_query(
    *,
    side: str,
    start_date: str,
    end_date: str,
    nature_code: str | None = None,
    movement_type: str | None = None,
) -> tuple[str, tuple]:
    """Missing FK7/SED counters over the filtered set — never drops rows."""
    b = _bindings(side)
    where, params = _where_and_params(
        b,
        start_date=start_date,
        end_date=end_date,
        nature_code=nature_code,
        movement_type=movement_type,
    )
    id_doc_field = "FK2_IDDOC" if b["table"] == "FK2010" else "FK1_IDDOC"
    query = f"""
SELECT
    COUNT(*) AS total_events,
    SUM(CASE WHEN T.FK7_IDDOC IS NULL THEN 1 ELSE 0 END) AS missing_document,
    SUM(CASE WHEN N.ED_CODIGO IS NULL THEN 1 ELSE 0 END) AS missing_nature,
    SUM(CASE WHEN LTRIM(RTRIM(F.{b["filial_field"]})) = '' THEN 1 ELSE 0 END)
        AS unresolved_branch
FROM {b["table"]} F WITH (NOLOCK)
OUTER APPLY (
    SELECT TOP 1 T2.FK7_IDDOC
    FROM FK7010 T2 WITH (NOLOCK)
    WHERE T2.D_E_L_E_T_ = ''
        AND T2.FK7_ALIAS = '{b["title_alias"]}'
        AND T2.FK7_IDDOC = F.{id_doc_field}
    ORDER BY T2.R_E_C_N_O_
) T
OUTER APPLY (
    SELECT TOP 1 N2.ED_CODIGO
    FROM SED010 N2 WITH (NOLOCK)
    WHERE N2.D_E_L_E_T_ = ''
        AND N2.ED_CODIGO = F.{b["nature_field"]}
    ORDER BY N2.ED_FILIAL
) N
WHERE {where}
""".strip()
    return query, tuple(params)


def _summary_side_block(b: dict, side: str) -> str:
    return f"""
SELECT
    '{side}' AS side,
    LTRIM(RTRIM(F.{b["currency_field"]})) AS currency_code,
    LTRIM(RTRIM(F.{b["nature_field"]})) AS nature_code,
    LTRIM(RTRIM(F.{b["tpdoc_field"]})) AS movement_type,
    COUNT(*) AS event_count,
    CAST(SUM(F.{b["amount_field"]}) AS DECIMAL(18, 2)) AS total_amount
FROM {b["table"]} F WITH (NOLOCK)
WHERE F.D_E_L_E_T_ = ''
    AND F.{b["date_field"]} >= ?
    AND F.{b["date_field"]} <= ?
    {{nature_filter}}
    {{movement_filter}}
GROUP BY LTRIM(RTRIM(F.{b["currency_field"]})),
    LTRIM(RTRIM(F.{b["nature_field"]})),
    LTRIM(RTRIM(F.{b["tpdoc_field"]}))
""".strip()


def build_settlements_summary_query(
    *,
    start_date: str,
    end_date: str,
    nature_code: str | None = None,
    movement_type: str | None = None,
) -> tuple[str, tuple]:
    """Grouped totals per side/currency/nature/movement — no merged official
    total while movement semantics stay unclassified (doc 48 D4)."""
    params: list = []
    blocks = []
    for side in ("payable", "receivable"):
        b = _bindings(side)
        block = _summary_side_block(b, side)
        block = block.replace(
            "{nature_filter}",
            f"AND F.{b['nature_field']} = ?" if nature_code else "",
        )
        block = block.replace(
            "{movement_filter}",
            f"AND F.{b['tpdoc_field']} = ?" if movement_type else "",
        )
        blocks.append(block)
        params.extend([start_date, end_date])
        if nature_code:
            params.append(nature_code)
        if movement_type:
            params.append(movement_type)
    query = "\nUNION ALL\n".join(blocks)
    query += "\nORDER BY side, currency_code, nature_code, movement_type"
    return query, tuple(params)


def build_nature_descriptions_query(
    *, nature_codes: tuple[str, ...]
) -> tuple[str, tuple]:
    placeholders = ", ".join("?" for _ in nature_codes)
    # SED can hold per-branch duplicates; DESC order makes the global
    # (ED_FILIAL='') row the last one, so dict last-wins stays deterministic.
    query = f"""
SELECT LTRIM(RTRIM(ED_CODIGO)) AS nature_code,
    LTRIM(RTRIM(ED_DESCRIC)) AS nature_description
FROM SED010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = ''
    AND ED_CODIGO IN ({placeholders})
ORDER BY ED_FILIAL DESC
""".strip()
    return query, tuple(nature_codes)


def build_movement_descriptions_query(
    *, movement_types: tuple[str, ...]
) -> tuple[str, tuple]:
    """FKB010 is the canonical catalog for FKx_TPDOC codes (X3_VALID
    ``ExistCpo("FKB")``). Same per-branch duplication as SED: DESC order
    keeps the global (FKB_FILIAL='') description as dict last-wins."""
    placeholders = ", ".join("?" for _ in movement_types)
    query = f"""
SELECT LTRIM(RTRIM(FKB_TPDOC)) AS movement_type,
    LTRIM(RTRIM(FKB_DESCR)) AS movement_description
FROM FKB010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = ''
    AND FKB_TPDOC IN ({placeholders})
ORDER BY FKB_FILIAL DESC
""".strip()
    return query, tuple(movement_types)
