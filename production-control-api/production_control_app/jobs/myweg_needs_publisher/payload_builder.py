"""Montagem do lote myweg.needs.batch.v1 reutilizando o domínio E1."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
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
    UN_TO_MI_DIVISOR,
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


def _split_unidentified_materials(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Segrega somente linhas sem qualquer identificador de material.

    Outros erros (unidade, quantidade, data, origem, duplicidade) continuam
    sujeitos à validação fail-closed do contrato E1.
    """
    valid_rows: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    excluded_un = Decimal("0")

    for index, row in enumerate(rows):
        def field(name: str) -> str:
            value = row.get(name)
            return str(value).strip() if value is not None else ""

        identifiers = (
            field("material_weg_tratado"),
            field("material_weg_original"),
            field("codigo_referencia_weg"),
            field("codigo_produto_delpi"),
        )
        if any(identifiers):
            valid_rows.append(row)
            continue

        unit = field("unidade").upper() or "UN"
        quantity_text = field("quantidade").replace(" ", "")
        if "," in quantity_text and "." in quantity_text:
            quantity_text = quantity_text.replace(".", "").replace(",", ".")
        elif "," in quantity_text:
            quantity_text = quantity_text.replace(",", ".")
        try:
            quantity = Decimal(quantity_text)
        except (InvalidOperation, ValueError):
            valid_rows.append(row)
            continue

        # Somente o material pode faltar neste caminho. Outros defeitos
        # permanecem bloqueantes, sem classificação enganosa de "excluído".
        if (
            unit != "UN"
            or not quantity.is_finite()
            or quantity <= 0
            or not field("origem_material_weg")
            or not field("data_remessa")
            or not (field("linha_fonte") or field("assinatura_registro"))
        ):
            valid_rows.append(row)
            continue

        excluded_un += quantity
        excluded.append({
            "index": index,
            "sourceLine": field("linha_fonte"),
            "reason": "material_unidentified",
            "quantityOriginalUn": decimal_to_canonical_str(quantity),
            "unit": unit,
        })

    if not excluded:
        return valid_rows, None
    return valid_rows, {
        "sourceRecordCount": len(rows),
        "excludedCount": len(excluded),
        "excludedQuantityUn": decimal_to_canonical_str(excluded_un),
        "excludedQuantityMi": decimal_to_canonical_str(
            excluded_un / UN_TO_MI_DIVISOR
        ),
        "excludedRecords": excluded,
    }


def build_ingest_payload(artifacts: CollectionArtifacts) -> dict[str, Any]:
    valid_rows, quality = _split_unidentified_materials(artifacts.source_rows)
    if not valid_rows:
        raise ValueError("Coleta sem registros válidos: todos os materiais estão indefinidos.")
    normalized = normalize_source_records(valid_rows)
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
    if quality:
        source_files["quality"] = quality
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
        "records": valid_rows,
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
        "quality": quality,
        "empty_referencia_count": sum(
            1
            for row in validation.batch["records"]
            if row.get("codigo_referencia_weg") is None
        ),
    }
