from __future__ import annotations


class StrategicIndicatorsGoalConflictError(RuntimeError):
    """Conflito de concorrência: a precondição de estado esperado falhou.

    Lançada quando o chamador informa uma precondição otimista
    (``expected_max_version`` no create ou ``expected_row_xmin`` nas demais
    mutações) e o estado atual da linha/escopo já não corresponde — a
    escrita é rejeitada sem efeitos colaterais (HTTP 409 na rota).
    """
