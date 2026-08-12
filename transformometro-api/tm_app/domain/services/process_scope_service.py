from __future__ import annotations


class ProcessoEscopoDomainError(ValueError):
    pass


def validate_processo_escopo(
    *,
    todas_filiais_ativas: bool,
    filial_ids: list[str],
    setor_ids: list[str],
) -> None:
    filiais = [item.strip() for item in filial_ids if str(item).strip()]
    setores = [item.strip() for item in setor_ids if str(item).strip()]

    if not filiais and not setores and not todas_filiais_ativas:
        return

    if not setores:
        raise ProcessoEscopoDomainError("Informe ao menos um departamento no escopo do processo.")

    if todas_filiais_ativas:
        return

    if not filiais:
        raise ProcessoEscopoDomainError(
            "Informe ao menos uma unidade ou marque todas as unidades ativas."
        )
