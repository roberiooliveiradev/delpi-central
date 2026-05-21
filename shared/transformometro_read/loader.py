from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, List

from transformometro_read.serialize import serialize_row


@dataclass(frozen=True)
class TransformometroRawPayload:
    processos: List[dict]
    revisoes: List[dict]
    medicoes: List[dict]
    investimentos: List[dict]
    recursos_compartilhados: List[dict]
    revisao_recursos_compartilhados: List[dict]


FetchAll = Callable[[str, tuple[Any, ...] | None], list[dict[str, Any]]]


def load_transformometro_raw(fetch_all: FetchAll) -> TransformometroRawPayload:
    """Carrega cadastro ativo do schema transformometro (mesma fonte do transformometro-api)."""
    return TransformometroRawPayload(
        processos=_load_table(fetch_all, "transformometro.processos"),
        revisoes=_load_table(fetch_all, "transformometro.revisoes"),
        medicoes=_load_table(fetch_all, "transformometro.medicoes"),
        investimentos=_load_table(fetch_all, "transformometro.investimentos"),
        recursos_compartilhados=_load_table(
            fetch_all, "transformometro.recursos_compartilhados"
        ),
        revisao_recursos_compartilhados=_load_table(
            fetch_all, "transformometro.revisao_recursos_compartilhados"
        ),
    )


def _load_table(fetch_all: FetchAll, table: str) -> list[dict]:
    rows = fetch_all(
        f"SELECT * FROM {table} WHERE deletado = FALSE",
        None,
    )
    return [serialize_row(dict(row)) for row in rows]


def plugins_db_configured() -> bool:
    required = ("PLUGINS_DB_HOST", "PLUGINS_DB_NAME", "PLUGINS_DB_USER", "PLUGINS_DB_PASSWORD")
    return all(os.getenv(key) for key in required)
