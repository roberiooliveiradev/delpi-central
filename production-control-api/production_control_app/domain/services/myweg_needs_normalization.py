"""Normalização e validação de lote MyWEG Necessidades (E1).

Domínio puro: Decimal, deduplicação, proteção filial 01, totais e SHA-256.
Não persiste, não chama Protheus/api-delpi.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Mapping, Sequence

from production_control_app.domain.myweg_needs_contract import (
    ALLOWED_BRANCH,
    CONTRACT_VERSION,
    ERROR_BRANCH_NOT_ALLOWED,
    ERROR_COMPANY_MISMATCH,
    ERROR_CONTRACT_VERSION_UNSUPPORTED,
    ERROR_DUPLICATE_LINE,
    ERROR_FILIAL_01_FORBIDDEN,
    ERROR_INVALID_RECORD,
    ERROR_PAYLOAD_SHA256_MISMATCH,
    ERROR_RECORD_COUNT_MISMATCH,
    ERROR_TOTALS_MISMATCH,
    ERROR_WORK_CENTER_MISMATCH,
    EXPECTED_UNIT,
    FORBIDDEN_BRANCH,
    MYWEG_COMPANY_CODE,
    MYWEG_WORK_CENTER,
    UN_TO_MI_DIVISOR,
    build_idempotency_key,
    build_line_fingerprint,
    compute_payload_sha256,
    decimal_to_canonical_str,
    pending_sb1_resolution,
)

_MI_QUANTIZE = Decimal("0.000001")


@dataclass(frozen=True)
class MyWegNeedsValidationIssue:
    code: str
    message: str
    path: str | None = None


@dataclass
class MyWegNeedsNormalizationResult:
    ok: bool
    batch: dict[str, Any] | None = None
    issues: list[MyWegNeedsValidationIssue] = field(default_factory=list)

    @property
    def error_codes(self) -> list[str]:
        return [issue.code for issue in self.issues]


def un_to_mi(quantidade_original_un: Decimal) -> Decimal:
    """Conversão exata UN → MI (divisor 1000)."""
    return (quantidade_original_un / UN_TO_MI_DIVISOR).quantize(
        _MI_QUANTIZE, rounding=ROUND_HALF_UP
    )


def _as_decimal(value: Any, *, path: str, issues: list[MyWegNeedsValidationIssue]) -> Decimal | None:
    if value is None or value == "":
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message="Quantidade ausente.",
                path=path,
            )
        )
        return None
    if isinstance(value, Decimal):
        number = value
    else:
        text = str(value).strip().replace(" ", "")
        # Compatibilidade PT-BR: 1.234,567 ou 1234,567 → Decimal
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        try:
            number = Decimal(text)
        except (InvalidOperation, ValueError):
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_INVALID_RECORD,
                    message=f"Quantidade inválida: {value!r}.",
                    path=path,
                )
            )
            return None
    if not number.is_finite() or number <= 0:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message="Quantidade deve ser finita e > 0.",
                path=path,
            )
        )
        return None
    return number


def _text(value: Any) -> str:
    return str(value or "").strip()


def _parse_remessa(value: Any) -> str | None:
    text = _text(value)
    if not text:
        return None
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        try:
            date.fromisoformat(text[:10])
            return text[:10]
        except ValueError:
            return None
    # Compatibilidade comum em CSV BR: DD/MM/YYYY
    if len(text) >= 10 and text[2] == "/" and text[5] == "/":
        day, month, year = text[:2], text[3:5], text[6:10]
        try:
            parsed = date(int(year), int(month), int(day))
            return parsed.isoformat()
        except ValueError:
            return None
    return None


def _contains_filial_01(payload: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> bool:
    branch = _text(payload.get("branch"))
    if branch == FORBIDDEN_BRANCH:
        return True
    for key in ("filial", "branch_code", "filial_codigo"):
        if _text(payload.get(key)) == FORBIDDEN_BRANCH:
            return True
    for row in records:
        for key in ("filial", "branch", "filial_codigo", "branch_code"):
            if _text(row.get(key)) == FORBIDDEN_BRANCH:
                return True
    return False


def normalize_source_record(
    raw: Mapping[str, Any],
    *,
    index: int,
    issues: list[MyWegNeedsValidationIssue],
) -> dict[str, Any] | None:
    """Normaliza uma linha compatível com necessidades_tratadas.*."""
    path = f"records[{index}]"
    material = _text(
        raw.get("material_weg_tratado")
        or raw.get("Material WEG Tratado")
        or raw.get("material")
    )
    referencia = _text(
        raw.get("codigo_referencia_weg")
        or raw.get("Codigo Referencia WEG")
        or raw.get("codigo_referencia")
    )
    origem = _text(
        raw.get("origem_material_weg")
        or raw.get("Origem Material WEG")
        or raw.get("origem")
    )
    unidade = _text(raw.get("unidade") or raw.get("Unidade") or EXPECTED_UNIT).upper()
    remessa = _parse_remessa(raw.get("data_remessa") or raw.get("Data Remessa") or raw.get("remessa"))
    documento_raw = raw.get("documento") if "documento" in raw else raw.get("Documento")
    documento = _text(documento_raw) or None
    rastreabilidade = _text(
        raw.get("rastreabilidade")
        or raw.get("Rastreabilidade")
        or raw.get("traceability")
    )
    qty_raw = (
        raw.get("quantidade_original_un")
        if "quantidade_original_un" in raw
        else raw.get("quantidade_original")
        if "quantidade_original" in raw
        else raw.get("Quantidade")
        if "Quantidade" in raw
        else raw.get("quantidade")
    )

    if not material or not referencia or not origem or remessa is None or not rastreabilidade:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message="Campos obrigatórios ausentes ou data_remessa inválida.",
                path=path,
            )
        )
        return None

    if unidade != EXPECTED_UNIT:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message=f"Unidade não suportada nesta etapa: {unidade!r} (esperado UN).",
                path=f"{path}.unidade",
            )
        )
        return None

    qty_un = _as_decimal(qty_raw, path=f"{path}.quantidade_original_un", issues=issues)
    if qty_un is None:
        return None

    qty_mi = un_to_mi(qty_un)
    fingerprint = build_line_fingerprint(
        material_weg_tratado=material,
        codigo_referencia_weg=referencia,
        origem_material_weg=origem,
        data_remessa=remessa,
        documento=documento,
        quantidade_original_un=qty_un,
    )
    return {
        "material_weg_tratado": material,
        "codigo_referencia_weg": referencia,
        "origem_material_weg": origem,
        "quantidade_original_un": decimal_to_canonical_str(qty_un),
        "quantidade_mi": decimal_to_canonical_str(qty_mi),
        "unidade": unidade,
        "data_remessa": remessa,
        "documento": documento,
        "rastreabilidade": rastreabilidade,
        "line_fingerprint": fingerprint,
        "sb1_resolution": pending_sb1_resolution(),
    }


def normalize_and_validate_batch(payload: Mapping[str, Any]) -> MyWegNeedsNormalizationResult:
    """Valida envelope + normaliza records a partir de payload de origem ou lote v1."""
    issues: list[MyWegNeedsValidationIssue] = []
    raw_records = payload.get("records")
    if not isinstance(raw_records, list):
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message="Campo records deve ser uma lista.",
                path="records",
            )
        )
        return MyWegNeedsNormalizationResult(ok=False, issues=issues)

    contract_version = _text(payload.get("contract_version") or CONTRACT_VERSION)
    if contract_version != CONTRACT_VERSION:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_CONTRACT_VERSION_UNSUPPORTED,
                message=f"Versão não suportada: {contract_version!r}.",
                path="contract_version",
            )
        )

    branch = _text(payload.get("branch"))
    if _contains_filial_01(payload, raw_records):
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_FILIAL_01_FORBIDDEN,
                message="Lote contém dados da filial 01 — rejeitado.",
                path="branch",
            )
        )
    elif branch != ALLOWED_BRANCH:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_BRANCH_NOT_ALLOWED,
                message=f"Filial {branch!r} não permitida; somente 02.",
                path="branch",
            )
        )

    company = _text(payload.get("myweg_company_code") or MYWEG_COMPANY_CODE)
    if company != MYWEG_COMPANY_CODE:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_COMPANY_MISMATCH,
                message=f"Empresa MyWEG {company!r} ≠ {MYWEG_COMPANY_CODE}.",
                path="myweg_company_code",
            )
        )

    work_center = _text(payload.get("myweg_work_center") or MYWEG_WORK_CENTER)
    if work_center != MYWEG_WORK_CENTER:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_WORK_CENTER_MISMATCH,
                message=f"Centro {work_center!r} ≠ {MYWEG_WORK_CENTER}.",
                path="myweg_work_center",
            )
        )

    collection_id = _text(payload.get("collection_id"))
    if not collection_id:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message="collection_id é obrigatório.",
                path="collection_id",
            )
        )

    collected_at = _require_aware_datetime(payload.get("collected_at"), "collected_at", issues)
    exported_at = _require_aware_datetime(payload.get("exported_at"), "exported_at", issues)

    normalized: list[dict[str, Any]] = []
    seen_fingerprints: set[str] = set()
    for index, raw in enumerate(raw_records):
        if not isinstance(raw, Mapping):
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_INVALID_RECORD,
                    message="Registro deve ser objeto.",
                    path=f"records[{index}]",
                )
            )
            continue
        row = normalize_source_record(raw, index=index, issues=issues)
        if row is None:
            continue
        fingerprint = str(row["line_fingerprint"])
        if fingerprint in seen_fingerprints:
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_DUPLICATE_LINE,
                    message="Linha duplicada no lote.",
                    path=f"records[{index}]",
                )
            )
            continue
        seen_fingerprints.add(fingerprint)
        normalized.append(row)

    declared_count = payload.get("record_count")
    if declared_count is None:
        declared_count = len(raw_records)
    try:
        declared_count_int = int(declared_count)
    except (TypeError, ValueError):
        declared_count_int = -1
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_RECORD_COUNT_MISMATCH,
                message="record_count inválido.",
                path="record_count",
            )
        )

    if declared_count_int != len(raw_records):
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_RECORD_COUNT_MISMATCH,
                message=(
                    f"record_count={declared_count_int} diverge de len(records)="
                    f"{len(raw_records)}."
                ),
                path="record_count",
            )
        )

    # Totais só sobre linhas normalizadas com sucesso (lote completo exige zero issues).
    total_un = sum(
        (Decimal(str(row["quantidade_original_un"])) for row in normalized),
        Decimal("0"),
    )
    total_mi = sum((Decimal(str(row["quantidade_mi"])) for row in normalized), Decimal("0"))

    declared_totals = payload.get("totals") if isinstance(payload.get("totals"), Mapping) else {}
    if declared_totals:
        declared_un = _optional_decimal(declared_totals.get("quantidade_original_un"))
        declared_mi = _optional_decimal(declared_totals.get("quantidade_mi"))
        if declared_un is not None and declared_un != total_un:
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_TOTALS_MISMATCH,
                    message=(
                        f"totals.quantidade_original_un={declared_un} ≠ soma {total_un}."
                    ),
                    path="totals.quantidade_original_un",
                )
            )
        if declared_mi is not None and declared_mi != total_mi:
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_TOTALS_MISMATCH,
                    message=f"totals.quantidade_mi={declared_mi} ≠ soma {total_mi}.",
                    path="totals.quantidade_mi",
                )
            )

    payload_sha256 = compute_payload_sha256(normalized)
    declared_sha = _text(payload.get("payload_sha256")).lower()
    if declared_sha and declared_sha != payload_sha256:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_PAYLOAD_SHA256_MISMATCH,
                message="payload_sha256 diverge do canônico das records normalizadas.",
                path="payload_sha256",
            )
        )

    if issues:
        return MyWegNeedsNormalizationResult(ok=False, issues=issues)

    source_files = payload.get("source_files") if isinstance(payload.get("source_files"), Mapping) else {}
    batch = {
        "contract_version": CONTRACT_VERSION,
        "collection_id": collection_id,
        "branch": ALLOWED_BRANCH,
        "myweg_company_code": MYWEG_COMPANY_CODE,
        "myweg_work_center": MYWEG_WORK_CENTER,
        "collected_at": collected_at.isoformat() if collected_at else None,
        "exported_at": exported_at.isoformat() if exported_at else None,
        "source_files": dict(source_files),
        "payload_sha256": payload_sha256,
        "record_count": len(normalized),
        "totals": {
            "quantidade_original_un": decimal_to_canonical_str(total_un),
            "quantidade_mi": decimal_to_canonical_str(total_mi),
        },
        "idempotency_key": build_idempotency_key(
            collection_id=collection_id,
            payload_sha256=payload_sha256,
        ),
        "records": normalized,
    }
    return MyWegNeedsNormalizationResult(ok=True, batch=batch, issues=[])


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        text = str(value).strip().replace(" ", "")
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def _require_aware_datetime(
    value: Any,
    path: str,
    issues: list[MyWegNeedsValidationIssue],
) -> datetime | None:
    if value is None or value == "":
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message=f"{path} é obrigatório.",
                path=path,
            )
        )
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = _text(value).replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_INVALID_RECORD,
                    message=f"{path} deve ser ISO-8601.",
                    path=path,
                )
            )
            return None
    if parsed.tzinfo is None:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message=f"{path} deve incluir timezone.",
                path=path,
            )
        )
        return None
    return parsed
