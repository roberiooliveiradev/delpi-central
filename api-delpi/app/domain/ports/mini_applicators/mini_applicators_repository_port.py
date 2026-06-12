from __future__ import annotations

from typing import Protocol

from app.application.dto.mini_applicators.list_ferramentas_request import (
    ListMiniApplicatorsFerramentasRequest,
)
from app.application.models.page import Page
from app.domain.entities.mini_applicators.mini_applicator_tool import MiniApplicatorTool


class MiniApplicatorsRepositoryPort(Protocol):
    def list_ferramentas(
        self,
        request: ListMiniApplicatorsFerramentasRequest,
    ) -> Page[MiniApplicatorTool]: ...

    def get_ferramenta(self, codigo: str) -> MiniApplicatorTool | None: ...

    def list_pecas(self, codigo_ferramenta: str) -> list[dict]: ...

    def get_golpes(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        data_inicial: str,
        data_final: str,
    ) -> dict: ...

    def list_componentes(self, *, codigo_ferramenta: str, filial: str) -> list[dict]: ...
