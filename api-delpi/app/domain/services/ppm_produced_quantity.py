"""Quantidade produzida no denominador PPM — regra programado − saldo = apontado."""


def resolve_produced_quantity_milheiro(
    *,
    programado: float | None,
    apontado_max: float,
) -> float:
    """
    Calcula a quantidade produzida (milheiro) por OP na operação final.

    Regra de negócio:
        saldo_pendente = max(0, programado − apontado)
        produzido = programado − saldo_pendente

    Equivalente a min(programado, apontado) quando programado > 0.
    Se programado ausente/zero, usa o apontado (MAX dos apontamentos).
    Se apontado > programado, limita ao programado (não infla acima da OP).
    """
    apontado = float(apontado_max or 0)
    prog = float(programado or 0)

    if prog <= 0:
        return apontado

    saldo_pendente = max(0.0, prog - apontado)
    return prog - saldo_pendente
