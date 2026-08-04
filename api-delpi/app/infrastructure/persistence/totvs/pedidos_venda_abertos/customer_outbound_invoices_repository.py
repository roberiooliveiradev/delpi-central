"""
Notas fiscais de saída por cliente (código + loja).

Fonte confirmada (INFORMATION_SCHEMA + SQL existentes no monorepo):
- Itens: SD2010 (D2_*)
- Cabeçalho: SF2010 (F2_*) — join obrigatório; soft-delete exclui canceladas
- Pedido cliente: SC5010.C5_PEDCLI via D2_PEDIDO
- Produto: SB1010
- Nome: SA1010

Totalização:
- valor da nota = F2_VALBRUT (cabeçalho), uma vez por (filial, doc, série)
- valor_total_faturado = soma dos totais de notas com situation != return (D2/F2 tipo D)

Cancelamento:
- registros com D_E_L_E_T_ preenchido não entram (soft-delete Protheus)
- não há campo de “cancelada viva” confirmado (F2_DAUTORI ausente)
"""

from __future__ import annotations

import math
from typing import Any, Optional

from app.domain.entities.pedidos_venda_abertos.customer_outbound_invoice import (
    CustomerOutboundInvoice,
    CustomerOutboundInvoiceItem,
    CustomerOutboundInvoiceSummary,
    CustomerOutboundInvoicesPage,
)
from app.domain.ports.pedidos_venda_abertos.customer_outbound_invoices_repository_port import (
    CustomerOutboundInvoicesRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pagination import paginate


def _trim(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_float(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _iso_date(value: Any) -> str:
    text = _trim(value)
    if not text:
        return ""
    if len(text) >= 10 and text[4] == "-":
        return text[:10]
    # Protheus AAAAMMDD
    if len(text) >= 8 and text[:8].isdigit():
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text


def map_situation(doc_type: str) -> str:
    """Mapeia F2_TIPO/D2_TIPO confirmados no ambiente (N/B/D/P/I/C)."""
    normalized = _trim(doc_type).upper()
    if normalized == "D":
        return "return"
    return "emitted"


class CustomerOutboundInvoicesRepository(
    BaseRepository,
    CustomerOutboundInvoicesRepositoryPort,
):
    def list_customer_outbound_invoices(
        self,
        *,
        customer_code: str,
        customer_store: str,
        start_date: str,
        end_date: str,
        page: int,
        page_size: int,
        situation: Optional[str],
        search: Optional[str],
    ) -> CustomerOutboundInvoicesPage:
        paging = paginate(page, page_size)
        code = _trim(customer_code)
        store = _trim(customer_store)
        search_term = _trim(search) if search else ""
        situation_filter = _trim(situation).lower() if situation else "all"

        base_params: list[Any] = [code, store, start_date, end_date]
        search_sql = ""
        if search_term:
            like = f"%{search_term}%"
            search_sql = """
                AND (
                    D2.D2_DOC LIKE ?
                    OR D2.D2_SERIE LIKE ?
                    OR D2.D2_PEDIDO LIKE ?
                    OR D2.D2_COD LIKE ?
                    OR ISNULL(C5.C5_PEDCLI, '') LIKE ?
                )
            """
            base_params.extend([like, like, like, like, like])

        situation_sql = ""
        if situation_filter == "emitted":
            situation_sql = "AND ISNULL(F2.F2_TIPO, '') <> 'D'"
        elif situation_filter in ("return", "devolucao", "devolução"):
            situation_sql = "AND ISNULL(F2.F2_TIPO, '') = 'D'"

        notes_cte = f"""
            WITH note_base AS (
                SELECT
                    D2.D2_FILIAL AS branch,
                    D2.D2_DOC AS invoice_number,
                    D2.D2_SERIE AS invoice_series,
                    MAX(D2.D2_EMISSAO) AS issue_date_raw,
                    MAX(D2.D2_CLIENTE) AS customer_code,
                    MAX(D2.D2_LOJA) AS customer_store,
                    MAX(ISNULL(F2.F2_TIPO, D2.D2_TIPO)) AS doc_type,
                    MAX(CONVERT(FLOAT, ISNULL(F2.F2_VALBRUT, 0))) AS header_total,
                    SUM(CONVERT(FLOAT, ISNULL(D2.D2_TOTAL, 0))) AS lines_total,
                    COUNT(*) AS item_count,
                    MAX(RTRIM(ISNULL(D2.D2_PEDIDO, ''))) AS sales_order_sample,
                    MAX(RTRIM(ISNULL(C5.C5_PEDCLI, ''))) AS customer_order_sample,
                    MAX(RTRIM(ISNULL(SA1.A1_NREDUZ, ISNULL(SA1.A1_NOME, '')))) AS customer_name,
                    MAX(RTRIM(ISNULL(F2.F2_CHVNFE, ''))) AS access_key,
                    MAX(RTRIM(ISNULL(F2.F2_TRANSP, ''))) AS carrier
                FROM SD2010 D2 WITH (NOLOCK)
                INNER JOIN SF2010 F2 WITH (NOLOCK)
                    ON F2.F2_FILIAL = D2.D2_FILIAL
                    AND F2.F2_DOC = D2.D2_DOC
                    AND F2.F2_SERIE = D2.D2_SERIE
                    AND F2.D_E_L_E_T_ = ''
                LEFT JOIN SA1010 SA1 WITH (NOLOCK)
                    ON SA1.A1_COD = D2.D2_CLIENTE
                    AND SA1.A1_LOJA = D2.D2_LOJA
                    AND SA1.D_E_L_E_T_ = ''
                LEFT JOIN SC5010 C5 WITH (NOLOCK)
                    ON C5.C5_FILIAL = D2.D2_FILIAL
                    AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(D2.D2_PEDIDO))
                    AND C5.D_E_L_E_T_ = ''
                WHERE D2.D_E_L_E_T_ = ''
                    AND D2.D2_CLIENTE = ?
                    AND D2.D2_LOJA = ?
                    AND D2.D2_EMISSAO >= ?
                    AND D2.D2_EMISSAO <= ?
                    {search_sql}
                    {situation_sql}
                GROUP BY D2.D2_FILIAL, D2.D2_DOC, D2.D2_SERIE
            )
        """

        summary_sql = notes_cte + """
            SELECT
                COUNT(*) AS invoice_count,
                ISNULL(SUM(
                    CASE
                        WHEN ISNULL(doc_type, '') = 'D' THEN 0
                        ELSE CASE
                            WHEN header_total > 0 THEN header_total
                            ELSE lines_total
                        END
                    END
                ), 0) AS total_billed_value,
                MAX(issue_date_raw) AS last_invoice_date_raw
            FROM note_base
        """

        count_sql = notes_cte + """
            SELECT COUNT(*) AS total FROM note_base
        """

        page_sql = notes_cte + """
            SELECT
                branch,
                invoice_number,
                invoice_series,
                issue_date_raw,
                customer_code,
                customer_store,
                customer_name,
                doc_type,
                header_total,
                lines_total,
                item_count,
                sales_order_sample,
                customer_order_sample,
                access_key,
                carrier
            FROM note_base
            ORDER BY issue_date_raw DESC, invoice_number DESC, invoice_series DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:
            summary_row = repo.execute_one(summary_sql, tuple(base_params)) or {}
            total_row = repo.execute_one(count_sql, tuple(base_params)) or {}
            total = int(total_row.get("total") or 0)

            page_rows = repo.execute_query(
                page_sql,
                tuple(base_params + [paging["offset"], paging["page_size"]]),
            )

            invoices: list[CustomerOutboundInvoice] = []
            if page_rows:
                keys = [
                    (
                        _trim(row.get("branch")),
                        _trim(row.get("invoice_number")),
                        _trim(row.get("invoice_series")),
                    )
                    for row in page_rows
                ]
                items_by_key = self._load_items(repo, code, store, keys)

                last_date = _iso_date(summary_row.get("last_invoice_date_raw"))
                last_value: Optional[float] = None
                for row in page_rows:
                    if _iso_date(row.get("issue_date_raw")) == last_date:
                        header_total = _to_float(row.get("header_total"))
                        lines_total = _to_float(row.get("lines_total"))
                        last_value = header_total if header_total > 0 else lines_total
                        break

                # Se a última nota não está na página atual, buscar valor à parte
                if last_date and last_value is None:
                    last_value = self._last_invoice_value(
                        repo, code, store, start_date, end_date, last_date, search_sql, situation_sql, base_params
                    )

                for row in page_rows:
                    branch = _trim(row.get("branch"))
                    number = _trim(row.get("invoice_number"))
                    series = _trim(row.get("invoice_series"))
                    key = f"{branch}|{number}|{series}"
                    header_total = _to_float(row.get("header_total"))
                    lines_total = _to_float(row.get("lines_total"))
                    total_value = header_total if header_total > 0 else lines_total
                    items = items_by_key.get(key, ())
                    invoices.append(
                        CustomerOutboundInvoice(
                            key=key,
                            branch=branch,
                            invoice_number=number,
                            invoice_series=series,
                            issue_date=_iso_date(row.get("issue_date_raw")),
                            customer_code=_trim(row.get("customer_code")),
                            customer_store=_trim(row.get("customer_store")),
                            customer_name=_trim(row.get("customer_name")),
                            total_value=total_value,
                            situation=map_situation(_trim(row.get("doc_type"))),
                            sales_order=_trim(row.get("sales_order_sample")),
                            customer_order=_trim(row.get("customer_order_sample")),
                            item_count=int(row.get("item_count") or len(items)),
                            access_key=_trim(row.get("access_key")) or None,
                            carrier=_trim(row.get("carrier")) or None,
                            items=items,
                        )
                    )
            else:
                last_date = _iso_date(summary_row.get("last_invoice_date_raw"))
                last_value = None

            # Recalcular last_invoice_value a partir do summary date quando há notas
            if page_rows and last_date:
                for inv in invoices:
                    if inv.issue_date == last_date:
                        last_value = inv.total_value
                        break

            summary = CustomerOutboundInvoiceSummary(
                total_billed_value=_to_float(summary_row.get("total_billed_value")),
                invoice_count=int(summary_row.get("invoice_count") or 0),
                last_invoice_date=last_date or None,
                last_invoice_value=last_value,
            )

        total_pages = math.ceil(total / paging["page_size"]) if total > 0 else 0
        return CustomerOutboundInvoicesPage(
            summary=summary,
            invoices=tuple(invoices),
            page=paging["page"],
            page_size=paging["page_size"],
            total=total,
            total_pages=total_pages,
        )

    def _load_items(
        self,
        repo: BaseRepository,
        customer_code: str,
        customer_store: str,
        keys: list[tuple[str, str, str]],
    ) -> dict[str, tuple[CustomerOutboundInvoiceItem, ...]]:
        if not keys:
            return {}

        clauses: list[str] = []
        params: list[Any] = [customer_code, customer_store]
        for branch, number, series in keys:
            clauses.append("(D2.D2_FILIAL = ? AND D2.D2_DOC = ? AND D2.D2_SERIE = ?)")
            params.extend([branch, number, series])

        sql = f"""
            SELECT
                D2.D2_FILIAL AS branch,
                D2.D2_DOC AS invoice_number,
                D2.D2_SERIE AS invoice_series,
                D2.D2_ITEM AS item,
                D2.D2_COD AS product_code,
                RTRIM(ISNULL(SB1.B1_DESC, '')) AS product_description,
                CONVERT(FLOAT, ISNULL(D2.D2_QUANT, 0)) AS quantity,
                RTRIM(ISNULL(SB1.B1_UM, '')) AS unit,
                CONVERT(FLOAT, ISNULL(D2.D2_PRCVEN, 0)) AS unit_price,
                CONVERT(FLOAT, ISNULL(D2.D2_TOTAL, 0)) AS total_value,
                RTRIM(ISNULL(D2.D2_PEDIDO, '')) AS sales_order,
                RTRIM(ISNULL(D2.D2_ITEMPV, '')) AS sales_order_item,
                RTRIM(ISNULL(C5.C5_PEDCLI, '')) AS customer_order
            FROM SD2010 D2 WITH (NOLOCK)
            LEFT JOIN SB1010 SB1 WITH (NOLOCK)
                ON SB1.B1_COD = D2.D2_COD
                AND SB1.D_E_L_E_T_ = ''
            LEFT JOIN SC5010 C5 WITH (NOLOCK)
                ON C5.C5_FILIAL = D2.D2_FILIAL
                AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(D2.D2_PEDIDO))
                AND C5.D_E_L_E_T_ = ''
            WHERE D2.D_E_L_E_T_ = ''
                AND D2.D2_CLIENTE = ?
                AND D2.D2_LOJA = ?
                AND ({' OR '.join(clauses)})
            ORDER BY D2.D2_FILIAL, D2.D2_DOC, D2.D2_SERIE, D2.D2_ITEM
        """
        rows = repo.execute_query(sql, tuple(params))
        grouped: dict[str, list[CustomerOutboundInvoiceItem]] = {}
        for row in rows:
            key = (
                f"{_trim(row.get('branch'))}|{_trim(row.get('invoice_number'))}|"
                f"{_trim(row.get('invoice_series'))}"
            )
            grouped.setdefault(key, []).append(
                CustomerOutboundInvoiceItem(
                    item=_trim(row.get("item")),
                    product_code=_trim(row.get("product_code")),
                    product_description=_trim(row.get("product_description")),
                    quantity=_to_float(row.get("quantity")),
                    unit=_trim(row.get("unit")),
                    unit_price=_to_float(row.get("unit_price")),
                    total_value=_to_float(row.get("total_value")),
                    sales_order=_trim(row.get("sales_order")),
                    sales_order_item=_trim(row.get("sales_order_item")),
                    customer_order=_trim(row.get("customer_order")),
                )
            )
        return {key: tuple(items) for key, items in grouped.items()}

    def _last_invoice_value(
        self,
        repo: BaseRepository,
        customer_code: str,
        customer_store: str,
        start_date: str,
        end_date: str,
        last_date: str,
        search_sql: str,
        situation_sql: str,
        base_params: list[Any],
    ) -> Optional[float]:
        # Converte ISO para AAAAMMDD se necessário para comparar com D2_EMISSAO
        raw_date = last_date.replace("-", "") if "-" in last_date else last_date
        sql = f"""
            SELECT TOP 1
                CASE
                    WHEN CONVERT(FLOAT, ISNULL(F2.F2_VALBRUT, 0)) > 0
                    THEN CONVERT(FLOAT, ISNULL(F2.F2_VALBRUT, 0))
                    ELSE SUM(CONVERT(FLOAT, ISNULL(D2.D2_TOTAL, 0)))
                END AS total_value
            FROM SD2010 D2 WITH (NOLOCK)
            INNER JOIN SF2010 F2 WITH (NOLOCK)
                ON F2.F2_FILIAL = D2.D2_FILIAL
                AND F2.F2_DOC = D2.D2_DOC
                AND F2.F2_SERIE = D2.D2_SERIE
                AND F2.D_E_L_E_T_ = ''
            LEFT JOIN SC5010 C5 WITH (NOLOCK)
                ON C5.C5_FILIAL = D2.D2_FILIAL
                AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(D2.D2_PEDIDO))
                AND C5.D_E_L_E_T_ = ''
            WHERE D2.D_E_L_E_T_ = ''
                AND D2.D2_CLIENTE = ?
                AND D2.D2_LOJA = ?
                AND D2.D2_EMISSAO >= ?
                AND D2.D2_EMISSAO <= ?
                AND D2.D2_EMISSAO = ?
                {search_sql}
                {situation_sql}
            GROUP BY D2.D2_FILIAL, D2.D2_DOC, D2.D2_SERIE, F2.F2_VALBRUT
            ORDER BY D2.D2_DOC DESC
        """
        params = list(base_params) + [raw_date]
        row = repo.execute_one(sql, tuple(params))
        if not row:
            return None
        return _to_float(row.get("total_value"))
