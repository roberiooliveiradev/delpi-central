"""Regras de Sequenciamento — E3: motor consumindo perfis por CT no Otimizar.

Cobre: CT sem perfil mantém comportamento legado; CT com perfil aplica
critérios próprios; precedência material/ferramenta; política flag para
missing/ambiguous; aborto controlado em incomplete/source_unavailable;
proteção de runs, drift de fila/perfis/vínculos; endpoint legado imune.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

import pytest

from production_control_app.application.services.machine_load_service import (
    MachineLoadService,
)
from production_control_app.domain.errors import MachineLoadSequenceConflict
from production_control_app.domain.sequencing_profile import (
    SequencingProfile,
    SequencingProfileBinding,
    validate_criteria,
)
from production_control_app.domain.services.branch_access_service import (
    BranchAccessService,
)
from production_control_app.domain.services.machine_load_optimization import (
    MachineLoadCenterCriteria,
    MachineLoadOptimizationCriteria,
    optimize_machine_load_queue,
)
from tests.test_machine_load import (
    FULL_PERMS,
    FakeGateway,
    FakePublicationRepo,
    FakeSnapshotRepo,
    _user,
)
from tests.test_machine_load_publication import _op, _queue_payload

_BRANCH = "01"
_CENTER = "CT-02B"
_OTHER_CENTER = "CT-01A"


def _profile(
    criteria: list[dict[str, Any]],
    *,
    name: str = "Perfil CT-02B",
    status: str = "active",
    revision: int = 1,
    origin_branch: str | None = _BRANCH,
) -> SequencingProfile:
    return SequencingProfile(
        id=uuid.uuid4(),
        name=name,
        description=None,
        status=status,
        revision=revision,
        criteria=validate_criteria(criteria),
        origin_branch=origin_branch,
    )


_MATERIAL_CRITERIA = [
    {"type": "pa_due_date"},
    {
        "type": "material_code",
        "params": {
            "material_type": "MP",
            "eligible_product_groups": ["1007"],
            "identity_source": "operation_then_order",
            "ignore_zeroed_allocations": True,
            "on_missing": "flag",
            "on_ambiguous": "flag",
        },
    },
]


class FakeProfileRepo:
    """Catálogo em memória: perfis por id + vínculos (filial, CT)."""

    def __init__(
        self,
        profiles: list[SequencingProfile] | None = None,
        bindings: list[SequencingProfileBinding] | None = None,
    ) -> None:
        self.profiles = {p.id: p for p in profiles or []}
        self.bindings = list(bindings or [])

    def list_bindings(self, *, branch: str, work_center: str | None = None):
        return [
            b
            for b in self.bindings
            if b.branch == branch
            and (work_center is None or b.work_center == work_center)
        ]

    def get_profile(self, *, profile_id: uuid.UUID):
        return self.profiles.get(profile_id)

    def list_bound_branches(self, *, profile_id: uuid.UUID) -> list[str]:
        return [b.branch for b in self.bindings if b.profile_id == profile_id]


class DriftingProfileRepo(FakeProfileRepo):
    """Na segunda leitura do mesmo perfil devolve revisão nova (drift)."""

    def __init__(self, *args: Any, drifted: SequencingProfile, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._drifted = drifted
        self._reads = 0

    def get_profile(self, *, profile_id: uuid.UUID):
        self._reads += 1
        if self._reads == 1:
            return self.profiles.get(profile_id)
        return self._drifted


class FakeMaterialResolver:
    """Resolvedor E2 em memória: items por CT; falta de chave = source_unavailable
    quando marcado, senão lista vazia."""

    def __init__(self, items_by_center: dict[str, list[dict[str, Any]]]):
        self._items = items_by_center
        self.calls: list[dict[str, Any]] = []

    def resolve_materials(
        self,
        *,
        branch: str,
        work_center: str,
        operations: Any,
        criteria: Any,
    ) -> dict[str, Any]:
        self.calls.append({"branch": branch, "work_center": work_center,
                           "operations": list(operations)})
        return {"items": list(self._items.get(work_center, []))}


def _resolved(op: dict[str, Any], code: str) -> dict[str, Any]:
    return {
        "production_order": op["production_order"],
        "operation_code": op["operation_code"],
        "status": "resolved",
        "product_code": code,
    }


def _flagged(op: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "production_order": op["production_order"],
        "operation_code": op["operation_code"],
        "status": status,
        "product_code": None,
    }


def _binding(center: str, profile: SequencingProfile, branch: str = _BRANCH):
    return SequencingProfileBinding(
        branch=branch, work_center=center, profile_id=profile.id,
        assigned_by="admin",
    )


def _service(
    snapshots: FakeSnapshotRepo,
    *,
    profiles: Any = None,
    resolver: Any = None,
) -> MachineLoadService:
    return MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        open_run_items=lambda **kwargs: [],
        sequencing_profiles=profiles,
        material_resolver=resolver,
    )


def _queued(operations: list[dict[str, Any]]) -> FakeSnapshotRepo:
    snapshots = FakeSnapshotRepo()
    snapshots.upsert(
        branch=_BRANCH,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        payload=_queue_payload(operations),
        refreshed_by="planner-1",
    )
    return snapshots


def _queue_orders(snapshots: FakeSnapshotRepo, center: str) -> list[str]:
    payload = snapshots.rows[_BRANCH]["payload_json"]
    return [
        item["production_order"]
        for item in payload["operations"]
        if item["work_center"] == center
    ]


# ---------------------------------------------------------------------------
# Motor puro
# ---------------------------------------------------------------------------


def test_engine_groups_by_material_within_same_due_date() -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111003", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111004", "01", work_center=_CENTER, due_date="2026-10-04"),
    ]
    codes = {
        (_CENTER, "111111001", "1"): "CABO-B",
        (_CENTER, "111111002", "1"): "CABO-A",
        (_CENTER, "111111003", "1"): "CABO-B",
    }
    result = optimize_machine_load_queue(
        ops,
        criteria=MachineLoadOptimizationCriteria(),
        center_criteria={_CENTER: MachineLoadCenterCriteria(("material_code",))},
        material_codes=codes,
    )
    orders = [op["production_order"] for op in result.operations]
    # Data soberana primeiro; dentro do dia 05, CABO-B (1ª ocorrência) junto,
    # depois CABO-A; op sem código não forma grupo e vai por último na data.
    assert orders == [
        "111111004",
        "111111001",
        "111111003",
        "111111002",
    ]


def test_engine_respects_profile_criteria_order_tool_then_material() -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER,
            due_date="2026-10-05", tool="MA-02"),
        _op("111111002", "01", work_center=_CENTER,
            due_date="2026-10-05", tool="MA-01"),
        _op("111111003", "01", work_center=_CENTER,
            due_date="2026-10-05", tool="MA-02"),
    ]
    codes = {
        (_CENTER, "111111001", "1"): "CABO-A",
        (_CENTER, "111111002", "1"): "CABO-B",
        (_CENTER, "111111003", "1"): "CABO-A",
    }
    result = optimize_machine_load_queue(
        ops,
        criteria=MachineLoadOptimizationCriteria(),
        center_criteria={
            _CENTER: MachineLoadCenterCriteria(("tool_group", "material_code"))
        },
        material_codes=codes,
    )
    orders = [op["production_order"] for op in result.operations]
    # Ferramenta manda primeiro: MA-02 (1ª ocorrência) → dentro dela CABO-A;
    # depois MA-01. Mesmo cabo em ferramentas diferentes não se junta.
    assert orders == ["111111001", "111111003", "111111002"]


def test_engine_center_without_plan_uses_general_criteria() -> None:
    ops = [
        _op("111111001", "01", work_center=_OTHER_CENTER,
            due_date="2026-10-05", tool="MA-02"),
        _op("111111002", "01", work_center=_OTHER_CENTER,
            due_date="2026-10-05", tool="MA-01"),
        _op("111111003", "01", work_center=_OTHER_CENTER,
            due_date="2026-10-05", tool="MA-02"),
    ]
    result = optimize_machine_load_queue(
        ops,
        criteria=MachineLoadOptimizationCriteria(group_by_tool=True),
        center_criteria={_CENTER: MachineLoadCenterCriteria(("material_code",))},
        material_codes={},
    )
    orders = [op["production_order"] for op in result.operations]
    # CT fora do plano segue o critério geral: MA-02 junta (1ª ocorrência),
    # MA-01 depois.
    assert orders == ["111111001", "111111003", "111111002"]


def test_engine_no_due_date_stays_last_without_regrouping() -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date=None, pa_due_date=None),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111003", "01", work_center=_CENTER, due_date=None, pa_due_date=None),
    ]
    codes = {
        (_CENTER, "111111001", "1"): "CABO-A",
        (_CENTER, "111111002", "1"): "CABO-B",
        (_CENTER, "111111003", "1"): "CABO-A",
    }
    result = optimize_machine_load_queue(
        ops,
        criteria=MachineLoadOptimizationCriteria(),
        center_criteria={_CENTER: MachineLoadCenterCriteria(("material_code",))},
        material_codes=codes,
    )
    orders = [op["production_order"] for op in result.operations]
    # Sem data → fim da fila, na ordem atual, sem agrupar por cabo.
    assert orders == ["111111002", "111111001", "111111003"]


# ---------------------------------------------------------------------------
# Serviço — perfis na otimização
# ---------------------------------------------------------------------------


def test_center_without_profile_keeps_legacy_behavior() -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER,
            due_date="2026-10-08", tool="MA-02"),
        _op("111111002", "01", work_center=_CENTER,
            due_date="2026-10-07", tool="MA-01"),
    ]
    snapshots = _queued(ops)
    profiles = FakeProfileRepo()
    resolver = FakeMaterialResolver({})
    service = _service(snapshots, profiles=profiles, resolver=resolver)

    result = service.optimize_sequence(
        _user(*FULL_PERMS),
        branch=_BRANCH,
        criteria=MachineLoadOptimizationCriteria(group_by_tool=True),
    )
    assert resolver.calls == []
    assert result["optimization"]["profiles"] == {}
    assert _queue_orders(snapshots, _CENTER) == ["111111002", "111111001"]


def test_center_with_active_profile_applies_own_criteria() -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111003", "01", work_center=_CENTER, due_date="2026-10-05"),
    ]
    profile = _profile(_MATERIAL_CRITERIA)
    profiles = FakeProfileRepo(
        profiles=[profile], bindings=[_binding(_CENTER, profile)]
    )
    resolver = FakeMaterialResolver(
        {
            _CENTER: [
                _resolved(ops[0], "10070371"),
                _resolved(ops[1], "10079999"),
                _resolved(ops[2], "10070371"),
            ]
        }
    )
    snapshots = _queued(ops)
    service = _service(snapshots, profiles=profiles, resolver=resolver)

    result = service.optimize_sequence(
        _user(*FULL_PERMS),
        branch=_BRANCH,
        criteria=MachineLoadOptimizationCriteria(group_by_tool=True),
    )
    assert _queue_orders(snapshots, _CENTER) == [
        "111111001",
        "111111003",
        "111111002",
    ]
    assert resolver.calls[0]["work_center"] == _CENTER
    reported = result["optimization"]["profiles"][_CENTER]
    assert reported["profile_id"] == str(profile.id)
    assert reported["criteria"] == ["pa_due_date", "material_code"]
    assert reported["flagged_count"] == 0


def test_two_centers_with_different_rules_same_optimize() -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER,
            due_date="2026-10-05", tool="MA-01"),
        _op("111111002", "01", work_center=_CENTER,
            due_date="2026-10-05", tool="MA-02"),
        _op("211111001", "01", work_center=_OTHER_CENTER,
            due_date="2026-10-05", tool="MA-02"),
        _op("211111002", "01", work_center=_OTHER_CENTER,
            due_date="2026-10-05", tool="MA-01"),
        _op("211111003", "01", work_center=_OTHER_CENTER,
            due_date="2026-10-05", tool="MA-02"),
    ]
    profile = _profile(_MATERIAL_CRITERIA)
    profiles = FakeProfileRepo(
        profiles=[profile], bindings=[_binding(_CENTER, profile)]
    )
    resolver = FakeMaterialResolver(
        {
            _CENTER: [
                _resolved(ops[0], "10070371"),
                _resolved(ops[1], "10070371"),
            ]
        }
    )
    snapshots = _queued(ops)
    service = _service(snapshots, profiles=profiles, resolver=resolver)

    service.optimize_sequence(
        _user(*FULL_PERMS),
        branch=_BRANCH,
        criteria=MachineLoadOptimizationCriteria(group_by_tool=True),
    )
    # CT-02B pelo perfil (material): mesmo cabo junto — ordem já está ok.
    assert _queue_orders(snapshots, _CENTER) == ["111111001", "111111002"]
    # CT-01A pelo critério geral (tool): grupo MA-02 (1ª ocorrência) junta.
    assert _queue_orders(snapshots, _OTHER_CENTER) == [
        "211111001",
        "211111003",
        "211111002",
    ]


def test_binding_to_draft_profile_aborts_without_mutation() -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-08"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-07"),
    ]
    profile = _profile(_MATERIAL_CRITERIA, status="draft")
    profiles = FakeProfileRepo(
        profiles=[profile], bindings=[_binding(_CENTER, profile)]
    )
    snapshots = _queued(ops)
    service = _service(
        snapshots, profiles=profiles, resolver=FakeMaterialResolver({})
    )
    with pytest.raises(ValueError, match="não está ativo"):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert snapshots.payload_updates == 0


def test_binding_to_missing_profile_aborts_without_mutation() -> None:
    ops = [_op("111111001", "01", work_center=_CENTER, due_date="2026-10-07")]
    ghost = _profile(_MATERIAL_CRITERIA)
    profiles = FakeProfileRepo(
        profiles=[], bindings=[_binding(_CENTER, ghost)]
    )
    snapshots = _queued(ops)
    service = _service(
        snapshots, profiles=profiles, resolver=FakeMaterialResolver({})
    )
    with pytest.raises(ValueError, match="inexistente"):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert snapshots.payload_updates == 0


def test_shared_profile_across_branches_is_blocked() -> None:
    """Perfil vinculado em outra filial não comanda mutação aqui."""
    ops = [_op("111111001", "01", work_center=_CENTER, due_date="2026-10-07")]
    profile = _profile(_MATERIAL_CRITERIA)
    profiles = FakeProfileRepo(
        profiles=[profile],
        bindings=[
            _binding(_CENTER, profile),
            _binding(_CENTER, profile, branch="02"),
        ],
    )
    snapshots = _queued(ops)
    service = _service(
        snapshots, profiles=profiles, resolver=FakeMaterialResolver({})
    )
    with pytest.raises(ValueError, match="compartilhado entre filiais"):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert snapshots.payload_updates == 0


def test_profile_from_other_branch_origin_is_blocked() -> None:
    ops = [_op("111111001", "01", work_center=_CENTER, due_date="2026-10-07")]
    profile = _profile(_MATERIAL_CRITERIA, origin_branch="02")
    profiles = FakeProfileRepo(
        profiles=[profile], bindings=[_binding(_CENTER, profile)]
    )
    snapshots = _queued(ops)
    service = _service(
        snapshots, profiles=profiles, resolver=FakeMaterialResolver({})
    )
    with pytest.raises(ValueError, match="compartilhado entre filiais"):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert snapshots.payload_updates == 0


@pytest.mark.parametrize("status", ["incomplete", "source_unavailable"])
def test_incomplete_resolution_aborts_entire_optimization(status: str) -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-08"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-07"),
    ]
    profile = _profile(_MATERIAL_CRITERIA)
    profiles = FakeProfileRepo(
        profiles=[profile], bindings=[_binding(_CENTER, profile)]
    )
    resolver = FakeMaterialResolver(
        {_CENTER: [_flagged(ops[0], status), _resolved(ops[1], "10070371")]}
    )
    snapshots = _queued(ops)
    service = _service(snapshots, profiles=profiles, resolver=resolver)
    with pytest.raises(ValueError, match="indisponíveis ou incompletos"):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert snapshots.payload_updates == 0


def test_missing_and_ambiguous_follow_flag_policy() -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111003", "01", work_center=_CENTER, due_date="2026-10-05"),
    ]
    profile = _profile(_MATERIAL_CRITERIA)
    profiles = FakeProfileRepo(
        profiles=[profile], bindings=[_binding(_CENTER, profile)]
    )
    resolver = FakeMaterialResolver(
        {
            _CENTER: [
                _flagged(ops[0], "missing"),
                _resolved(ops[1], "10070371"),
                _flagged(ops[2], "ambiguous"),
            ]
        }
    )
    snapshots = _queued(ops)
    service = _service(snapshots, profiles=profiles, resolver=resolver)
    result = service.optimize_sequence(
        _user(*FULL_PERMS),
        branch=_BRANCH,
        criteria=MachineLoadOptimizationCriteria(),
    )
    # Sem código resolvido não forma grupo: resolved primeiro (único grupo),
    # flagged preservam a ordem relativa depois.
    assert _queue_orders(snapshots, _CENTER) == [
        "111111002",
        "111111001",
        "111111003",
    ]
    assert result["optimization"]["profiles"][_CENTER]["flagged_count"] == 2


def test_queue_drift_inside_lock_is_conflict() -> None:
    """A fila mudou entre a leitura e o lock → 409, nunca grava com base velha."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-08"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-07"),
    ]
    profile = _profile(_MATERIAL_CRITERIA)
    profiles = FakeProfileRepo(
        profiles=[profile], bindings=[_binding(_CENTER, profile)]
    )
    resolver = FakeMaterialResolver(
        {_CENTER: [_resolved(ops[0], "A"), _resolved(ops[1], "A")]}
    )
    snapshots = _queued(ops)
    service = _service(snapshots, profiles=profiles, resolver=resolver)

    original_get_for_update = snapshots.get_for_update

    def drifted_get_for_update(*, branch: str, conn: Any = None):
        row = original_get_for_update(branch=branch, conn=conn)
        row["payload_json"]["operations"] = [
            item
            for item in row["payload_json"]["operations"]
            if item["production_order"] != "111111002"
        ]
        return row

    snapshots.get_for_update = drifted_get_for_update
    with pytest.raises(MachineLoadSequenceConflict):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert snapshots.payload_updates == 0


