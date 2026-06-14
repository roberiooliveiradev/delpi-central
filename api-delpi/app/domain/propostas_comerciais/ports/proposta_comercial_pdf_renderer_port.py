from __future__ import annotations

from typing import Protocol


class PropostaComercialPdfRendererPort(Protocol):
    def render(self, detail: dict) -> bytes:
        """Renderiza o detalhe formatado da proposta comercial em PDF."""
