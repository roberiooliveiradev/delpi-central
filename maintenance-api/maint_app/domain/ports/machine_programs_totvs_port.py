from __future__ import annotations

from typing import Any, Protocol


class MachineProgramsTotvsPort(Protocol):
    def listar_top_intermediates(
        self,
        *,
        filial: str,
        data_inicial: str | None = None,
        data_final: str | None = None,
        page: int = 1,
        page_size: int = 50,
        search: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]: ...