def test_profile_revision_drift_inside_lock_is_conflict() -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-08"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-07"),
    ]
    profile = _profile(_MATERIAL_CRITERIA)
    drifted = SequencingProfile(
        id=profile.id, name=profile.name, description=None,
        status="active", revision=profile.revision + 1,
        criteria=profile.criteria, origin_branch=_BRANCH,
    )
    profiles = DriftingProfileRepo(
        profiles=[profile],
        bindings=[_binding(_CENTER, profile)],
        drifted=drifted,
    )
    resolver = FakeMaterialResolver(
        {_CENTER: [_resolved(ops[0], "A"), _resolved(ops[1], "A")]}
    )
    snapshots = _queued(ops)
    service = _service(snapshots, profiles=profiles, resolver=resolver)
    with pytest.raises(MachineLoadSequenceConflict):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert snapshots.payload_updates == 0


def test_binding_drift_inside_lock_is_conflict() -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-08"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-07"),
    ]
    profile = _profile(_MATERIAL_CRITERIA)
    profiles = FakeProfileRepo(
        profiles=[profile], bindings=[_binding(_CENTER, profile)]
    )
    resolver = FakeMaterialResolver(
        {_CENTER: [_resolved(ops[0], "A"), _resolved(ops[1], "A")]}
    )
    snapshots = _queued(ops)
    service = _service(snapshots, profiles=profiles, resolver=resolver)

    original_list = profiles.list_bindings
    reads = {"n": 0}

    def drifting_bindings(*, branch: str, work_center=None):
        reads["n"] += 1
        if reads["n"] == 1:
            return original_list(branch=branch, work_center=work_center)
        return []  # vínculo sumiu dentro do lock

    profiles.list_bindings = drifting_bindings
    with pytest.raises(MachineLoadSequenceConflict):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert snapshots.payload_updates == 0


