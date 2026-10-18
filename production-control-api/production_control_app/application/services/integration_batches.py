"""Fatiamento e fan-out de consultas em lote à api-delpi.

Owner da regra transversal "como este BFF fatia e paraleliza chamadas em lote":
o teto de OPs por requisição é contrato da api-delpi, o pool limitado evita
explodir o gateway, e o contexto (JWT) é replicado nos workers. Hoje serve o
Alimentador de Linha e o resolvedor de materiais do sequenciamento — nenhum dos
dois implementa fatiamento/paralelismo próprio.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from typing import Any, Callable, Sequence

from production_control_app.application.services.line_feeder_settings import (
    setting_int,
)
from production_control_app.domain.errors import DelpiGatewayError


def commitment_batch_size() -> int:
    """Lote menor que o teto da api-delpi: são vários em paralelo, não um só."""
    cap = max(setting_int("maxProductionOrdersPerBatch", 300), 1)
    return max(1, min(setting_int("commitmentBatchSize", 100), cap))


def max_commitment_batches() -> int:
    """Teto de lotes por consulta — proteção contra janela de OPs ilimitada."""
    return max(setting_int("maxCommitmentBatches", 30), 1)


def caller_context_initializer() -> Callable[[], None]:
    """Replica o contexto de quem pediu em cada worker do pool.

    ``contextvars`` não são herdadas por thread: sem isto o gateway perderia o
    JWT do usuário justamente nas fatias paralelas, e a mesma rota trocaria a
    identidade do usuário pelo token de serviço só porque o corte ficou grande.
    A captura tem de acontecer aqui, na thread chamadora — dentro do worker ela
    copiaria o contexto vazio dele. Cada worker escreve no próprio contexto, em
    vez de compartilhar um ``Context``, que não pode ser entrado por duas
    threads ao mesmo tempo.
    """
    snapshot = list(copy_context().items())

    def initialize() -> None:
        for variable, value in snapshot:
            variable.set(value)

    return initialize


def fan_out(
    call: Callable[[Any], Any],
    arguments: Sequence[Any],
    *,
    failure: str,
    max_workers: int | None = None,
) -> list[Any]:
    """Leituras independentes em paralelo, com teto de workers.

    A primeira falha vira ``DelpiGatewayError``: bloco incompleto não é bloco
    degradado, e quem decide degradar é o chamador.
    """
    if not arguments:
        return []
    try:
        if len(arguments) == 1:
            return [call(arguments[0])]
        limit = max_workers or setting_int("fetchMaxWorkers", 6)
        workers = max(1, min(limit, len(arguments)))
        with ThreadPoolExecutor(
            max_workers=workers,
            initializer=caller_context_initializer(),
        ) as pool:
            return list(pool.map(call, arguments))
    except DelpiGatewayError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DelpiGatewayError(failure) from exc
