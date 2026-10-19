"""Seleção determinística da fonte de paradas do cockpit por (filial, CT).

Regra pura, sem IO: decide se o cockpit deve consumir paradas do MES
(postos com contador Pulse vinculado), do TOTVS (postos comprovadamente sem
sensoriamento nem atividade MES no dia) ou reportar fonte indisponível —
nunca com fallback silencioso.

device.online NUNCA participa da decisão: um contador vinculado offline
ou stale continua sendo um CT sensorizado (fonte MES).
"""

from __future__ import annotations

from typing import Literal

DowntimeSource = Literal["mes", "totvs", "unavailable"]

SOURCE_MES: DowntimeSource = "mes"
SOURCE_TOTVS: DowntimeSource = "totvs"
SOURCE_UNAVAILABLE: DowntimeSource = "unavailable"

REASON_BOUND_COUNTER = "bound_counter"
REASON_MES_ACTIVITY_TODAY = "mes_activity_today"
REASON_NO_BOUND_COUNTER = "no_bound_counter"
REASON_MULTIPLE_BOUND_COUNTERS = "multiple_bound_counters"
REASON_SOURCE_LOOKUP_UNAVAILABLE = "source_lookup_unavailable"


def resolve_downtime_source(
    *,
    lookup_ok: bool,
    bound_counters: int,
    mes_activity_today: bool,
) -> tuple[DowntimeSource, str]:
    """Resolve (fonte, motivo) para um (filial, CT).

    - lookup_ok=False (Pulse fora/timeout/payload inválido/vínculo
      inconclusivo) → unavailable: falha de consulta nunca é prova de
      ausência de sensores.
    - >1 contador elegível → unavailable: configuração ambígua.
    - exatamente 1 → mes (independente de online/stale).
    - 0 com fatos MES no dia (vínculo removido hoje) → mes: a remoção não
      troca a fonte no meio do dia civil.
    - 0 sem fatos MES no dia → totvs: ausência comprovada.
    """
    if not lookup_ok:
        return SOURCE_UNAVAILABLE, REASON_SOURCE_LOOKUP_UNAVAILABLE
    if bound_counters > 1:
        return SOURCE_UNAVAILABLE, REASON_MULTIPLE_BOUND_COUNTERS
    if bound_counters == 1:
        return SOURCE_MES, REASON_BOUND_COUNTER
    if mes_activity_today:
        return SOURCE_MES, REASON_MES_ACTIVITY_TODAY
    return SOURCE_TOTVS, REASON_NO_BOUND_COUNTER