def test_legacy_optimize_delivery_never_uses_profiles() -> None:
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-08"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-07"),
    ]
    profile = _profile(_MATERIAL_CRITERIA)
    profiles = FakeProfileRepo(
        profiles=[profile], bindings=[_binding(_CENTER, profile)]
    )
    resolver = FakeMaterialResolver({})
    snapshots = _queued(ops)
    service = _service(snapshots, profiles=profiles, resolver=resolver)

    service.optimize_delivery_sequence(_user(*FULL_PERMS), branch=_BRANCH)
    assert resolver.calls == []
    assert _queue_orders(snapshots, _CENTER) == ["111111002", "111111001"]


def test_live_optimization_updates_published_payload() -> None:
    """LIVE: WORKING e PUBLISHED recebem o mesmo payload na mesma mutação."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-08"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-07"),
    ]
    profile = _profile(_MATERIAL_CRITERIA)
    profiles = FakeProfileRepo(
        profiles=[profile], bindings=[_binding(_CENTER, profile)]
    )
    resolver = FakeMaterialResolver(
        {_CENTER: [_resolved(ops[0], "A"), _resolved(ops[1], "A")]}
    )
    snapshots = _queued(ops)
    snapshots.publish(_BRANCH)
    service = _service(snapshots, profiles=profiles, resolver=resolver)

    service.optimize_sequence(
        _user(*FULL_PERMS),
        branch=_BRANCH,
        criteria=MachineLoadOptimizationCriteria(),
    )
    published_ops = snapshots.published[_BRANCH]["payload_json"]["operations"]
    assert [op["production_order"] for op in published_ops] == [
        "111111002",
        "111111001",
    ]


def test_noop_with_profile_does_not_write() -> None:
    """Fila já ordenada pelas regras do perfil → sem write, sem broadcast."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-04"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-05"),
    ]
    profile = _profile(_MATERIAL_CRITERIA)
    profiles = FakeProfileRepo(
        profiles=[profile], bindings=[_binding(_CENTER, profile)]
    )
    resolver = FakeMaterialResolver(
        {_CENTER: [_resolved(ops[0], "A"), _resolved(ops[1], "A")]}
    )
    snapshots = _queued(ops)
    service = _service(snapshots, profiles=profiles, resolver=resolver)

    result = service.optimize_sequence(
        _user(*FULL_PERMS),
        branch=_BRANCH,
        criteria=MachineLoadOptimizationCriteria(),
    )
    assert snapshots.payload_updates == 0
    assert result["optimization"]["work_centers"] == []


