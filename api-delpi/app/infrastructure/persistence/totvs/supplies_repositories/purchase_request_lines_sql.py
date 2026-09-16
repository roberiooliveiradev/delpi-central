"""SQL builders — purchase request lines (SC1) with SC7/SD1 batch companions."""

from __future__ import annotations

from app.domain.services.pagination_tier_service import PaginationTierService
from app.domain.totvs.protheus_branches import normalize_branch_code

from datetime import date, timedelta
from typing import Iterable

from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_sql import (
    branch_filter_and,
)

PURCHASE_REQUESTS_SORT_FIELDS: tuple[str, ...] = (
    "request_number",
    "issue_date",
    "requester",
    "cost_center",
    "request_item",
    "product_code",
    "product_description",
)

DEFAULT_LOOKBACK_DAYS = 90
MAX_PAGE_SIZE = int(PaginationTierService.max_size("page_50_200") or 0)
DEFAULT_PAGE_SIZE = PaginationTierService.require_int("page_50_200", None)
def default_date_range(
    *,
    date_from: str | None,
    date_to: str | None,
    reference: date | None = None,
) -> tuple[str, str]:
    today = reference or date.today()
    end = date_to or today.isoformat()
    if date_from:
        return date_from, end
    start = (today - timedelta(days=DEFAULT_LOOKBACK_DAYS)).isoformat()
    return start, end


def _protheus_date_param(iso_date: str) -> str:
    return iso_date.replace("-", "")


def normalize_purchase_request_branches(
    *,
    branch: str | None = None,
    branches: list[str] | None = None,
) -> list[str]:
    raw: list[str] = []
    if isinstance(branches, str):
        raw = [branches]
    elif branches:
        raw = list(branches)
    if not raw and branch:
        raw = [branch]
    codes: list[str] = []
    seen: set[str] = set()
    for item in raw:
        code = normalize_branch_code(str(item or "").strip())
        if code in seen:
            continue
        seen.add(code)
        codes.append(code)
    if not codes:
        raise ValueError("at least one branch is required")
    return codes


def parse_cost_center_scopes(raw: Iterable[str] | None) -> list[tuple[str, str]]:
    scopes: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in raw or []:
        text = str(item or "").strip()
        if ":" not in text:
            raise ValueError("Invalid cc_scope")
        branch_raw, code = text.split(":", 1)
        branch = normalize_branch_code(branch_raw.strip())
        cost_center = code.strip()
        if not cost_center:
            raise ValueError("Invalid cc_scope")
        key = (branch, cost_center)
        if key in seen:
            continue
        seen.add(key)
        scopes.append(key)
    return scopes


def _branch_in_sql(codes: list[str]) -> tuple[str, list[str]]:
    if len(codes) == 1:
        return "RTRIM(SC1.C1_FILIAL) = ?", codes
    placeholders = ", ".join("?" * len(codes))
    return f"RTRIM(SC1.C1_FILIAL) IN ({placeholders})", codes


def _cost_center_scope_sql(scopes: list[tuple[str, str]]) -> tuple[str, list]:
    grouped: dict[str, list[str]] = {}
    for branch, code in scopes:
        grouped.setdefault(branch, []).append(code)
    clauses: list[str] = []
    params: list = []
    for branch, codes in grouped.items():
        placeholders = ", ".join("?" * len(codes))
        clauses.append(
            f"(RTRIM(SC1.C1_FILIAL) = ? AND RTRIM(SC1.C1_CC) IN ({placeholders}))"
        )
        params.append(branch)
        params.extend(codes)
    return "(" + " OR ".join(clauses) + ")", params


