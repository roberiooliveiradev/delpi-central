from __future__ import annotations

from app.config import settings
from app.domain.propostas_comerciais.exceptions import PropostaComercialNotFoundError
from app.domain.propostas_comerciais.ports.proposta_comercial_repository_port import (
    PropostaComercialRepositoryPort,
)
from app.domain.propostas_comerciais.services.proposta_comercial_formatter import (
    PropostaComercialFormatter,
)


class GetPropostaComercialUseCase:
    def __init__(self, repository: PropostaComercialRepositoryPort):
        self._repository = repository

    def execute(self, proposta_interna: str) -> dict:
        code = (proposta_interna or "").strip()
        if not code:
            raise PropostaComercialNotFoundError(proposta_interna)

        header, items = self._repository.get_detail_rows(code)
        if not header:
            raise PropostaComercialNotFoundError(code)

        header = dict(header)
        header["observacoes"] = PropostaComercialFormatter.normalize_observacoes(
            header.get("observacoes")
        )

        return PropostaComercialFormatter.format_detail(
            header,
            items,
            empresa_site=settings.PROPOSTAS_COMERCIAIS_EMPRESA_SITE,
        )
