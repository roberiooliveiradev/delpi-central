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