def resolve_purchase_requests_order_by(
    *,
    sort_by: str | None = None,
    sort_dir: str | None = None,
    grain: str = "header",
) -> str:
    key = (sort_by or "").strip()
    direction = (sort_dir or "desc").strip().lower()
    if direction not in {"asc", "desc"}:
        raise ValueError("Invalid sort_dir")
    if grain == "header":
        default = """
        MIN(RTRIM(SC1.C1_EMISSAO)) DESC,
        RTRIM(SC1.C1_NUM) DESC,
        RTRIM(SC1.C1_FILIAL) DESC
        """
        mapping = {
            "request_number": "RTRIM(SC1.C1_NUM)",
            "issue_date": "MIN(RTRIM(SC1.C1_EMISSAO))",
            "requester": "MIN(RTRIM(COALESCE(SC1.C1_SOLICIT, '')))",
            "cost_center": "MIN(RTRIM(ISNULL(SC1.C1_CC, '')))",
            # Header page SQL has no SB1 join — use SC1 description only.
            "request_item": "MIN(RTRIM(SC1.C1_ITEM))",
            "product_code": "MIN(RTRIM(SC1.C1_PRODUTO))",
            "product_description": "MIN(RTRIM(COALESCE(SC1.C1_DESCRI, '')))",
        }
        if not key:
            return default.strip()
        expression = mapping.get(key)
        if expression is None:
            raise ValueError("Invalid sort_by")
        return (
            f"{expression} {direction.upper()}, "
            "RTRIM(SC1.C1_NUM) DESC, RTRIM(SC1.C1_FILIAL) DESC"
        )
    default = "SC1.C1_EMISSAO DESC, SC1.C1_FILIAL ASC, SC1.C1_NUM DESC, SC1.C1_ITEM ASC"
    mapping = {
        "request_number": "SC1.C1_NUM",
        "issue_date": "SC1.C1_EMISSAO",
        "requester": "RTRIM(COALESCE(SC1.C1_SOLICIT, ''))",
        "cost_center": "RTRIM(ISNULL(SC1.C1_CC, ''))",
        "request_item": "RTRIM(SC1.C1_ITEM)",
        "product_code": "RTRIM(SC1.C1_PRODUTO)",
        "product_description": "RTRIM(COALESCE(SB1.B1_DESC, SC1.C1_DESCRI, ''))",
    }
    if not key:
        return default
    expression = mapping.get(key)
    if expression is None:
        raise ValueError("Invalid sort_by")
    return (
        f"{expression} {direction.upper()}, "
        "SC1.C1_FILIAL ASC, SC1.C1_NUM ASC, SC1.C1_ITEM ASC"
    )