# ---------------------------------------------------------------------------
# Hotfix E3 — versão da fila, runs lidos no lock e hierarquia aninhada
# ---------------------------------------------------------------------------


class _VersionDriftingSnapshots(FakeSnapshotRepo):
    """Simula qualquer escrita concorrente entre get e get_for_update."""

    def get_for_update(self, *, branch, conn=None):
        row = dict(super().get_for_update(branch=branch, conn=conn))
        row["row_version"] = str(uuid.uuid4())
        return row


def _opt_criteria(*grouping: str) -> MachineLoadCenterCriteria:
    return MachineLoadCenterCriteria(grouping)


def test_previous_manual_reorder_is_replaced_by_optimization() -> None:
    """Ajuste manual ANTERIOR (gravado antes do Otimizar) pode ser substituído."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-04"),
        _op("111111003", "01", work_center=_CENTER, due_date="2026-10-06"),
    ]
    snapshots = _queued(ops)
    # Manual anterior: analista gravou uma ordem própria antes de otimizar.
    manual = list(ops)
    manual[0], manual[2] = manual[2], manual[0]
    snapshots.update_payload(branch=_BRANCH, payload=_queue_payload(manual))
    service = _service(snapshots)

    result = service.optimize_sequence(
        _user(*FULL_PERMS),
        branch=_BRANCH,
        criteria=MachineLoadOptimizationCriteria(),
        use_sequencing_profiles=True,
    )
    orders = [op["production_order"] for op in result["operations"]]
    assert orders == ["111111002", "111111001", "111111003"]
    assert _queue_orders(snapshots, _CENTER) == orders


def test_concurrent_write_is_conflict_for_all_centers() -> None:
    """Escrita entre leitura e lock (reordenação, refresh, retirada) = 409,
    sem qualquer gravação — com ou sem perfil ativo."""
    ops = [_op("111111001", "01", work_center=_CENTER, due_date="2026-10-05")]

    drifting = _VersionDriftingSnapshots()
    drifting.upsert(
        branch=_BRANCH, start_date=date(2026, 9, 1), end_date=date(2026, 9, 30),
        payload=_queue_payload(ops), refreshed_by="planner-1",
    )

    # Sem perfil ativo
    service = _service(drifting)
    with pytest.raises(MachineLoadSequenceConflict):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert drifting.payload_updates == 0

    # Com perfil ativo
    profile = _profile([{"type": "pa_due_date"}])
    service = _service(
        drifting,
        profiles=FakeProfileRepo(
            profiles=[profile], bindings=[_binding(_CENTER, profile)]
        ),
        resolver=FakeMaterialResolver({}),
    )
    with pytest.raises(MachineLoadSequenceConflict):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert drifting.payload_updates == 0


def test_run_started_during_material_resolution_keeps_slot() -> None:
    """Run aberto DEPOIS da leitura inicial mas antes da reordenação trava o
    slot — os runs são relidos já dentro da transação."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-04"),
    ]
    snapshots = _queued(ops)
    late_runs: list[dict[str, Any]] = []

    class RunStartingResolver:
        def resolve_materials(self, **kwargs):
            late_runs.append({
                "work_center": _CENTER,
                "production_order": "111111002",
                "operation_code": "01",
                "run_status": "producing",
            })
            return {"items": [_resolved(o, "10070371") for o in kwargs["operations"]]}

    profile = _profile(_MATERIAL_CRITERIA)
    service = MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        open_run_items=lambda **kwargs: list(late_runs),
        sequencing_profiles=FakeProfileRepo(
            profiles=[profile], bindings=[_binding(_CENTER, profile)]
        ),
        material_resolver=RunStartingResolver(),
    )
    result = service.optimize_sequence(
        _user(*FULL_PERMS),
        branch=_BRANCH,
        criteria=MachineLoadOptimizationCriteria(),
    )
    orders = [op["production_order"] for op in result["operations"]]
    assert orders[1] == "111111002"  # slot do run aberto preservado


