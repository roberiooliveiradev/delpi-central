"""Administração dos perfis de sequenciamento por centro de trabalho.

Fundação administrativa da iniciativa «Regras de Sequenciamento»: cadastro,
edição versionada e vínculo perfil ↔ (filial, CT). Nada aqui toca a fila
WORKING/PUBLISHED — o motor de `machine_load_optimization.py` segue inalterado
e não consome estes perfis nesta etapa.

Autorização: leitura exige `machine-load.view` + filial; escrita exige a
permissão administrativa dedicada `sequencing-profiles.manage` + filial. O
backend é a única autoridade — nenhum dado do frontend é confiável.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from production_control_app.core.security import (
    ALLOWED_BRANCHES,
    BRANCH_VIEW_PERMISSIONS,
    PC_MACHINE_LOAD_VIEW,
    PC_SEQUENCING_PROFILES_MANAGE,
    can,
)
from production_control_app.domain.errors import (
    SequencingProfileConflict,
    SequencingProfileInvalid,
    SequencingProfileNotFound,
)
from production_control_app.domain.ports.sequencing_profile_repository import (
    SequencingProfileRepositoryPort,
)
from production_control_app.domain.sequencing_profile import (
    PROFILE_STATUS_DRAFT,
    SequencingProfile,
    SequencingProfileBinding,
    validate_criteria,
    validate_name,
    validate_status,
)
from production_control_app.domain.services.branch_access_service import (
    BranchAccessService,
)


def _user_label(user: object | None) -> str | None:
    if user is None:
        return None
    for attr in ("id", "username", "email", "preferred_username"):
        value = getattr(user, attr, None)
        if value:
            return str(value)[:120]
    return None


def _profile_payload(profile: SequencingProfile) -> dict[str, Any]:
    return {
        "id": str(profile.id),
        "name": profile.name,
        "description": profile.description,
        "status": profile.status,
        "revision": profile.revision,
        "criteria": profile.criteria,
        "origin_branch": profile.origin_branch,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "created_by": profile.created_by,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        "updated_by": profile.updated_by,
    }


def _binding_payload(binding: SequencingProfileBinding) -> dict[str, Any]:
    return {
        "branch": binding.branch,
        "work_center": binding.work_center,
        "profile_id": str(binding.profile_id),
        "assigned_by": binding.assigned_by,
        "assigned_at": (
            binding.assigned_at.isoformat() if binding.assigned_at else None
        ),
    }


class SequencingProfileService:
    def __init__(
        self,
        repository: SequencingProfileRepositoryPort,
        branch_access: BranchAccessService | None = None,
    ) -> None:
        self._repo = repository
        self._branch_access = branch_access or BranchAccessService()

    # ---- autorização -----------------------------------------------------

    def _assert_can_view(self, user: object | None, branch: str) -> str:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_MACHINE_LOAD_VIEW):
            raise PermissionError(
                "Você não tem permissão para ver as regras de sequenciamento."
            )
        return self._branch_access.assert_valid_branch(branch)

    def _assert_can_manage(self, user: object | None, branch: str) -> str:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_SEQUENCING_PROFILES_MANAGE):
            raise PermissionError(
                "Você não tem permissão para administrar regras de sequenciamento."
            )
        return self._branch_access.assert_valid_branch(branch)

    def _managed_branches(self, user: object | None) -> frozenset[str]:
        """Filiais que o usuário pode administrar (acesso de filial + manage).

        O parâmetro `branch` do request NÃO é autorização — o escopo real vem
        das permissões do usuário, avaliadas aqui no backend.
        """
        if not can(user, PC_SEQUENCING_PROFILES_MANAGE):
            return frozenset()
        return frozenset(
            b for b in ALLOWED_BRANCHES
            if can(user, BRANCH_VIEW_PERMISSIONS[b])
        )

    # ---- perfis ----------------------------------------------------------

    def list_profiles(
        self, user: object | None, *, branch: str
    ) -> dict[str, Any]:
        branch = self._assert_can_view(user, branch)
        profiles = self._repo.list_profiles()
        bindings = self._repo.list_bindings(branch=branch)
        binding_by_profile: dict[str, list[dict[str, Any]]] = {}
        for binding in bindings:
            binding_by_profile.setdefault(str(binding.profile_id), []).append(
                _binding_payload(binding)
            )
        items = []
        for profile in profiles:
            # Visibilidade por escopo autorizado: perfil originado em outra
            # filial não é administrável aqui (política cross-branch pendente)
            # e não deve nem aparecer na listagem da filial. Perfis legados
            # sem origin_branch permanecem visíveis para correção.
            if profile.origin_branch not in (None, branch):
                continue
            item = _profile_payload(profile)
            item["bindings"] = binding_by_profile.get(str(profile.id), [])
            items.append(item)
        return {"items": items, "total": len(items)}

    def get_profile(
        self, user: object | None, *, branch: str, profile_id: UUID
    ) -> dict[str, Any]:
        branch = self._assert_can_view(user, branch)
        profile = self._repo.get_profile(profile_id=profile_id)
        # Mesma política de visibilidade da listagem: perfil de outra filial
        # responde 404 (não vaza existência); legado sem origem segue acessível.
        if profile is None or profile.origin_branch not in (None, branch):
            raise SequencingProfileNotFound(
                "Perfil de sequenciamento não encontrado."
            )
        data = _profile_payload(profile)
        bindings = self._repo.list_bindings(branch=branch)
        data["bindings"] = [
            _binding_payload(b) for b in bindings if b.profile_id == profile.id
        ]
        return data

    def create_profile(
        self,
        user: object | None,
        *,
        branch: str,
        name: str,
        description: str | None,
        criteria: Any,
    ) -> dict[str, Any]:
        branch = self._assert_can_manage(user, branch)
        # Todo perfil nasce rascunho — a ativação é uma decisão posterior
        # explícita, nunca implícita no cadastro.
        profile = self._repo.create_profile(
            name=validate_name(name),
            description=(description or "").strip() or None,
            status=PROFILE_STATUS_DRAFT,
            criteria=validate_criteria(criteria),
            origin_branch=branch,
            actor=_user_label(user),
        )
        return _profile_payload(profile)

    def update_profile(
        self,
        user: object | None,
        *,
        branch: str,
        profile_id: UUID,
        expected_revision: int,
        name: str,
        description: str | None,
        status: str,
        criteria: Any,
    ) -> dict[str, Any]:
        self._assert_can_manage(user, branch)
        if not isinstance(expected_revision, int) or expected_revision < 1:
            raise SequencingProfileInvalid(
                "expected_revision é obrigatório e deve ser >= 1."
            )
        # Política estrita (pendente de ratificação formal — ADR no doc):
        # o repositório re-lê, DENTRO da transação que atualiza, as filiais
        # afetadas (origem ∪ vínculos) e exige que o chamador administre
        # TODAS elas. Isso fecha o TOCTOU entre a verificação e o write —
        # `set_binding` trava a mesma linha do perfil antes de mutar.
        updated = self._repo.update_profile(
            profile_id=profile_id,
            expected_revision=expected_revision,
            managed_branches=self._managed_branches(user),
            name=validate_name(name),
            description=(description or "").strip() or None,
            status=validate_status(status),
            criteria=validate_criteria(criteria),
            actor=_user_label(user),
        )
        if updated is None:
            if self._repo.get_profile(profile_id=profile_id) is None:
                raise SequencingProfileNotFound(
                    "Perfil de sequenciamento não encontrado."
                )
            raise SequencingProfileConflict(
                "O perfil foi alterado por outra pessoa. Recarregue antes de "
                "salvar novamente."
            )
        return _profile_payload(updated)

    # ---- vínculos --------------------------------------------------------

    def list_bindings(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        branch = self._assert_can_view(user, branch)
        bindings = self._repo.list_bindings(
            branch=branch, work_center=work_center
        )
        items = [_binding_payload(b) for b in bindings]
        return {"items": items, "total": len(items)}

    def set_binding(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str,
        profile_id: UUID | None,
    ) -> dict[str, Any]:
        branch = self._assert_can_manage(user, branch)
        center = str(work_center or "").strip()
        if not center or len(center) > 40:
            raise SequencingProfileInvalid(
                "Centro de trabalho é obrigatório (máx. 40 caracteres)."
            )
        if profile_id is not None:
            profile = self._repo.get_profile(profile_id=profile_id)
            if profile is None:
                raise SequencingProfileNotFound(
                    "Perfil de sequenciamento não encontrado."
                )
            if profile.status == "archived":
                raise SequencingProfileConflict(
                    "Não é possível vincular um perfil arquivado."
                )
        binding = self._repo.set_binding(
            branch=branch,
            work_center=center,
            profile_id=profile_id,
            managed_branches=self._managed_branches(user),
            actor=_user_label(user),
        )
        return {
            "branch": branch,
            "work_center": center,
            "profile_id": str(binding.profile_id) if binding else None,
            "assigned_by": binding.assigned_by if binding else None,
            "assigned_at": (
                binding.assigned_at.isoformat()
                if binding and binding.assigned_at
                else None
            ),
        }
