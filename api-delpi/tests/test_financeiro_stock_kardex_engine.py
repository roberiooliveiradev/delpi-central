"""MATR910 kardex engine — classification, REF decode and request rules."""

from __future__ import annotations

import pytest

from app.application.dto.financeiro_stock_kardex.stock_kardex_request import (
    StockKardexQueryRequest,
)
from app.application.use_cases.financeiro_stock_kardex._engine import (
    build_reference,
    classify_movement,
)


class TestClassifyMovement:
    """Printed-column rule (matr910_dlp.prx): TM <= 500 entrada,
    TM > 500 saída; devoluções invertem coluna com sinal negativo."""

    @pytest.mark.parametrize(
        "tm,expected",
        [
            ("010", "entry"),
            ("499", "entry"),
            ("500", "entry"),
            ("501", "output"),
            ("999", "output"),
        ],
    )
    def test_sd3_threshold(self, tm: str, expected: str) -> None:
        kind, sign = classify_movement("SD3", tm, False)
        assert kind == expected
        assert sign == 1

    def test_invent_adjustment_tms(self) -> None:
        """R07: TES 499/DE0 entradas e TES 999/RE0 saídas (SD3 INVENT)."""
        assert classify_movement("SD3", "499", False) == ("entry", 1)
        assert classify_movement("SD3", "999", False) == ("output", 1)

    def test_sd1_purchase_return_prints_negative_output(self) -> None:
        """Devolução de compra (SD1 TIPONF=D): coluna saída, sinal -1."""
        kind, sign = classify_movement("SD1", "010", True)
        assert (kind, sign) == ("output", -1)

    def test_sd1_normal_is_entry(self) -> None:
        assert classify_movement("SD1", "010", False) == ("entry", 1)

    def test_sd2_sale_return_prints_negative_entry(self) -> None:
        """Devolução de venda (SD2 TIPONF=D): coluna entrada, sinal -1."""
        kind, sign = classify_movement("SD2", "501", True)
        assert (kind, sign) == ("entry", -1)

    def test_sd2_normal_is_output(self) -> None:
        assert classify_movement("SD2", "501", False) == ("output", 1)


class TestBuildReference:
    """REF column decode (matr910_dlp.prx L1280+)."""

    def test_sd1_supplier_reference(self) -> None:
        row = {"source_table": "SD1", "partner_code": "001149"}
        assert build_reference(row) == "F-001149"

    def test_sd2_order_reference(self) -> None:
        row = {"source_table": "SD2", "order_number": "003456"}
        assert build_reference(row) == "P-003456"

    def test_sd3_project_takes_priority(self) -> None:
        row = {
            "source_table": "SD3",
            "project_code": "PJT9",
            "production_order": "OP1",
            "cost_center": "CC1",
        }
        assert build_reference(row) == "PJPJT9"

    def test_sd3_op_then_cc(self) -> None:
        row = {
            "source_table": "SD3",
            "project_code": "",
            "production_order": "000123",
            "cost_center": "9001",
        }
        assert build_reference(row) == "OP000123"
        row["production_order"] = ""
        assert build_reference(row) == "CC9001"

    def test_no_reference(self) -> None:
        assert build_reference({"source_table": "SD1"}) is None
        assert build_reference({"source_table": "SD3"}) is None


class TestStockKardexQueryRequest:
    def test_period_window_and_opening_snapshot(self) -> None:
        req = StockKardexQueryRequest.from_query(period="2026-09")
        assert req.period_start() == "20260901"
        assert req.reference_date() == "20260930"
        # SB9 snapshot is the PREVIOUS month-end, never substituted.
        assert req.opening_snapshot_date() == "20260831"

    def test_opening_snapshot_year_rollover(self) -> None:
        req = StockKardexQueryRequest.from_query(period="2026-01")
        assert req.opening_snapshot_date() == "20251231"

    def test_branch_defaults_to_all(self) -> None:
        req = StockKardexQueryRequest.from_query(period="2026-09")
        assert req.requested_branches() == ("01", "02")
        req = StockKardexQueryRequest.from_query(
            period="2026-09", branch="02"
        )
        assert req.requested_branches() == ("02",)

    def test_warehouse_csv_normalized(self) -> None:
        req = StockKardexQueryRequest.from_query(
            period="2026-09", warehouse="01, 99"
        )
        assert req.requested_warehouses() == ("01", "99")

    def test_invalid_period_rejected(self) -> None:
        with pytest.raises(ValueError):
            StockKardexQueryRequest.from_query(period="2026-9")

    def test_invalid_document_kind_rejected(self) -> None:
        with pytest.raises(ValueError):
            StockKardexQueryRequest.from_query(
                period="2026-09", document_kind="ajust"
            )

    def test_invalid_movement_kind_rejected(self) -> None:
        with pytest.raises(ValueError):
            StockKardexQueryRequest.from_query(
                period="2026-09", movement_kind="both"
            )

    def test_invalid_warehouse_rejected(self) -> None:
        with pytest.raises(ValueError):
            StockKardexQueryRequest.from_query(
                period="2026-09", warehouse="01;DROP"
            )
