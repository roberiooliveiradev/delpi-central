"""Normalização de origem e validação de lote MyWEG Necessidades (E1).

Duas fases distintas:

1. ``normalize_source_records`` — planilha/CSV real → linhas normalizadas
2. ``validate_ingest_batch`` — lote ``myweg.needs.batch.v1`` pronto para ingestão

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
    ERROR_INVALID_SOURCE_FILES,
    ERROR_MISSING_REQUIRED_FIELD,
    ERROR_PAYLOAD_SHA256_MISMATCH,
    ERROR_RECORD_COUNT_MISMATCH,
    ERROR_TOTALS_MISMATCH,
    ERROR_WORK_CENTER_MISMATCH,
    EXPECTED_UNIT,
    FORBIDDEN_BRANCH,
    MYWEG_COMPANY_CODE,
    MYWEG_WORK_CENTER,
    REQUIRED_SOURCE_FILE_HASH_KEYS,
    UN_TO_MI_DIVISOR,
    build_idempotency_key,
    build_line_fingerprint,
    compute_payload_sha256,
    decimal_to_canonical_str,
    is_sha256_hex,
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
    records: list[dict[str, Any]] = field(default_factory=list)
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
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        try:
            number = Decimal(text)
        except (InvalidOperation, ValueError, TypeError):
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
    if value is None:
        return ""
    return str(value).strip()


def _optional_text(value: Any) -> str | None:
    text = _text(value)
    return text or None


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
    if len(text) >= 10 and text[2] == "/" and text[5] == "/":
        day, month, year = text[:2], text[3:5], text[6:10]
        try:
            parsed = date(int(year), int(month), int(day))
            return parsed.isoformat()
        except ValueError:
            return None
    return None


def _pick_first(raw: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw:
            return raw.get(key)
    return None


def _build_rastreabilidade(raw: Mapping[str, Any]) -> str:
    """Preserva rastreabilidade explícita ou monta a partir da origem real."""
    existing = _text(
        _pick_first(raw, "rastreabilidade", "Rastreabilidade", "traceability")
    )
    if existing:
        return existing

    linha_fonte = _pick_first(raw, "linha_fonte", "Linha Fonte")
    assinatura = _optional_text(
        _pick_first(raw, "assinatura_registro", "Assinatura Registro")
    )
    parts: list[str] = []
    if linha_fonte is not None and _text(linha_fonte) != "":
        parts.append(f"linha_fonte={_text(linha_fonte)}")
    if assinatura:
        # Preservado na rastreabilidade; NÃO é identidade entre coletas.
        parts.append(f"assinatura_registro={assinatura}")
    return "|".join(parts)


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
    """Normaliza uma linha da planilha/CSV real (fase origem).

    ``codigo_referencia_weg`` pode ser vazio/nulo — permanece null com SB1 pending.
    """
    path = f"records[{index}]"
    try:
        if not isinstance(raw, Mapping):
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_INVALID_RECORD,
                    message="Registro deve ser objeto.",
                    path=path,
                )
            )
            return None

        material = _text(
            _pick_first(raw, "material_weg_tratado", "Material WEG Tratado", "material")
        )
        # Referência opcional: vazio/nulo é válido (não inventar código).
        referencia_raw = _pick_first(
            raw,
            "codigo_referencia_weg",
            "Codigo Referencia WEG",
            "codigo_referencia",
        )
        if referencia_raw is None or _text(referencia_raw) == "":
            referencia: str | None = None
        else:
            referencia = _text(referencia_raw)

        origem = _text(
            _pick_first(raw, "origem_material_weg", "Origem Material WEG", "origem")
        )
        unidade = _text(_pick_first(raw, "unidade", "Unidade") or EXPECTED_UNIT).upper()
        remessa = _parse_remessa(
            _pick_first(raw, "data_remessa", "Data Remessa", "remessa")
        )
        documento = _optional_text(_pick_first(raw, "documento", "Documento"))
        linha_fonte = _optional_text(_pick_first(raw, "linha_fonte", "Linha Fonte"))
        assinatura_registro = _optional_text(
            _pick_first(raw, "assinatura_registro", "Assinatura Registro")
        )
        rastreabilidade = _build_rastreabilidade(raw)

        qty_raw = _pick_first(
            raw,
            "quantidade_original_un",
            "quantidade_original",
            "quantidade",
            "Quantidade",
        )

        if not material or not origem or remessa is None or not rastreabilidade:
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_INVALID_RECORD,
                    message=(
                        "Campos obrigatórios ausentes, data_remessa inválida "
                        "ou rastreabilidade não derivável "
                        "(rastreabilidade / linha_fonte / assinatura_registro)."
                    ),
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
            linha_fonte=linha_fonte,
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
            "linha_fonte": linha_fonte,
            "assinatura_registro": assinatura_registro,
            "rastreabilidade": rastreabilidade,
            "line_fingerprint": fingerprint,
            "sb1_resolution": pending_sb1_resolution(),
        }
    except Exception as exc:  # noqa: BLE001 — malformado → erro de validação
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message=f"Registro malformado: {exc.__class__.__name__}.",
                path=path,
            )
        )
        return None


def normalize_source_records(
    raw_records: Sequence[Any],
) -> MyWegNeedsNormalizationResult:
    """Fase 1: normaliza dados de origem sem exigir envelope de ingestão."""
    issues: list[MyWegNeedsValidationIssue] = []
    if not isinstance(raw_records, list) and not isinstance(raw_records, tuple):
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message="Campo records deve ser uma lista.",
                path="records",
            )
        )
        return MyWegNeedsNormalizationResult(ok=False, issues=issues)

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

    if issues:
        return MyWegNeedsNormalizationResult(
            ok=False, records=normalized, issues=issues
        )
    return MyWegNeedsNormalizationResult(ok=True, records=normalized, issues=[])


def validate_ingest_batch(payload: Mapping[str, Any]) -> MyWegNeedsNormalizationResult:
    """Fase 2: valida lote versionado pronto para ingestão (campos e hashes obrigatórios)."""
    issues: list[MyWegNeedsValidationIssue] = []
    try:
        return _validate_ingest_batch(payload, issues)
    except Exception as exc:  # noqa: BLE001
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message=f"Payload malformado: {exc.__class__.__name__}.",
                path="$",
            )
        )
        return MyWegNeedsNormalizationResult(ok=False, issues=issues)


def normalize_and_validate_batch(payload: Mapping[str, Any]) -> MyWegNeedsNormalizationResult:
    """Compatibilidade: normaliza records de origem e valida o lote de ingestão.

    Se ``records`` já parecerem normalizadas (possuem ``quantidade_original_un``),
    ainda assim passam pela normalização idempotente de campos.
    """
    return validate_ingest_batch(payload)


def _validate_ingest_batch(
    payload: Mapping[str, Any],
    issues: list[MyWegNeedsValidationIssue],
) -> MyWegNeedsNormalizationResult:
    if not isinstance(payload, Mapping):
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_INVALID_RECORD,
                message="Payload do lote deve ser objeto.",
                path="$",
            )
        )
        return MyWegNeedsNormalizationResult(ok=False, issues=issues)

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

    # --- envelope obrigatório (lote pronto) ---
    if "contract_version" not in payload or _text(payload.get("contract_version")) == "":
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="contract_version é obrigatório.",
                path="contract_version",
            )
        )
    else:
        contract_version = _text(payload.get("contract_version"))
        if contract_version != CONTRACT_VERSION:
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_CONTRACT_VERSION_UNSUPPORTED,
                    message=f"Versão não suportada: {contract_version!r}.",
                    path="contract_version",
                )
            )

    collection_id = _text(payload.get("collection_id"))
    if not collection_id:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="collection_id é obrigatório.",
                path="collection_id",
            )
        )

    if "branch" not in payload or _text(payload.get("branch")) == "":
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="branch é obrigatório.",
                path="branch",
            )
        )
    else:
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

    if "myweg_company_code" not in payload or _text(payload.get("myweg_company_code")) == "":
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="myweg_company_code é obrigatório.",
                path="myweg_company_code",
            )
        )
    else:
        company = _text(payload.get("myweg_company_code"))
        if company != MYWEG_COMPANY_CODE:
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_COMPANY_MISMATCH,
                    message=f"Empresa MyWEG {company!r} ≠ {MYWEG_COMPANY_CODE}.",
                    path="myweg_company_code",
                )
            )

    if "myweg_work_center" not in payload or _text(payload.get("myweg_work_center")) == "":
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="myweg_work_center é obrigatório.",
                path="myweg_work_center",
            )
        )
    else:
        work_center = _text(payload.get("myweg_work_center"))
        if work_center != MYWEG_WORK_CENTER:
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_WORK_CENTER_MISMATCH,
                    message=f"Centro {work_center!r} ≠ {MYWEG_WORK_CENTER}.",
                    path="myweg_work_center",
                )
            )

    collected_at = _require_aware_datetime(payload.get("collected_at"), "collected_at", issues)
    exported_at = _require_aware_datetime(payload.get("exported_at"), "exported_at", issues)

    source_files = payload.get("source_files")
    if not isinstance(source_files, Mapping):
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="source_files é obrigatório.",
                path="source_files",
            )
        )
        source_files = {}
    else:
        for key in REQUIRED_SOURCE_FILE_HASH_KEYS:
            value = _text(source_files.get(key)).lower()
            if not value:
                issues.append(
                    MyWegNeedsValidationIssue(
                        code=ERROR_MISSING_REQUIRED_FIELD,
                        message=f"source_files.{key} é obrigatório.",
                        path=f"source_files.{key}",
                    )
                )
            elif not is_sha256_hex(value):
                issues.append(
                    MyWegNeedsValidationIssue(
                        code=ERROR_INVALID_SOURCE_FILES,
                        message=f"source_files.{key} deve ser SHA-256 hex (64).",
                        path=f"source_files.{key}",
                    )
                )

    if "record_count" not in payload:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="record_count é obrigatório.",
                path="record_count",
            )
        )
        declared_count_int = -1
    else:
        try:
            declared_count_int = int(payload.get("record_count"))
        except (TypeError, ValueError):
            declared_count_int = -1
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_RECORD_COUNT_MISMATCH,
                    message="record_count inválido.",
                    path="record_count",
                )
            )

    if declared_count_int != -1 and declared_count_int != len(raw_records):
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

    if "totals" not in payload or not isinstance(payload.get("totals"), Mapping):
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="totals é obrigatório.",
                path="totals",
            )
        )
        declared_totals: Mapping[str, Any] = {}
    else:
        declared_totals = payload["totals"]  # type: ignore[assignment]
        if (
            "quantidade_original_un" not in declared_totals
            or _text(declared_totals.get("quantidade_original_un")) == ""
        ):
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_MISSING_REQUIRED_FIELD,
                    message="totals.quantidade_original_un é obrigatório.",
                    path="totals.quantidade_original_un",
                )
            )
        if (
            "quantidade_mi" not in declared_totals
            or _text(declared_totals.get("quantidade_mi")) == ""
        ):
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_MISSING_REQUIRED_FIELD,
                    message="totals.quantidade_mi é obrigatório.",
                    path="totals.quantidade_mi",
                )
            )

    declared_sha = _text(payload.get("payload_sha256")).lower()
    if not declared_sha:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="payload_sha256 é obrigatório.",
                path="payload_sha256",
            )
        )
    elif not is_sha256_hex(declared_sha):
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_PAYLOAD_SHA256_MISMATCH,
                message="payload_sha256 deve ser SHA-256 hex (64).",
                path="payload_sha256",
            )
        )

    # --- normalização das linhas (fase origem embutida) ---
    source_result = normalize_source_records(raw_records)
    issues.extend(source_result.issues)
    normalized = list(source_result.records)

    total_un = sum(
        (Decimal(str(row["quantidade_original_un"])) for row in normalized),
        Decimal("0"),
    )
    total_mi = sum((Decimal(str(row["quantidade_mi"])) for row in normalized), Decimal("0"))

    if declared_totals:
        declared_un = _optional_decimal(declared_totals.get("quantidade_original_un"))
        declared_mi = _optional_decimal(declared_totals.get("quantidade_mi"))
        if (
            "quantidade_original_un" in declared_totals
            and _text(declared_totals.get("quantidade_original_un")) != ""
            and declared_un is not None
            and declared_un != total_un
        ):
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_TOTALS_MISMATCH,
                    message=(
                        f"totals.quantidade_original_un={declared_un} ≠ soma {total_un}."
                    ),
                    path="totals.quantidade_original_un",
                )
            )
        if (
            "quantidade_mi" in declared_totals
            and _text(declared_totals.get("quantidade_mi")) != ""
            and declared_mi is not None
            and declared_mi != total_mi
        ):
            issues.append(
                MyWegNeedsValidationIssue(
                    code=ERROR_TOTALS_MISMATCH,
                    message=f"totals.quantidade_mi={declared_mi} ≠ soma {total_mi}.",
                    path="totals.quantidade_mi",
                )
            )

    payload_sha256 = compute_payload_sha256(normalized)
    if declared_sha and is_sha256_hex(declared_sha) and declared_sha != payload_sha256:
        issues.append(
            MyWegNeedsValidationIssue(
                code=ERROR_PAYLOAD_SHA256_MISMATCH,
                message="payload_sha256 diverge do canônico das records normalizadas.",
                path="payload_sha256",
            )
        )

    if issues:
        return MyWegNeedsNormalizationResult(
            ok=False, records=normalized, issues=issues
        )

    batch = {
        "contract_version": CONTRACT_VERSION,
        "collection_id": collection_id,
        "branch": ALLOWED_BRANCH,
        "myweg_company_code": MYWEG_COMPANY_CODE,
        "myweg_work_center": MYWEG_WORK_CENTER,
        "collected_at": collected_at.isoformat() if collected_at else None,
        "exported_at": exported_at.isoformat() if exported_at else None,
        "source_files": {
            key: _text(source_files.get(key)).lower()
            for key in REQUIRED_SOURCE_FILE_HASH_KEYS
        },
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
    return MyWegNeedsNormalizationResult(
        ok=True, batch=batch, records=normalized, issues=[]
    )


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
    except (InvalidOperation, ValueError, TypeError):
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
                code=ERROR_MISSING_REQUIRED_FIELD,
                message=f"{path} é obrigatório.",
                path=path,
            )
        )
        return None
    try:
        if isinstance(value, datetime):
            parsed = value
        else:
            text = _text(value).replace("Z", "+00:00")
            parsed = datetime.fromisoformat(text)
    except (TypeError, ValueError):
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
