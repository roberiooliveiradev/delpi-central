from __future__ import annotations

import pytest

from tm_app.domain.services.processo_escopo_service import (
    ProcessoEscopoDomainError,
    validate_processo_escopo,
)


def test_validate_processo_escopo_allows_empty():
    validate_processo_escopo(
        todas_filiais_ativas=False,
        filial_ids=[],
        setor_ids=[],
    )


def test_validate_processo_escopo_requires_setores_when_filiais_informadas():
    with pytest.raises(ProcessoEscopoDomainError):
        validate_processo_escopo(
            todas_filiais_ativas=False,
            filial_ids=["01"],
            setor_ids=[],
        )


def test_validate_processo_escopo_requires_filiais_quando_nao_consolidado():
    with pytest.raises(ProcessoEscopoDomainError):
        validate_processo_escopo(
            todas_filiais_ativas=False,
            filial_ids=[],
            setor_ids=["engenharia"],
        )


def test_validate_processo_escopo_todas_filiais_exige_setores():
    with pytest.raises(ProcessoEscopoDomainError):
        validate_processo_escopo(
            todas_filiais_ativas=True,
            filial_ids=[],
            setor_ids=[],
        )
