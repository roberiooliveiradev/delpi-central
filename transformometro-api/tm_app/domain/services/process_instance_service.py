from __future__ import annotations


class ProcessoInstanciaDomainError(ValueError):
    pass


def validate_instancia_par(
    *,
    setor_ativo_na_filial: bool,
    filial_codigo: str,
    setor_codigo: str,
) -> None:
    if not setor_ativo_na_filial:
        raise ProcessoInstanciaDomainError(
            f"setor_id '{setor_codigo}' não está vinculado à unidade {filial_codigo}"
        )
