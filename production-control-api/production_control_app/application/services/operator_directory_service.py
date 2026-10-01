"""Serviço de aplicação do diretório de operadores (C2).

Camada fina entre consumidores (bench session, run — C3) e o port do
diretório: valida o formato textual da matrícula e delega a resolução.
Nenhuma regra de sessão/run/Pulse aqui — inatividade do colaborador será
aplicada na camada de aplicação da C3, não neste serviço.
"""

from __future__ import annotations

from production_control_app.domain.errors import InvalidOperatorRegistration
from production_control_app.domain.operator_identity import OperatorIdentity
from production_control_app.domain.ports.operator_directory import (
    OperatorDirectoryPort,
)

MAX_REGISTRATION_LENGTH = 30


class OperatorDirectoryService:
    def __init__(self, directory: OperatorDirectoryPort) -> None:
        self._directory = directory

    def find_by_registration(self, registration: str) -> OperatorIdentity:
        """Valida a matrícula textual e resolve a identidade oficial."""
        value = (registration or "").strip()
        if not value or len(value) > MAX_REGISTRATION_LENGTH:
            raise InvalidOperatorRegistration(
                "Matrícula inválida: texto obrigatório de até 30 caracteres."
            )
        return self._directory.find_by_registration(value)