def build_purchase_request_lines_filters(
    *,
    branch: str | None = None,
    branches: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    cost_centers: Iterable[str] | None = None,
    cost_center_scopes: Iterable[str] | None = None,
    request_number: str | None = None,
    requester_protheus_user_ids: Iterable[str] | None = None,
    product_code: str | None = None,
    supplier_code: str | None = None,
    order_number: str | None = None,
) -> tuple[str, list]:
    start_iso, end_iso = default_date_range(date_from=date_from, date_to=date_to)
    qb = QueryBuilder()
    codes = normalize_purchase_request_branches(branch=branch, branches=branches)
    if len(codes) == 1 and not cost_center_scopes:
        branch_clause, branch_params = branch_filter_and("RTRIM(SC1.C1_FILIAL)", codes[0])
    else:
        branch_clause, branch_params = _branch_in_sql(codes)
        branch_clause = f"AND {branch_clause}"
    filters = ["SC1.D_E_L_E_T_ = ''"]
    params: list = list(branch_params)
    if branch_clause:
        filters.append(branch_clause.strip().removeprefix("AND ").strip())
    filters.append("RTRIM(SC1.C1_EMISSAO) >= ?")
    params.append(_protheus_date_param(start_iso))
    filters.append("RTRIM(SC1.C1_EMISSAO) <= ?")
    params.append(_protheus_date_param(end_iso))
    if request_number:
        filters.append("RTRIM(SC1.C1_NUM) = ?")
        params.append(request_number.strip())
    if requester_protheus_user_ids:
        ids = [str(item).strip() for item in requester_protheus_user_ids if str(item).strip()]
        if ids:
            placeholders = ", ".join("?" for _ in ids)
            filters.append(f"RTRIM(SC1.C1_USER) IN ({placeholders})")
            params.extend(ids)
    if product_code:
        filters.append("RTRIM(SC1.C1_PRODUTO) = ?")
        params.append(product_code.strip())
    scopes = parse_cost_center_scopes(cost_center_scopes)
    centers = [str(code).strip() for code in (cost_centers or []) if str(code).strip()]
    if scopes:
        cc_clause, cc_params = _cost_center_scope_sql(scopes)
        filters.append(cc_clause)
        params.extend(cc_params)
    elif centers:
        placeholders = ", ".join("?" for _ in centers)
        filters.append(f"RTRIM(SC1.C1_CC) IN ({placeholders})")
        params.extend(centers)
    if supplier_code:
        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM SC7010 SC7F WITH (NOLOCK)
                WHERE SC7F.D_E_L_E_T_ = ''
                  AND RTRIM(SC7F.C7_FILIAL) = RTRIM(SC1.C1_FILIAL)
                  AND RTRIM(SC7F.C7_NUMSC) = RTRIM(SC1.C1_NUM)
                  AND RTRIM(SC7F.C7_ITEMSC) = RTRIM(SC1.C1_ITEM)
                  AND RTRIM(SC7F.C7_FORNECE) = ?
            )
            """.strip()
        )
        params.append(supplier_code.strip())
    if order_number:
        filters.append(
            """
            EXISTS (
                SELECT 1
                FROM SC7010 SC7O WITH (NOLOCK)
                WHERE SC7O.D_E_L_E_T_ = ''
                  AND RTRIM(SC7O.C7_FILIAL) = RTRIM(SC1.C1_FILIAL)
                  AND RTRIM(SC7O.C7_NUMSC) = RTRIM(SC1.C1_NUM)
                  AND RTRIM(SC7O.C7_ITEMSC) = RTRIM(SC1.C1_ITEM)
                  AND RTRIM(SC7O.C7_NUM) = ?
            )
            """.strip()
        )
        params.append(order_number.strip())
    return " AND ".join(filters), params


def build_purchase_request_lines_count_sql(where_clause: str) -> str:
    return f"""
    SELECT COUNT(1) AS total
    FROM SC1010 SC1 WITH (NOLOCK)
    WHERE {where_clause}
    """


def build_purchase_request_headers_count_sql(where_clause: str) -> str:
    return f"""
    SELECT COUNT(1) AS total
    FROM (
        SELECT DISTINCT
            RTRIM(SC1.C1_FILIAL) AS branch,
            RTRIM(SC1.C1_NUM) AS request_number
        FROM SC1010 SC1 WITH (NOLOCK)
        WHERE {where_clause}
    ) AS visible_requests
    """


def build_purchase_request_headers_page_sql(
    *,
    where_clause: str,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> str:
    order_by = resolve_purchase_requests_order_by(
        sort_by=sort_by,
        sort_dir=sort_dir,
        grain="header",
    )
    return f"""
    SELECT
        RTRIM(SC1.C1_FILIAL) AS branch,
        RTRIM(SC1.C1_NUM) AS request_number,
        MIN(RTRIM(SC1.C1_EMISSAO)) AS request_issue_date
    FROM SC1010 SC1 WITH (NOLOCK)
    WHERE {where_clause}
    GROUP BY RTRIM(SC1.C1_FILIAL), RTRIM(SC1.C1_NUM)
    ORDER BY
        {order_by}
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """


def _purchase_request_line_select_sql(where_clause: str) -> str:
    return f"""
    SELECT
        RTRIM(SC1.C1_FILIAL) AS branch,
        RTRIM(SC1.C1_NUM) AS request_number,
        RTRIM(SC1.C1_ITEM) AS request_item,
        RTRIM(SC1.C1_PRODUTO) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, SC1.C1_DESCRI, '')) AS product_description,
        RTRIM(ISNULL(SC1.C1_UM, '')) AS unit,
        CAST(ISNULL(SC1.C1_QUANT, 0) AS FLOAT) AS requested_quantity,
        CAST(ISNULL(SC1.C1_QUJE, 0) AS FLOAT) AS ordered_quantity,
        CAST(
            CASE
                WHEN SC1.C1_QUANT > SC1.C1_QUJE THEN SC1.C1_QUANT - SC1.C1_QUJE
                ELSE 0
            END AS FLOAT
        ) AS request_open_quantity,
        RTRIM(SC1.C1_EMISSAO) AS request_issue_date,
        RTRIM(SC1.C1_DATPRF) AS request_required_date,
        RTRIM(ISNULL(SC1.C1_USER, '')) AS requester_protheus_user_id,
        RTRIM(ISNULL(REQ.USR_CODIGO, '')) AS requester_code,
        RTRIM(COALESCE(SC1.C1_SOLICIT, REQ.USR_NOME, '')) AS requester_name,
        RTRIM(ISNULL(SC1.C1_CC, '')) AS cost_center_code,
        RTRIM(ISNULL(CTT.CTT_DESC01, '')) AS cost_center_description,
        RTRIM(ISNULL(SC1.C1_CONTA, '')) AS account_code,
        RTRIM(ISNULL(SC1.C1_APROV, '')) AS approval_raw,
        RTRIM(ISNULL(SC1.C1_NOMAPRO, '')) AS approver_name,
        CASE WHEN ISNULL(SC1.C1_RESIDUO, '') = 'S' THEN 1 ELSE 0 END AS residual,
        RTRIM(ISNULL(SC1.C1_FORNECE, '')) AS suggested_supplier_code,
        RTRIM(ISNULL(SC1.C1_LOJA, '')) AS suggested_supplier_store,
        RTRIM(COALESCE(SA2.A2_NREDUZ, SA2.A2_NOME, '')) AS suggested_supplier_name
    FROM SC1010 SC1 WITH (NOLOCK)
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SC1.C1_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SYS_USR REQ WITH (NOLOCK)
        ON REQ.USR_ID = SC1.C1_USER
       AND REQ.D_E_L_E_T_ = ''
    LEFT JOIN CTT010 CTT WITH (NOLOCK)
        ON CTT.CTT_FILIAL = SC1.C1_FILIAL
       AND CTT.CTT_CUSTO = SC1.C1_CC
       AND CTT.D_E_L_E_T_ = ''
    LEFT JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = SC1.C1_FORNECE
       AND SA2.A2_LOJA = SC1.C1_LOJA
       AND SA2.D_E_L_E_T_ = ''
    WHERE {where_clause}
    """


def build_purchase_request_lines_for_request_numbers_sql(
    *,
    where_clause: str,
    request_numbers: list[str],
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> tuple[str, list]:
    if not request_numbers:
        return _purchase_request_line_select_sql("1 = 0"), []
    placeholders = ", ".join("?" for _ in request_numbers)
    scoped_where = f"{where_clause} AND RTRIM(SC1.C1_NUM) IN ({placeholders})"
    order_by = resolve_purchase_requests_order_by(
        sort_by=sort_by,
        sort_dir=sort_dir,
        grain="line",
    )
    sql = (
        _purchase_request_line_select_sql(scoped_where)
        + f"""
    ORDER BY {order_by}
    """
    )
    return sql, list(request_numbers)


def build_purchase_request_lines_for_request_keys_sql(
    *,
    where_clause: str,
    request_keys: list[tuple[str, str]],
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> tuple[str, list]:
    if not request_keys:
        return _purchase_request_line_select_sql("1 = 0"), []
    clauses: list[str] = []
    extra: list = []
    for branch, request_number in request_keys:
        clauses.append("(RTRIM(SC1.C1_FILIAL) = ? AND RTRIM(SC1.C1_NUM) = ?)")
        extra.extend([branch, request_number])
    scoped_where = f"{where_clause} AND ({' OR '.join(clauses)})"
    order_by = resolve_purchase_requests_order_by(
        sort_by=sort_by,
        sort_dir=sort_dir,
        grain="line",
    )
    sql = (
        _purchase_request_line_select_sql(scoped_where)
        + f"""
    ORDER BY {order_by}
    """
    )
    return sql, extra


def build_purchase_request_lines_export_sql(
    *,
    where_clause: str,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> str:
    order_by = resolve_purchase_requests_order_by(
        sort_by=sort_by,
        sort_dir=sort_dir,
        grain="line",
    )
    return (
        _purchase_request_line_select_sql(where_clause)
        + f"""
    ORDER BY {order_by}
    """
    )


def build_purchase_request_lines_list_sql(
    *,
    where_clause: str,
    offset: int,
    page_size: int,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> str:
    order_by = resolve_purchase_requests_order_by(
        sort_by=sort_by,
        sort_dir=sort_dir,
        grain="line",
    )
    return (
        _purchase_request_line_select_sql(where_clause)
        + f"""
    ORDER BY {order_by}
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    )


