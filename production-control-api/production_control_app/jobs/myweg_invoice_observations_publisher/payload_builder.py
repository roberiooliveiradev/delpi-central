"""Montagem do lote `myweg.invoice-observations.batch.v1`."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from production_control_app.domain.myweg_invoice_observations_contract import (
    ALLOWED_BRANCH,
    CONTRACT_VERSION,
    MYWEG_COMPANY_CODE,
    MYWEG_SUPPLIER_CODE,
    MYWEG_WORK_CENTER,
    build_idempotency_key,
    compute_payload_sha256,
    compute_semantic_sha256,
    decimal_to_canonical_str,
)
from production_control_app.domain.services.myweg_invoice_observations_normalization import (
    validate_ingest_observation,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.collection_reader import (
    InvoiceCollectionArtifacts,
)


def build_ingest_payload(artifacts: InvoiceCollectionArtifacts) -> dict[str, Any]:
    payload_sha256 = compute_payload_sha256(artifacts.records)
    semantic_sha256 = compute_semantic_sha256(artifacts.records)
    total_un = sum(
        (
            Decimal(str(row["quantity_un"]))
            for row in artifacts.records
            if row.get("quantity_un") is not None
        ),
        Decimal("0"),
    )

    payload: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "collection_id": artifacts.collection_id,
        "branch": ALLOWED_BRANCH,
        "myweg_company_code": MYWEG_COMPANY_CODE,
        "myweg_work_center": MYWEG_WORK_CENTER,
        "myweg_supplier_code": MYWEG_SUPPLIER_CODE,
        "document_date": artifacts.document_date.isoformat(),
        "observation_status": artifacts.observation_status,
        "observed_at": (
            artifacts.observed_at.isoformat() if artifacts.observed_at else None
        ),
        "source_prepared_at": artifacts.source_prepared_at.isoformat(),
        "source_sha256": artifacts.source_sha256,
        "payload_sha256": payload_sha256,
        "semantic_sha256": semantic_sha256,
        "record_count": len(artifacts.records),
        "manifesto": artifacts.manifesto,
        "records": artifacts.records,
    }

    validation = validate_ingest_observation(payload)
    if not validation.ok or validation.batch is None:
        issues = "; ".join(
            f"{issue.path or '?'}: {issue.message}" for issue in validation.issues[:8]
        )
        raise ValueError(f"Validação de observação rejeitada: {issues}")

    return {
        "payload": payload,
        "batch": validation.batch,
        "idempotency_key": build_idempotency_key(
            collection_id=artifacts.collection_id,
            payload_sha256=payload_sha256,
        ),
        "record_count": len(artifacts.records),
        "total_quantity_un": decimal_to_canonical_str(total_un),
        "payload_sha256": payload_sha256,
        "semantic_sha256": semantic_sha256,
        "source_sha256": artifacts.source_sha256,
        "observation_status": artifacts.observation_status,
        "document_date": artifacts.document_date.isoformat(),
        "collection_id": artifacts.collection_id,
    }
