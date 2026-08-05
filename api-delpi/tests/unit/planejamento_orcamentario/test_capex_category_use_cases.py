"""Testes Fase 2A.3 — catálogo de categorias CAPEX (repositório fake)."""
from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

import pytest

from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.application.use_cases.planejamento_orcamentario.capex_category_use_cases import (
    CapexCategoryUseCases,
)
from app.domain.services.planejamento_orcamentario.capex_category_constants import (
    DEFAULT_CAPEX_CATEGORIES,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetUserNotAuthorizedError,
    CapexCategoryConflictError,
    CapexCategoryInvalidError,
    CapexCategoryNotFoundError,
)


class FakeRepo:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self.audits: list[dict] = []

    def seed_defaults(self) -> None:
        for code, name, order in DEFAULT_CAPEX_CATEGORIES:
            if any(r["code"] == code for r in self.rows.values()):
                continue
            rid = str(uuid4())
            self.rows[rid] = {
                "id": rid,
                "code": code,
                "name": name,
                "description": None,
                "display_order": order,
                "is_active": True,
                "is_system_default": True,
                "created_by": "system",
                "created_at": "t",
                "updated_by": "system",
                "updated_at": "t",
                "deactivated_by": None,
                "deactivated_at": None,
            }

    def get_capex_category(self, category_id: str):
        return deepcopy(self.rows.get(category_id))

    def get_capex_category_by_code(self, code: str):
        for r in self.rows.values():
            if r["code"] == code:
                return deepcopy(r)
        return None

    def list_capex_categories(self, *, is_active=None, q=None):
        items = list(self.rows.values())
        if is_active is not None:
            items = [i for i in items if i["is_active"] is is_active]
        if q:
            ql = q.lower()
            items = [
                i
                for i in items
                if ql in i["code"].lower()
                or ql in i["name"].lower()
                or ql in (i.get("description") or "").lower()
            ]
        items.sort(key=lambda i: (i["display_order"], i["name"], i["code"]))
        return deepcopy(items)

    def create_capex_category(self, payload: dict[str, Any]):
        rid = str(uuid4())
        row = {
            **payload,
            "id": rid,
            "is_active": True,
            "created_at": "t",
            "updated_at": "t",
            "deactivated_by": None,
            "deactivated_at": None,
        }
        self.rows[rid] = row
        return deepcopy(row)

    def update_capex_category(self, category_id: str, fields: dict[str, Any]):
        self.rows[category_id].update(fields)
        return deepcopy(self.rows[category_id])

    def deactivate_capex_category(self, category_id, *, actor_id, reason=None):
        row = self.rows[category_id]
        row.update(
            {
                "is_active": False,
                "deactivated_by": actor_id,
                "deactivated_at": "now",
                "updated_by": actor_id,
            }
        )
        return deepcopy(row)

    def reactivate_capex_category(self, category_id, *, actor_id):
        row = self.rows[category_id]
        row.update(
            {
                "is_active": True,
                "deactivated_by": None,
                "deactivated_at": None,
                "updated_by": actor_id,
            }
        )
        return deepcopy(row)

    def append_audit(self, **kwargs):
        self.audits.append(kwargs)


def _admin() -> BudgetActor:
    return BudgetActor(
        user_id="admin-1",
        user_name="Admin",
        permissions={
            "planejamento-orcamentario.admin",
            "planejamento-orcamentario.scopes.manage",
        },
    )


def _user() -> BudgetActor:
    return BudgetActor(
        user_id="user-1",
        user_name="User",
        permissions={"planejamento-orcamentario.access"},
    )


def _uc(repo: FakeRepo | None = None) -> CapexCategoryUseCases:
    return CapexCategoryUseCases(repository=repo or FakeRepo())  # type: ignore[arg-type]


def test_default_seed_catalog_has_twenty_four():
    assert len(DEFAULT_CAPEX_CATEGORIES) == 24
    codes = [c[0] for c in DEFAULT_CAPEX_CATEGORIES]
    assert len(codes) == len(set(codes))
    assert DEFAULT_CAPEX_CATEGORIES[0][1] == "Computadores e Periféricos"


