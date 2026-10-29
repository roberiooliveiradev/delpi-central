"""Âncora «primeira OV» do streak NC — adaptador transitório.

Enquanto o contrato facts dedicado (F-LMP-xx earliest-ov) não existe, o
streak oficial da api-delpi já expõe ``reference_start_date`` — esta
fonte delega com o Bearer humano e extrai apenas a âncora. Dependência
transitória registrada no ADR (docs 47/49); não é caminho de escrita.
"""

from __future__ import annotations

import logging
from datetime import date

from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
)

logger = logging.getLogger(__name__)


class DelegatedEarliestOvDate:
    """Implementa ``EarliestOvDateSource`` via contrato oficial api-delpi."""

    def __init__(self, client: DownstreamClient) -> None:
        self._client = client

    async def get_reference_start_date(
        self, access_token: str
    ) -> date | None:
        data = await self._client.get(
            "/engineering/lmps/nonconformities/streak",
            access_token=access_token,
        )
        if not isinstance(data, dict):
            return None
        raw = data.get("reference_start_date")
        if not raw:
            return None
        try:
            return date.fromisoformat(str(raw)[:10])
        except ValueError:
            return None
