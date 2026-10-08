"""Port — consulta ao desenho PDF do produto na biblioteca oficial (P4).

O desenho NÃO é persistido nem copiado para o Requests: a resolução acontece
em tempo real contra a api-delpi (fonte canônica). Somente o código do PA,
congelado no payload do request, identifica qual desenho consultar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProductDrawingFile:
    filename: str
    content: bytes
    media_type: str = "application/pdf"


class ProductDrawingGatewayPort(Protocol):
    def resolve_pdf(self, code: str) -> ProductDrawingFile:
        """Resolve o PDF corrente do produto. Levanta ApplicationError:
        drawing_not_found (404), drawing_source_unavailable (503),
        drawing_upstream_error (502)."""
        ...
