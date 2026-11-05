"""E5 — motor puro de comparação MyWEG + FIFO hipotético."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from production_control_app.domain.services.myweg_needs_comparison import (
    aggregate_needs,
    build_product_fifo_scenarios,
    compare_aggregated,
    simulate_fifo_abatement,
)


def _row(
    *,
    material: str,
    remessa: str,
    qty_un: str,
    code: str | None = None,
    verified: str | None = None,
    status: str = "pending",
) -> dict:
    qty = Decimal(qty_un)
    return {
        "material_weg_tratado": material,
        "codigo_referencia_weg": code,
        "data_remessa": remessa,
        "quantidade_original_un": qty_un,
        "quantidade_mi": str(qty / Decimal("1000")),
        "sb1_resolution": {
            "status": status,
            "protheus_product_code": verified,
        },
    }


def test_ac01_identical_collections_zero_delta() -> None:
    rows = [
        _row(material="M1", remessa="2026-11-06", qty_un="200", verified="P1", status="confirmed"),
        _row(material="M1", remessa="2026-11-10", qty_un="500", verified="P1", status="confirmed"),
    ]
    prev = aggregate_needs(rows)
    curr = aggregate_needs(rows)
    result = compare_aggregated(prev, curr, reference_date=date(2026, 11, 4))
    assert result["summary"]["unchanged"] == 2
    assert all(c["deltaQuantityUn"] == "0" for c in result["changes"])


def test_ac02_quantity_change_detected() -> None:
    prev = aggregate_needs(
        [_row(material="M1", remessa="2026-11-06", qty_un="200", verified="P1", status="confirmed")]
    )
    curr = aggregate_needs(
        [_row(material="M1", remessa="2026-11-06", qty_un="150", verified="P1", status="confirmed")]
    )
    result = compare_aggregated(prev, curr, reference_date=date(2026, 11, 4))
    assert result["summary"]["decreased"] == 1
    assert result["changes"][0]["deltaQuantityUn"] == "-50"


def test_ac03_multiple_lines_same_product_aggregated() -> None:
    rows = [
        _row(material="M1", remessa="2026-11-06", qty_un="100", verified="P1", status="confirmed"),
        _row(material="M1", remessa="2026-11-06", qty_un="100", verified="P1", status="confirmed"),
    ]
    agg = aggregate_needs(rows)
    assert len(agg) == 1
    need = next(iter(agg.values()))
    assert need.quantity_un == Decimal("200")
    assert need.line_count == 2


def test_ac04_probable_advancement_without_line_identity() -> None:
    prev = aggregate_needs(
        [
            _row(material="M1", remessa="2026-11-15", qty_un="300", verified="P1", status="confirmed"),
        ]
    )
    curr = aggregate_needs(
        [
            _row(material="M1", remessa="2026-11-06", qty_un="300", verified="P1", status="confirmed"),
        ]
    )
    result = compare_aggregated(prev, curr, reference_date=date(2026, 11, 4))
    assert result["probableDateShifts"]
    assert result["probableDateShifts"][0]["kind"] == "possible_advancement"
    assert result["probableDateShifts"][0]["confidence"] == "probable_not_proven"


def test_ac05_fifo_400_on_200_500_300() -> None:
    prev = aggregate_needs(
        [
            _row(material="M1", remessa="2026-11-06", qty_un="200", verified="P1", status="confirmed"),
            _row(material="M1", remessa="2026-11-10", qty_un="500", verified="P1", status="confirmed"),
            _row(material="M1", remessa="2026-11-15", qty_un="300", verified="P1", status="confirmed"),
        ]
    )
    fifo = simulate_fifo_abatement(
        prev, product_key="code:P1", candidate_quantity_un=Decimal("400")
    )
    assert [r["hypotheticalQuantityUn"] for r in fifo["rows"]] == ["0", "300", "300"]
    assert fifo["unusedCandidateQuantityUn"] == "0"
    assert "Não comprova" in fifo["disclaimer"] or "não comprova" in fifo["disclaimer"].lower()


def test_ac06_billing_above_need_no_negative() -> None:
    prev = aggregate_needs(
        [_row(material="M1", remessa="2026-11-06", qty_un="100", verified="P1", status="confirmed")]
    )
    fifo = simulate_fifo_abatement(
        prev, product_key="code:P1", candidate_quantity_un=Decimal("250")
    )
    assert fifo["rows"][0]["hypotheticalQuantityUn"] == "0"
    assert fifo["unusedCandidateQuantityUn"] == "150"
    assert all(Decimal(r["hypotheticalQuantityUn"]) >= 0 for r in fifo["rows"])


def test_ac07_fifo_is_hypothesis_not_confirmed_abatement() -> None:
    prev = aggregate_needs(
        [
            _row(material="M1", remessa="2026-11-06", qty_un="200", verified="P1", status="confirmed"),
            _row(material="M1", remessa="2026-11-10", qty_un="500", verified="P1", status="confirmed"),
        ]
    )
    curr = aggregate_needs(
        [
            _row(material="M1", remessa="2026-11-06", qty_un="200", verified="P1", status="confirmed"),
            _row(material="M1", remessa="2026-11-10", qty_un="500", verified="P1", status="confirmed"),
        ]
    )
    # Faturamento candidato existe, mas observação atual não mudou → não inventar redução confirmada.
    observed = compare_aggregated(prev, curr, reference_date=date(2026, 11, 4))
    assert observed["summary"]["decreased"] == 0
    scenarios = build_product_fifo_scenarios(
        prev, curr, {"code:P1": Decimal("400")}
    )
    assert scenarios[0]["rows"][0]["hypotheticalQuantityUn"] == "0"
    assert "hipotético" in scenarios[0]["disclaimer"].lower() or "Hipótese" in scenarios[0]["disclaimer"] or "hipotético" in scenarios[0]["disclaimer"]


def test_ac11_unresolved_identity_explicit() -> None:
    rows = [_row(material="", remessa="2026-11-06", qty_un="10", code="", verified=None)]
    # material empty and no code → unresolved
    rows[0]["material_weg_tratado"] = ""
    rows[0]["codigo_referencia_weg"] = ""
    agg = aggregate_needs(rows)
    key = next(iter(agg))
    assert key.identity_kind == "unresolved"
