"""Decisão do monitoramento autônomo de CT (PC-MES-CT-AUTONOMOUS-DOWNTIME).

Regra pura, sem IO: dado o cursor durável do observador, o snapshot Pulse
e a existência de run ativo, decide o que o tick autônomo grava. Nunca
inventa produção — só reconhece atividade (incremento real) e inatividade
observada (ausência de incremento além do threshold legado).

Nenhum pulso vira contagem de peça de OP — os fatos autônomos nascem com
run_id=NULL e sem atribuição de produção.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AutonomousAction(str, Enum):
    """Resultado do tick autônomo para um (branch, work_center)."""

    SKIP = "skip"                       # run ativo — o caminho do run governa
    DEGRADED = "degraded"               # observabilidade indisponível — nunca fato
    OBSERVE = "observe"                 # só atualiza cursor (primeira observação)
    ACTIVITY = "activity"               # incremento real → producing / retomada
    STOPPED = "stopped"                 # inatividade ≥ threshold → parada autônoma
    NOTHING = "nothing"                 # sem mudança relevante


@dataclass(frozen=True)
class AutonomousTickDecision:
    action: AutonomousAction
    degraded_reason: str | None = None
    # started_at da parada autônoma — retroage ao último incremento.
    started_at: datetime | None = None


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if getattr(value, "tzinfo", None) is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def decide_autonomous_tick(
    *,
    has_active_run: bool,
    observer: dict[str, Any] | None,
    devices: list[dict[str, Any]],
    usable: bool,
    offline: bool,
    threshold_seconds: int,
    at: datetime,
) -> AutonomousTickDecision:
    """Decide o efeito do tick para um CT sensorizado sem contexto de run.

    devices = contadores pulse_counter amarrados ao CT no snapshot.
    usable/offline = classificação do dispositivo escolhido
    (classify_pulse_snapshot) — calculada fora para manter esta função
    sem acesso ao contrato de conectividade.

    Ordem de decisão — cada ramo preserva o fail-closed:

    1. run ativo → o caminho do run é dono dos fatos do posto;
    2. zero vínculos → observador degradado, nenhum fato;
    3. mais de um contador → vínculo ambíguo, observador degradado;
    4. snapshot offline/indisponível → degradado — offline não é parada;
    5. epoch/device diferente do cursor → realinhar identidade, baseline
       reinicia (nunca parada retroativa por mudança de sensor);
    6. incremento real → ACTIVITY (a aplicação decide producing × retomada);
    7. contador estável + baseline estabelecido + inatividade ≥ threshold
       → STOPPED na última atividade conhecida;
    8. regressão de contador no mesmo epoch → realinhar sem fato novo;
    9. demais casos → NOTHING/OBSERVE.
    """
    if has_active_run:
        return AutonomousTickDecision(AutonomousAction.SKIP)

    if not devices:
        return AutonomousTickDecision(
            AutonomousAction.DEGRADED, degraded_reason="no_binding"
        )
    if len(devices) > 1:
        return AutonomousTickDecision(
            AutonomousAction.DEGRADED, degraded_reason="ambiguous_binding"
        )

    device = devices[0]
    if offline:
        return AutonomousTickDecision(
            AutonomousAction.DEGRADED, degraded_reason="offline"
        )
    if not usable:
        return AutonomousTickDecision(
            AutonomousAction.DEGRADED, degraded_reason="invalid_snapshot"
        )

    counter = int(device.get("counter") or 0)
    epoch = int(device.get("counterEpoch") or 0)
    device_id = str(device.get("deviceId") or "")

    if observer is None:
        # Primeira observação: só cursor — sem baseline, sem fato.
        return AutonomousTickDecision(AutonomousAction.OBSERVE)

    same_device = str(observer.get("device_id") or "") == device_id
    same_epoch = int(observer.get("counter_epoch") or 0) == epoch
    last_counter = int(observer.get("last_counter") or 0)

    if not same_device or not same_epoch:
        # Identidade do contador mudou: realinha e reinicia o baseline —
        # jamais interpreta a descontinuidade como parada.
        return AutonomousTickDecision(AutonomousAction.OBSERVE)

    if counter > last_counter:
        # Incremento real: a camada de aplicação decide entre abrir
        # producing ou encerrar a parada autônoma aberta — aqui só o
        # sinal de atividade observada importa.
        return AutonomousTickDecision(AutonomousAction.ACTIVITY)

    if counter < last_counter:
        # Regressão/replay do contador no mesmo epoch: realinha o cursor,
        # nenhum fato novo (não é produção e não é parada).
        return AutonomousTickDecision(AutonomousAction.OBSERVE)

    # Contador estável.
    last_increment_at = _aware(observer.get("last_increment_at"))
    if last_increment_at is None:
        # Sem baseline confiável — nunca parada retroativa (AC-10).
        return AutonomousTickDecision(AutonomousAction.NOTHING)
    if threshold_seconds <= 0:
        return AutonomousTickDecision(AutonomousAction.NOTHING)
    idle = (at - last_increment_at).total_seconds()
    if idle < threshold_seconds:
        return AutonomousTickDecision(AutonomousAction.NOTHING)
    return AutonomousTickDecision(
        AutonomousAction.STOPPED, started_at=last_increment_at
    )
