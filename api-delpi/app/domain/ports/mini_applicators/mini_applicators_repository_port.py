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
