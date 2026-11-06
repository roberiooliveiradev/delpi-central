"""Contrato versionado MyWEG NF Emitidas — `myweg.invoice-observations.batch.v1`.

Constantes, fingerprints e hashes canônicos. Sem I/O, sem Protheus, sem abatimento.
Totais da amostra 05/11/2026 NÃO são invariantes permanentes do contrato.
"""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from typing import Any, Mapping, Sequence

CONTRACT_VERSION = "myweg.invoice-observations.batch.v1"

ALLOWED_BRANCH = "02"
FORBIDDEN_BRANCH = "01"
MYWEG_COMPANY_CODE = "1009"
MYWEG_WORK_CENTER = "1106"
MYWEG_SUPPLIER_CODE = "50471"

OBSERVATION_STATUS_WITH_RECORDS = "with_records"
OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP = "empty_signaled_by_sap"
ALLOWED_OBSERVATION_STATUSES = frozenset(
    {
        OBSERVATION_STATUS_WITH_RECORDS,
        OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP,
    }
)

UNIT_COMPARABILITY_COMPARABLE = "comparable"
UNIT_COMPARABILITY_NON_COMPARABLE = "non_comparable"

UN_TO_MI_MULTIPLIER = Decimal("1000")
COMPARABLE_UNITS = frozenset({"UN", "MI"})

# Manifesto Windows (origem) → status de observação do contrato HTTP.
MANIFEST_STATUS_VALIDATED = "VALIDADO"
MANIFEST_STATUS_EMPTY_SAP = "SEM_REGISTROS_SINALIZADOS_PELO_SAP"

ERROR_BRANCH_NOT_ALLOWED = "branch_not_allowed"
ERROR_FILIAL_01_FORBIDDEN = "filial_01_forbidden"
ERROR_COMPANY_MISMATCH = "company_mismatch"
ERROR_WORK_CENTER_MISMATCH = "work_center_mismatch"
ERROR_SUPPLIER_MISMATCH = "supplier_mismatch"
ERROR_RECORD_COUNT_MISMATCH = "record_count_mismatch"
ERROR_PAYLOAD_SHA256_MISMATCH = "payload_sha256_mismatch"
ERROR_SEMANTIC_SHA256_MISMATCH = "semantic_sha256_mismatch"
ERROR_SOURCE_SHA256_MISMATCH = "source_sha256_mismatch"
ERROR_INVALID_RECORD = "invalid_record"
ERROR_CONTRACT_VERSION_UNSUPPORTED = "contract_version_unsupported"
ERROR_MISSING_REQUIRED_FIELD = "missing_required_field"
ERROR_INVALID_OBSERVATION_STATUS = "invalid_observation_status"
ERROR_EMPTY_WITH_RECORDS = "empty_status_with_records"
ERROR_WITH_RECORDS_EMPTY = "with_records_status_empty"
ERROR_UNKNOWN_UNIT = "unknown_unit"
ERROR_INVALID_QUANTITY = "invalid_quantity"
ERROR_INVALID_DATE = "invalid_date"

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

_RECORD_HASH_FIELDS = (
    "source_line_no",
    "invoice_number",
    "invoice_series",
    "material_weg",
    "material_description",
    "quantity_original",
    "source_unit",
    "quantity_un",
    "unit_comparability",
    "departure_date",
)

_SEMANTIC_FIELDS = (
    "invoice_number",
    "invoice_series",
    "material_weg",
    "quantity_original",
    "source_unit",
    "departure_date",
)


def decimal_to_canonical_str(value: Decimal) -> str:
    """Representação decimal estável (sem notação científica, sem zeros inúteis)."""
    normalized = value.normalize() if value != 0 else Decimal("0")
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_sha256_hex(value: str) -> bool:
    return bool(_SHA256_HEX_RE.fullmatch(value.strip().lower()))


def build_idempotency_key(*, collection_id: str, payload_sha256: str) -> str:
    return f"{collection_id.strip()}:{payload_sha256.strip().lower()}"


def quantity_to_un(*, quantity_original: Decimal, source_unit: str) -> tuple[Decimal | None, str]:
    """Converte UN/MI → UN. Outras unidades → não comparáveis (sem conversão)."""
    unit = source_unit.strip().upper()
    if unit == "UN":
        return quantity_original, UNIT_COMPARABILITY_COMPARABLE
    if unit == "MI":
        return quantity_original * UN_TO_MI_MULTIPLIER, UNIT_COMPARABILITY_COMPARABLE
    return None, UNIT_COMPARABILITY_NON_COMPARABLE


def canonical_records_payload(records: Sequence[Mapping[str, Any]]) -> str:
    slim: list[dict[str, Any]] = []
    for row in records:
        slim.append({field: row.get(field) for field in _RECORD_HASH_FIELDS})
    return json.dumps(slim, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def compute_payload_sha256(records: Sequence[Mapping[str, Any]]) -> str:
    return sha256_hex(canonical_records_payload(records))


def compute_semantic_sha256(records: Sequence[Mapping[str, Any]]) -> str:
    """Hash do multiconjunto normalizado (ordem irrelevante; multiplicidade preservada)."""
    tokens: list[str] = []
    for row in records:
        parts = []
        for field in _SEMANTIC_FIELDS:
            value = row.get(field)
            if value is None:
                parts.append("")
            elif isinstance(value, Decimal):
                parts.append(decimal_to_canonical_str(value))
            else:
                parts.append(str(value).strip())
        tokens.append("|".join(parts))
    tokens.sort()
    return sha256_hex("\n".join(tokens))


def manifest_status_to_observation_status(manifest_status: str) -> str | None:
    status = (manifest_status or "").strip().upper()
    if status == MANIFEST_STATUS_VALIDATED:
        return OBSERVATION_STATUS_WITH_RECORDS
    if status == MANIFEST_STATUS_EMPTY_SAP:
        return OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP
    return None