def test_nested_criteria_rank_within_parent_group() -> None:
    """tool_group → material_code: os cabos são classificados por primeira
    ocorrência DENTRO de cada ferramenta, não na data inteira."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T1"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T2"),
        _op("111111003", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T1"),
        _op("111111004", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T2"),
    ]
    material_codes = {
        (_CENTER, "111111001", "1"): "CB",   # T1/Mb
        (_CENTER, "111111002", "1"): "CA",   # T2/Ma
        (_CENTER, "111111003", "1"): "CA",   # T1/Ma — Mb aparece primeiro em T1
        (_CENTER, "111111004", "1"): "CB",   # T2/Mb — Ma aparece primeiro em T2
    }
    criteria = MachineLoadOptimizationCriteria()
    center_criteria = {_CENTER: _opt_criteria("tool_group", "material_code")}
    result = optimize_machine_load_queue(
        operations=ops,
        criteria=criteria,
        protected_keys=set(),
        center_criteria=center_criteria,
        material_codes=material_codes,
    )
    orders = [op["production_order"] for op in result.operations]
    # T1: Mb(001) veio antes de Ma(003); T2: Ma(002) veio antes de Mb(004)
    assert orders == ["111111001", "111111003", "111111002", "111111004"]


def test_nested_criteria_material_then_tool() -> None:
    """material_code → tool_group: ferramenta ranqueia dentro de cada cabo."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T2"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T1"),
        _op("111111003", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T1"),
        _op("111111004", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T2"),
    ]
    material_codes = {
        (_CENTER, "111111001", "1"): "CA",   # Ca/T2
        (_CENTER, "111111002", "1"): "CB",   # Cb/T1
        (_CENTER, "111111003", "1"): "CA",   # Ca/T1 — T2 antes de T1 em CA
        (_CENTER, "111111004", "1"): "CB",   # Cb/T2 — T1 antes de T2 em CB
    }
    criteria = MachineLoadOptimizationCriteria()
    center_criteria = {_CENTER: _opt_criteria("material_code", "tool_group")}
    result = optimize_machine_load_queue(
        operations=ops,
        criteria=criteria,
        protected_keys=set(),
        center_criteria=center_criteria,
        material_codes=material_codes,
    )
    orders = [op["production_order"] for op in result.operations]
    # CA: T2(001) antes de T1(003); CB: T1(002) antes de T2(004)
    assert orders == ["111111001", "111111003", "111111002", "111111004"]


@pytest.mark.parametrize(
    "mutate_items",
    [
        lambda items: items + [dict(items[0])],          # item duplicado
        lambda items: items[1:],                          # item ausente
        lambda items: items + [{                           # identidade estranha
            "branch": "01",
            "work_center": _CENTER,
            "production_order": "999999999",
            "operation_code": "99",
            "status": "resolved",
            "product_code": "10070371",
        }],
        lambda items: [dict(items[0], work_center="CT-XX")] + items[1:],
        lambda items: [dict(items[0], product_code="")] + items[1:],
    ],
    ids=["duplicate", "missing", "extra", "other_center", "resolved_no_code"],
)
def test_inconsistent_resolution_aborts_without_write(mutate_items) -> None:
    """Resposta do resolvedor fora do pedido nunca chega ao motor nem grava."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-05"),
    ]
    snapshots = _queued(ops)
    base_items = [_resolved(o, "10070371") for o in ops]

    class InconsistentResolver:
        def resolve_materials(self, **kwargs):
            return {"items": mutate_items(list(base_items))}

    profile = _profile(_MATERIAL_CRITERIA)
    service = _service(
        snapshots,
        profiles=FakeProfileRepo(
            profiles=[profile], bindings=[_binding(_CENTER, profile)]
        ),
        resolver=InconsistentResolver(),
    )
    with pytest.raises(ValueError):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert snapshots.payload_updates == 0


def test_binding_created_during_optimization_is_conflict() -> None:
    """Vínculo criado enquanto a otimização era preparada — quando não havia
    perfil ativo na leitura inicial — invalida a decisão de usar os critérios
    gerais: 409 e nenhuma gravação."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-04"),
    ]
    snapshots = _queued(ops)
    profile = _profile([{"type": "pa_due_date"}])

    class LateBindingRepo(FakeProfileRepo):
        """Primeira leitura sem vínculos; a partir da segunda o vínculo existe."""

        def __init__(self) -> None:
            super().__init__(profiles=[profile])
            self._reads = 0

        def list_bindings(self, *, branch, work_center=None):
            self._reads += 1
            if self._reads == 1:
                return []
            return [_binding(_CENTER, profile)]

    service = _service(
        snapshots,
        profiles=LateBindingRepo(),
        resolver=FakeMaterialResolver({}),
    )
    with pytest.raises(MachineLoadSequenceConflict):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert snapshots.payload_updates == 0


