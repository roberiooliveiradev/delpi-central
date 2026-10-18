from __future__ import annotations

from typing import Protocol
from uuid import UUID

from production_control_app.domain.sequencing_profile import (
    SequencingProfile,
    SequencingProfileBinding,
)


class SequencingProfileRepositoryPort(Protocol):
    """Persistência administrativa dos perfis de sequenciamento.

    Nenhuma operação toca a fila WORKING/PUBLISHED — é catálogo do PCP.
    """

    def list_profiles(self) -> list[SequencingProfile]:
        ...

    def get_profile(self, *, profile_id: UUID) -> SequencingProfile | None:
        ...

    def create_profile(
        self,
        *,
        name: str,
        description: str | None,
        status: str,
        criteria: list[dict],
        actor: str | None,
    ) -> SequencingProfile:
        """Insere perfil + revisão 1 (audit) na mesma transação."""
        ...

    def update_profile(
        self,
        *,
        profile_id: UUID,
        expected_revision: int,
        name: str,
        description: str | None,
        status: str,
        criteria: list[dict],
        actor: str | None,
    ) -> SequencingProfile | None:
        """UPDATE otimista: retorna None quando a revisão diverge (→ 409)."""
        ...

    def get_binding(
        self, *, branch: str, work_center: str
    ) -> SequencingProfileBinding | None:
        ...

    def list_bindings(
        self, *, branch: str, work_center: str | None = None
    ) -> list[SequencingProfileBinding]:
        ...

    def set_binding(
        self,
        *,
        branch: str,
        work_center: str,
        profile_id: UUID | None,
        actor: str | None,
    ) -> SequencingProfileBinding | None:
        """UPSERT/DELETE do vínculo + evento de auditoria na mesma transação."""
        ...
