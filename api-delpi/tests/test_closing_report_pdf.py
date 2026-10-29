"""PDF export policy for the closing analytical reports (CP7).

Covers: the shared renderer emits a valid multi-section PDF with the
parity watermark; the three export use cases serialize the SAME engine
payload (never a header-only fake zero) and never persist anything —
document attachment stays a separate governed workflow (CP9).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.application.dto.financeiro_stock_inventory.stock_inventory_request import (
    StockInventoryQueryRequest,
)
from app.application.dto.financeiro_stock_movements.stock_movements_request import (
    StockMovementsQueryRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScope,
    UnresolvedStockInventoryScopeResolver,
)
from app.application.use_cases.financeiro_reports_export.report_export_common import (
    ReportNotExportableError,
)
from app.application.use_cases.financeiro_stock_inventory.export_stock_inventory_use_case import (
    ExportStockInventoryUseCase,
)
from app.application.use_cases.financeiro_stock_inventory.get_stock_inventory_use_case import (
    GetStockInventoryUseCase,
)
from app.application.use_cases.financeiro_stock_movements.export_stock_movements_use_case import (
    ExportStockMovementsUseCase,
)
from app.application.use_cases.financeiro_stock_movements.get_stock_movements_use_case import (
    GetStockMovementsUseCase,
)
from app.application.use_cases.financeiro_work_in_process.export_work_in_process_use_case import (
    ExportWorkInProcessUseCase,
)
from app.application.use_cases.financeiro_work_in_process.get_work_in_process_use_case import (
    GetWorkInProcessUseCase,
)
from app.infrastructure.pdf.closing_reports.closing_report_pdf import (
    ClosingReportPdfSpec,
    ReportTableSection,
    _cell_text,
    format_money_pt_br,
    format_quantity_pt_br,
    render_closing_report_pdf,
)
from app.interface.http.routes.financeiro.stock_inventory_route_helpers import (
    export_binary_response,
)


@dataclass
class _ResolvedResolver:
    def resolve(self, *, user_subject):
        return StockInventoryScope(resolved=True, reason="test")


# ---------- shared renderer -------------------------------------------

def test_renderer_emits_pdf_with_watermark_and_sections() -> None:
    spec = ClosingReportPdfSpec(
        title="R08 — MATERIAL EM PROCESSO (MATR989)",
        metadata=[
            ("Competência", "2026-09"),
            ("Filial", "01"),
            ("Escopo", "Todos os produtos"),
            ("Referência", "2026-09-30"),
            ("Fonte", "protheus_sb9_sd3_sc2_sb1"),
            ("Paridade", "PENDING"),
        ],
        sections=[
            ReportTableSection(
                title="Material em processo por tipo",
                columns=[("productType", "Tipo"), ("totalValue", "Total (R$)")],
                rows=[{"productType": "MP", "totalValue": "871416.33"}],
                totals_row={"productType": "TOTAL", "totalValue": "871416.33"},
                align_right_keys=frozenset({"totalValue"}),
            )
        ],
        watermark="RELATÓRIO OPERACIONAL — PARIDADE OFICIAL PENDENTE.",
        footer_note="RELATÓRIO OPERACIONAL — PARIDADE OFICIAL PENDENTE.",
    )
    pdf = render_closing_report_pdf(spec, generated_stamp="2026-10-01T00:00:00+00:00")
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 1000
    # Latin-1 encoded text is searchable in the raw stream.
    assert b"MATR989" in pdf
    assert b"PENDENTE" in pdf


def test_renderer_handles_long_table_across_pages() -> None:
    spec = ClosingReportPdfSpec(
        title="P7 — REGISTRO DE INVENTÁRIO",
        metadata=[("Competência", "2026-09")],
        sections=[
            ReportTableSection(
                title="Itens",
                columns=[("productCode", "Produto"), ("value", "Valor")],
                rows=[
                    {"productCode": f"P{i:04d}", "value": f"{i}.00"}
                    for i in range(120)
                ],
                align_right_keys=frozenset({"value"}),
            )
        ],
    )
    pdf = render_closing_report_pdf(spec, generated_stamp="2026-10-01T00:00:00+00:00")
    assert pdf[:5] == b"%PDF-"
    # Multi-page document: more than one /Type /Page object.
    assert pdf.count(b"/Type /Page") >= 2


# ---------- RW-012: presentation quality --------------------------------

def test_money_and_quantity_format_pt_br() -> None:
    section = ReportTableSection(
        title="Totais",
        columns=[("amount", "Valor"), ("qty", "Qtd")],
        rows=[
            {"amount": "14638712.476000", "qty": "39651428.075"},
            {"amount": "-11964.39", "qty": "1"},
            {"amount": "0", "qty": "0"},
            {"amount": None, "qty": None},
        ],
        money_keys=frozenset({"amount"}),
        quantity_keys=frozenset({"qty"}),
    )
    assert _cell_text(section, "amount", "14638712.476000") == (
        "R$ 14.638.712,48"
    )
    assert _cell_text(section, "amount", "-11964.39") == "R$ -11.964,39"
    assert _cell_text(section, "amount", "0") == "R$ 0,00"
    assert _cell_text(section, "amount", None) == "—"
    assert _cell_text(section, "qty", "39651428.075") == "39.651.428,075"
    assert _cell_text(section, "qty", "1") == "1,00"
    # Presentation is display-only — Decimal precision is never fed back.
    assert format_money_pt_br(Decimal("0.005")) == "R$ 0,01"
    assert format_quantity_pt_br("2.5") == "2,50"


def test_long_description_wraps_without_silent_truncation() -> None:
    tail = "Z99TOKENFIM"
    long_desc = "CHICOTE ATERRAMENTO " * 8 + tail  # ~170 chars
    spec = ClosingReportPdfSpec(
        title="P7 — REGISTRO DE INVENTÁRIO",
        metadata=[("Competência", "2026-09")],
        sections=[
            ReportTableSection(
                title="Itens",
                columns=[
                    ("code", "Produto"),
                    ("description", "Descrição"),
                    ("unit", "UM"),
                ],
                rows=[{"code": "P1", "description": long_desc, "unit": "MI"}],
            )
        ],
    )
    pdf = render_closing_report_pdf(spec, generated_stamp="2026-10-01T00:00:00+00:00")
    # The full content must survive — the tail token proves no truncation.
    assert tail.encode() in pdf


def test_pathological_cell_truncates_with_explicit_marker() -> None:
    section = ReportTableSection(
        title="Itens",
        columns=[("description", "Descrição")],
        rows=[{"description": "X" * 1500}],
    )
    text = _cell_text(section, "description", "X" * 1500)
    assert text.endswith("… [conteúdo truncado]")
    assert len(text) <= 1000


def test_page_numbers_and_repeated_headers() -> None:
    spec = ClosingReportPdfSpec(
        title="P7 — REGISTRO DE INVENTÁRIO",
        metadata=[("Competência", "2026-09")],
        sections=[
            ReportTableSection(
                title="Itens",
                columns=[("productCode", "Produto")],
                rows=[
                    {"productCode": f"P{i:05d}"} for i in range(300)
                ],
            )
        ],
    )
    pdf = render_closing_report_pdf(spec, generated_stamp="2026-10-01T00:00:00+00:00")
    # "Página X de Y" numbering — ReportLab octal-escapes non-ASCII
    # in literal strings (á → \341).
    assert b"P\\341gina 1 de " in pdf
    assert pdf.count(b"/Type /Page") >= 2
    # Header repeats on continuation pages ("/Pages" inflates the page
    # count — repetition is proven by multiple header occurrences).
    assert pdf.count(b"PRODUTO") >= 2


def test_small_summary_stays_together_and_labels_translate() -> None:
    from app.application.use_cases.financeiro_reports_export.report_export_common import (
        branch_label,
        emission_stamp,
        parity_label,
        status_label,
    )

    assert branch_label("all") == "Todas as filiais"
    assert branch_label("01") == "01"
    assert status_label("available") == "Disponível"
    assert status_label("source_missing") == "Posição histórica indisponível"
    assert parity_label("PENDING") == "Paridade oficial pendente"
    stamp = emission_stamp()
    assert stamp.endswith(" (Brasília)")
    assert len(stamp.split(" ")[0].split("/")) == 3


def test_export_binary_response_is_buffered_with_content_length() -> None:
    body = b"%PDF-1.4 fake bytes"
    result = {
        "stream": __import__("io").BytesIO(body),
        "content_type": "application/pdf",
        "filename": "r05-test.pdf",
        "exported_count": 7,
    }
    response = export_binary_response(result)
    assert response.body == body
    assert response.media_type == "application/pdf"
    assert response.headers["content-length"] == str(len(body))
    assert "r05-test.pdf" in response.headers["content-disposition"]
    assert response.headers["x-exported-count"] == "7"


# ---------- P7 PDF export ----------------------------------------------

class _P7Repo:
    def __init__(self, presence=None):
        self.presence = presence or {}

    def snapshot_branch_counts(self, **kwargs):
        return self.presence

    def totals(self, **kwargs):
        return {}

    def list_items(self, **kwargs):
        return [{
            "product_code": "P1",
            "description": "Item",
            "product_type": "MP",
            "product_group": "1000",
            "unit": "KG",
            "warehouse": "01",
            "branch_code": "01",
            "historical_quantity": Decimal("10"),
            "historical_stock_value": Decimal("50"),
        }]

    def summary_by_type(self, **kwargs):
        return [{
            "product_type": "MP",
            "item_count": 1,
            "total_quantity": Decimal("10"),
            "total_stock_value": Decimal("50"),
        }]

    def summary_by_warehouse(self, **kwargs):
        return [{
            "branch_code": "01",
            "warehouse": "01",
            "item_count": 1,
            "total_quantity": Decimal("10"),
            "total_stock_value": Decimal("50"),
        }]

    def p7_totals(self, **kwargs):
        return {
            "stock_value": Decimal("50"),
            "process_physical_value": Decimal("0"),
        }

    def work_in_process_by_type(self, **kwargs):
        return []


def _p7_export(repo):
    return ExportStockInventoryUseCase(
        get_use_case=GetStockInventoryUseCase(
            repository=repo, scope_resolver=_ResolvedResolver()
        )
    )


def test_p7_pdf_export_returns_pdf_bytes() -> None:
    request = StockInventoryQueryRequest.from_query(
        period="2026-09", branch="01", page_size=50000
    )
    result = _p7_export(_P7Repo(presence={"01": 1})).execute(
        request, export_format="pdf", user_subject="user-1"
    )
    assert result["content_type"] == "application/pdf"
    assert result["filename"].endswith(".pdf")
    assert result["stream"].getvalue()[:5] == b"%PDF-"


def test_p7_export_default_format_stays_csv() -> None:
    request = StockInventoryQueryRequest.from_query(
        period="2026-09", branch="01", page_size=50000
    )
    result = _p7_export(_P7Repo(presence={"01": 1})).execute(
        request, user_subject="user-1"
    )
    assert result["content_type"].startswith("text/csv")
    assert result["filename"].endswith(".csv")


# ---------- R05 PDF export ---------------------------------------------

class _R05Repo:
    def __init__(self, presence=None):
        self.presence = presence or {}

    def snapshot_branch_counts(self, **kwargs):
        return self.presence

    def closing_balance_by_type(self, **kwargs):
        return [{"product_type": "MP", "total_stock_value": "100.00"}]

    def sd1_by_type(self, **kwargs):
        return [{"product_type": "MP", "purchases": "10.00"}]

    def sd2_by_type(self, **kwargs):
        return []

    def sd3_by_type(self, **kwargs):
        return []


def _r05_export(repo):
    return ExportStockMovementsUseCase(
        get_use_case=GetStockMovementsUseCase(
            repository=repo, scope_resolver=_ResolvedResolver()
        )
    )


def test_r05_pdf_export_returns_pdf_bytes() -> None:
    request = StockMovementsQueryRequest.from_query(
        period="2026-09", branch="01"
    )
    result = _r05_export(_R05Repo(presence={"01": 1})).execute(
        request, export_format="pdf", user_subject="user-1"
    )
    assert result["content_type"] == "application/pdf"
    assert result["filename"].startswith("r05-stock-movements-")
    assert result["stream"].getvalue()[:5] == b"%PDF-"


def test_r05_export_refused_when_source_missing() -> None:
    """A header-only file must never masquerade as a certified report."""
    request = StockMovementsQueryRequest.from_query(
        period="2026-09", branch="01"
    )
    with pytest.raises(ReportNotExportableError):
        _r05_export(_R05Repo(presence={})).execute(
            request, export_format="pdf", user_subject="user-1"
        )


# ---------- R08 PDF export ---------------------------------------------

class _R08Repo:
    def __init__(self, presence=None):
        self.presence = presence or {}

    def snapshot_branch_counts(self, **kwargs):
        return self.presence

    def summary_by_type(self, **kwargs):
        return [{"product_type": "MP", "total_stock_value": "100.00"}]

    def work_in_process_by_type(self, **kwargs):
        return [{
            "product_type": "MP",
            "allocated_value": "50.00",
            "open_order_count": 1,
        }]

    def work_in_process_detail(self, **kwargs):
        return [{
            "branch_code": "01",
            "product_code": "MP001",
            "description": "Matéria-prima",
            "product_type": "MP",
            "production_order": "00012300101",
            "allocated_quantity": Decimal("5"),
            "allocated_value": Decimal("50"),
        }]

    def work_in_process_detail_count(self, **kwargs):
        return 1


def _r08_export(repo):
    return ExportWorkInProcessUseCase(
        get_use_case=GetWorkInProcessUseCase(
            repository=repo, scope_resolver=_ResolvedResolver()
        )
    )


def test_r08_pdf_export_returns_pdf_bytes() -> None:
    request = StockInventoryQueryRequest.from_query(
        period="2026-09", branch="01", page_size=50000
    )
    result = _r08_export(_R08Repo(presence={"01": 1})).execute(
        request, export_format="pdf", user_subject="user-1"
    )
    assert result["content_type"] == "application/pdf"
    assert result["filename"].startswith("r08-work-in-process-")
    assert result["stream"].getvalue()[:5] == b"%PDF-"


def test_r08_export_refused_when_source_missing() -> None:
    request = StockInventoryQueryRequest.from_query(
        period="2026-09", branch="01", page_size=50000
    )
    with pytest.raises(ReportNotExportableError):
        _r08_export(_R08Repo(presence={})).execute(
            request, export_format="pdf", user_subject="user-1"
        )


def test_exports_run_unpaginated_same_engine() -> None:
    """The export use case composes the query use case — one engine."""
    repo = _R08Repo(presence={"01": 1})
    request = StockInventoryQueryRequest.from_query(
        period="2026-09", branch="01", page_size=50000
    )
    result = _r08_export(repo).execute(
        request, export_format="csv", user_subject="user-1"
    )
    assert result["exported_count"] == 1
    csv_text = result["stream"].getvalue().decode("utf-8-sig")
    assert "RELATORIO R08" in csv_text
    assert "hash_conteudo_sha256" in csv_text
    assert "NAO OFICIAL" in csv_text


def test_scope_gate_still_applies_to_exports() -> None:
    from app.application.security.stock_inventory_scope import (
        StockInventoryScopeUnavailableError,
    )

    export = ExportStockMovementsUseCase(
        get_use_case=GetStockMovementsUseCase(
            repository=_R05Repo(),
            scope_resolver=UnresolvedStockInventoryScopeResolver(),
        )
    )
    with pytest.raises(StockInventoryScopeUnavailableError):
        export.execute(
            StockMovementsQueryRequest.from_query(
                period="2026-09", branch="01"
            ),
            export_format="pdf",
            user_subject="user-1",
        )
