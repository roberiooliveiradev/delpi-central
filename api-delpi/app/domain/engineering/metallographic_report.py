"""Relatório metalográfico — regras de payload, versão e identidade.

Não calcula conformidade. Critério e valor medido são texto informado pelo analista.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from typing import Any

IMAGE_SLOTS = ("original", "measured")
CONCLUSION_RESULTS = ("conforming", "nonconforming")
REPORT_STATUS = "draft"
SORT_VALUES = (
    "created_at_desc",
    "created_at_asc",
    "report_date_desc",
    "report_number_asc",
)
MEASUREMENT_KEYS = (
    "crimp_height_ch",
    "crimp_width_cb",
    "void_area_av",
    "left_burr_gh_e",
    "right_burr_gh_d",
)
SAMPLE_FIELDS = (
    "terminal_code",
    "terminal_part_number",
    "product_harness",
    "cable",
    "conductor_section",
    "applicator_tool",
    "press_equipment",
    "batch_production_order",
    "sample_identification",
)
TEXT_FILTER_FIELDS = ("report_number", *SAMPLE_FIELDS)

SAMPLE_TEXT_MAX = 240
NOTES_MAX = 4000
CRITERION_MAX = 120
MEASURED_MAX = 40
REVISION_MAX = 16
ANALYST_NAME_MAX = 160
IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,200}$")
BUSINESS_TIMEZONE = "America/Sao_Paulo"


class MetallographicReportError(Exception):
    status_code = 400
    code = "METALLOGRAPHIC_REPORT_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ReportNotFoundError(MetallographicReportError):
    status_code = 404
    code = "REPORT_NOT_FOUND"


class ImageNotFoundError(MetallographicReportError):
    status_code = 404
    code = "IMAGE_NOT_FOUND"


class ReportVersionConflictError(MetallographicReportError):
    status_code = 412
    code = "REPORT_VERSION_CONFLICT"


class PreconditionRequiredError(MetallographicReportError):
    status_code = 428
    code = "PRECONDITION_REQUIRED"


class IdempotencyKeyRequiredError(MetallographicReportError):
    status_code = 400
    code = "IDEMPOTENCY_KEY_REQUIRED"


class IdempotencyConflictError(MetallographicReportError):
    status_code = 409
    code = "IDEMPOTENCY_CONFLICT"


class InvalidFilterError(MetallographicReportError):
    status_code = 400
    code = "INVALID_FILTER"


class PayloadValidationError(MetallographicReportError):
    status_code = 422
    code = "VALIDATION_ERROR"


class UnsupportedImageError(MetallographicReportError):
    status_code = 415
    code = "UNSUPPORTED_MEDIA_TYPE"


class ImageTooLargeError(MetallographicReportError):
    status_code = 413
    code = "PAYLOAD_TOO_LARGE"


class InvalidImageError(MetallographicReportError):
    status_code = 422
    code = "INVALID_IMAGE"


class ImageStorageError(MetallographicReportError):
    status_code = 503
    code = "IMAGE_STORAGE_UNAVAILABLE"


def etag_for(version: int) -> str:
    return f'"{int(version)}"'


def parse_if_match(value: str | None) -> int:
    if value is None or not str(value).strip():
        raise PreconditionRequiredError(
            "Informe o cabeçalho If-Match com a versão do relatório."
        )
    text = str(value).strip()
    if text.upper().startswith("W/"):
        text = text[2:].strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    if not text.isdigit():
        raise ReportVersionConflictError("If-Match não corresponde à versão do relatório.")
    return int(text)


def require_idempotency_key(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        raise IdempotencyKeyRequiredError(
            "Informe o cabeçalho Idempotency-Key."
        )
    if IDEMPOTENCY_KEY_PATTERN.fullmatch(text) is None:
        raise IdempotencyKeyRequiredError(
            "Idempotency-Key deve ter 8 a 200 caracteres (letras, números, ponto, hífen, sublinhado ou dois-pontos)."
        )
    return text


def request_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _blank(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise PayloadValidationError("Campos de texto devem ser enviados como string.")
    text = value.strip()
    return text or None


def _bounded(value: Any, *, limit: int, label: str) -> str | None:
    text = _blank(value)
    if text is not None and len(text) > limit:
        raise PayloadValidationError(f"{label} excede {limit} caracteres.")
    return text


def _measurement_pair(raw: Any) -> dict[str, str | None]:
    if raw is None:
        return {"criterion": None, "measured": None}
    if not isinstance(raw, dict):
        raise PayloadValidationError("Cada medição deve ser um objeto com criterion e measured.")
    unknown = set(raw) - {"criterion", "measured"}
    if unknown:
        raise PayloadValidationError("Medição contém campo não permitido.")
    return {
        "criterion": _bounded(raw.get("criterion"), limit=CRITERION_MAX, label="Critério"),
        "measured": _bounded(raw.get("measured"), limit=MEASURED_MAX, label="Valor medido"),
    }


def empty_measurements() -> dict[str, dict[str, str | None]]:
    return {key: {"criterion": None, "measured": None} for key in MEASUREMENT_KEYS}


def normalize_measurements(raw: Any, *, partial: bool) -> dict[str, dict[str, str | None]]:
    if raw is None:
        return {} if partial else empty_measurements()
    if not isinstance(raw, dict):
        raise PayloadValidationError("measurements deve ser um objeto.")
    unknown = set(raw) - set(MEASUREMENT_KEYS)
    if unknown:
        raise PayloadValidationError("measurements contém parâmetro não permitido.")
    base = {} if partial else empty_measurements()
    for key in MEASUREMENT_KEYS:
        if key in raw:
            base[key] = _measurement_pair(raw.get(key))
    return base


def normalize_sample(raw: Any, *, partial: bool) -> dict[str, str | None]:
    if raw is None:
        return {} if partial else {field: None for field in SAMPLE_FIELDS}
    if not isinstance(raw, dict):
        raise PayloadValidationError("sample deve ser um objeto.")
    unknown = set(raw) - set(SAMPLE_FIELDS)
    if unknown:
        raise PayloadValidationError("sample contém campo não permitido.")
    base = {} if partial else {field: None for field in SAMPLE_FIELDS}
    for field in SAMPLE_FIELDS:
        if field in raw:
            base[field] = _bounded(raw.get(field), limit=SAMPLE_TEXT_MAX, label=field)
    return base


def normalize_conclusion(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {"result": None, "notes": None}
    if not isinstance(raw, dict):
        raise PayloadValidationError("conclusion deve ser um objeto.")
    unknown = set(raw) - {"result", "notes"}
    if unknown:
        raise PayloadValidationError("conclusion contém campo não permitido.")
    result = raw.get("result", None)
    if result is not None and result not in CONCLUSION_RESULTS:
        raise PayloadValidationError(
            "conclusion.result deve ser conforming, nonconforming ou null."
        )
    notes = _bounded(raw.get("notes"), limit=NOTES_MAX, label="Observações") if "notes" in raw or raw.get("notes") else None
    if "notes" in raw:
        notes = _bounded(raw.get("notes"), limit=NOTES_MAX, label="Observações")
    return {"result": result, "notes": notes}


def normalize_analyst_name(raw: Any) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise PayloadValidationError("analyst deve ser um objeto.")
    unknown = set(raw) - {"name"}
    if unknown:
        raise PayloadValidationError(
            "analyst aceita apenas name. A identidade do usuário não é informada pelo cliente."
        )
    return _bounded(raw.get("name"), limit=ANALYST_NAME_MAX, label="Responsável")


def _revision(raw: Any, *, required_default: str | None) -> str | None:
    if raw is None:
        return required_default
    text = _bounded(raw, limit=REVISION_MAX, label="Revisão")
    if text is None:
        if required_default is None:
            raise PayloadValidationError("Revisão não pode ser vazia.")
        return required_default
    return text


def _report_date(raw: Any) -> str | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, datetime):
        return raw.date().isoformat()
    if isinstance(raw, date):
        return raw.isoformat()
    if not isinstance(raw, str):
        raise PayloadValidationError("report_date deve ser uma data AAAA-MM-DD.")
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError as exc:
        raise PayloadValidationError("report_date deve ser uma data AAAA-MM-DD.") from exc


def _status(raw: Any) -> str:
    if raw is None:
        return REPORT_STATUS
    if raw != REPORT_STATUS:
        raise PayloadValidationError("status aceito nesta versão é apenas draft.")
    return REPORT_STATUS


_CREATE_KEYS = {
    "report_date",
    "revision",
    "sample",
    "measurements",
    "conclusion",
    "analyst",
    "status",
}


def normalize_create_payload(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise PayloadValidationError("Corpo do relatório deve ser um objeto JSON.")
    unknown = set(raw) - _CREATE_KEYS
    if unknown:
        raise PayloadValidationError(
            "O corpo contém campos controlados pelo servidor ou não permitidos."
        )
    conclusion = normalize_conclusion(raw.get("conclusion"))
    return {
        "report_date": _report_date(raw.get("report_date")),
        "revision": _revision(raw.get("revision"), required_default="00"),
        "sample": normalize_sample(raw.get("sample"), partial=False),
        "measurements": normalize_measurements(raw.get("measurements"), partial=False),
        "conclusion_result": conclusion["result"],
        "conclusion_notes": conclusion["notes"],
        "analyst_name": normalize_analyst_name(raw.get("analyst")),
        "status": _status(raw.get("status")),
    }


def normalize_patch_payload(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise PayloadValidationError("Corpo do relatório deve ser um objeto JSON.")
    if not raw:
        raise PayloadValidationError("Informe ao menos um campo para atualizar.")
    unknown = set(raw) - _CREATE_KEYS
    if unknown:
        raise PayloadValidationError(
            "O corpo contém campos controlados pelo servidor ou não permitidos."
        )
    changes: dict[str, Any] = {}
    if "report_date" in raw:
        changes["report_date"] = _report_date(raw.get("report_date"))
    if "revision" in raw:
        changes["revision"] = _revision(raw.get("revision"), required_default=None)
    if "sample" in raw:
        changes["sample"] = normalize_sample(raw.get("sample"), partial=True)
    if "measurements" in raw:
        changes["measurements"] = normalize_measurements(raw.get("measurements"), partial=True)
    if "conclusion" in raw:
        conclusion = normalize_conclusion(raw.get("conclusion"))
        if raw.get("conclusion") is None or "result" in (raw.get("conclusion") or {}):
            changes["conclusion_result"] = conclusion["result"]
        if raw.get("conclusion") is None or "notes" in (raw.get("conclusion") or {}):
            changes["conclusion_notes"] = conclusion["notes"]
    if "analyst" in raw:
        changes["analyst_name"] = normalize_analyst_name(raw.get("analyst"))
    if "status" in raw:
        changes["status"] = _status(raw.get("status"))
    if not changes:
        raise PayloadValidationError("Informe ao menos um campo para atualizar.")
    return changes


def parse_filter_date(value: str | None, *, label: str) -> str | None:
    if value is None or not str(value).strip():
        return None
    try:
        return date.fromisoformat(str(value).strip()).isoformat()
    except ValueError as exc:
        raise InvalidFilterError(f"{label} deve ser uma data AAAA-MM-DD.") from exc


def validate_slot(slot: str) -> str:
    if slot not in IMAGE_SLOTS:
        raise PayloadValidationError("slot deve ser original ou measured.")
    return slot
