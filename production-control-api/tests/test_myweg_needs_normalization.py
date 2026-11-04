"""E1 — compatibilidade MyWEG Necessidades com planilha real (filial 02)."""

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
    ERROR_INVALID_RECORD,
    ERROR_MISSING_REQUIRED_FIELD,
    ERROR_PAYLOAD_SHA256_MISMATCH,
    MYWEG_COMPANY_CODE,
    MYWEG_WORK_CENTER,
    SB1_STATUS_PENDING,
    compute_payload_sha256,
    decimal_to_canonical_str,
)
from production_control_app.domain.services.myweg_needs_normalization import (
    normalize_and_validate_batch,
    normalize_source_records,
    un_to_mi,
    validate_ingest_batch,
)
from tests.fixtures.myweg.sanitized_real_format import (
    SAMPLE_RECORD_COUNT,
    SAMPLE_REFS_EMPTY,
    SAMPLE_REFS_STARTING_8,
    SAMPLE_REFS_STARTING_9,
    SAMPLE_TOTAL_MI,
    SAMPLE_TOTAL_UN,
    build_sanitized_real_format_records,
    summarize_codigo_referencia,
)

_FIXTURES = Path(__file__).parent / "fixtures" / "myweg"


def _aware(ts: str = "2026-11-04T12:00:00+00:00") -> str:
    return ts


def _source_files() -> dict[str, str]:
    return {
        "necessidades_tratadas_csv_sha256": "a" * 64,
        "necessidades_tratadas_xlsx_sha256": "b" * 64,
        "para_conferencia_pcp_csv_sha256": "c" * 64,
        "resumo_json_sha256": "d" * 64,
    }


def _ingest_envelope(records: list[dict], **overrides) -> dict:
    """Monta lote pronto: normaliza origem, calcula totais/sha e preenche envelope."""
    source = normalize_source_records(records)
    assert source.ok, source.issues
    totals_un = sum(
        (Decimal(str(row["quantidade_original_un"])) for row in source.records),
        Decimal("0"),
    )
    totals_mi = sum(
        (Decimal(str(row["quantidade_mi"])) for row in source.records),
        Decimal("0"),
    )
    payload = {
        "contract_version": CONTRACT_VERSION,
        "collection_id": "col-homolog-001",
        "branch": ALLOWED_BRANCH,
        "myweg_company_code": MYWEG_COMPANY_CODE,
        "myweg_work_center": MYWEG_WORK_CENTER,
        "collected_at": _aware("2026-11-04T10:00:00+00:00"),
        "exported_at": _aware("2026-11-04T11:00:00+00:00"),
        "source_files": _source_files(),
        "record_count": len(source.records),
        "totals": {
            "quantidade_original_un": decimal_to_canonical_str(totals_un),
            "quantidade_mi": decimal_to_canonical_str(totals_mi),
        },
        "payload_sha256": compute_payload_sha256(source.records),
        "records": records,
    }
    payload.update(overrides)
    return payload


def test_un_to_mi_sample_totals_are_exact_but_not_contract_invariants():
    assert un_to_mi(Decimal("745746")) == Decimal("745.746")
    assert un_to_mi(SAMPLE_TOTAL_UN) == SAMPLE_TOTAL_MI
    # Coleta futura com outro total continua válida na conversão.
    assert un_to_mi(Decimal("1000")) == Decimal("1")


def test_resumo_referencia_describes_sample_not_permanent_rule():
    data = json.loads((_FIXTURES / "resumo_referencia.json").read_text(encoding="utf-8"))
    assert data["record_count"] == SAMPLE_RECORD_COUNT
    assert Decimal(data["quantidade_original_un_total"]) == SAMPLE_TOTAL_UN
    assert data["codigo_referencia_weg_distribution"]["empty"] == 2
    assert "nao sao restricoes permanentes" in data["notes"].lower().replace("ã", "a")


def test_sanitize_fixture_json_matches_real_format_distribution():
    payload = json.loads(
        (_FIXTURES / "planilha_real_sanitizada.json").read_text(encoding="utf-8")
    )
    records = payload["records"]
    assert len(records) == 532
    assert summarize_codigo_referencia(records) == {
        "start_9": 528,
        "start_8": 2,
        "empty": 2,
        "other": 0,
    }
    assert "linha_fonte" in records[0]
    assert "assinatura_registro" in records[0]
    assert "quantidade" in records[0]
    assert "data_remessa" in records[0]
    total = sum(Decimal(str(row["quantidade"])) for row in records)
    assert total == SAMPLE_TOTAL_UN


