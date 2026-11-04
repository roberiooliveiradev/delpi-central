"""Montagem do lote myweg.needs.batch.v1 reutilizando o domínio E1."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from production_control_app.domain.myweg_needs_contract import (
    ALLOWED_BRANCH,
    CONTRACT_VERSION,
    MYWEG_COMPANY_CODE,
    MYWEG_WORK_CENTER,
    build_idempotency_key,
    compute_payload_sha256,
    decimal_to_canonical_str,
)
from production_control_app.domain.services.myweg_needs_normalization import (
    normalize_source_records,
    validate_ingest_batch,
)
from production_control_app.jobs.myweg_needs_publisher.collection_reader import (
    CollectionArtifacts,
)

_SAO_PAULO = ZoneInfo("America/Sao_Paulo")

_SOURCE_HASH_KEYS = {
    "necessidades_tratadas.csv": "necessidades_tratadas_csv_sha256",
    "necessidades_tratadas.xlsx": "necessidades_tratadas_xlsx_sha256",
    "para_conferencia_pcp.csv": "para_conferencia_pcp_csv_sha256",
    "resumo.json": "resumo_json_sha256",
}


def build_ingest_payload(artifacts: CollectionArtifacts) -> dict[str, Any]:
    normalized = normalize_source_records(artifacts.source_rows)
    if not normalized.ok:
        issues = "; ".join(
            f"{issue.path or '?'}: {issue.message}" for issue in normalized.issues[:8]
        )
        raise ValueError(f"Normalização de origem rejeitada: {issues}")

    totals_un = sum(
        (Decimal(str(row["quantidade_original_un"])) for row in normalized.records),
        Decimal("0"),
    )
    totals_mi = sum(
        (Decimal(str(row["quantidade_mi"])) for row in normalized.records),
        Decimal("0"),
    )
    payload_sha256 = compute_payload_sha256(normalized.records)
    source_files = {
        _SOURCE_HASH_KEYS[name]: digest
        for name, digest in artifacts.file_hashes.items()
    }
    exported_at = datetime.now(tz=_SAO_PAULO).astimezone(timezone.utc)

    payload = {
        "contract_version": CONTRACT_VERSION,
        "collection_id": artifacts.collection_id,
        "branch": ALLOWED_BRANCH,
        "myweg_company_code": MYWEG_COMPANY_CODE,
        "myweg_work_center": MYWEG_WORK_CENTER,
        "collected_at": artifacts.collected_at.isoformat(),
        "exported_at": exported_at.isoformat(),
        "source_files": source_files,
        "record_count": len(normalized.records),
        "totals": {
            "quantidade_original_un": decimal_to_canonical_str(totals_un),
            "quantidade_mi": decimal_to_canonical_str(totals_mi),
        },
        "payload_sha256": payload_sha256,
        "records": artifacts.source_rows,
    }

    validation = validate_ingest_batch(payload)
    if not validation.ok or validation.batch is None:
        issues = "; ".join(
            f"{issue.path or '?'}: {issue.message}" for issue in validation.issues[:8]
        )
        raise ValueError(f"Validação de lote rejeitada: {issues}")

    return {
        "payload": payload,
        "batch": validation.batch,
        "idempotency_key": build_idempotency_key(
            collection_id=artifacts.collection_id,
            payload_sha256=payload_sha256,
        ),
        "record_count": len(normalized.records),
        "empty_referencia_count": sum(
            1
            for row in validation.batch["records"]
            if row.get("codigo_referencia_weg") is None
        ),
    }
