import pytest

from app.domain.services.ppm_produced_quantity import resolve_produced_quantity_milheiro


@pytest.mark.parametrize(
    ("programado", "apontado_max", "expected"),
    [
        (1.0, 0.8, 0.8),
        (1.0, 1.0, 1.0),
        (1.0, 1.2, 1.0),
        (0.0, 0.5, 0.5),
        (None, 0.75, 0.75),
        (2.0, 0.0, 0.0),
    ],
)
def test_resolve_produced_quantity_milheiro(
    programado: float | None,
    apontado_max: float,
    expected: float,
) -> None:
    assert resolve_produced_quantity_milheiro(
        programado=programado,
        apontado_max=apontado_max,
    ) == pytest.approx(expected)


def test_formula_programado_menos_saldo_igual_apontado() -> None:
    programado = 10.0
    apontado = 7.5
    saldo = max(0.0, programado - apontado)
    produzido = programado - saldo
    assert produzido == pytest.approx(apontado)
    assert resolve_produced_quantity_milheiro(
        programado=programado,
        apontado_max=apontado,
    ) == pytest.approx(produzido)
