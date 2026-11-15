"""Cabeça das migrations de produto para os testes PostgreSQL.

A lista vive no diretório ``migrations`` (ordem de versão). A subpasta
``lancamento_notas_fiscais`` fica de fora: outro runner, outro schema.
"""

from __future__ import annotations

import re
from pathlib import Path

_MIGRATION_NAME = re.compile(r"^V(\d+)__.+\.sql$")
_MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def product_migration_names() -> list[str]:
    files: list[tuple[int, str]] = []
    for path in _MIGRATIONS_DIR.iterdir():
        if not path.is_file():
            continue
        match = _MIGRATION_NAME.match(path.name)
        if match:
            files.append((int(match.group(1)), path.name))
    files.sort(key=lambda item: item[0])
    return [name for _, name in files]


def latest_product_migration() -> str:
    names = product_migration_names()
    if not names:
        raise AssertionError(f"nenhuma migration em {_MIGRATIONS_DIR}")
    return names[-1]