def test_normalize_source_preserves_empty_codigo_referencia_and_all_532():
    records = build_sanitized_real_format_records()
    result = normalize_source_records(records)
    assert result.ok, result.issues
    assert len(result.records) == 532

    empty = [row for row in result.records if row["codigo_referencia_weg"] is None]
    start_9 = [
        row
        for row in result.records
        if (row["codigo_referencia_weg"] or "").startswith("9")
    ]
    start_8 = [
        row
        for row in result.records
        if (row["codigo_referencia_weg"] or "").startswith("8")
    ]
    assert len(empty) == SAMPLE_REFS_EMPTY
    assert len(start_9) == SAMPLE_REFS_STARTING_9
    assert len(start_8) == SAMPLE_REFS_STARTING_8

    for row in empty:
        assert row["sb1_resolution"]["status"] == SB1_STATUS_PENDING
        assert row["sb1_resolution"]["protheus_product_code"] is None
        assert "linha_fonte=" in row["rastreabilidade"]
        assert "assinatura_registro=" in row["rastreabilidade"]

    assert Decimal(
        decimal_to_canonical_str(
            sum(
                (Decimal(str(r["quantidade_original_un"])) for r in result.records),
                Decimal("0"),
            )
        )
    ) == SAMPLE_TOTAL_UN
    assert Decimal(
        decimal_to_canonical_str(
            sum((Decimal(str(r["quantidade_mi"])) for r in result.records), Decimal("0"))
        )
    ) == SAMPLE_TOTAL_MI


def test_validate_ingest_batch_accepts_sanitized_real_format():
    records = json.loads(
        (_FIXTURES / "planilha_real_sanitizada.json").read_text(encoding="utf-8")
    )["records"]
    payload = _ingest_envelope(records)
    result = validate_ingest_batch(payload)
    assert result.ok, result.issues
    assert result.batch is not None
    assert result.batch["record_count"] == 532
    empty = [
        row
        for row in result.batch["records"]
        if row["codigo_referencia_weg"] is None
    ]
    assert len(empty) == 2


def test_sample_source_rows_sibling_formats_including_empty_ref():
    rows = json.loads((_FIXTURES / "sample_source_rows.json").read_text(encoding="utf-8"))
    source = normalize_source_records(rows)
    assert source.ok, source.issues
    assert source.records[0]["data_remessa"] == "2026-11-15"
    assert source.records[0]["quantidade_mi"] == "1.5"
    assert source.records[1]["codigo_referencia_weg"] is None
    assert source.records[1]["sb1_resolution"]["status"] == SB1_STATUS_PENDING
    assert source.records[2]["codigo_referencia_weg"].startswith("8")

    result = normalize_and_validate_batch(_ingest_envelope(rows))
    assert result.ok, result.issues
    assert Decimal(result.batch["totals"]["quantidade_original_un"]) == Decimal("2750")


def test_source_normalization_does_not_require_ingest_envelope():
    rows = build_sanitized_real_format_records()[:3]
    result = normalize_source_records(rows)
    assert result.ok
    assert result.batch is None
    assert len(result.records) == 3


def test_ingest_validation_requires_payload_sha256_and_source_files():
    rows = build_sanitized_real_format_records()[:2]
    source = normalize_source_records(rows)
    assert source.ok
    incomplete = {
        "contract_version": CONTRACT_VERSION,
        "collection_id": "col-x",
        "branch": "02",
        "myweg_company_code": "1009",
        "myweg_work_center": "1106",
        "collected_at": _aware(),
        "exported_at": _aware(),
        "records": rows,
        "record_count": 2,
        "totals": {
            "quantidade_original_un": "2802",
            "quantidade_mi": "2.802",
        },
    }
    result = validate_ingest_batch(incomplete)
    assert not result.ok
    assert ERROR_MISSING_REQUIRED_FIELD in result.error_codes
    assert any(issue.path == "payload_sha256" for issue in result.issues)
    assert any(
        issue.path and issue.path.startswith("source_files") for issue in result.issues
    )


def test_future_collection_different_totals_still_valid():
    """Totais da amostra 532/745746 não travam coletas futuras."""
    rows = [
        {
            "material_weg_tratado": "X",
            "codigo_referencia_weg": "90000001",
            "origem_material_weg": "O",
            "quantidade": "10",
            "unidade": "UN",
            "data_remessa": "2026-12-01",
            "linha_fonte": 1,
            "assinatura_registro": "sig-future-1",
        },
        {
            "material_weg_tratado": "Y",
            "codigo_referencia_weg": "",
            "origem_material_weg": "O",
            "quantidade": "20",
            "unidade": "UN",
            "data_remessa": "2026-12-01",
            "linha_fonte": 2,
            "assinatura_registro": "sig-future-2",
        },
    ]
    result = validate_ingest_batch(_ingest_envelope(rows, collection_id="future-col"))
    assert result.ok, result.issues
    assert result.batch["record_count"] == 2
    assert result.batch["totals"]["quantidade_original_un"] == "30"
    assert result.batch["totals"]["quantidade_mi"] == "0.03"


def test_rejects_filial_01_in_envelope():
    records = build_sanitized_real_format_records()[:2]
    result = validate_ingest_batch(_ingest_envelope(records, branch="01"))
    assert not result.ok
    assert ERROR_FILIAL_01_FORBIDDEN in result.error_codes


