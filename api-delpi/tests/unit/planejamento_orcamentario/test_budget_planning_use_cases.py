"""Use cases com repositório fake em memória (sem Postgres)."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any
from uuid import uuid4

import pytest

from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
    BudgetPlanningUseCases,
)
from app.application.services.planejamento_orcamentario.document_storage import (
    BudgetDocumentStorage,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetExerciseAlreadyActiveError,
    BudgetExerciseInvalidDatesError,
    BudgetGuidanceImmutableError,
    BudgetScopeConflictError,
    BudgetUserNotAuthorizedError,
)
from tests.unit.planejamento_orcamentario.fake_po_repository_helpers import (
    default_po_cc_seed,
    get_org_cost_center_from_store,
    list_org_cost_centers_by_code_from_store,
    list_org_cost_centers_from_store,
    upsert_org_cost_center_in_store,
)


class InMemoryRepo:
    def __init__(self) -> None:
        self.exercises: dict[str, dict] = {}
        self.guidance: dict[str, dict] = {}
        self.premises: dict[str, list] = {}
        self.schedule: dict[str, list] = {}
        self.documents: dict[str, dict] = {}
        self.acks: dict[tuple[str, str], dict] = {}
        self.units = {"01": {"code": "01", "name": "SC", "active": True}}
        self.areas = {"PROD": {"code": "PROD", "name": "Produção", "unit_code": "01", "active": True}}
        self.ccs: dict[tuple[str, str], dict] = default_po_cc_seed()
        self.scopes: dict[str, dict] = {}
        self.audits: list[dict] = []

    def list_exercises(self):
        return sorted(self.exercises.values(), key=lambda e: e["year"], reverse=True)

    def get_exercise(self, exercise_id: str):
        return deepcopy(self.exercises.get(exercise_id))

    def get_exercise_by_year(self, year: int):
        for e in self.exercises.values():
            if e["year"] == year:
                return deepcopy(e)
        return None

    def get_active_exercise(self):
        for e in self.exercises.values():
            if e.get("is_active"):
                return deepcopy(e)
        return None

    def create_exercise(self, payload: dict[str, Any]):
        eid = str(uuid4())
        row = {**payload, "id": eid, "created_at": "t", "updated_at": "t"}
        self.exercises[eid] = row
        return deepcopy(row)

    def update_exercise(self, exercise_id: str, fields: dict[str, Any]):
        self.exercises[exercise_id].update(fields)
        return deepcopy(self.exercises[exercise_id])

    def clear_other_active(self, exercise_id: str):
        for eid, e in self.exercises.items():
            if eid != exercise_id:
                e["is_active"] = False

    def get_guidance_draft(self, exercise_id: str):
        for g in self.guidance.values():
            if g["exercise_id"] == exercise_id and g["status"] == "draft":
                return deepcopy(g)
        return None

    def get_guidance(self, guidance_id: str):
        return deepcopy(self.guidance.get(guidance_id))

    def get_current_published_guidance(self, exercise_id: str):
        pubs = [
            g for g in self.guidance.values()
            if g["exercise_id"] == exercise_id and g["status"] == "published"
        ]
        if not pubs:
            return None
        pubs.sort(key=lambda g: g["version_number"], reverse=True)
        return deepcopy(pubs[0])

    def list_published_guidance(self, exercise_id: str):
        return [
            deepcopy(g)
            for g in self.guidance.values()
            if g["exercise_id"] == exercise_id and g["status"] == "published"
        ]

    def create_guidance_draft(self, payload: dict[str, Any]):
        gid = str(uuid4())
        row = {
            **payload,
            "id": gid,
            "status": "draft",
            "version_number": None,
            "published_at": None,
        }
        self.guidance[gid] = row
        self.premises[gid] = []
        self.schedule[gid] = []
        return deepcopy(row)

    def update_guidance_draft(self, guidance_id: str, fields: dict[str, Any]):
        assert self.guidance[guidance_id]["status"] == "draft"
        self.guidance[guidance_id].update(fields)
        return deepcopy(self.guidance[guidance_id])

    def publish_guidance(self, guidance_id: str, *, actor_id: str, actor_name: str | None):
        g = self.guidance[guidance_id]
        assert g["status"] == "draft"
        max_v = max(
            (x["version_number"] or 0 for x in self.guidance.values() if x["exercise_id"] == g["exercise_id"] and x["status"] == "published"),
            default=0,
        )
        g["status"] = "published"
        g["version_number"] = max_v + 1
        g["published_at"] = "2026-08-04T12:00:00+00:00"
        g["published_by_user_id"] = actor_id
        g["published_by_name"] = actor_name
        return deepcopy(g)

    def replace_premises(self, guidance_id: str, premises: list[dict[str, Any]]):
        self.premises[guidance_id] = deepcopy(premises)
        return deepcopy(premises)

    def list_premises(self, guidance_id: str):
        return deepcopy(self.premises.get(guidance_id, []))

    def replace_schedule(self, guidance_id: str, items: list[dict[str, Any]]):
        self.schedule[guidance_id] = deepcopy(items)
        return deepcopy(items)

    def list_schedule(self, guidance_id: str):
        return deepcopy(self.schedule.get(guidance_id, []))

    def create_document(self, payload: dict[str, Any]):
        did = str(uuid4())
        row = {**payload, "id": did, "status": "active"}
        self.documents[did] = row
        return deepcopy(row)

    def get_document(self, document_id: str):
        return deepcopy(self.documents.get(document_id))

    def list_documents(self, *, exercise_id: str, guidance_version_id: str | None = None, active_only: bool = True):
        docs = [d for d in self.documents.values() if d["exercise_id"] == exercise_id]
        if guidance_version_id is not None:
            docs = [d for d in docs if d.get("guidance_version_id") == guidance_version_id]
        if active_only:
            docs = [d for d in docs if d["status"] == "active"]
        return deepcopy(docs)

    def update_document(self, document_id: str, fields: dict[str, Any]):
        self.documents[document_id].update(fields)
        return {k: v for k, v in self.documents[document_id].items() if k != "storage_key"}

    def archive_document(self, document_id: str, *, actor_id: str):
        self.documents[document_id]["status"] = "archived"
        return deepcopy(self.documents[document_id])

    def get_acknowledgement(self, *, user_sub: str, guidance_version_id: str):
        return deepcopy(self.acks.get((user_sub, guidance_version_id)))

    def create_acknowledgement(self, payload: dict[str, Any]):
        key = (payload["user_sub"], payload["guidance_version_id"])
        if key not in self.acks:
            self.acks[key] = {
                "id": str(uuid4()),
                **payload,
                "acknowledged_at": "2026-08-04T12:00:00+00:00",
            }
        return deepcopy(self.acks[key])

    def list_org_units(self, *, active_only: bool = True):
        return list(self.units.values())

    def list_org_areas(self, *, active_only: bool = True):
        return list(self.areas.values())

    def list_org_cost_centers(self, *, active_only: bool = True, branch: str | None = None):
        return list_org_cost_centers_from_store(
            self.ccs, active_only=active_only, branch=branch
        )

    def get_org_cost_center(self, code: str, *, branch: str | None = None):
        return get_org_cost_center_from_store(self.ccs, code, branch=branch)

    def list_org_cost_centers_by_code(self, code: str):
        return list_org_cost_centers_by_code_from_store(self.ccs, code)

    def upsert_org_unit(self, code: str, name: str):
        self.units[code] = {"code": code, "name": name, "active": True}

    def upsert_org_area(self, code: str, name: str, unit_code: str | None):
        self.areas[code] = {"code": code, "name": name, "unit_code": unit_code, "active": True}

    def upsert_org_cost_center(self, payload: dict[str, Any]):
        return upsert_org_cost_center_in_store(self.ccs, payload)

    def list_scopes(self, *, active_only: bool = False):
        items = list(self.scopes.values())
        if active_only:
            items = [s for s in items if s["active"]]
        return deepcopy(items)

    def list_scopes_for_user(self, user_sub: str):
        return deepcopy([s for s in self.scopes.values() if s["user_sub"] == user_sub and s["active"]])

    def get_scope(self, scope_id: str):
        return deepcopy(self.scopes.get(scope_id))

    def create_scope(self, payload: dict[str, Any]):
        sid = str(uuid4())
        row = {**payload, "id": sid, "active": True}
        self.scopes[sid] = row
        return deepcopy(row)

    def update_scope(self, scope_id: str, fields: dict[str, Any]):
        self.scopes[scope_id].update(fields)
        return deepcopy(self.scopes[scope_id])

    def deactivate_scope(self, scope_id: str, *, actor_id: str):
        self.scopes[scope_id]["active"] = False
        return deepcopy(self.scopes[scope_id])

    def find_conflicting_scope(self, **kwargs):
        for s in self.scopes.values():
            if not s["active"]:
                continue
            if (
                s["user_sub"] == kwargs["user_sub"]
                and s["unit_code"] == kwargs["unit_code"]
                and s["scope_level"] == kwargs["scope_level"]
                and (s.get("area_code") or None) == (kwargs.get("area_code") or None)
                and (s.get("cost_center_code") or None) == (kwargs.get("cost_center_code") or None)
            ):
                if kwargs.get("exclude_id") and s["id"] == kwargs["exclude_id"]:
                    continue
                return deepcopy(s)
        return None

    def append_audit(self, **kwargs):
        self.audits.append(kwargs)


def _admin() -> BudgetActor:
    return BudgetActor(
        user_id="admin-1",
        user_name="Admin",
        permissions=frozenset({
            "planejamento-orcamentario.access",
            "planejamento-orcamentario.admin",
            "planejamento-orcamentario.guidance.manage",
            "planejamento-orcamentario.scopes.manage",
        }),
    )


def _user() -> BudgetActor:
    return BudgetActor(
        user_id="user-1",
        user_name="User",
        permissions=frozenset({
            "planejamento-orcamentario.access",
            "planejamento-orcamentario.guidance.view",
        }),
    )


@pytest.fixture
def uc(tmp_path):
    repo = InMemoryRepo()
    return BudgetPlanningUseCases(repository=repo, storage=BudgetDocumentStorage(str(tmp_path))), repo


def test_create_exercise_and_invalid_dates(uc):
    use_cases, repo = uc
    created = use_cases.create_exercise(
        _admin(),
        {
            "year": 2027,
            "name": "PO 2027",
            "preparation_starts_at": "2026-09-01",
            "filling_starts_at": "2026-10-01",
            "deadline_at": "2026-10-31",
        },
    )
    assert created["status"] == "draft"
    assert created["year"] == 2027
    with pytest.raises(BudgetExerciseInvalidDatesError):
        use_cases.create_exercise(
            _admin(),
            {
                "year": 2028,
                "name": "bad",
                "filling_starts_at": "2026-12-01",
                "deadline_at": "2026-01-01",
            },
        )


def test_publish_guidance_immutable_and_new_version(uc):
    use_cases, repo = uc
    ex = use_cases.create_exercise(_admin(), {"year": 2027, "name": "PO 2027"})
    use_cases.transition_exercise(_admin(), ex["id"], action="publish")
    draft = use_cases.get_or_create_guidance_draft(_admin(), ex["id"])
    use_cases.update_guidance_draft(
        _admin(),
        draft["id"],
        {
            "title": "Carta 2027",
            "board_message": "Mensagem da diretoria",
            "premises": [{"name": "Inflação", "value_text": "4,5%", "unit_label": "%"}],
            "schedule": [{"title": "Início", "starts_on": "2026-10-01"}],
        },
    )
    published = use_cases.publish_guidance(_admin(), draft["id"])
    assert published["version_number"] == 1
    assert published["status"] == "published"
    with pytest.raises(BudgetGuidanceImmutableError):
        use_cases.update_guidance_draft(_admin(), published["id"], {"title": "hack"})
    draft2 = use_cases.get_or_create_guidance_draft(_admin(), ex["id"])
    assert draft2["status"] == "draft"
    use_cases.update_guidance_draft(
        _admin(), draft2["id"], {"board_message": "Nova mensagem", "title": "Carta v2"}
    )
    published2 = use_cases.publish_guidance(_admin(), draft2["id"])
    assert published2["version_number"] == 2


def test_acknowledge_idempotent_and_modules_unlock(uc):
    use_cases, repo = uc
    ex = use_cases.create_exercise(_admin(), {"year": 2027, "name": "PO 2027"})
    use_cases.transition_exercise(_admin(), ex["id"], action="publish")
    draft = use_cases.get_or_create_guidance_draft(_admin(), ex["id"])
    use_cases.update_guidance_draft(
        _admin(), draft["id"], {"title": "T", "board_message": "M"}
    )
    use_cases.publish_guidance(_admin(), draft["id"])
    ctx = use_cases.get_context(_user())
    assert ctx["modules_unlocked"] is False
    r1 = use_cases.acknowledge_current_guidance(_user())
    r2 = use_cases.acknowledge_current_guidance(_user())
    assert r1["acknowledged"] is True
    assert r2["idempotent_replay"] is True
    assert r1["acknowledged_at"] == r2["acknowledged_at"]
    ctx2 = use_cases.get_context(_user())
    assert ctx2["modules_unlocked"] is True
    # nova versão exige nova confirmação
    draft3 = use_cases.get_or_create_guidance_draft(_admin(), ex["id"])
    use_cases.update_guidance_draft(
        _admin(), draft3["id"], {"title": "T2", "board_message": "M2"}
    )
    use_cases.publish_guidance(_admin(), draft3["id"])
    ctx3 = use_cases.get_context(_user())
    assert ctx3["modules_unlocked"] is False


def test_scope_requires_catalog_cc(uc):
    use_cases, repo = uc
    with pytest.raises(BudgetScopeConflictError):
        use_cases.create_scope(
            _admin(),
            {
                "user_sub": "u1",
                "unit_code": "01",
                "scope_level": "cost_center",
                "cost_center_code": "999-FAKE",
            },
        )
    created = use_cases.create_scope(
        _admin(),
        {
            "user_sub": "u1",
            "unit_code": "01",
            "scope_level": "cost_center",
            "cost_center_code": "205",
        },
    )
    assert created["cost_center_code"] == "205"
    with pytest.raises(BudgetScopeConflictError):
        use_cases.create_scope(
            _admin(),
            {
                "user_sub": "u1",
                "unit_code": "01",
                "scope_level": "cost_center",
                "cost_center_code": "205",
            },
        )


def test_download_requires_permission(uc):
    use_cases, repo = uc
    ex = use_cases.create_exercise(_admin(), {"year": 2027, "name": "PO"})
    doc = use_cases.upload_document(
        _admin(),
        exercise_id=ex["id"],
        guidance_id=None,
        display_name="doc",
        original_name="a.pdf",
        content=b"%PDF",
        mime_type="application/pdf",
        description=None,
        display_order=0,
    )
    stranger = BudgetActor(user_id="x", user_name="x", permissions=frozenset())
    with pytest.raises(BudgetUserNotAuthorizedError):
        use_cases.resolve_download(stranger, doc["id"])
    public = use_cases.resolve_download(_user(), doc["id"])
    assert "storage_key" not in public["document"]
    assert public["kind"] == "file"


def test_ack_bound_to_guidance_version_id_not_version_number(uc):
    use_cases, repo = uc
    ex = use_cases.create_exercise(_admin(), {"year": 2027, "name": "PO 2027"})
    use_cases.transition_exercise(_admin(), ex["id"], action="publish")
    d1 = use_cases.get_or_create_guidance_draft(_admin(), ex["id"])
    use_cases.update_guidance_draft(_admin(), d1["id"], {"title": "V1", "board_message": "M1"})
    p1 = use_cases.publish_guidance(_admin(), d1["id"])
    use_cases.acknowledge_current_guidance(_user())
    d2 = use_cases.get_or_create_guidance_draft(_admin(), ex["id"])
    use_cases.update_guidance_draft(_admin(), d2["id"], {"title": "V2", "board_message": "M2"})
    p2 = use_cases.publish_guidance(_admin(), d2["id"])
    assert p1["id"] != p2["id"]
    assert use_cases.get_context(_user())["modules_unlocked"] is False
    assert ( _user().user_id, p1["id"] ) in repo.acks
    assert ( _user().user_id, p2["id"] ) not in repo.acks


def test_public_document_hides_storage_key_and_audit_has_no_binary(uc):
    use_cases, repo = uc
    ex = use_cases.create_exercise(_admin(), {"year": 2027, "name": "PO"})
    draft = use_cases.get_or_create_guidance_draft(_admin(), ex["id"])
    doc = use_cases.upload_document(
        _admin(),
        exercise_id=ex["id"],
        guidance_id=draft["id"],
        display_name="carta",
        original_name="carta.pdf",
        content=b"%PDF-secret",
        mime_type="application/pdf",
        description="apoio",
        display_order=1,
    )
    assert "storage_key" not in doc
    listed = use_cases.list_admin_documents(draft["id"])
    assert listed[0]["id"] == doc["id"]
    assert "storage_key" not in listed[0]
    audit = repo.audits[-1]
    assert audit["action"] == "document.uploaded"
    assert b"%PDF" not in str(audit).encode()
    assert "storage_key" not in (audit.get("after_state") or {})


def test_exercise_year_uniqueness_and_single_active(uc):
    use_cases, repo = uc
    a = use_cases.create_exercise(_admin(), {"year": 2027, "name": "A"})
    with pytest.raises(BudgetExerciseAlreadyActiveError):
        use_cases.create_exercise(_admin(), {"year": 2027, "name": "dup"})
    use_cases.transition_exercise(_admin(), a["id"], action="publish")
    b = use_cases.create_exercise(_admin(), {"year": 2028, "name": "B"})
    use_cases.transition_exercise(_admin(), b["id"], action="publish")
    active = [e for e in repo.list_exercises() if e.get("is_active")]
    assert len(active) == 1
    assert active[0]["id"] == b["id"]
