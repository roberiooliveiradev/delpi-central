from __future__ import annotations

from typing import Protocol


class OpsAbertasQueryRepositoryPort(Protocol):

    def list_open_ops(self) -> tuple[list[dict], list[dict]]:
        """Retorna (linhas detalhadas, linhas resumidas por filial+produto)."""