def test_rejects_filial_01_on_record_negative():
    records = build_sanitized_real_format_records()[:2]
    records[1]["filial"] = "01"
    result = validate_ingest_batch(_ingest_envelope(records))
    assert not result.ok
    assert ERROR_FILIAL_01_FORBIDDEN in result.error_codes


def test_rejects_branch_other_than_02():
    records = build_sanitized_real_format_records()[:2]
    result = validate_ingest_batch(_ingest_envelope(records, branch="99"))
    assert not result.ok
    assert ERROR_BRANCH_NOT_ALLOWED in result.error_codes


def test_rejects_duplicate_line():
    row = {
        "material_weg_tratado": "MAT",
        "codigo_referencia_weg": "90000099",
        "origem_material_weg": "ORG",
        "quantidade": "1000",
        "unidade": "UN",
        "data_remessa": "2026-11-15",
        "documento": "D1",
        "linha_fonte": 10,
        "assinatura_registro": "sig-dup",
    }
    result = normalize_source_records([row, dict(row)])
    assert not result.ok
    assert ERROR_DUPLICATE_LINE in result.error_codes


def test_empty_refs_with_distinct_linha_fonte_are_not_duplicates():
    rows = [
        {
            "material_weg_tratado": "MAT",
            "codigo_referencia_weg": "",
            "origem_material_weg": "ORG",
            "quantidade": "100",
            "unidade": "UN",
            "data_remessa": "2026-11-15",
            "linha_fonte": 1,
            "assinatura_registro": "sig-a",
        },
        {
            "material_weg_tratado": "MAT",
            "codigo_referencia_weg": "",
            "origem_material_weg": "ORG",
            "quantidade": "100",
            "unidade": "UN",
            "data_remessa": "2026-11-15",
            "linha_fonte": 2,
            "assinatura_registro": "sig-b",
        },
    ]
    result = normalize_source_records(rows)
    assert result.ok, result.issues
    assert len(result.records) == 2


def test_rejects_tampered_payload_sha256():
    records = build_sanitized_real_format_records()[:3]
    result = validate_ingest_batch(
        _ingest_envelope(records, payload_sha256="0" * 64)
    )
    assert not result.ok
    assert ERROR_PAYLOAD_SHA256_MISMATCH in result.error_codes


def test_rejects_naive_timestamp():
    records = build_sanitized_real_format_records()[:1]
    result = validate_ingest_batch(
        _ingest_envelope(records, collected_at="2026-11-04T10:00:00")
    )
    assert not result.ok
    assert any(issue.path == "collected_at" for issue in result.issues)


def test_malformed_quantity_yields_validation_error_not_exception():
    rows = [
        {
            "material_weg_tratado": "MAT",
            "codigo_referencia_weg": "90000001",
            "origem_material_weg": "ORG",
            "quantidade": {"oops": True},
            "unidade": "UN",
            "data_remessa": "2026-11-15",
            "linha_fonte": 1,
            "assinatura_registro": "sig-bad",
        }
    ]
    result = normalize_source_records(rows)
    assert not result.ok
    assert ERROR_INVALID_RECORD in result.error_codes


def test_malformed_non_mapping_record_yields_validation_error():
    result = normalize_source_records(["not-an-object"])
    assert not result.ok
    assert ERROR_INVALID_RECORD in result.error_codes


def test_idempotency_key_stable_for_same_payload():
    records = build_sanitized_real_format_records()[:5]
    first = validate_ingest_batch(_ingest_envelope(records, collection_id="same-col"))
    second = validate_ingest_batch(_ingest_envelope(records, collection_id="same-col"))
    assert first.ok and second.ok
    assert first.batch["idempotency_key"] == second.batch["idempotency_key"]
    assert first.batch["payload_sha256"] == second.batch["payload_sha256"]


def test_datetime_objects_accepted():
    records = build_sanitized_real_format_records()[:1]
    result = validate_ingest_batch(
        _ingest_envelope(
            records,
            collected_at=datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc),
            exported_at=datetime(2026, 11, 4, 11, 0, tzinfo=timezone.utc),
        )
    )
    assert result.ok, result.issues


def test_assinatura_registro_not_used_as_cross_collection_identity():
    """Mesma assinatura em coletas distintas → idempotency_key diferente."""
    row = {
        "material_weg_tratado": "MAT",
        "codigo_referencia_weg": "90000001",
        "origem_material_weg": "ORG",
        "quantidade": "500",
        "unidade": "UN",
        "data_remessa": "2026-11-15",
        "linha_fonte": 1,
        "assinatura_registro": "same-signature",
    }
    a = validate_ingest_batch(_ingest_envelope([row], collection_id="col-a"))
    b = validate_ingest_batch(_ingest_envelope([row], collection_id="col-b"))
    assert a.ok and b.ok
    assert a.batch["idempotency_key"] != b.batch["idempotency_key"]
    assert a.batch["records"][0]["assinatura_registro"] == "same-signature"
