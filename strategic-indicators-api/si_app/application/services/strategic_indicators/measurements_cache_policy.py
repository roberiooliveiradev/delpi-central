from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)

# Departamentos esperados numa medição consolidada (todos os collectors do provider real).
FULL_MEASUREMENT_DEPARTMENT_IDS: frozenset[str] = frozenset(
    {
        "engineering",
        "production",
        "commercial",
        "quality",
        "hr",
        "financial",
        "supplies",
    }
)

DEPARTMENT_LABELS: dict[str, str] = {
    "engineering": "Engenharia",
    "production": "Produção",
    "commercial": "Comercial",
    "quality": "Qualidade",
    "hr": "RH",
    "financial": "Financeiro",
    "supplies": "Suprimentos",
}

MEASUREMENT_QUALITY_SOURCE = "si_measurements_quality"
MISSING_DEPARTMENT_ERROR_CODE = "missing_department_measurements"
FETCH_ERROR_CODE = "measurement_fetch_error"


def has_measurement_errors(errors: list[dict] | None) -> bool:
    """Qualquer erro de medição impede cache (leitura e gravação)."""
    return bool(errors)


def _department_ids_in_items(
    items: list[StrategicIndicatorMeasuredValue],
) -> set[str]:
    return {
        (item.department_id or "").strip()
        for item in items
        if (item.department_id or "").strip()
    }


def find_missing_measurement_departments(
    items: list[StrategicIndicatorMeasuredValue],
    *,
    department_id: str | None = None,
) -> list[str]:
    normalized_department = (department_id or "").strip()
    if normalized_department:
        if any(
            (item.department_id or "").strip() == normalized_department for item in items
        ):
            return []
        return [normalized_department]

    present = _department_ids_in_items(items)
    return sorted(FULL_MEASUREMENT_DEPARTMENT_IDS - present)


def _has_full_department_coverage(items: list[StrategicIndicatorMeasuredValue]) -> bool:
    present = _department_ids_in_items(items)
    return FULL_MEASUREMENT_DEPARTMENT_IDS.issubset(present)


def _normalize_measurement_error(
    raw: dict,
    *,
    competence: str | None = None,
    branch: str | None = None,
) -> dict:
    department_id = str(raw.get("department_id") or "").strip()
    source = str(raw.get("source") or "desconhecida").strip()
    message = str(raw.get("message") or "Falha não detalhada na coleta.").strip()
    code = str(raw.get("code") or FETCH_ERROR_CODE).strip() or FETCH_ERROR_CODE

    context_parts: list[str] = []
    if competence:
        context_parts.append(f"competência {competence}")
    if branch:
        context_parts.append(f"filial {branch}")
    if context_parts and context_parts[0] not in message.lower():
        message = f"{message} ({', '.join(context_parts)})."

    return {
        "department_id": department_id,
        "source": source,
        "message": message,
        "code": code,
    }


def _build_missing_department_error(
    department_id: str,
    *,
    competence: str | None = None,
    branch: str | None = None,
) -> dict:
    label = DEPARTMENT_LABELS.get(department_id, department_id)
    message = (
        f"Nenhuma medição foi retornada para {label}. "
        "O painel pode exibir IGD 0,0 nesse departamento até a coleta completar."
    )
    if competence:
        message += f" Período: {competence}."
    if branch:
        message += f" Escopo filial: {branch}."
    return {
        "department_id": department_id,
        "source": MEASUREMENT_QUALITY_SOURCE,
        "message": message,
        "code": MISSING_DEPARTMENT_ERROR_CODE,
    }


def enrich_measurement_errors(
    items: list[StrategicIndicatorMeasuredValue],
    errors: list[dict] | None,
    *,
    department_id: str | None = None,
    competence: str | None = None,
    branch: str | None = None,
) -> list[dict]:
    """Unifica erros de fetch e cobertura incompleta para a UI e alertas."""
    merged: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    for raw in list(errors or []):
        if not isinstance(raw, dict):
            continue
        normalized = _normalize_measurement_error(
            raw,
            competence=competence,
            branch=branch,
        )
        key = (
            normalized["department_id"],
            normalized["source"],
            normalized["message"],
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(normalized)

    for missing_id in find_missing_measurement_departments(
        items,
        department_id=department_id,
    ):
        normalized = _build_missing_department_error(
            missing_id,
            competence=competence,
            branch=branch,
        )
        key = (
            normalized["department_id"],
            normalized["source"],
            normalized["message"],
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(normalized)

    return merged


def should_cache_measurements(
    items: list[StrategicIndicatorMeasuredValue],
    errors: list[dict] | None,
    *,
    department_id: str | None,
) -> bool:
    if has_measurement_errors(errors):
        return False
    if not items:
        return False

    normalized_department = (department_id or "").strip()
    if normalized_department:
        return any(
            (item.department_id or "").strip() == normalized_department for item in items
        )

    return _has_full_department_coverage(items)


def should_use_cached_measurements(
    items: list[StrategicIndicatorMeasuredValue],
    errors: list[dict] | None,
    *,
    department_id: str | None,
) -> bool:
    return should_cache_measurements(items, errors, department_id=department_id)


def format_measurement_errors_summary(
    errors: list[dict],
    *,
    limit: int = 8,
) -> str:
    if not errors:
        return ""

    lines: list[str] = []
    for entry in errors[:limit]:
        department_id = str(entry.get("department_id") or "geral").strip()
        label = DEPARTMENT_LABELS.get(department_id, department_id or "geral")
        message = str(entry.get("message") or "Falha na coleta.").strip()
        source = str(entry.get("source") or "").strip()
        suffix = f" [fonte: {source}]" if source else ""
        lines.append(f"• {label}: {message}{suffix}")

    if len(errors) > limit:
        lines.append(f"• … e mais {len(errors) - limit} ocorrência(s).")

    return "\n".join(lines)


def should_cache_rol_payload(payload: dict | None) -> bool:
    if not payload:
        return False
    if "rol" in payload:
        return True
    data = payload.get("data")
    if isinstance(data, dict) and "rol" in data:
        return True
    return False
