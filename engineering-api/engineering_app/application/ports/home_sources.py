"""Ports de leitura das fontes oficiais da Home (F2a.S2).

Um port existe por seção elegível com backend oficial comprovado no G0.
Cada adapter normaliza o payload do owner para `HomeItem` — o use case
não conhece campos de sistemas downstream nem reproduz regras de domínio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from engineering_app.application.models.home import HomeItem

FetchStatus = Literal["available", "empty", "unavailable", "forbidden"]


@dataclass(frozen=True)
class HomeSourceContext:
    """Contexto mínimo autorizado para leitura em nome do usuário.

    `access_token` é o JWT do usuário autenticado — delegação oficial
    (mesma audience); o owner downstream revalida a autorização do recurso.
    """

    user_id: str
    access_token: str
    request_id: str | None = None


@dataclass(frozen=True)
class SectionFetch:
    """Resultado normalizado de uma leitura de fonte oficial."""

    status: FetchStatus
    items: tuple[HomeItem, ...] = ()
    total: int | None = None
    reason: str | None = None
    message: str | None = None


class HomeSectionSource(Protocol):
    """Fonte oficial de uma seção elegível da Home."""

    system: str  # owner: "api-delpi" | "requests-api"
    endpoint: str  # rota oficial consumida, ex.: "GET /requests/work-queue"

    async def fetch(self, ctx: HomeSourceContext, *, limit: int) -> SectionFetch:
        """Lê os itens da seção em nome do usuário, até `limit` itens.

        O adapter traduz o resultado para SectionFetch:
        - available/empty conforme o owner responder;
        - forbidden quando o owner negar acesso (401/403 downstream);
        - unavailable com reason para falhas de transporte/timeout/contrato.
        """
        ...
