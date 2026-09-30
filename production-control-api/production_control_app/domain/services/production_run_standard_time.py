"""Normalização do snapshot de tempo padrão congelado no Play do run.

A api-delpi (Parte 2.1) é a fonte canônica: devolve o ciclo já em
segundos por peça física. Este módulo só defende a persistência local —
nunca recalcula SHY/SG2.

Três situações de qualidade são distintas:
- ``standard_time_unavailable``: a api-delpi respondeu corretamente, mas a
  operação não tem tempo padrão;
- ``piece_conversion_unavailable``: há tempo padrão, mas a unidade não
  converte para peça física (ex.: MT);
- ``upstream_unavailable``: classificação local — a api-delpi não pôde ser
  consultada de forma confiável (timeout, 5xx, 404, JSON inválido).
"""

from __future__ import annotations

from typing import Any

UPSTREAM_UNAVAILABLE = "upstream_unavailable"
COMPLETE = "complete"
MANUAL_WORKSTATION = "manual_workstation"


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def normalize_standard_time_snapshot(
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    """Traduz a resposta do contrato standard-time em snapshot persistível.

    ``payload=None`` (ou resposta não-dict) significa upstream indisponível.
    Valores degradados (ciclo <= 0, setup < 0) são zerados para NULL em vez
    de bloquear o Play.
    """
    if not isinstance(payload, dict):
        return {
            "ideal_cycle_seconds_snapshot": None,
            "setup_seconds_snapshot": None,
            "standard_time_source": "unavailable",
            "standard_time_data_quality_snapshot": UPSTREAM_UNAVAILABLE,
        }

    ideal = _float_or_none(payload.get("ideal_cycle_seconds"))
    if ideal is not None and ideal <= 0:
        ideal = None

    setup = _float_or_none(payload.get("setup_seconds"))
    if setup is not None and setup < 0:
        setup = None

    source = str(payload.get("standard_time_source") or "unavailable").strip()
    quality = str(payload.get("data_quality") or UPSTREAM_UNAVAILABLE).strip()

    if quality == COMPLETE and ideal is None:
        # Contrato diz completo mas o ciclo é inválido/ausente: degradação
        # defensiva — o run persiste estado seguro, nunca um ciclo inventado.
        quality = "standard_time_unavailable"

    return {
        "ideal_cycle_seconds_snapshot": ideal,
        "setup_seconds_snapshot": setup,
        "standard_time_source": source or "unavailable",
        "standard_time_data_quality_snapshot": quality or UPSTREAM_UNAVAILABLE,
    }


def resolve_workstation_type_snapshot(
    operation_context: dict[str, Any] | None,
) -> str | None:
    """``manual_workstation`` apenas quando a fila marca H8_FERRAM=MOD.

    A Delpi não possui fonte canônica para automático/semiautomático —
    qualquer outro caso permanece NULL, sem inferência por nome de CT/device.
    """
    if not isinstance(operation_context, dict):
        return None
    if operation_context.get("is_manual_operation") is True:
        return MANUAL_WORKSTATION
    return None