def test_binding_on_center_without_operations_does_not_block() -> None:
    """Vínculo em CT sem operações na fila não bloqueia a otimização —
    apenas os CTs participantes entram no drift-check."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05"),
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-04"),
    ]
    snapshots = _queued(ops)
    idle_profile = _profile([{"type": "pa_due_date"}], name="Perfil CT-01A")
    service = _service(
        snapshots,
        profiles=FakeProfileRepo(
            profiles=[idle_profile],
            bindings=[_binding(_OTHER_CENTER, idle_profile)],
        ),
        resolver=FakeMaterialResolver({}),
    )
    result = service.optimize_sequence(
        _user(*FULL_PERMS),
        branch=_BRANCH,
        criteria=MachineLoadOptimizationCriteria(),
    )
    orders = [op["production_order"] for op in result["operations"]]
    assert orders == ["111111002", "111111001"]
    assert result["optimization"]["profiles"] == {}


def test_missing_material_keeps_relative_order_with_tool() -> None:
    """material_code → tool_group: operações missing/ambiguous mantêm a
    ordem relativa — a ferramenta não pode reagrupá-las."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T1"),   # missing
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T9"),   # resolved
        _op("111111003", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T2"),   # missing
    ]
    snapshots = _queued(ops)
    items = [
        _flagged(ops[0], "missing"),
        _resolved(ops[1], "10070371"),
        _flagged(ops[2], "missing"),
    ]
    profile = _profile(
        [
            {"type": "pa_due_date"},
            _MATERIAL_CRITERIA[1],
            {"type": "tool_group"},
        ]
    )
    service = _service(
        snapshots,
        profiles=FakeProfileRepo(
            profiles=[profile], bindings=[_binding(_CENTER, profile)]
        ),
        resolver=FakeMaterialResolver({_CENTER: items}),
    )
    result = service.optimize_sequence(
        _user(*FULL_PERMS),
        branch=_BRANCH,
        criteria=MachineLoadOptimizationCriteria(),
    )
    orders = [op["production_order"] for op in result["operations"]]
    # Resolvido agrupa primeiro; os missing ficam depois NA ORDEM ORIGINAL
    # (001 antes de 003), não pela ferramenta (T1 antes de T2 já coincide).
    assert orders == ["111111002", "111111001", "111111003"]


