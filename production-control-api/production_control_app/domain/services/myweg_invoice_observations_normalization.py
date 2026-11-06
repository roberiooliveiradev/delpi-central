"""Validação do contrato `myweg.invoice-observations.batch.v1`."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from production_control_app.domain.myweg_invoice_observations_contract import (
    ALLOWED_BRANCH,
    ALLOWED_OBSERVATION_STATUSES,
    COMPARABLE_UNITS,
    CONTRACT_VERSION,
    ERROR_BRANCH_NOT_ALLOWED,
    ERROR_COMPANY_MISMATCH,
    ERROR_CONTRACT_VERSION_UNSUPPORTED,
    ERROR_EMPTY_WITH_RECORDS,
    ERROR_FILIAL_01_FORBIDDEN,
    ERROR_INVALID_DATE,
    ERROR_INVALID_OBSERVATION_STATUS,
    ERROR_INVALID_QUANTITY,
    ERROR_INVALID_RECORD,
    ERROR_MISSING_REQUIRED_FIELD,
    ERROR_PAYLOAD_SHA256_MISMATCH,
    ERROR_RECORD_COUNT_MISMATCH,
    ERROR_SEMANTIC_SHA256_MISMATCH,
    ERROR_SOURCE_SHA256_MISMATCH,
    ERROR_SUPPLIER_MISMATCH,
    ERROR_UNKNOWN_UNIT,
    ERROR_WITH_RECORDS_EMPTY,
    ERROR_WORK_CENTER_MISMATCH,
    FORBIDDEN_BRANCH,
    MYWEG_COMPANY_CODE,
    MYWEG_SUPPLIER_CODE,
    MYWEG_WORK_CENTER,
    OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP,
    OBSERVATION_STATUS_WITH_RECORDS,
    compute_payload_sha256,
    compute_semantic_sha256,
    decimal_to_canonical_str,
    is_sha256_hex,
    quantity_to_un,
)


@dataclass(frozen=True)
class MyWegInvoiceValidationIssue:
    code: str
    message: str
    path: str | None = None


@dataclass
class MyWegInvoiceNormalizationResult:
    ok: bool
    batch: dict[str, Any] | None = None
    records: list[dict[str, Any]] = field(default_factory=list)
    issues: list[MyWegInvoiceValidationIssue] = field(default_factory=list)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_decimal(
    value: Any, *, path: str, issues: list[MyWegInvoiceValidationIssue]
) -> Decimal | None:
    if value is None or _text(value) == "":
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_INVALID_QUANTITY,
                message="Quantidade obrigatória.",
                path=path,
            )
        )
        return None
    try:
        if isinstance(value, Decimal):
            qty = value
        elif isinstance(value, (int, float)):
            qty = Decimal(str(value))
        else:
            text = _text(value).replace(",", ".")
            qty = Decimal(text)
    except (InvalidOperation, ValueError, TypeError):
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_INVALID_QUANTITY,
                message=f"Quantidade inválida: {value!r}.",
                path=path,
            )
        )
        return None
    if qty <= 0:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_INVALID_QUANTITY,
                message="Quantidade deve ser positiva.",
                path=path,
            )
        )
        return None
    return qty


def _parse_date(
    value: Any, *, path: str, issues: list[MyWegInvoiceValidationIssue]
) -> str | None:
    text = _text(value)
    if not text:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_INVALID_DATE,
                message="Data obrigatória.",
                path=path,
            )
        )
        return None
    try:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, datetime):
            return value.date().isoformat()
        if "/" in text:
            day, month, year = text.split("/")
            parsed = date(int(year), int(month), int(day))
        else:
            parsed = date.fromisoformat(text[:10])
        return parsed.isoformat()
    except (TypeError, ValueError):
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_INVALID_DATE,
                message=f"Data inválida: {value!r}.",
                path=path,
            )
        )
        return None


def _parse_datetime_optional(
    value: Any, *, path: str, issues: list[MyWegInvoiceValidationIssue], required: bool
) -> str | None:
    text = _text(value)
    if not text:
        if required:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_MISSING_REQUIRED_FIELD,
                    message=f"Campo obrigatório ausente: {path}.",
                    path=path,
                )
            )
        return None
    try:
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_INVALID_DATE,
                    message="Timestamp deve incluir timezone.",
                    path=path,
                )
            )
            return None
        return dt.isoformat()
    except (TypeError, ValueError):
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_INVALID_DATE,
                message=f"Timestamp inválido: {value!r}.",
                path=path,
            )
        )
        return None


def normalize_invoice_records(
    records: list[Any] | None,
) -> MyWegInvoiceNormalizationResult:
    issues: list[MyWegInvoiceValidationIssue] = []
    if records is None:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="records é obrigatório.",
                path="records",
            )
        )
        return MyWegInvoiceNormalizationResult(ok=False, issues=issues)
    if not isinstance(records, list):
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_INVALID_RECORD,
                message="records deve ser um array.",
                path="records",
            )
        )
        return MyWegInvoiceNormalizationResult(ok=False, issues=issues)

    normalized: list[dict[str, Any]] = []
    seen_line_nos: set[int] = set()

    for index, raw in enumerate(records):
        path_prefix = f"records[{index}]"
        if not isinstance(raw, Mapping):
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_INVALID_RECORD,
                    message="Registro deve ser objeto.",
                    path=path_prefix,
                )
            )
            continue

        line_raw = raw.get("source_line_no", raw.get("sourceLineNo"))
        try:
            source_line_no = int(line_raw)
        except (TypeError, ValueError):
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_INVALID_RECORD,
                    message="source_line_no inválido.",
                    path=f"{path_prefix}.source_line_no",
                )
            )
            continue
        if source_line_no < 1:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_INVALID_RECORD,
                    message="source_line_no deve ser >= 1.",
                    path=f"{path_prefix}.source_line_no",
                )
            )
            continue
        if source_line_no in seen_line_nos:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_INVALID_RECORD,
                    message=f"source_line_no duplicado: {source_line_no}.",
                    path=f"{path_prefix}.source_line_no",
                )
            )
            continue
        seen_line_nos.add(source_line_no)

        invoice_number = _text(raw.get("invoice_number", raw.get("invoiceNumber")))
        invoice_series = _text(raw.get("invoice_series", raw.get("invoiceSeries")))
        material_weg = _text(raw.get("material_weg", raw.get("materialWeg")))
        material_description = _text(
            raw.get("material_description", raw.get("materialDescription"))
        )
        source_unit = _text(raw.get("source_unit", raw.get("sourceUnit"))).upper()

        if not invoice_number:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_MISSING_REQUIRED_FIELD,
                    message="invoice_number obrigatório.",
                    path=f"{path_prefix}.invoice_number",
                )
            )
        if not invoice_series:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_MISSING_REQUIRED_FIELD,
                    message="invoice_series obrigatório.",
                    path=f"{path_prefix}.invoice_series",
                )
            )
        if not material_weg:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_MISSING_REQUIRED_FIELD,
                    message="material_weg obrigatório.",
                    path=f"{path_prefix}.material_weg",
                )
            )
        if not source_unit:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_MISSING_REQUIRED_FIELD,
                    message="source_unit obrigatório.",
                    path=f"{path_prefix}.source_unit",
                )
            )

        qty = _as_decimal(
            raw.get("quantity_original", raw.get("quantityOriginal")),
            path=f"{path_prefix}.quantity_original",
            issues=issues,
        )
        departure = _parse_date(
            raw.get("departure_date", raw.get("departureDate")),
            path=f"{path_prefix}.departure_date",
            issues=issues,
        )

        if source_unit and source_unit not in COMPARABLE_UNITS:
            # Etapa 1: rejeitar unidades sem equivalência conhecida.
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_UNKNOWN_UNIT,
                    message=(
                        f"Unidade {source_unit!r} não comparável "
                        "(somente UN e MI são aceitas nesta etapa)."
                    ),
                    path=f"{path_prefix}.source_unit",
                )
            )

        if (
            not invoice_number
            or not invoice_series
            or not material_weg
            or not source_unit
            or qty is None
            or departure is None
            or source_unit not in COMPARABLE_UNITS
        ):
            continue

        quantity_un, unit_comparability = quantity_to_un(
            quantity_original=qty, source_unit=source_unit
        )
        declared_un = raw.get("quantity_un", raw.get("quantityUn"))
        if declared_un is not None and _text(declared_un) != "":
            parsed_declared = _as_decimal(
                declared_un,
                path=f"{path_prefix}.quantity_un",
                issues=issues,
            )
            if (
                parsed_declared is not None
                and quantity_un is not None
                and parsed_declared != quantity_un
            ):
                issues.append(
                    MyWegInvoiceValidationIssue(
                        code=ERROR_INVALID_QUANTITY,
                        message=(
                            f"quantity_un declarado {parsed_declared} ≠ "
                            f"convertido {quantity_un}."
                        ),
                        path=f"{path_prefix}.quantity_un",
                    )
                )
                continue

        normalized.append(
            {
                "source_line_no": source_line_no,
                "invoice_number": invoice_number,
                "invoice_series": invoice_series,
                "material_weg": material_weg,
                "material_description": material_description,
                "quantity_original": decimal_to_canonical_str(qty),
                "source_unit": source_unit,
                "quantity_un": (
                    decimal_to_canonical_str(quantity_un)
                    if quantity_un is not None
                    else None
                ),
                "unit_comparability": unit_comparability,
                "departure_date": departure,
            }
        )

    if issues:
        return MyWegInvoiceNormalizationResult(ok=False, issues=issues, records=normalized)
    return MyWegInvoiceNormalizationResult(ok=True, records=normalized, issues=[])


def validate_ingest_observation(
    payload: Mapping[str, Any],
) -> MyWegInvoiceNormalizationResult:
    issues: list[MyWegInvoiceValidationIssue] = []
    if not isinstance(payload, Mapping):
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_INVALID_RECORD,
                message="Payload deve ser um objeto JSON.",
                path="$",
            )
        )
        return MyWegInvoiceNormalizationResult(ok=False, issues=issues)

    contract_version = _text(payload.get("contract_version", payload.get("contractVersion")))
    if contract_version != CONTRACT_VERSION:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_CONTRACT_VERSION_UNSUPPORTED,
                message=f"contract_version deve ser {CONTRACT_VERSION}.",
                path="contract_version",
            )
        )
        return MyWegInvoiceNormalizationResult(ok=False, issues=issues)

    collection_id = _text(payload.get("collection_id", payload.get("collectionId")))
    if not collection_id:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="collection_id obrigatório.",
                path="collection_id",
            )
        )

    branch = _text(payload.get("branch"))
    if branch == FORBIDDEN_BRANCH:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_FILIAL_01_FORBIDDEN,
                message="Filial 01 não é aceita neste contrato.",
                path="branch",
            )
        )
    elif branch != ALLOWED_BRANCH:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_BRANCH_NOT_ALLOWED,
                message="Somente branch=02 é permitida.",
                path="branch",
            )
        )

    company = _text(payload.get("myweg_company_code", payload.get("mywegCompanyCode")))
    if company != MYWEG_COMPANY_CODE:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_COMPANY_MISMATCH,
                message=f"myweg_company_code deve ser {MYWEG_COMPANY_CODE}.",
                path="myweg_company_code",
            )
        )

    work_center = _text(payload.get("myweg_work_center", payload.get("mywegWorkCenter")))
    if work_center != MYWEG_WORK_CENTER:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_WORK_CENTER_MISMATCH,
                message=f"myweg_work_center deve ser {MYWEG_WORK_CENTER}.",
                path="myweg_work_center",
            )
        )

    supplier = _text(payload.get("myweg_supplier_code", payload.get("mywegSupplierCode")))
    if supplier != MYWEG_SUPPLIER_CODE:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_SUPPLIER_MISMATCH,
                message=f"myweg_supplier_code deve ser {MYWEG_SUPPLIER_CODE}.",
                path="myweg_supplier_code",
            )
        )

    document_date = _parse_date(
        payload.get("document_date", payload.get("documentDate")),
        path="document_date",
        issues=issues,
    )

    observation_status = _text(
        payload.get("observation_status", payload.get("observationStatus"))
    )
    if observation_status not in ALLOWED_OBSERVATION_STATUSES:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_INVALID_OBSERVATION_STATUS,
                message=(
                    "observation_status deve ser with_records ou "
                    "empty_signaled_by_sap."
                ),
                path="observation_status",
            )
        )

    observed_at = _parse_datetime_optional(
        payload.get("observed_at", payload.get("observedAt")),
        path="observed_at",
        issues=issues,
        required=False,
    )
    source_prepared_at = _parse_datetime_optional(
        payload.get("source_prepared_at", payload.get("sourcePreparedAt")),
        path="source_prepared_at",
        issues=issues,
        required=True,
    )

    source_sha256_raw = payload.get("source_sha256", payload.get("sourceSha256"))
    source_sha256 = _text(source_sha256_raw).lower() if source_sha256_raw is not None else ""
    if source_sha256 and not is_sha256_hex(source_sha256):
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_SOURCE_SHA256_MISMATCH,
                message="source_sha256 inválido.",
                path="source_sha256",
            )
        )

    records_result = normalize_invoice_records(payload.get("records"))
    issues.extend(records_result.issues)
    records = records_result.records

    declared_count = payload.get("record_count", payload.get("recordCount"))
    try:
        record_count = int(declared_count)
    except (TypeError, ValueError):
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_RECORD_COUNT_MISMATCH,
                message="record_count inválido.",
                path="record_count",
            )
        )
        record_count = -1
    else:
        if record_count != len(payload.get("records") or []):
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_RECORD_COUNT_MISMATCH,
                    message=(
                        f"record_count={record_count} ≠ "
                        f"len(records)={len(payload.get('records') or [])}."
                    ),
                    path="record_count",
                )
            )

    if observation_status == OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP:
        if records or record_count > 0:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_EMPTY_WITH_RECORDS,
                    message="empty_signaled_by_sap exige records vazios e record_count=0.",
                    path="records",
                )
            )
        if source_sha256:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_SOURCE_SHA256_MISMATCH,
                    message="empty_signaled_by_sap exige source_sha256 nulo.",
                    path="source_sha256",
                )
            )
    elif observation_status == OBSERVATION_STATUS_WITH_RECORDS:
        if not records:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_WITH_RECORDS_EMPTY,
                    message="with_records exige ao menos um item.",
                    path="records",
                )
            )
        if not source_sha256:
            issues.append(
                MyWegInvoiceValidationIssue(
                    code=ERROR_MISSING_REQUIRED_FIELD,
                    message="with_records exige source_sha256 do XLSX.",
                    path="source_sha256",
                )
            )

    expected_payload = compute_payload_sha256(records)
    expected_semantic = compute_semantic_sha256(records)

    declared_payload = _text(
        payload.get("payload_sha256", payload.get("payloadSha256"))
    ).lower()
    if not declared_payload:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="payload_sha256 obrigatório.",
                path="payload_sha256",
            )
        )
    elif not is_sha256_hex(declared_payload):
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_PAYLOAD_SHA256_MISMATCH,
                message="payload_sha256 inválido.",
                path="payload_sha256",
            )
        )
    elif declared_payload != expected_payload:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_PAYLOAD_SHA256_MISMATCH,
                message="payload_sha256 diverge do canônico dos records.",
                path="payload_sha256",
            )
        )

    declared_semantic = _text(
        payload.get("semantic_sha256", payload.get("semanticSha256"))
    ).lower()
    if not declared_semantic:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_MISSING_REQUIRED_FIELD,
                message="semantic_sha256 obrigatório.",
                path="semantic_sha256",
            )
        )
    elif not is_sha256_hex(declared_semantic):
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_SEMANTIC_SHA256_MISMATCH,
                message="semantic_sha256 inválido.",
                path="semantic_sha256",
            )
        )
    elif declared_semantic != expected_semantic:
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_SEMANTIC_SHA256_MISMATCH,
                message="semantic_sha256 diverge do multiconjunto canônico.",
                path="semantic_sha256",
            )
        )

    manifesto = payload.get("manifesto") or payload.get("source_manifest") or {}
    if manifesto is not None and not isinstance(manifesto, Mapping):
        issues.append(
            MyWegInvoiceValidationIssue(
                code=ERROR_INVALID_RECORD,
                message="manifesto deve ser objeto JSON.",
                path="manifesto",
            )
        )
        manifesto = {}

    if issues:
        return MyWegInvoiceNormalizationResult(ok=False, issues=issues)

    if (
        not collection_id
        or branch != ALLOWED_BRANCH
        or company != MYWEG_COMPANY_CODE
        or work_center != MYWEG_WORK_CENTER
        or supplier != MYWEG_SUPPLIER_CODE
        or document_date is None
        or observation_status not in ALLOWED_OBSERVATION_STATUSES
        or source_prepared_at is None
    ):
        return MyWegInvoiceNormalizationResult(
            ok=False,
            issues=[
                MyWegInvoiceValidationIssue(
                    code=ERROR_INVALID_RECORD,
                    message="Campos obrigatórios incompletos após validação.",
                    path="$",
                )
            ],
        )

    total_un = sum(
        (
            Decimal(str(row["quantity_un"]))
            for row in records
            if row.get("quantity_un") is not None
        ),
        Decimal("0"),
    )

    batch = {
        "contract_version": CONTRACT_VERSION,
        "collection_id": collection_id,
        "branch": ALLOWED_BRANCH,
        "myweg_company_code": MYWEG_COMPANY_CODE,
        "myweg_work_center": MYWEG_WORK_CENTER,
        "myweg_supplier_code": MYWEG_SUPPLIER_CODE,
        "document_date": document_date,
        "observation_status": observation_status,
        "observed_at": observed_at,
        "source_prepared_at": source_prepared_at,
        "source_sha256": source_sha256 or None,
        "payload_sha256": expected_payload,
        "semantic_sha256": expected_semantic,
        "record_count": len(records),
        "total_quantity_un": decimal_to_canonical_str(total_un),
        "manifesto": dict(manifesto) if isinstance(manifesto, Mapping) else {},
        "records": records,
    }
    return MyWegInvoiceNormalizationResult(ok=True, batch=batch, records=records, issues=[])