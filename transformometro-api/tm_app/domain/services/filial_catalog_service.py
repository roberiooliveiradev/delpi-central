from __future__ import annotations

import re

_CODIGO_FILIAL_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def normalize_codigo_filial(value: str) -> str:
    codigo = value.strip()
    if not codigo or not _CODIGO_FILIAL_PATTERN.match(codigo):
        raise ValueError(
            "codigo_filial inválido: use letras, números, hífen ou underscore (ex.: 01, matriz-sp)."
        )
    return codigo


def validate_codigos_filiais(codigos: list[str], active_codigos: set[str]) -> None:
    if not codigos:
        raise ValueError("Informe ao menos uma unidade.")
    invalid = sorted({codigo for codigo in codigos if codigo not in active_codigos})
    if invalid:
        raise ValueError(f"filial_id inválido: {', '.join(invalid)}")


def assert_filial_ativa(codigo_filial: str, active_codigos: set[str], *, field: str = "filial_id") -> None:
    if codigo_filial not in active_codigos:
        raise ValueError(f"{field} inválido: {codigo_filial}")
