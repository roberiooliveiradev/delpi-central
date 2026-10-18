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
        origin_branch: str,
        actor: str | None,
    ) -> SequencingProfile:
        """Insere perfil + revisão 1 (audit) na mesma transação."""
        ...

    def list_bound_branches(self, *, profile_id: UUID) -> list[str]:
        """Filiais onde o perfil está vinculado — autorização de edição."""
        ...

    def update_profile(
        self,
        *,
        profile_id: UUID,
        expected_revision: int,
        managed_branches: frozenset[str],
        name: str,
        description: str | None,
        status: str,
        criteria: list[dict],
        actor: str | None,
    ) -> SequencingProfile | None:
        """UPDATE otimista: retorna None quando a revisão diverge (→ 409).

        A verificação de filiais afetadas (origem ∪ vínculos ⊆
        `managed_branches`) acontece DENTRO da transação, com a linha do
        perfil travada — não há janela para um vínculo concorrente
        autorizar uma edição indevida. Violação → PermissionError.
        """
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
        managed_branches: frozenset[str],
        actor: str | None,
    ) -> SequencingProfileBinding | None:
        """UPSERT/DELETE do vínculo + evento de auditoria na mesma transação.

        Vincular expande as filiais afetadas pelo perfil: exige que o
        chamador administre TODAS elas (origem ∪ vínculos ∪ nova filial),
        verificado sob a trava da linha do perfil. Vínculo dentro de filial
        já associada não exige escopo extra. Perfil legado sem
        `origin_branch` não pode ser reivindicado por primeiro vínculo.
        """
        ...
