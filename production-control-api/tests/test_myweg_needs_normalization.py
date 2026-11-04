"""E1 — contrato e normalização MyWEG Necessidades (filial 02)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from production_control_app.domain.myweg_needs_contract import (
    ALLOWED_BRANCH,
    CONTRACT_VERSION,
    ERROR_BRANCH_NOT_ALLOWED,
    ERROR_DUPLICATE_LINE,
    ERROR_FILIAL_01_FORBIDDEN,
    ERROR_PAYLOAD_SHA256_MISMATCH,
    MYWEG_COMPANY_CODE,
    MYWEG_WORK_CENTER,
    REFERENCE_RECORD_COUNT,
    REFERENCE_TOTAL_MI,
    REFERENCE_TOTAL_UN,
    SB1_STATUS_PENDING,
    compute_payload_sha256,
    decimal_to_canonical_str,
)
from production_control_app.domain.services.myweg_needs_normalization import (
    normalize_and_validate_batch,
    un_to_mi,
)

_FIXTURES = Path(__file__).parent / "fixtures" / "myweg"


def _aware(ts: str = "2026-11-04T12:00:00+00:00") -> str:
    return ts


def _base_envelope(**overrides):
    payload = {
        "contract_version": CONTRACT_VERSION,
        "collection_id": "col-homolog-001",
        "branch": ALLOWED_BRANCH,
        "myweg_company_code": MYWEG_COMPANY_CODE,
        "myweg_work_center": MYWEG_WORK_CENTER,
        "collected_at": _aware("2026-11-04T10:00:00+00:00"),
        "exported_at": _aware("2026-11-04T11:00:00+00:00"),
        "source_files": {
            "necessidades_tratadas_csv_sha256": "a" * 64,
            "necessidades_tratadas_xlsx_sha256": "b" * 64,
            "para_conferencia_pcp_csv_sha256": "c" * 64,
            "resumo_json_sha256": "d" * 64,
        },
        "records": [],
    }
    payload.update(overrides)
    return payload


def build_reference_source_records(
    count: int = REFERENCE_RECORD_COUNT,
    total_un: Decimal = REFERENCE_TOTAL_UN,
) -> list[dict]:
    """Corpus sintético com a mesma cardinalidade e totais da referência homologada."""
    assert count > 0
    base = total_un // count
    remainder = total_un - (base * count)
    rows: list[dict] = []
    for index in range(count):
        qty = base + (remainder if index == count - 1 else Decimal("0"))
        rows.append(
            {
                "material_weg_tratado": f"MAT-WEG-{index:04d}",
                "codigo_referencia_weg": f"REF-{index:04d}",
                "origem_material_weg": "ORIGEM-REF",
                "quantidade_original_un": decimal_to_canonical_str(qty),
                "unidade": "UN",
                "data_remessa": "2026-11-15",
                "documento": f"DOC-{index:04d}" if index % 7 == 0 else None,
                "rastreabilidade": f"linux-etl:ref:{index:04d}",
            }
        )
    return rows


def test_un_to_mi_exact_reference_totals():
    assert un_to_mi(Decimal("745746")) == Decimal("745.746")
    assert un_to_mi(REFERENCE_TOTAL_UN) == REFERENCE_TOTAL_MI


def test_resumo_referencia_fixture_matches_constants():
    data = json.loads((_FIXTURES / "resumo_referencia.json").read_text(encoding="utf-8"))
    assert data["record_count"] == REFERENCE_RECORD_COUNT
    assert Decimal(data["quantidade_original_un_total"]) == REFERENCE_TOTAL_UN
    assert Decimal(data["quantidade_mi_total"]) == REFERENCE_TOTAL_MI
    assert data["branch"] == "02"
    assert data["myweg_company_code"] == "1009"
    assert data["myweg_work_center"] == "1106"


def test_normalize_reference_batch_532_records_positive():
    records = build_reference_source_records()
    assert len(records) == 532
    payload = _base_envelope(records=records, record_count=532)
    result = normalize_and_validate_batch(payload)
    assert result.ok, result.issues
    assert result.batch is not None
    assert result.batch["record_count"] == 532
    assert result.batch["branch"] == "02"
    assert result.batch["myweg_company_code"] == "1009"
    assert result.batch["myweg_work_center"] == "1106"
    assert Decimal(result.batch["totals"]["quantidade_original_un"]) == REFERENCE_TOTAL_UN
    assert Decimal(result.batch["totals"]["quantidade_mi"]) == REFERENCE_TOTAL_MI
    assert result.batch["payload_sha256"] == compute_payload_sha256(result.batch["records"])
    assert result.batch["idempotency_key"].startswith("col-homolog-001:")
    sample = result.batch["records"][0]
    assert sample["sb1_resolution"]["status"] == SB1_STATUS_PENDING
    assert sample["sb1_resolution"]["protheus_product_code"] is None


def test_sample_source_rows_sibling_formats():
    rows = json.loads((_FIXTURES / "sample_source_rows.json").read_text(encoding="utf-8"))
    result = normalize_and_validate_batch(_base_envelope(records=rows, record_count=2))
    assert result.ok, result.issues
    assert result.batch is not None
    assert result.batch["records"][0]["data_remessa"] == "2026-11-15"
    assert result.batch["records"][0]["quantidade_original_un"] == "1500"
    assert result.batch["records"][0]["quantidade_mi"] == "1.5"
    assert result.batch["records"][1]["data_remessa"] == "2026-11-20"
    assert result.batch["records"][1]["quantidade_mi"] == "0.25"
    assert Decimal(result.batch["totals"]["quantidade_original_un"]) == Decimal("1750")
    assert Decimal(result.batch["totals"]["quantidade_mi"]) == Decimal("1.75")


def test_rejects_filial_01_in_envelope():
    records = build_reference_source_records(count=2, total_un=Decimal("2000"))
    result = normalize_and_validate_batch(
        _base_envelope(branch="01", records=records, record_count=2)
    )
    assert not result.ok
    assert ERROR_FILIAL_01_FORBIDDEN in result.error_codes


def test_rejects_filial_01_on_record_negative():
    records = build_reference_source_records(count=2, total_un=Decimal("2000"))
    records[1]["filial"] = "01"
    result = normalize_and_validate_batch(
        _base_envelope(records=records, record_count=2)
    )
    assert not result.ok
    assert ERROR_FILIAL_01_FORBIDDEN in result.error_codes


def test_rejects_branch_other_than_02():
    records = build_reference_source_records(count=2, total_un=Decimal("2000"))
    result = normalize_and_validate_batch(
        _base_envelope(branch="99", records=records, record_count=2)
    )
    assert not result.ok
    assert ERROR_BRANCH_NOT_ALLOWED in result.error_codes


def test_rejects_duplicate_line():
    row = {
        "material_weg_tratado": "MAT",
        "codigo_referencia_weg": "REF",
        "origem_material_weg": "ORG",
        "quantidade_original_un": "1000",
        "unidade": "UN",
        "data_remessa": "2026-11-15",
        "documento": "D1",
        "rastreabilidade": "t1",
    }
    result = normalize_and_validate_batch(
        _base_envelope(records=[row, dict(row)], record_count=2)
    )
    assert not result.ok
    assert ERROR_DUPLICATE_LINE in result.error_codes


def test_rejects_tampered_payload_sha256():
    records = build_reference_source_records(count=3, total_un=Decimal("3000"))
    result = normalize_and_validate_batch(
        _base_envelope(
            records=records,
            record_count=3,
            payload_sha256="0" * 64,
        )
    )
    assert not result.ok
    assert ERROR_PAYLOAD_SHA256_MISMATCH in result.error_codes


def test_rejects_naive_timestamp():
    records = build_reference_source_records(count=1, total_un=Decimal("1000"))
    result = normalize_and_validate_batch(
        _base_envelope(
            records=records,
            record_count=1,
            collected_at="2026-11-04T10:00:00",
        )
    )
    assert not result.ok
    assert any(issue.path == "collected_at" for issue in result.issues)


def test_idempotency_key_stable_for_same_payload():
    records = build_reference_source_records(count=5, total_un=Decimal("5000"))
    first = normalize_and_validate_batch(
        _base_envelope(records=records, record_count=5, collection_id="same-col")
    )
    second = normalize_and_validate_batch(
        _base_envelope(records=records, record_count=5, collection_id="same-col")
    )
    assert first.ok and second.ok
    assert first.batch["idempotency_key"] == second.batch["idempotency_key"]
    assert first.batch["payload_sha256"] == second.batch["payload_sha256"]


def test_datetime_objects_accepted():
    records = build_reference_source_records(count=1, total_un=Decimal("1000"))
    result = normalize_and_validate_batch(
        _base_envelope(
            records=records,
            record_count=1,
            collected_at=datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc),
            exported_at=datetime(2026, 11, 4, 11, 0, tzinfo=timezone.utc),
        )
    )
    assert result.ok, result.issues
