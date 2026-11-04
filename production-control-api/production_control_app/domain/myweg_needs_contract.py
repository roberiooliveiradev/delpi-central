"""Contrato versionado MyWEG Necessidades — `myweg.needs.batch.v1`.

Somente constantes, fingerprints e hash canônico. Sem I/O, sem Protheus.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any, Mapping, Sequence

CONTRACT_VERSION = "myweg.needs.batch.v1"

ALLOWED_BRANCH = "02"
FORBIDDEN_BRANCH = "01"
MYWEG_COMPANY_CODE = "1009"
MYWEG_WORK_CENTER = "1106"

UN_TO_MI_DIVISOR = Decimal("1000")
EXPECTED_UNIT = "UN"

# Referência homologada (corpus conhecido).
REFERENCE_RECORD_COUNT = 532
REFERENCE_TOTAL_UN = Decimal("745746")
REFERENCE_TOTAL_MI = Decimal("745.746")

SB1_STATUS_PENDING = "pending"

ERROR_BRANCH_NOT_ALLOWED = "branch_not_allowed"
ERROR_FILIAL_01_FORBIDDEN = "filial_01_forbidden"
ERROR_COMPANY_MISMATCH = "company_mismatch"
ERROR_WORK_CENTER_MISMATCH = "work_center_mismatch"
ERROR_RECORD_COUNT_MISMATCH = "record_count_mismatch"
ERROR_TOTALS_MISMATCH = "totals_mismatch"
ERROR_PAYLOAD_SHA256_MISMATCH = "payload_sha256_mismatch"
ERROR_DUPLICATE_LINE = "duplicate_line"
ERROR_INVALID_RECORD = "invalid_record"
ERROR_CONTRACT_VERSION_UNSUPPORTED = "contract_version_unsupported"

_RECORD_HASH_FIELDS = (
    "material_weg_tratado",
    "codigo_referencia_weg",
    "origem_material_weg",
    "quantidade_original_un",
    "quantidade_mi",
    "unidade",
    "data_remessa",
    "documento",
    "rastreabilidade",
)


def decimal_to_canonical_str(value: Decimal) -> str:
    """Representação decimal estável (sem notação científica, sem zeros inúteis)."""
    normalized = value.normalize() if value != 0 else Decimal("0")
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def build_line_fingerprint(
    *,
    material_weg_tratado: str,
    codigo_referencia_weg: str,
    origem_material_weg: str,
    data_remessa: str,
    documento: str | None,
    quantidade_original_un: Decimal,
) -> str:
    """Chave de deduplicação estável dentro do lote."""
    payload = "|".join(
        [
            material_weg_tratado.strip(),
            codigo_referencia_weg.strip(),
            origem_material_weg.strip(),
            data_remessa.strip(),
            (documento or "").strip(),
            decimal_to_canonical_str(quantidade_original_un),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_idempotency_key(*, collection_id: str, payload_sha256: str) -> str:
    return f"{collection_id.strip()}:{payload_sha256.strip().lower()}"


def canonical_records_payload(records: Sequence[Mapping[str, Any]]) -> str:
    """JSON canônico das linhas (ordenação de chaves, sem espaços)."""
    slim: list[dict[str, Any]] = []
    for row in records:
        slim.append({field: row.get(field) for field in _RECORD_HASH_FIELDS})
    return json.dumps(slim, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_payload_sha256(records: Sequence[Mapping[str, Any]]) -> str:
    return sha256_hex(canonical_records_payload(records))


def pending_sb1_resolution() -> dict[str, Any]:
    return {
        "status": SB1_STATUS_PENDING,
        "protheus_product_code": None,
        "matched_by": None,
        "resolved_at": None,
    }
