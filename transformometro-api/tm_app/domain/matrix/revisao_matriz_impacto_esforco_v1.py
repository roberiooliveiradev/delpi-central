from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

MATRIX_FORMAT = "revisao_matriz_impacto_esforco_v1"
FORMAT_VERSION = 1
MODOS = frozenset({"auto", "manual", "hibrido"})
MANUAL_SCALE_KEYS = frozenset(
    {
        "impacto_qualitativo",
        "esforco_qualitativo",
        "alinhamento_estrategico",
        "dependencias_externas",
        "mudanca_comportamental",
    }
)
MANUAL_NON_SCALE_KEYS = frozenset(
    {
        "pessoas_afetadas",
        "esforco_implantacao_semanas",
        "esforco_horas_equipe",
        "observacao",
    }
)


class MatrizImpactoEsforcoValidationError(ValueError):
    """Payload inválido para revisao_matriz_impacto_esforco_v1."""


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MatrizImpactoEsforcoValidationError(f"{label} deve ser um objeto.")
    return value


def _validate_scale(value: Any, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise MatrizImpactoEsforcoValidationError(f"{field} deve ser inteiro entre 1 e 5.")
    if value < 1 or value > 5:
        raise MatrizImpactoEsforcoValidationError(f"{field} deve estar entre 1 e 5.")
    return value


def _validate_override(value: Any, *, field: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise MatrizImpactoEsforcoValidationError(f"{field} deve ser número entre 0 e 100 ou null.")
    numeric = float(value)
    if numeric < 0 or numeric > 100:
        raise MatrizImpactoEsforcoValidationError(f"{field} deve estar entre 0 e 100.")
    return numeric


def validate_inputs_manuais(doc: Any) -> dict[str, Any]:
    if doc is None:
        return {}
    data = _require_dict(doc, "inputs_manuais")
    validated: dict[str, Any] = {}

    for key in MANUAL_SCALE_KEYS:
        if key not in data:
            continue
        validated[key] = _validate_scale(data[key], field=f"inputs_manuais.{key}")

    if "pessoas_afetadas" in data:
        value = data["pessoas_afetadas"]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise MatrizImpactoEsforcoValidationError("inputs_manuais.pessoas_afetadas inválido.")
        validated["pessoas_afetadas"] = value

    if "esforco_implantacao_semanas" in data:
        value = data["esforco_implantacao_semanas"]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise MatrizImpactoEsforcoValidationError(
                "inputs_manuais.esforco_implantacao_semanas inválido."
            )
        validated["esforco_implantacao_semanas"] = value

    if "esforco_horas_equipe" in data:
        value = data["esforco_horas_equipe"]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or float(value) < 0:
            raise MatrizImpactoEsforcoValidationError("inputs_manuais.esforco_horas_equipe inválido.")
        validated["esforco_horas_equipe"] = float(value)

    if "observacao" in data:
        obs = data["observacao"]
        if not isinstance(obs, str):
            raise MatrizImpactoEsforcoValidationError("inputs_manuais.observacao deve ser texto.")
        if len(obs) > 2000:
            raise MatrizImpactoEsforcoValidationError(
                "inputs_manuais.observacao excede 2000 caracteres."
            )
        validated["observacao"] = obs

    unknown = set(data.keys()) - MANUAL_SCALE_KEYS - MANUAL_NON_SCALE_KEYS
    if unknown:
        raise MatrizImpactoEsforcoValidationError(
            f"inputs_manuais contém campos desconhecidos: {', '.join(sorted(unknown))}."
        )

    return validated


def validate_overrides(doc: Any) -> dict[str, float | None]:
    if doc is None:
        return {}
    data = _require_dict(doc, "overrides")
    unknown = set(data.keys()) - {"impacto", "esforco"}
    if unknown:
        raise MatrizImpactoEsforcoValidationError(
            f"overrides contém campos desconhecidos: {', '.join(sorted(unknown))}."
        )
    validated: dict[str, float | None] = {}
    if "impacto" in data:
        validated["impacto"] = _validate_override(data["impacto"], field="overrides.impacto")
    if "esforco" in data:
        validated["esforco"] = _validate_override(data["esforco"], field="overrides.esforco")
    return validated


def validate_revisao_matriz_impacto_esforco_v1(doc: Any) -> dict[str, Any]:
    data = _require_dict(doc, "matriz_impacto_esforco")
    if data.get("format") != MATRIX_FORMAT:
        raise MatrizImpactoEsforcoValidationError("format deve ser revisao_matriz_impacto_esforco_v1.")
    if data.get("format_version") != FORMAT_VERSION:
        raise MatrizImpactoEsforcoValidationError("format_version inválida.")

    modo = str(data.get("modo") or "auto")
    if modo not in MODOS:
        raise MatrizImpactoEsforcoValidationError("modo inválido.")

    payload: dict[str, Any] = {
        "format": MATRIX_FORMAT,
        "format_version": FORMAT_VERSION,
        "modo": modo,
        "inputs_manuais": validate_inputs_manuais(data.get("inputs_manuais")),
        "overrides": validate_overrides(data.get("overrides")),
    }

    atualizado_em = data.get("atualizado_em")
    if atualizado_em is not None and not isinstance(atualizado_em, str):
        raise MatrizImpactoEsforcoValidationError("atualizado_em inválido.")
    if atualizado_em:
        payload["atualizado_em"] = atualizado_em

    atualizado_por = data.get("atualizado_por")
    if atualizado_por is not None:
        if not isinstance(atualizado_por, str) or len(atualizado_por) > 320:
            raise MatrizImpactoEsforcoValidationError("atualizado_por inválido.")
        payload["atualizado_por"] = atualizado_por

    return payload


def build_persisted_matriz_payload(
    body: dict[str, Any],
    *,
    atualizado_por: str,
    atualizado_em: datetime | None = None,
) -> dict[str, Any]:
    """Monta documento persistível a partir do body do PUT."""
    modo = str(body.get("modo") or "auto")
    if modo not in MODOS:
        raise MatrizImpactoEsforcoValidationError("modo inválido.")

    timestamp = (atualizado_em or datetime.now(timezone.utc)).isoformat()
    return validate_revisao_matriz_impacto_esforco_v1(
        {
            "format": MATRIX_FORMAT,
            "format_version": FORMAT_VERSION,
            "modo": modo,
            "inputs_manuais": validate_inputs_manuais(body.get("inputs_manuais")),
            "overrides": validate_overrides(body.get("overrides")),
            "atualizado_em": timestamp,
            "atualizado_por": atualizado_por[:320],
        }
    )
