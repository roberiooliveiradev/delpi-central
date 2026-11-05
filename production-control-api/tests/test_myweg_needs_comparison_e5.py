"""E5 — motor puro de comparação MyWEG + FIFO hipotético."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from production_control_app.domain.services.myweg_needs_comparison import (
    aggregate_needs,
    build_product_fifo_scenarios,
    compare_aggregated,
    consolidate_by_product,
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


def test_probable_postponement_preserves_confidence() -> None:
    prev = aggregate_needs(
        [_row(material="M1", remessa="2026-11-08", qty_un="100", verified="P1", status="confirmed")]
    )
    curr = aggregate_needs(
        [_row(material="M1", remessa="2026-11-13", qty_un="100", verified="P1", status="confirmed")]
    )
    result = compare_aggregated(prev, curr, reference_date=date(2026, 11, 4))
    assert result["probableDateShifts"][0]["kind"] == "possible_postponement"
    assert result["probableDateShifts"][0]["confidence"] == "probable_not_proven"
    assert result["probableDateShifts"][0]["quantityUn"] == "100"
    # Totais observados permanecem entradas/saídas — não viram "reprogramação confirmada".
    assert result["summary"]["appeared"] == 1
    assert result["summary"]["disappeared"] == 1
    assert result["summary"]["increased"] == 0
    assert result["summary"]["decreased"] == 0


def test_probable_partial_pairing_and_multi_date_product() -> None:
    # Exemplo operacional: 2 UN de 12/11 → 10/11 (antecipação parcial possível).
    prev = aggregate_needs(
        [
            _row(
                material="M800",
                remessa="2026-11-12",
                qty_un="2",
                verified="80016354",
                status="confirmed",
            ),
            _row(
                material="M800",
                remessa="2026-11-20",
                qty_un="5",
                verified="80016354",
                status="confirmed",
            ),
        ]
    )
    curr = aggregate_needs(
        [
            _row(
                material="M800",
                remessa="2026-11-10",
                qty_un="2",
                verified="80016354",
                status="confirmed",
            ),
            _row(
                material="M800",
                remessa="2026-11-20",
                qty_un="3",
                verified="80016354",
                status="confirmed",
            ),
        ]
    )
    result = compare_aggregated(prev, curr, reference_date=date(2026, 11, 5))
    shifts = result["probableDateShifts"]
    assert any(
        s["kind"] == "possible_advancement"
        and s["fromRemessa"] == "2026-11-12"
        and s["toRemessa"] == "2026-11-10"
        and s["quantityUn"] == "2"
        for s in shifts
    )
    # Redução residual em 20/11 (5→3) sem entrada correspondente → sem inventar shift.
    assert not any(
        s["fromRemessa"] == "2026-11-20" and s["quantityUn"] == "2" for s in shifts
    )
    assert result["summary"]["decreased"] == 1
    assert result["summary"]["appeared"] == 1
    assert result["summary"]["disappeared"] == 1


def test_probable_no_candidates_when_only_appeared_or_disappeared() -> None:
    prev = aggregate_needs(
        [_row(material="M1", remessa="2026-11-12", qty_un="2", verified="P1", status="confirmed")]
    )
    curr_only_out = aggregate_needs([])
    out_only = compare_aggregated(prev, curr_only_out, reference_date=date(2026, 11, 5))
    assert out_only["probableDateShifts"] == []
    assert out_only["summary"]["disappeared"] == 1

    prev_empty = aggregate_needs([])
    curr_only_in = aggregate_needs(
        [_row(material="M1", remessa="2026-11-10", qty_un="2", verified="P1", status="confirmed")]
    )
    in_only = compare_aggregated(prev_empty, curr_only_in, reference_date=date(2026, 11, 5))
    assert in_only["probableDateShifts"] == []
    assert in_only["summary"]["appeared"] == 1


def test_probable_no_shift_when_quantity_changes_same_date() -> None:
    prev = aggregate_needs(
        [_row(material="M1", remessa="2026-11-12", qty_un="2", verified="P1", status="confirmed")]
    )
    curr = aggregate_needs(
        [_row(material="M1", remessa="2026-11-12", qty_un="5", verified="P1", status="confirmed")]
    )
    result = compare_aggregated(prev, curr, reference_date=date(2026, 11, 5))
    assert result["probableDateShifts"] == []
    assert result["summary"]["increased"] == 1


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


def test_consolidate_product_stable_total_with_date_change_80016354() -> None:
    prev = aggregate_needs(
        [
            _row(
                material="M800",
                remessa="2026-11-12",
                qty_un="2",
                verified="80016354",
                status="confirmed",
            )
        ]
    )
    curr = aggregate_needs(
        [
            _row(
                material="M800",
                remessa="2026-11-10",
                qty_un="2",
                verified="80016354",
                status="confirmed",
            )
        ]
    )
    observed = compare_aggregated(prev, curr, reference_date=date(2026, 11, 5))
    products = consolidate_by_product(
        prev, curr, probable_date_shifts=observed["probableDateShifts"]
    )
    assert len(products) == 1
    row = products[0]
    assert row["verifiedProductCode"] == "80016354"
    assert row["previousQuantityUn"] == "2"
    assert row["currentQuantityUn"] == "2"
    assert row["deltaQuantityUn"] == "0"
    assert row["situation"] == "stable_with_date_changes"
    assert {r["remessa"] for r in row["remessas"]} == {"2026-11-10", "2026-11-12"}
    assert row["probableDateShifts"]
    assert row["probableDateShifts"][0]["kind"] == "possible_advancement"
    # Totais não mudam por causa do shift.
    assert Decimal(row["deltaQuantityUn"]) == Decimal("0")


def test_consolidate_product_net_reduction_90261883_fixture() -> None:
    prev = aggregate_needs(
        [
            _row(material="M902", remessa="2026-11-03", qty_un="1066", verified="90261883", status="confirmed"),
            _row(material="M902", remessa="2026-11-09", qty_un="1", verified="90261883", status="confirmed"),
            _row(material="M902", remessa="2026-11-12", qty_un="1600", verified="90261883", status="confirmed"),
        ]
    )
    curr = aggregate_needs(
        [
            _row(material="M902", remessa="2026-11-12", qty_un="1356", verified="90261883", status="confirmed"),
            _row(material="M902", remessa="2026-11-16", qty_un="210", verified="90261883", status="confirmed"),
        ]
    )
    observed = compare_aggregated(prev, curr, reference_date=date(2026, 11, 5))
    products = consolidate_by_product(
        prev, curr, probable_date_shifts=observed["probableDateShifts"]
    )
    row = products[0]
    assert row["previousQuantityUn"] == "2667"
    assert row["currentQuantityUn"] == "1566"
    assert row["deltaQuantityUn"] == "-1101"
    assert row["situation"] == "decreased"
    remessa_sum_prev = sum(Decimal(r["previousQuantityUn"]) for r in row["remessas"])
    remessa_sum_curr = sum(Decimal(r["currentQuantityUn"]) for r in row["remessas"])
    assert remessa_sum_prev == Decimal("2667")
    assert remessa_sum_curr == Decimal("1566")
    # Shift eventual não elimina a redução líquida.
    assert Decimal(row["deltaQuantityUn"]) == Decimal("-1101")


def test_consolidate_includes_unchanged_remessa_in_detail() -> None:
    prev = aggregate_needs(
        [
            _row(material="M1", remessa="2026-11-10", qty_un="50", verified="P1", status="confirmed"),
            _row(material="M1", remessa="2026-11-12", qty_un="50", verified="P1", status="confirmed"),
        ]
    )
    curr = aggregate_needs(
        [
            _row(material="M1", remessa="2026-11-10", qty_un="50", verified="P1", status="confirmed"),
            _row(material="M1", remessa="2026-11-15", qty_un="50", verified="P1", status="confirmed"),
        ]
    )
    products = consolidate_by_product(prev, curr)
    row = products[0]
    assert row["situation"] == "stable_with_date_changes"
    by_date = {r["remessa"]: r for r in row["remessas"]}
    assert by_date["2026-11-10"]["movement"] == "unchanged"
    assert by_date["2026-11-12"]["movement"] == "disappeared"
    assert by_date["2026-11-15"]["movement"] == "appeared"


def test_consolidate_percent_none_when_previous_zero() -> None:
    prev = aggregate_needs([])
    curr = aggregate_needs(
        [_row(material="M1", remessa="2026-11-10", qty_un="10", verified="P1", status="confirmed")]
    )
    row = consolidate_by_product(prev, curr)[0]
    assert row["situation"] == "appeared"
    assert row["percentChange"] is None
    assert row["previousQuantityUn"] == "0"
    assert row["currentQuantityUn"] == "10"


def test_consolidate_unconfirmed_identity_not_verified() -> None:
    prev = aggregate_needs(
        [_row(material="MAT-X", remessa="2026-11-10", qty_un="5", status="pending")]
    )
    curr = aggregate_needs(
        [_row(material="MAT-X", remessa="2026-11-10", qty_un="8", status="pending")]
    )
    row = consolidate_by_product(prev, curr)[0]
    assert row["identityKind"] == "customer_reference"
    assert row["identityConfirmed"] is False
    assert row["verifiedProductCode"] is None
    assert row["situation"] == "increased"
