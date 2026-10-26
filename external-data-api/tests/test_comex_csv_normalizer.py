"""PROC-0076 R2 EX1 — deterministic MDIC import CSV contract tests."""

from datetime import date
from decimal import Decimal
from io import StringIO

import pytest

from app.infrastructure.providers.comex_csv_normalizer import (
    ComexCsvContractError,
    normalize_import_csv,
)

HEADER = (
    "CO_ANO;CO_MES;CO_NCM;CO_UNID;CO_PAIS;SG_UF_NCM;CO_VIA;"
    "CO_URF;QT_ESTAT;KG_LIQUIDO;VL_FOB;VL_FRETE;VL_SEGURO\n"
)


def _row(
    ncm="12345678", *,
    month="9", country="160", state="SC",
    kg="1000", fob="5000"
):
    return (
        f"2026;{month};{ncm};10;{country};{state};1;1;1;"
        f"{kg};{fob};0;0\n"
    )


def _parse(*rows, approved=frozenset({"12345678"}), **options):
    return normalize_import_csv(
        StringIO(HEADER + "".join(rows)),
        approved_ncm_codes=approved,
        **options,
    )


def test_weighted_unit_value_uses_totals_not_average_of_ratios():
    data = _parse(_row(kg="1000", fob="2000"), _row(kg="3000", fob="12000"))
    assert len(data) == 1
    row = data[0]
    assert row.reference_month == date(2026, 9, 1)
    assert row.fob_usd_total == Decimal("14000")
    assert row.net_weight_kg_total == Decimal("4000")
    assert row.unit_value_usd_per_t == Decimal("3500")
    assert row.contributing_rows == 2
    assert row.quality_status == "validated"


def test_sibling_month_country_and_state_remain_separate():
    data = _parse(
        _row(month="9", state="SC"),
        _row(month="10", state="SC"),
        _row(month="9", state="ES"),
        _row(month="9", country="249", state="SC"),
    )
    assert len(data) == 4
    assert {r.reference_month.month for r in data} == {9, 10}
    assert {r.state_code for r in data} == {"SC", "ES"}


def test_unapproved_ncm_is_never_imported():
    assert _parse(_row(ncm="99999999")) == []


def test_zero_weight_is_null_and_explicitly_invalid():
    row = _parse(_row(kg="0", fob="5000"))[0]
    assert row.unit_value_usd_per_t is None
    assert row.quality_status == "invalid_weight"


@pytest.mark.parametrize("bad", ["-1", "NaN", "Infinity", "foo", ""])
def test_invalid_weight_fails_closed(bad):
    with pytest.raises(ComexCsvContractError):
        _parse(_row(kg=bad))


def test_header_missing_required_column_fails_closed():
    with pytest.raises(ComexCsvContractError):
        normalize_import_csv(
            StringIO("CO_ANO;CO_MES;CO_NCM;KG_LIQUIDO\n2026;9;12345678;1000\n"),
            approved_ncm_codes=frozenset({"12345678"}),
        )


@pytest.mark.parametrize("approved", [frozenset(), frozenset({"12"}), frozenset({"NCM12345"})])
def test_no_implicit_allow_all_or_invalid_mapping(approved):
    with pytest.raises(ComexCsvContractError):
        _parse(_row(), approved=approved)


def test_bounded_file_rejects_truncated_processing():
    with pytest.raises(ComexCsvContractError, match="row limit"):
        _parse(_row(), _row(), max_rows=1)


def test_bad_ncm_in_csv_rejected():
    with pytest.raises(ComexCsvContractError, match="invalid NCM"):
        _parse(_row(ncm="INVALID!"))


def test_bad_month_rejected():
    with pytest.raises(ComexCsvContractError, match="reference month"):
        _parse(_row(month="13"))


def test_extra_column_rejected():
    with pytest.raises(ComexCsvContractError, match="malformed"):
        normalize_import_csv(
            StringIO(HEADER + _row().rstrip("\n") + ";unexpected\n"),
            approved_ncm_codes=frozenset({"12345678"}),
        )