def build_purchase_request_requesters_sql(*, where_clause: str) -> str:
    return f"""
    SELECT DISTINCT
        RTRIM(ISNULL(SC1.C1_USER, '')) AS requester_protheus_user_id,
        RTRIM(ISNULL(REQ.USR_CODIGO, '')) AS requester_code,
        RTRIM(COALESCE(NULLIF(RTRIM(SC1.C1_SOLICIT), ''), REQ.USR_NOME, '')) AS requester_name
    FROM SC1010 SC1 WITH (NOLOCK)
    LEFT JOIN SYS_USR REQ WITH (NOLOCK)
        ON REQ.USR_ID = SC1.C1_USER
       AND REQ.D_E_L_E_T_ = ''
    WHERE {where_clause}
      AND RTRIM(ISNULL(SC1.C1_USER, '')) <> ''
    ORDER BY requester_name ASC, requester_code ASC
    """


def _line_keys_or_clause(keys: list[tuple[str, str, str]]) -> tuple[str, list]:
    if not keys:
        return "1 = 0", []
    clauses: list[str] = []
    params: list = []
    for branch, request_number, request_item in keys:
        clauses.append(
            "(RTRIM(SC7.C7_FILIAL) = ? AND RTRIM(SC7.C7_NUMSC) = ? AND RTRIM(SC7.C7_ITEMSC) = ?)"
        )
        params.extend([branch, request_number, request_item])
    return "(" + " OR ".join(clauses) + ")", params


