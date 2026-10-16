"""Otimização da fila pela data de entrega do PA.

Regra de negócio: o carga máquina do TOTVS às vezes deixa material de entrega
distante à frente de material vencendo. Otimizar resequencia a fila de **todos**
os centros de trabalho pela entrega efetiva da OP, sem ultrapassar operação com
run aberto no cockpit e preservando a ordem atual entre operações da mesma data — o ajuste
manual do PCP dentro do dia continua valendo.

Wrapper de compatibilidade sobre o motor genérico de machine_load_optimization
(O1): data de entrega sempre obrigatória, sem critérios secundários.
"""

from __future__ import annotations

from typing import Any

from production_control_app.domain.services.machine_load_optimization import (
    MachineLoadOptimizationCriteria,
    MachineLoadOptimizationResult,
    optimize_machine_load_queue,
)
from production_control_app.domain.services.machine_load_queue_slots import (
    ProtectedOperationKey,
)

# Alias de compatibilidade: o resultado do motor genérico carrega exatamente os
# mesmos campos que o resultado histórico da otimização por entrega.
DeliverySequencing = MachineLoadOptimizationResult


def optimize_by_delivery_date(
    operations: list[dict[str, Any]],
    *,
    protected_keys: set[ProtectedOperationKey] | None = None,
) -> DeliverySequencing:
    """Ordena a fila de cada centro pela entrega do PA.

    ``protected_keys`` traz as operações com run aberto no cockpit por
    (work_center, production_order, operation_code) — a única fonte que
    trava posição; flags do snapshot congelado não protegem.
    """
    return optimize_machine_load_queue(
        operations,
        criteria=MachineLoadOptimizationCriteria(group_by_tool=False),
        protected_keys=protected_keys,
    )
