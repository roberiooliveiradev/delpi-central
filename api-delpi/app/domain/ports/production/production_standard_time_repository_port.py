"""Port — contexto de tempo padrão de uma operação de OP (SC2/SHY/SG2)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProductionStandardTimeRepositoryPort(ABC):
    @abstractmethod
    def get_operation_standard_time_context(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any] | None:
        """Contexto cru da operação (campos SHY/SG2 + produto/unidade).

        ``None`` quando a OP não existe na filial; ``operation_exists``
        sinaliza quando a OP existe mas a operação não aparece nem no
        snapshot SHY nem no roteiro SG2.
        """
        ...