def build_purchase_orders_for_lines_sql(keys: list[tuple[str, str, str]]) -> tuple[str, list]:
    where_keys, params = _line_keys_or_clause(keys)
    sql = f"""
    SELECT
        RTRIM(SC7.C7_FILIAL) AS branch,
        RTRIM(SC7.C7_NUM) AS order_number,
        RTRIM(SC7.C7_ITEM) AS order_item,
        RTRIM(SC7.C7_NUMSC) AS source_request_number,
        RTRIM(SC7.C7_ITEMSC) AS source_request_item,
        RTRIM(SC7.C7_PRODUTO) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, SC7.C7_DESCRI, '')) AS product_description,
        CAST(ISNULL(SC7.C7_QUANT, 0) AS FLOAT) AS ordered_quantity,
        CAST(ISNULL(SC7.C7_QUJE, 0) AS FLOAT) AS received_quantity,
        CAST(
            CASE
                WHEN SC7.C7_QUANT > SC7.C7_QUJE THEN SC7.C7_QUANT - SC7.C7_QUJE
                ELSE 0
            END AS FLOAT
        ) AS open_quantity,
        RTRIM(SC7.C7_EMISSAO) AS issue_date,
        RTRIM(SC7.C7_DATPRF) AS expected_delivery_date,
        RTRIM(SC7.C7_FORNECE) AS supplier_code,
        RTRIM(SC7.C7_LOJA) AS supplier_store,
        RTRIM(COALESCE(SA2.A2_NREDUZ, SA2.A2_NOME, '')) AS supplier_name,
        RTRIM(ISNULL(SC7.C7_COMPRA, '')) AS buyer_code,
        RTRIM(ISNULL(SC7.C7_USER, '')) AS order_user_protheus_user_id,
        RTRIM(ISNULL(OU.USR_CODIGO, '')) AS order_user_code,
        RTRIM(ISNULL(OU.USR_NOME, '')) AS order_user_name,
        CASE WHEN ISNULL(SC7.C7_RESIDUO, '') = 'S' THEN 1 ELSE 0 END AS residual
    FROM SC7010 SC7 WITH (NOLOCK)
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SC7.C7_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = SC7.C7_FORNECE
       AND SA2.A2_LOJA = SC7.C7_LOJA
       AND SA2.D_E_L_E_T_ = ''
    LEFT JOIN SYS_USR OU WITH (NOLOCK)
        ON OU.USR_ID = SC7.C7_USER
       AND OU.D_E_L_E_T_ = ''
    WHERE SC7.D_E_L_E_T_ = ''
      AND {where_keys}
    ORDER BY SC7.C7_EMISSAO ASC, SC7.C7_NUM ASC, SC7.C7_ITEM ASC
    """
    return sql, params


