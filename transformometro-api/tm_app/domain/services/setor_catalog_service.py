from __future__ import annotations

import re

_CODIGO_SETOR_PATTERN = re.compile(r"^[a-z0-9_]+$")


def normalize_codigo_setor(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9_]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug or not _CODIGO_SETOR_PATTERN.match(slug):
        raise ValueError("codigo_setor inválido: use apenas letras minúsculas, números e _")
    return slug


def validate_codigos_setores(codigos: list[str], active_codigos: set[str]) -> None:
    if not codigos:
        raise ValueError("Informe ao menos um setor.")
    invalid = sorted({codigo for codigo in codigos if codigo not in active_codigos})
    if invalid:
        raise ValueError(f"setor_id inválido: {', '.join(invalid)}")
