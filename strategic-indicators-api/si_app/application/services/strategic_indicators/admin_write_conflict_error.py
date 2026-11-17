from __future__ import annotations


class StrategicIndicatorsAdminConflictError(RuntimeError):
    """Conflito de concorrência em mutação administrativa.

    Lançada quando o chamador informa uma precondição otimista
    (``expected_row_xmin``/``expected_xmin`` em updates e transições de
    estado, ou transição de status impossível) e o estado atual da linha
    já não corresponde — a escrita é rejeitada sem efeitos colaterais
    (HTTP 409 na rota).
    """