def test_seed_idempotent_does_not_overwrite_admin_rename():
    repo = FakeRepo()
    repo.seed_defaults()
    first = next(r for r in repo.rows.values() if r["code"] == "FERRAMENTAS")
    first["name"] = "Ferramentas (custom)"
    repo.seed_defaults()
    again = next(r for r in repo.rows.values() if r["code"] == "FERRAMENTAS")
    assert again["name"] == "Ferramentas (custom)"
    assert len(repo.rows) == 24


def test_create_and_audit():
    repo = FakeRepo()
    uc = _uc(repo)
    created = uc.create_category(
        _admin(),
        {"code": "OUTROS_TESTE", "name": "Outros teste", "display_order": 999},
    )
    assert created["code"] == "OUTROS_TESTE"
    assert created["is_system_default"] is False
    assert any(a["action"] == "capex_category.created" for a in repo.audits)


def test_duplicate_code_blocked():
    repo = FakeRepo()
    uc = _uc(repo)
    uc.create_category(_admin(), {"code": "DUP", "name": "Um"})
    with pytest.raises(CapexCategoryConflictError):
        uc.create_category(_admin(), {"code": "dup", "name": "Dois"})


def test_name_required():
    with pytest.raises(CapexCategoryInvalidError):
        _uc().create_category(_admin(), {"code": "X", "name": "  "})


def test_update_name_description_order():
    repo = FakeRepo()
    uc = _uc(repo)
    created = uc.create_category(
        _admin(), {"code": "EDIT", "name": "Antes", "display_order": 1}
    )
    updated = uc.update_category(
        _admin(),
        created["id"],
        {"name": "Depois", "description": "desc", "display_order": 5},
    )
    assert updated["name"] == "Depois"
    assert updated["description"] == "desc"
    assert updated["display_order"] == 5
    actions = {a["action"] for a in repo.audits}
    assert "capex_category.updated" in actions
    assert "capex_category.order_changed" in actions


def test_code_immutable():
    repo = FakeRepo()
    uc = _uc(repo)
    created = uc.create_category(_admin(), {"code": "FIXO", "name": "Nome"})
    with pytest.raises(CapexCategoryInvalidError, match="imutável"):
        uc.update_category(_admin(), created["id"], {"code": "OUTRO"})


def test_deactivate_and_reactivate():
    repo = FakeRepo()
    uc = _uc(repo)
    created = uc.create_category(_admin(), {"code": "TMP", "name": "Temp"})
    off = uc.deactivate_category(_admin(), created["id"])
    assert off["is_active"] is False
    on = uc.reactivate_category(_admin(), created["id"])
    assert on["is_active"] is True
    assert any(a["action"] == "capex_category.deactivated" for a in repo.audits)
    assert any(a["action"] == "capex_category.reactivated" for a in repo.audits)


def test_public_list_only_active():
    repo = FakeRepo()
    repo.seed_defaults()
    uc = _uc(repo)
    tools = next(r for r in repo.rows.values() if r["code"] == "FERRAMENTAS")
    uc.deactivate_category(_admin(), tools["id"])
    public = uc.list_active_categories(_user())
    codes = {i["code"] for i in public["items"]}
    assert "FERRAMENTAS" not in codes
    assert "VEICULOS" in codes
    assert all(i["is_active"] for i in public["items"])


def test_admin_search_and_status_filter():
    repo = FakeRepo()
    repo.seed_defaults()
    uc = _uc(repo)
    found = uc.list_admin_categories(_admin(), q="Veíc")
    assert any(i["code"] == "VEICULOS" for i in found["items"])
    tools = next(r for r in repo.rows.values() if r["code"] == "FERRAMENTAS")
    uc.deactivate_category(_admin(), tools["id"])
    inactive = uc.list_admin_categories(_admin(), is_active=False)
    assert all(not i["is_active"] for i in inactive["items"])
    assert any(i["code"] == "FERRAMENTAS" for i in inactive["items"])


def test_authorization():
    with pytest.raises(BudgetUserNotAuthorizedError):
        _uc().create_category(_user(), {"code": "X", "name": "Y"})
    with pytest.raises(BudgetUserNotAuthorizedError):
        _uc().list_admin_categories(_user())


def test_not_found():
    with pytest.raises(CapexCategoryNotFoundError):
        _uc().update_category(_admin(), str(uuid4()), {"name": "x"})
