"""Regras de Sequenciamento — fundação administrativa (Etapa 1).

Cobre: validação de critérios tipados, CRUD versionado (concorrência otimista),
vínculo perfil ↔ (filial, CT), autorização view/manage por filial, auditoria e
isolamento da fila WORKING/PUBLISHED (o motor não é tocado nesta etapa).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.sequencing_profile_service import (
    SequencingProfileService,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    SequencingProfileConflict,
    SequencingProfileInvalid,
    SequencingProfileNotFound,
)
from production_control_app.domain.sequencing_profile import (
    PROFILE_STATUS_ARCHIVED,
    PROFILE_STATUS_DRAFT,
    SequencingProfile,
    SequencingProfileBinding,
    validate_criteria,
)
from production_control_app.interface.http.routes.sequencing_profile_routes import (
    router,
)

BRANCH = "02"
CENTER = "CT-02B"

# Grupos B1_GRUPO que identificam cabos elegíveis para o CT-02B (filial 02 —
# corte e decape). O agrupamento usa o D4_COD exato; o grupo só filtra a
# elegibilidade do componente.
CABLE_PRODUCT_GROUPS = [
    "1037", "1038", "1053", "1007", "1042", "1047", "1040", "1041",
    "1055", "1049", "1002", "1001", "1005", "1051", "1044", "1036",
]


def pilot_profile_payload() -> dict:
    """Perfil-piloto «Corte e Decape — Entrega e Cabo» (CT-02B, filial 02).

    Fixture de teste — nada aqui é semeado automaticamente em produção.
    """
    return {
        "name": "Corte e Decape - Entrega e Cabo",
        "description": "Entrega do PA primeiro; dentro da data, agrupa pelo "
        "código exato do cabo (D4_COD) elegível nos grupos MP.",
        "criteria": [
            {"type": "pa_due_date"},
            {
                "type": "material_code",
                "params": {
                    "material_type": "MP",
                    "eligible_product_groups": CABLE_PRODUCT_GROUPS,
                    "identity_source": "operation_then_order",
                    "ignore_zeroed_allocations": True,
                    "on_missing": "flag",
                    "on_ambiguous": "flag",
                },
            },
        ],
    }


def _manager(**perms: str) -> SimpleNamespace:
    return SimpleNamespace(
        is_superadmin=False,
        permissions=[
            "production-control.access",
            "production-control.machine-load.view",
            "production-control.sequencing-profiles.manage",
            "production-control.view.filial-02",
            *perms,
        ],
        email="pcp.admin@delpi.local",
    )


def _viewer() -> SimpleNamespace:
    return SimpleNamespace(
        is_superadmin=False,
        permissions=[
            "production-control.access",
            "production-control.machine-load.view",
            "production-control.view.filial-02",
        ],
        email="pcp.viewer@delpi.local",
    )


def _dual_manager() -> SimpleNamespace:
    return SimpleNamespace(
        is_superadmin=False,
        permissions=[
            "production-control.access",
            "production-control.machine-load.view",
            "production-control.sequencing-profiles.manage",
            "production-control.view.filial-01",
            "production-control.view.filial-02",
        ],
        email="pcp.admin.dual@delpi.local",
    )


def _superadmin() -> SimpleNamespace:
    return SimpleNamespace(
        is_superadmin=True,
        permissions=[],
        email="root@delpi.local",
    )


def _branch01_user() -> SimpleNamespace:
    return SimpleNamespace(
        is_superadmin=False,
        permissions=[
            "production-control.access",
            "production-control.machine-load.view",
            "production-control.sequencing-profiles.manage",
            "production-control.view.filial-01",
        ],
        email="pcp.filial01@delpi.local",
    )


class FakeSequencingProfileRepository:
    """Mesma semântica do Postgres: revisão otimista e auditoria transacional."""

    def __init__(self) -> None:
        self.profiles: dict[UUID, SequencingProfile] = {}
        self.revisions: list[dict] = []
        self.bindings: dict[tuple[str, str], SequencingProfileBinding] = {}
        self.binding_events: list[dict] = []
        self.fail_writes = False

    def _check(self) -> None:
        if self.fail_writes:
            raise RuntimeError("db down")

    def list_profiles(self) -> list[SequencingProfile]:
        return sorted(self.profiles.values(), key=lambda p: p.name)

    def get_profile(self, *, profile_id: UUID) -> SequencingProfile | None:
        return self.profiles.get(profile_id)

    def create_profile(
        self, *, name, description, status, criteria, origin_branch, actor
    ):
        self._check()
        profile = SequencingProfile(
            id=uuid4(),
            name=name,
            description=description,
            status=status,
            revision=1,
            criteria=criteria,
            origin_branch=origin_branch,
            created_at=datetime.now(timezone.utc),
            created_by=actor,
            updated_at=datetime.now(timezone.utc),
            updated_by=actor,
        )
        self.profiles[profile.id] = profile
        self.revisions.append(
            {
                "profile_id": profile.id,
                "revision": 1,
                "action": "created",
                "actor": actor,
            }
        )
        return profile

    def update_profile(
        self, *, profile_id, expected_revision, managed_branches, name,
        description, status, criteria, actor,
    ):
        self._check()
        current = self.profiles.get(profile_id)
        if current is not None:
            affected = {
                b.branch
                for b in self.bindings.values()
                if b.profile_id == profile_id
            }
            if current.origin_branch:
                affected.add(current.origin_branch)
            if not affected or not affected <= set(managed_branches):
                raise PermissionError(
                    "Edição exige administração em todas as filiais afetadas."
                )
        if current is None or current.revision != expected_revision:
            return None
        updated = SequencingProfile(
            id=profile_id,
            name=name,
            description=description,
            status=status,
            revision=current.revision + 1,
            criteria=criteria,
            origin_branch=current.origin_branch,
            created_at=current.created_at,
            created_by=current.created_by,
            updated_at=datetime.now(timezone.utc),
            updated_by=actor,
        )
        self.profiles[profile_id] = updated
        self.revisions.append(
            {
                "profile_id": profile_id,
                "revision": updated.revision,
                "action": "updated",
                "actor": actor,
            }
        )
        return updated

    def list_bound_branches(self, *, profile_id):
        return sorted(
            {b.branch for b in self.bindings.values() if b.profile_id == profile_id}
        )

    def get_binding(self, *, branch, work_center):
        return self.bindings.get((branch, work_center))

    def list_bindings(self, *, branch, work_center=None):
        items = [b for (b_branch, _), b in self.bindings.items() if b_branch == branch]
        if work_center is not None:
            items = [b for b in items if b.work_center == work_center]
        return items

    def set_binding(
        self, *, branch, work_center, profile_id, managed_branches, actor
    ):
        self._check()
        key = (branch, work_center)
        previous = self.bindings.get(key)
        if profile_id is not None:
            profile = self.profiles[profile_id]
            bound = {
                b.branch
                for b in self.bindings.values()
                if b.profile_id == profile_id
            }
            if profile.origin_branch is None and branch not in bound:
                raise PermissionError(
                    "Perfil sem filial de origem não pode ser reivindicado."
                )
            required = set(bound) | {branch}
            if profile.origin_branch:
                required.add(profile.origin_branch)
            if not required <= set(managed_branches):
                raise PermissionError(
                    "Vincular exige administração em todas as filiais afetadas."
                )
        if profile_id is None:
            if previous is None:
                return None
            del self.bindings[key]
            self.binding_events.append(
                {"action": "unbound", "previous_profile_id": previous.profile_id,
                 "actor": actor}
            )
            return None
        if previous is None:
            action = "bound"
        elif previous.profile_id == profile_id:
            return previous
        else:
            action = "rebound"
        binding = SequencingProfileBinding(
            branch=branch,
            work_center=work_center,
            profile_id=profile_id,
            assigned_by=actor,
            assigned_at=datetime.now(timezone.utc),
        )
        self.bindings[key] = binding
        self.binding_events.append(
            {
                "action": action,
                "profile_id": profile_id,
                "previous_profile_id": previous.profile_id if previous else None,
                "actor": actor,
            }
        )
        return binding


def _service() -> tuple[SequencingProfileService, FakeSequencingProfileRepository]:
    repo = FakeSequencingProfileRepository()
    return SequencingProfileService(repository=repo), repo


def _client(service: SequencingProfileService, user) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = user
        return await call_next(request)

    app.include_router(router)

    import production_control_app.interface.http.routes.sequencing_profile_routes as routes

    routes.build_sequencing_profile_service = lambda: service  # type: ignore[method-assign]
    return TestClient(app)


# --- domínio: critérios -----------------------------------------------------


class TestCriteriaValidation:
    def test_pa_due_date_must_be_first(self) -> None:
        with pytest.raises(SequencingProfileInvalid, match="primeiro critério"):
            validate_criteria([{"type": "tool_group"}])
        with pytest.raises(SequencingProfileInvalid, match="primeiro critério"):
            validate_criteria(
                [{"type": "tool_group"}, {"type": "pa_due_date"}]
            )

    def test_empty_and_missing_criteria_rejected(self) -> None:
        with pytest.raises(SequencingProfileInvalid):
            validate_criteria([])
        with pytest.raises(SequencingProfileInvalid):
            validate_criteria(None)

    def test_unknown_type_rejected(self) -> None:
        with pytest.raises(SequencingProfileInvalid, match="desconhecido"):
            validate_criteria(
                [{"type": "pa_due_date"}, {"type": "custom_script"}]
            )

    def test_duplicate_type_rejected(self) -> None:
        with pytest.raises(SequencingProfileInvalid, match="duplicado"):
            validate_criteria(
                [{"type": "pa_due_date"}, {"type": "pa_due_date"}]
            )
        with pytest.raises(SequencingProfileInvalid, match="duplicado"):
            validate_criteria(
                [
                    {"type": "pa_due_date"},
                    {"type": "material_code",
                     "params": {"eligible_product_groups": ["1037"]}},
                    {"type": "material_code",
                     "params": {"eligible_product_groups": ["1001"]}},
                ]
            )

    def test_simple_criteria_reject_params(self) -> None:
        with pytest.raises(SequencingProfileInvalid, match="não aceita"):
            validate_criteria(
                [{"type": "pa_due_date", "params": {"foo": 1}}]
            )
        with pytest.raises(SequencingProfileInvalid, match="não aceita"):
            validate_criteria(
                [{"type": "pa_due_date"}, {"type": "tool_group", "params": {"x": 1}}]
            )

    def test_order_is_preserved(self) -> None:
        criteria = validate_criteria(
            [
                {"type": "pa_due_date"},
                {"type": "material_code",
                 "params": {"eligible_product_groups": ["1037"]}},
                {"type": "tool_group"},
            ]
        )
        assert [c["type"] for c in criteria] == [
            "pa_due_date",
            "material_code",
            "tool_group",
        ]

    def test_material_params_normalized(self) -> None:
        criteria = validate_criteria(
            [
                {"type": "pa_due_date"},
                {
                    "type": "material_code",
                    "params": {
                        "eligible_product_groups": ["1037", " 1038 "],
                    },
                },
            ]
        )
        params = criteria[1]["params"]
        assert params["material_type"] == "MP"
        assert params["eligible_product_groups"] == ["1037", "1038"]
        assert params["identity_source"] == "operation_then_order"
        assert params["ignore_zeroed_allocations"] is True
        assert params["on_missing"] == "flag"
        assert params["on_ambiguous"] == "flag"

    def test_pilot_sixteen_groups_accepted(self) -> None:
        criteria = validate_criteria(pilot_profile_payload()["criteria"])
        assert criteria[1]["params"]["eligible_product_groups"] == CABLE_PRODUCT_GROUPS
        assert len(CABLE_PRODUCT_GROUPS) == 16

    def test_material_params_rejected(self) -> None:
        base = {"type": "material_code", "params": {}}
        with pytest.raises(SequencingProfileInvalid):
            validate_criteria([{"type": "pa_due_date"}, base])
        for params in (
            {"eligible_product_groups": []},
            {"eligible_product_groups": ["1037", "1037"]},
            {"eligible_product_groups": ["abc!"]},
            {"eligible_product_groups": ["1037"], "material_type": "PA"},
            {"eligible_product_groups": ["1037"], "identity_source": "order_only"},
            {"eligible_product_groups": ["1037"], "ignore_zeroed_allocations": "yes"},
            {"eligible_product_groups": ["1037"], "on_missing": "skip"},
            {"eligible_product_groups": ["1037"], "unknown_param": 1},
        ):
            with pytest.raises(SequencingProfileInvalid):
                validate_criteria(
                    [
                        {"type": "pa_due_date"},
                        {"type": "material_code", "params": params},
                    ]
                )


# --- aplicação: CRUD + vínculo ---------------------------------------------


class TestProfileService:
    def test_create_and_get_roundtrip(self) -> None:
        service, repo = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        assert created["status"] == PROFILE_STATUS_DRAFT
        assert created["revision"] == 1
        assert created["created_by"] == "pcp.admin@delpi.local"

        fetched = service.get_profile(
            _viewer(), branch=BRANCH, profile_id=UUID(created["id"])
        )
        assert fetched["name"] == "Corte e Decape - Entrega e Cabo"
        assert fetched["criteria"][1]["params"]["eligible_product_groups"] == (
            CABLE_PRODUCT_GROUPS
        )

        # Auditoria: revisão 1 registrada com o ator.
        assert repo.revisions == [
            {
                "profile_id": UUID(created["id"]),
                "revision": 1,
                "action": "created",
                "actor": "pcp.admin@delpi.local",
            }
        ]

    def test_update_bumps_revision_and_audits(self) -> None:
        service, repo = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        updated = service.update_profile(
            _manager(),
            branch=BRANCH,
            profile_id=UUID(created["id"]),
            expected_revision=1,
            name="Corte e Decape - Entrega e Cabo v2",
            description=None,
            status="active",
            criteria=pilot_profile_payload()["criteria"],
        )
        assert updated["revision"] == 2
        assert updated["status"] == "active"
        assert [r["revision"] for r in repo.revisions] == [1, 2]
        assert repo.revisions[-1]["action"] == "updated"

    def test_update_with_stale_revision_conflicts(self) -> None:
        service, _ = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        service.update_profile(
            _manager(),
            branch=BRANCH,
            profile_id=UUID(created["id"]),
            expected_revision=1,
            name="v2",
            description=None,
            status="draft",
            criteria=pilot_profile_payload()["criteria"],
        )
        with pytest.raises(SequencingProfileConflict):
            service.update_profile(
                _manager(),
                branch=BRANCH,
                profile_id=UUID(created["id"]),
                expected_revision=1,  # revisão velha — quem salvou depois ganhou
                name="v3",
                description=None,
                status="draft",
                criteria=pilot_profile_payload()["criteria"],
            )

    def test_update_missing_profile_is_not_found(self) -> None:
        service, _ = _service()
        with pytest.raises(SequencingProfileNotFound):
            service.update_profile(
                _manager(),
                branch=BRANCH,
                profile_id=uuid4(),
                expected_revision=1,
                name="x",
                description=None,
                status="draft",
                criteria=pilot_profile_payload()["criteria"],
            )

    def test_binding_and_unbinding(self) -> None:
        service, repo = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])

        bound = service.set_binding(
            _manager(), branch=BRANCH, work_center=CENTER, profile_id=profile_id
        )
        assert bound["profile_id"] == created["id"]
        assert bound["assigned_by"] == "pcp.admin@delpi.local"
        assert repo.binding_events[-1]["action"] == "bound"

        listing = service.list_bindings(_viewer(), branch=BRANCH, work_center=CENTER)
        assert listing["total"] == 1
        assert listing["items"][0]["work_center"] == CENTER

        unbound = service.set_binding(
            _manager(), branch=BRANCH, work_center=CENTER, profile_id=None
        )
        assert unbound["profile_id"] is None
        assert repo.binding_events[-1]["action"] == "unbound"
        assert service.list_bindings(_viewer(), branch=BRANCH)["total"] == 0

    def test_rebind_same_profile_is_idempotent(self) -> None:
        service, repo = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        first = service.set_binding(
            _manager(), branch=BRANCH, work_center=CENTER, profile_id=profile_id
        )
        second = service.set_binding(
            _manager(), branch=BRANCH, work_center=CENTER, profile_id=profile_id
        )
        # mesma linha, sem evento novo, ator original preservado
        assert second["profile_id"] == first["profile_id"]
        assert len(repo.binding_events) == 1
        assert repo.bindings[(BRANCH, CENTER)].assigned_by == "pcp.admin@delpi.local"

    def test_profile_reused_across_work_centers(self) -> None:
        service, repo = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        for center in ("CT-02B", "CT-02C"):
            service.set_binding(
                _manager(), branch=BRANCH, work_center=center, profile_id=profile_id
            )
        assert service.list_bindings(_viewer(), branch=BRANCH)["total"] == 2
        # O mesmo perfil não pode ser assumido como vínculo de outra filial sem
        # a permissão da filial — verificado no teste de escopo abaixo.
        assert len(repo.bindings) == 2

    def test_binding_to_archived_profile_rejected(self) -> None:
        service, _ = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        service.update_profile(
            _manager(),
            branch=BRANCH,
            profile_id=UUID(created["id"]),
            expected_revision=1,
            name="x",
            description=None,
            status=PROFILE_STATUS_ARCHIVED,
            criteria=pilot_profile_payload()["criteria"],
        )
        with pytest.raises(SequencingProfileConflict, match="arquivado"):
            service.set_binding(
                _manager(),
                branch=BRANCH,
                work_center=CENTER,
                profile_id=UUID(created["id"]),
            )

    def test_binding_to_missing_profile_is_not_found(self) -> None:
        service, _ = _service()
        with pytest.raises(SequencingProfileNotFound):
            service.set_binding(
                _manager(), branch=BRANCH, work_center=CENTER, profile_id=uuid4()
            )

    def test_view_permission_is_not_enough_to_write(self) -> None:
        service, _ = _service()
        with pytest.raises(PermissionError):
            service.create_profile(
                _viewer(), branch=BRANCH, **pilot_profile_payload()
            )

    def test_manage_without_view_still_blocked_by_branch(self) -> None:
        service, _ = _service()
        # Tem manage mas não tem acesso à filial 02 — branch gate primeiro.
        with pytest.raises(BranchAccessDenied):
            service.create_profile(
                _branch01_user(), branch=BRANCH, **pilot_profile_payload()
            )

    def test_branch_without_permission_cannot_bind(self) -> None:
        service, _ = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        # O perfil é global e pode ser vinculado em qualquer filial — mas quem
        # só tem acesso à filial 01 não pode escrever na 02.
        with pytest.raises(BranchAccessDenied):
            service.set_binding(
                _branch01_user(),
                branch=BRANCH,
                work_center=CENTER,
                profile_id=UUID(created["id"]),
            )

    def _update(self, service, user, branch, profile_id, revision=1):
        return service.update_profile(
            user,
            branch=branch,
            profile_id=profile_id,
            expected_revision=revision,
            name="tentativa cross-branch",
            description=None,
            status="draft",
            criteria=pilot_profile_payload()["criteria"],
        )

    def test_cross_branch_update_denied(self) -> None:
        """Admin da filial 01 não edita perfil que só afeta a filial 02 —
        mesmo enxergando o catálogo global com branch=01."""
        service, _ = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        service.set_binding(
            _manager(), branch=BRANCH, work_center=CENTER, profile_id=profile_id
        )
        with pytest.raises(PermissionError, match="todas as filiais"):
            self._update(service, _branch01_user(), "01", profile_id)

    def test_unbound_profile_cross_branch_denied(self) -> None:
        """Perfil ainda não vinculado só é editável pela filial de origem."""
        service, _ = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        with pytest.raises(PermissionError, match="todas as filiais"):
            self._update(service, _branch01_user(), "01", profile_id)
        # O dono (filial de origem 02) edita normalmente.
        updated = self._update(service, _manager(), BRANCH, profile_id)
        assert updated["revision"] == 2

    def test_shared_profile_requires_all_affected_branches(self) -> None:
        """Admin só da filial 01 NÃO edita perfil compartilhado com a 02 —
        a política estrita exige administração em TODAS as filiais afetadas."""
        service, _ = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        service.set_binding(
            _manager(), branch=BRANCH, work_center=CENTER, profile_id=profile_id
        )
        service.set_binding(
            _dual_manager(),
            branch="01",
            work_center="CT-01X",
            profile_id=profile_id,
        )
        with pytest.raises(PermissionError, match="todas as filiais"):
            self._update(service, _branch01_user(), "01", profile_id)

    def test_shared_profile_editable_by_dual_branch_admin(self) -> None:
        """Quem administra as duas filiais afetadas edita o perfil
        compartilhado — a reutilização legítima é preservada."""
        service, _ = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        service.set_binding(
            _manager(), branch=BRANCH, work_center=CENTER, profile_id=profile_id
        )
        service.set_binding(
            _dual_manager(),
            branch="01",
            work_center="CT-01X",
            profile_id=profile_id,
        )
        updated = self._update(service, _dual_manager(), "01", profile_id)
        assert updated["revision"] == 2
        # Superadmin (can() resolve todas as permissões) também edita.
        updated = self._update(
            service, _superadmin(), "01", profile_id, revision=2
        )
        assert updated["revision"] == 3

    def test_branch_param_is_not_authorization(self) -> None:
        """Declarar branch=02 no request não concede acesso à filial 02 —
        o escopo vem das permissões, nunca do parâmetro."""
        service, _ = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        with pytest.raises(BranchAccessDenied):
            self._update(service, _branch01_user(), BRANCH, profile_id)

    def test_list_profiles_hides_profiles_from_other_branches(self) -> None:
        """Revisão E4: perfil originado em outra filial não aparece na lista —
        não é administrável aqui (cross-branch pendente de ratificação)."""
        import dataclasses

        service, repo = _service()
        own = service.create_profile(
            _dual_manager(), branch=BRANCH, **pilot_profile_payload()
        )
        other_branch = "01" if BRANCH == "02" else "02"
        other_payload = dict(pilot_profile_payload(), name="Perfil da outra")
        service.create_profile(
            _dual_manager(), branch=other_branch, **other_payload
        )
        legacy = service.create_profile(
            _dual_manager(),
            branch=BRANCH,
            **dict(pilot_profile_payload(), name="Legado sem origem"),
        )
        repo.profiles[UUID(legacy["id"])] = dataclasses.replace(
            repo.profiles[UUID(legacy["id"])], origin_branch=None
        )

        listed = service.list_profiles(_dual_manager(), branch=BRANCH)
        names = [item["name"] for item in listed["items"]]
        assert own["name"] in names
        assert "Legado sem origem" in names  # legado NULL segue visível
        assert "Perfil da outra" not in names
        assert listed["total"] == len(names)

    def test_get_profile_denies_other_branch_profile_by_uuid(self) -> None:
        """Revisão E4.2: o GET individual aplica a mesma visibilidade da
        listagem — perfil de outra filial responde 404 mesmo com o UUID."""
        import dataclasses

        service, repo = _service()
        other_branch = "01" if BRANCH == "02" else "02"
        foreign = service.create_profile(
            _dual_manager(),
            branch=other_branch,
            **dict(pilot_profile_payload(), name="Perfil da outra"),
        )
        legacy = service.create_profile(
            _dual_manager(),
            branch=BRANCH,
            **dict(pilot_profile_payload(), name="Legado sem origem"),
        )
        repo.profiles[UUID(legacy["id"])] = dataclasses.replace(
            repo.profiles[UUID(legacy["id"])], origin_branch=None
        )

        with pytest.raises(SequencingProfileNotFound):
            service.get_profile(
                _dual_manager(), branch=BRANCH, profile_id=UUID(foreign["id"])
            )
        visible = service.get_profile(
            _dual_manager(), branch=BRANCH, profile_id=UUID(legacy["id"])
        )
        assert visible["name"] == "Legado sem origem"

    def test_legacy_null_origin_unbound_profile_is_locked(self) -> None:
        """Perfil legado sem origin_branch e sem vínculo: conjunto de
        filiais afetadas vazio → edição negada (não inventa proprietário)."""
        import dataclasses

        service, repo = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        repo.profiles[profile_id] = dataclasses.replace(
            repo.profiles[profile_id], origin_branch=None
        )
        with pytest.raises(PermissionError, match="todas as filiais"):
            self._update(service, _dual_manager(), BRANCH, profile_id)

    def test_cross_branch_bind_denied_and_owner_keeps_editing(self) -> None:
        """Admin só da filial 01 NÃO pode vincular a seu CT um perfil com
        origem/vínculos na 02 — e o dono da 02 segue editando normalmente."""
        service, repo = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        service.set_binding(
            _manager(), branch=BRANCH, work_center=CENTER, profile_id=profile_id
        )
        with pytest.raises(PermissionError, match="nova filial|afetadas"):
            service.set_binding(
                _branch01_user(),
                branch="01",
                work_center="CT-01X",
                profile_id=profile_id,
            )
        # O vínculo foi negado — a filial 01 não entrou no conjunto afetado
        # e o dono continua podendo editar o próprio perfil.
        updated = self._update(service, _manager(), BRANCH, profile_id)
        assert updated["revision"] == 2
        assert not any(b == "01" for b, _ in repo.bindings)

    def test_same_branch_additional_bind_needs_no_extra_scope(self) -> None:
        """Novo CT na MESMA filial já associada não exige escopo extra."""
        service, _ = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        service.set_binding(
            _manager(), branch=BRANCH, work_center=CENTER, profile_id=profile_id
        )
        service.set_binding(
            _manager(),
            branch=BRANCH,
            work_center="CT-02C",
            profile_id=profile_id,
        )
        assert service.list_bindings(_viewer(), branch=BRANCH)["total"] == 2

    def test_dual_branch_admin_expands_to_new_branch(self) -> None:
        """Quem administra todas as filiais afetadas (a 02 já associada e a
        nova 01) pode expandir o compartilhamento."""
        service, _ = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        service.set_binding(
            _manager(), branch=BRANCH, work_center=CENTER, profile_id=profile_id
        )
        bound = service.set_binding(
            _dual_manager(),
            branch="01",
            work_center="CT-01X",
            profile_id=profile_id,
        )
        assert bound["profile_id"] == created["id"]

    def test_unbound_profile_first_bind_by_owning_branch_only(self) -> None:
        """Perfil ainda sem vínculo só pode ser primeiro-vinculado por quem
        administra a filial de origem (senão outra filial o reivindicaria)."""
        service, _ = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        with pytest.raises(PermissionError):
            service.set_binding(
                _branch01_user(),
                branch="01",
                work_center="CT-01X",
                profile_id=profile_id,
            )
        service.set_binding(
            _manager(), branch=BRANCH, work_center=CENTER, profile_id=profile_id
        )

    def test_legacy_null_origin_cannot_be_claimed_by_first_bind(self) -> None:
        """Perfil legado sem origin_branch e sem vínculo: nenhum primeiro
        vínculo é permitido — não se adquire ownership arbitrariamente."""
        import dataclasses

        service, repo = _service()
        created = service.create_profile(
            _manager(), branch=BRANCH, **pilot_profile_payload()
        )
        profile_id = UUID(created["id"])
        repo.profiles[profile_id] = dataclasses.replace(
            repo.profiles[profile_id], origin_branch=None
        )
        with pytest.raises(PermissionError, match="reivindicado"):
            service.set_binding(
                _dual_manager(),
                branch="01",
                work_center="CT-01X",
                profile_id=profile_id,
            )

    def test_write_failure_leaves_no_partial_state(self) -> None:
        service, repo = _service()
        repo.fail_writes = True
        with pytest.raises(RuntimeError):
            service.create_profile(
                _manager(), branch=BRANCH, **pilot_profile_payload()
            )
        assert repo.profiles == {}
        assert repo.revisions == []

    def test_profiles_do_not_touch_the_queue(self) -> None:
        """O serviço admin não recebe nem conhece o repositório de snapshots —
        criar/editar/vincular perfil não pode alterar WORKING/PUBLISHED por
        construção (a fila não está na superfície injetável)."""
        import inspect

        params = inspect.signature(SequencingProfileService.__init__).parameters
        assert set(params) == {"self", "repository", "branch_access"}


# --- HTTP -------------------------------------------------------------------


class TestSequencingRoutes:
    def test_full_http_roundtrip(self) -> None:
        service, _ = _service()
        client = _client(service, _manager())

        created = client.post(
            "/machine-load/sequencing-profiles?branch=02",
            json=pilot_profile_payload(),
        )
        assert created.status_code == 200
        profile = created.json()["data"]
        assert profile["status"] == "draft"
        assert profile["revision"] == 1

        listed = client.get("/machine-load/sequencing-profiles?branch=02")
        assert listed.status_code == 200
        assert listed.json()["data"]["total"] == 1

        fetched = client.get(
            f"/machine-load/sequencing-profiles/{profile['id']}?branch=02"
        )
        assert fetched.status_code == 200

        updated = client.put(
            f"/machine-load/sequencing-profiles/{profile['id']}?branch=02",
            json={
                **pilot_profile_payload(),
                "name": "Corte e Decape - Entrega e Cabo v2",
                "status": "active",
                "expected_revision": 1,
            },
        )
        assert updated.status_code == 200
        assert updated.json()["data"]["revision"] == 2

        bound = client.put(
            "/machine-load/sequencing-bindings?branch=02&workCenter=CT-02B",
            json={"profile_id": profile["id"]},
        )
        assert bound.status_code == 200
        assert bound.json()["data"]["profile_id"] == profile["id"]

        binding = client.get(
            "/machine-load/sequencing-bindings?branch=02&workCenter=CT-02B"
        )
        assert binding.json()["data"]["items"][0]["profile_id"] == profile["id"]

    def test_http_conflict_on_stale_revision(self) -> None:
        service, _ = _service()
        client = _client(service, _manager())
        profile = client.post(
            "/machine-load/sequencing-profiles?branch=02",
            json=pilot_profile_payload(),
        ).json()["data"]
        client.put(
            f"/machine-load/sequencing-profiles/{profile['id']}?branch=02",
            json={
                **pilot_profile_payload(),
                "status": "draft",
                "expected_revision": 1,
            },
        )
        stale = client.put(
            f"/machine-load/sequencing-profiles/{profile['id']}?branch=02",
            json={
                **pilot_profile_payload(),
                "status": "draft",
                "expected_revision": 1,
            },
        )
        assert stale.status_code == 409

    def test_http_forbidden_for_view_only_user(self) -> None:
        service, _ = _service()
        client = _client(service, _viewer())

        # Leitura permitida…
        assert client.get("/machine-load/sequencing-profiles?branch=02").status_code == 200
        # …escrita negada.
        assert (
            client.post(
                "/machine-load/sequencing-profiles?branch=02",
                json=pilot_profile_payload(),
            ).status_code
            == 403
        )
        assert (
            client.put(
                "/machine-load/sequencing-bindings?branch=02&workCenter=CT-02B",
                json={"profile_id": str(uuid4())},
            ).status_code
            == 403
        )

    def test_http_branch_scope_enforced(self) -> None:
        service, _ = _service()
        client = _client(service, _branch01_user())
        response = client.post(
            "/machine-load/sequencing-profiles?branch=02",
            json=pilot_profile_payload(),
        )
        assert response.status_code == 403

    def test_http_cross_branch_update_forbidden(self) -> None:
        service, _ = _service()
        owner = _client(service, _manager())
        profile = owner.post(
            "/machine-load/sequencing-profiles?branch=02",
            json=pilot_profile_payload(),
        ).json()["data"]
        owner.put(
            "/machine-load/sequencing-bindings?branch=02&workCenter=CT-02B",
            json={"profile_id": profile["id"]},
        )
        other = _client(service, _branch01_user())
        response = other.put(
            f"/machine-load/sequencing-profiles/{profile['id']}?branch=01",
            json={
                **pilot_profile_payload(),
                "status": "draft",
                "expected_revision": 1,
            },
        )
        assert response.status_code == 403

    def test_http_cross_branch_bind_forbidden(self) -> None:
        service, _ = _service()
        owner = _client(service, _manager())
        profile = owner.post(
            "/machine-load/sequencing-profiles?branch=02",
            json=pilot_profile_payload(),
        ).json()["data"]
        owner.put(
            "/machine-load/sequencing-bindings?branch=02&workCenter=CT-02B",
            json={"profile_id": profile["id"]},
        )
        other = _client(service, _branch01_user())
        response = other.put(
            "/machine-load/sequencing-bindings?branch=01&workCenter=CT-01X",
            json={"profile_id": profile["id"]},
        )
        assert response.status_code == 403

    def test_http_unauthenticated_is_forbidden(self) -> None:
        service, _ = _service()
        client = _client(service, None)
        response = client.get("/machine-load/sequencing-profiles?branch=02")
        assert response.status_code == 403

    def test_http_invalid_branch_is_422(self) -> None:
        service, _ = _service()
        client = _client(service, _manager())
        response = client.get("/machine-load/sequencing-profiles?branch=99")
        assert response.status_code == 422

    def test_http_invalid_criteria_is_422(self) -> None:
        service, _ = _service()
        client = _client(service, _manager())
        response = client.post(
            "/machine-load/sequencing-profiles?branch=02",
            json={
                "name": "Inválido",
                "criteria": [{"type": "tool_group"}, {"type": "pa_due_date"}],
            },
        )
        assert response.status_code == 422

    def test_http_missing_profile_is_404(self) -> None:
        service, _ = _service()
        client = _client(service, _manager())
        response = client.get(
            f"/machine-load/sequencing-profiles/{uuid4()}?branch=02"
        )
        assert response.status_code == 404
        response = client.put(
            "/machine-load/sequencing-bindings?branch=02&workCenter=CT-02B",
            json={"profile_id": str(uuid4())},
        )
        assert response.status_code == 404


# --- integração Postgres real (migration V018 + repo) ------------------------

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestSequencingProfilePostgres:
    @pytest.fixture()
    def repo(self):
        from production_control_app.infrastructure.persistence.postgres_sequencing_profile_repository import (  # noqa: E501
            PostgresSequencingProfileRepository,
        )
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        tag = "ZZ-TEST-SEQ"

        def cleanup() -> None:
            # Filhos primeiro — o RESTRICT do schema impede apagar perfil que
            # ainda tem revisão ou vínculo (proteção intencional do histórico).
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.sequencing_profile_binding_events "
                        "WHERE work_center LIKE %s",
                        (f"{tag}%",),
                    )
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.sequencing_profile_bindings "
                        "WHERE work_center LIKE %s",
                        (f"{tag}%",),
                    )
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.sequencing_profile_revisions "
                        "WHERE profile_id IN (SELECT id FROM "
                        f"{PC_SCHEMA_NAME}.sequencing_profiles WHERE name LIKE %s)",
                        (f"{tag}%",),
                    )
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.sequencing_profiles "
                        "WHERE name LIKE %s",
                        (f"{tag}%",),
                    )
                conn.commit()

        cleanup()
        yield PostgresSequencingProfileRepository(), tag
        cleanup()

    def test_real_db_roundtrip_optimistic_revision_and_audit(self, repo) -> None:
        repo, tag = repo
        from production_control_app.domain.sequencing_profile import (
            validate_criteria,
        )

        criteria = validate_criteria(pilot_profile_payload()["criteria"])
        created = repo.create_profile(
            name=f"{tag} Corte e Decape",
            description="fixture",
            status="draft",
            criteria=criteria,
            origin_branch="02",
            actor="pcp.test",
        )
        assert created.revision == 1

        stale = repo.update_profile(
            profile_id=created.id,
            expected_revision=99,
            managed_branches=frozenset({"02"}),
            name="x",
            description=None,
            status="draft",
            criteria=criteria,
            actor="pcp.test",
        )
        assert stale is None  # revisão divergente — nada escrito

        updated = repo.update_profile(
            profile_id=created.id,
            expected_revision=1,
            managed_branches=frozenset({"02"}),
            name=f"{tag} v2",
            description=None,
            status="active",
            criteria=criteria,
            actor="pcp.test",
        )
        assert updated and updated.revision == 2

        binding = repo.set_binding(
            branch="02",
            work_center=f"{tag}-CT",
            profile_id=created.id,
            managed_branches=frozenset({"02"}),
            actor="pcp.test",
        )
        assert binding and binding.profile_id == created.id
        fetched = repo.get_binding(branch="02", work_center=f"{tag}-CT")
        assert fetched and fetched.profile_id == created.id

        # Auditoria real: 2 revisões + 1 evento de vínculo.
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) AS n FROM {PC_SCHEMA_NAME}.sequencing_profile_revisions "
                    "WHERE profile_id = %s",
                    (created.id,),
                )
                assert cur.fetchone()["n"] == 2
                cur.execute(
                    f"SELECT COUNT(*) AS n FROM {PC_SCHEMA_NAME}.sequencing_profile_binding_events "
                    "WHERE work_center = %s AND action = 'bound'",
                    (f"{tag}-CT",),
                )
                assert cur.fetchone()["n"] == 1

    def test_real_db_concurrent_first_bind_is_controlled(self, repo) -> None:
        """Corrida de INSERT: dois vínculos simultâneos no mesmo CT.

        O SELECT FOR UPDATE não trava linha inexistente — um dos lados
        recebe UniqueViolation e o retry controlado resolve como rebind.
        Nenhum 500/UniqueViolation pode vazar para o chamador.
        """
        repo, tag = repo
        import threading
        from production_control_app.domain.sequencing_profile import (
            validate_criteria,
        )

        criteria = validate_criteria(pilot_profile_payload()["criteria"])
        ids = []
        for i in (1, 2):
            created = repo.create_profile(
                name=f"{tag} Race {i}",
                description=None,
                status="draft",
                criteria=criteria,
                origin_branch="02",
                actor="pcp.test",
            )
            ids.append(created.id)

        barrier = threading.Barrier(3)
        results: list = []
        errors: list = []

        def bind(profile_id):
            barrier.wait()
            try:
                results.append(
                    repo.set_binding(
                        branch="02",
                        work_center=f"{tag}-RACE",
                        profile_id=profile_id,
                        managed_branches=frozenset({"02"}),
                        actor="pcp.test",
                    )
                )
            except Exception as exc:  # noqa: BLE001 — assert abaixo
                errors.append(exc)

        threads = [threading.Thread(target=bind, args=(pid,)) for pid in ids]
        for t in threads:
            t.start()
        barrier.wait()  # largada simultânea
        for t in threads:
            t.join(timeout=30)

        assert errors == []
        assert len(results) == 2
        final = repo.get_binding(branch="02", work_center=f"{tag}-RACE")
        assert final is not None and final.profile_id in ids

    def test_real_db_update_vs_bind_race_is_serializable(self, repo) -> None:
        """Edição e vínculo concorrentes na mesma trava do perfil.

        Se o bind na filial 01 comitar antes, o update (que só administra
        a filial 02) DEVE ser negado; se o update vencer a trava, o bind
        ocorre depois — ambas as ordens são linearizáveis, nunca um write
        autorizado por vínculo fantasma nem erro 500.
        """
        repo, tag = repo
        import threading
        from production_control_app.domain.sequencing_profile import (
            validate_criteria,
        )

        criteria = validate_criteria(pilot_profile_payload()["criteria"])
        created = repo.create_profile(
            name=f"{tag} UpdateRace",
            description=None,
            status="draft",
            criteria=criteria,
            origin_branch="02",
            actor="pcp.test",
        )
        barrier = threading.Barrier(3)
        errors: list = []
        updated: list = []

        def edit():
            barrier.wait()
            try:
                result = repo.update_profile(
                    profile_id=created.id,
                    expected_revision=1,
                    managed_branches=frozenset({"02"}),
                    name=f"{tag} renamed",
                    description=None,
                    status="draft",
                    criteria=criteria,
                    actor="pcp.test",
                )
                updated.append(result)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        def bind():
            barrier.wait()
            try:
                repo.set_binding(
                    branch="01",
                    work_center=f"{tag}-URACE",
                    profile_id=created.id,
                    managed_branches=frozenset({"01", "02"}),
                    actor="pcp.test",
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        t1, t2 = threading.Thread(target=edit), threading.Thread(target=bind)
        t1.start(); t2.start()
        barrier.wait()
        t1.join(timeout=30); t2.join(timeout=30)

        # Sem exceção inesperada: ou o update venceu (rev 2) ou foi negado
        # pelo vínculo que comitou antes (PermissionError — não 500).
        unexpected = [e for e in errors if not isinstance(e, PermissionError)]
        assert unexpected == []
        assert len(updated) + len(errors) == 1
        final_profile = repo.get_profile(profile_id=created.id)
        if updated:
            assert final_profile.revision == 2