def test_missing_material_relative_order_inverted_tools() -> None:
    """Mesmo com ferramentas em ordem inversa à fila, missing preserva ordem."""
    ops = [
        _op("111111001", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T2"),   # missing — T2
        _op("111111002", "01", work_center=_CENTER, due_date="2026-10-05",
            tool="T1"),   # missing — T1 viria antes se tool agrupasse
    ]
    snapshots = _queued(ops)
    items = [_flagged(o, "missing") for o in ops]
    profile = _profile(
        [
            {"type": "pa_due_date"},
            _MATERIAL_CRITERIA[1],
            {"type": "tool_group"},
        ]
    )
    service = _service(
        snapshots,
        profiles=FakeProfileRepo(
            profiles=[profile], bindings=[_binding(_CENTER, profile)]
        ),
        resolver=FakeMaterialResolver({_CENTER: items}),
    )
    result = service.optimize_sequence(
        _user(*FULL_PERMS),
        branch=_BRANCH,
        criteria=MachineLoadOptimizationCriteria(),
    )
    orders = [op["production_order"] for op in result["operations"]]
    assert orders == ["111111001", "111111002"]  # relativa, não por tool


def test_missing_row_version_fails_closed() -> None:
    """Sem row_version a proteção de concorrência não é dispensada —
    a otimização falha de forma controlada e sem escrita."""

    class NoVersionSnapshots(FakeSnapshotRepo):
        def get(self, *, branch):
            row = super().get(branch=branch)
            if row is not None:
                row = dict(row)
                row.pop("row_version", None)
            return row

    snapshots = NoVersionSnapshots()
    snapshots.upsert(
        branch=_BRANCH,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        payload=_queue_payload(
            [_op("111111001", "01", work_center=_CENTER, due_date="2026-10-05")]
        ),
        refreshed_by="planner-1",
    )
    service = _service(snapshots)
    with pytest.raises(ValueError, match="Versão da fila"):
        service.optimize_sequence(
            _user(*FULL_PERMS),
            branch=_BRANCH,
            criteria=MachineLoadOptimizationCriteria(),
        )
    assert snapshots.payload_updates == 0
