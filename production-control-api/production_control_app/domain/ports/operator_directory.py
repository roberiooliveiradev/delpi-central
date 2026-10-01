"""Port do diretório oficial de colaboradores (Portal RH) — C2.

Domínio não conhece HTTP, URL, header S2S ou o modelo Django do Portal RH.
"""

from __future__ import annotations

from typing import Protocol

from production_control_app.domain.operator_identity import OperatorIdentity


class OperatorDirectoryPort(Protocol):
    def find_by_registration(self, registration: str) -> OperatorIdentity:
        """Resolve a matrícula textual em identidade oficial.

        registration chega já validada pela camada de aplicação
        (strip + não vazia + <= 30) e permanece string — "001" != "1".

        Erros de domínio: OperatorNotFound (404),
        OperatorDirectoryUnauthorized (401/403),
        OperatorDirectoryUnavailable (rede/timeout/5xx/config),
        OperatorDirectoryContractError (200 fora do contrato).
        """
        ...
