from __future__ import annotations

import pytest

from tm_app.domain.services.processo_instancia_service import (
    ProcessoInstanciaDomainError,
    validate_instancia_par,
)


def test_validate_instancia_par_requires_setor_in_filial():
    validate_instancia_par(
        setor_ativo_na_filial=True,
        filial_codigo="01",
        setor_codigo="engenharia",
    )
    with pytest.raises(ProcessoInstanciaDomainError, match="não está vinculado"):
        validate_instancia_par(
            setor_ativo_na_filial=False,
            filial_codigo="01",
            setor_codigo="engenharia",
        )