def build_receipts_for_orders_sql(
    order_keys: list[tuple[str, str, str, str, str, str]],
) -> tuple[str, list]:
    if not order_keys:
        return "SELECT TOP 0 1 AS noop FROM SC7010 SC7", []
    clauses: list[str] = []
    params: list = []
    for branch, order_number, order_item, supplier_code, supplier_store, product_code in order_keys:
        clauses.append(
            """
            (
                RTRIM(SD1.D1_FILIAL) = ?
                AND RTRIM(SD1.D1_PEDIDO) = ?
                AND RTRIM(SD1.D1_FORNECE) = ?
                AND RTRIM(SD1.D1_LOJA) = ?
                AND RTRIM(SD1.D1_COD) = ?
                AND RTRIM(SD1.D1_ITEMPC) = ?
            )
            """.strip()
        )
        params.extend([branch, order_number, supplier_code, supplier_store, product_code, order_item])
    where_keys = " OR ".join(clauses)
    sql = f"""
    SELECT
        RTRIM(SD1.D1_FILIAL) AS branch,
        RTRIM(SD1.D1_DOC) AS invoice_number,
        RTRIM(SD1.D1_SERIE) AS invoice_series,
        RTRIM(SD1.D1_ITEM) AS invoice_item,
        RTRIM(SD1.D1_PEDIDO) AS purchase_order_number,
        RTRIM(SD1.D1_ITEMPC) AS purchase_order_item,
        RTRIM(SD1.D1_COD) AS product_code,
        RTRIM(SD1.D1_FORNECE) AS supplier_code,
        RTRIM(SD1.D1_LOJA) AS supplier_store,
        CAST(ISNULL(SD1.D1_QUANT, 0) AS FLOAT) AS quantity,
        CAST(ISNULL(SD1.D1_VUNIT, 0) AS FLOAT) AS unit_price,
        CAST(ISNULL(SD1.D1_TOTAL, 0) AS FLOAT) AS total_value,
        RTRIM(SD1.D1_EMISSAO) AS invoice_issue_date,
        RTRIM(SD1.D1_DTDIGIT) AS entry_date
    FROM SD1010 SD1 WITH (NOLOCK)
    WHERE SD1.D_E_L_E_T_ = ''
      AND ({where_keys})
    ORDER BY SD1.D1_DTDIGIT ASC, SD1.D1_DOC ASC, SD1.D1_ITEM ASC
    """
    return sql, params
