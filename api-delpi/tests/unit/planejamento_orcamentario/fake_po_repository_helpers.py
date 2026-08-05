"""Helpers compartilhados — fakes branch-aware de centros de custo PO."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any
from uuid import uuid4


def _cc_row(
    *,
    code: str,
    name: str,
    branch: str,
    area_code: str = "PROD",
    source: str = "manual",
) -> dict[str, Any]:
    return {
        "id": f"cc-{code}-{branch}",
        "code": code,
        "name": name,
        "branch": branch,
        "unit_code": branch,
        "area_code": area_code,
        "active": True,
        "source": source,
    }


def default_po_cc_seed() -> dict[tuple[str, str], dict[str, Any]]:
    """CCs padrão para testes — chave (branch, code), branch = unit_code."""
    return {
        ("01", "205"): _cc_row(code="205", name="TI", branch="01"),
        ("01", "210"): _cc_row(code="210", name="Manutenção", branch="01"),
    }


def default_po_cc_seed_with_es() -> dict[tuple[str, str], dict[str, Any]]:
    seed = default_po_cc_seed()
    seed[("02", "301")] = _cc_row(
        code="301", name="ES-Eng", branch="02", area_code="ENG"
    )
    return seed


def cc_dict_by_code(store: dict[tuple[str, str], dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Índice legado por código (testes com códigos únicos entre filiais)."""
    return {code: cc for (_, code), cc in store.items()}


def cc_lookup_for_seed(
    store: dict[tuple[str, str], dict[str, Any]], cost_center_id: str
) -> dict[str, Any]:
    """Resolve CC por código quando o seed usa códigos distintos por filial."""
    matches = [cc for (_, code), cc in store.items() if code == cost_center_id]
    if not matches:
        raise KeyError(cost_center_id)
    if len(matches) > 1:
        raise KeyError(f"Ambíguo: {cost_center_id}")
    return matches[0]


def get_org_cost_center_from_store(
    store: dict[tuple[str, str], dict[str, Any]],
    code: str,
    *,
    branch: str | None = None,
) -> dict[str, Any] | None:
    code_norm = str(code or "").strip()
    if branch:
        return deepcopy(store.get((str(branch).strip(), code_norm)))
    matches = list_org_cost_centers_by_code_from_store(store, code_norm)
    if len(matches) != 1:
        return None
    return matches[0]


def list_org_cost_centers_by_code_from_store(
    store: dict[tuple[str, str], dict[str, Any]], code: str
) -> list[dict[str, Any]]:
    code_norm = str(code or "").strip()
    return deepcopy([r for (_, c), r in store.items() if c == code_norm])


def list_org_cost_centers_from_store(
    store: dict[tuple[str, str], dict[str, Any]],
    *,
    active_only: bool = True,
    branch: str | None = None,
) -> list[dict[str, Any]]:
    rows = list(store.values())
    if branch:
        branch_norm = str(branch).strip()
        rows = [r for r in rows if str(r.get("branch") or r.get("unit_code")) == branch_norm]
    if active_only:
        rows = [r for r in rows if r.get("active", True)]
    return deepcopy(rows)


def upsert_org_cost_center_in_store(
    store: dict[tuple[str, str], dict[str, Any]], payload: dict[str, Any]
) -> dict[str, Any]:
    branch = str(payload.get("branch") or payload.get("unit_code") or "").strip()
    code = str(payload["code"]).strip()
    key = (branch, code)
    existing = store.get(key)
    row = {
        "id": (existing or {}).get("id") or str(uuid4()),
        "branch": branch,
        "code": code,
        "name": payload["name"],
        "unit_code": str(payload.get("unit_code") or branch).strip(),
        "area_code": payload.get("area_code"),
        "source": payload.get("source") or "manual",
        "active": True,
        "created_by_user_id": payload.get("created_by_user_id"),
    }
    store[key] = row
    return deepcopy(row)


def filter_unit_cost_center_pairs(
    items: list[dict[str, Any]],
    pairs: list[tuple[str, str]] | None,
    *,
    unit_col: str = "unit_id",
    cc_col: str = "cost_center_id",
) -> list[dict[str, Any]]:
    if pairs is None:
        return items
    if not pairs:
        return []
    allowed = set(pairs)
    return [i for i in items if (i.get(unit_col), i.get(cc_col)) in allowed]


def find_valid_responsibility_in_rows(
    rows: list[dict[str, Any]] | dict[str, dict[str, Any]],
    *,
    user_sub: str,
    exercise_id: str,
    module: str,
    cost_center_id: str,
    unit_id: str | None = None,
    on_date: date | None = None,
) -> dict[str, Any] | None:
    check = on_date or date.today()
    iterable = rows.values() if isinstance(rows, dict) else rows
    for r in iterable:
        if not r.get("is_active", True):
            continue
        if (
            r["user_sub"] != user_sub
            or r["exercise_id"] != exercise_id
            or r["module"] != module
            or r["cost_center_id"] != cost_center_id
        ):
            continue
        if unit_id is not None and str(r.get("unit_id") or "") != str(unit_id):
            continue
        vf, vu = r.get("valid_from"), r.get("valid_until")
        if isinstance(vf, str):
            vf = date.fromisoformat(vf[:10])
        if isinstance(vu, str):
            vu = date.fromisoformat(vu[:10])
        if vf and check < vf:
            continue
        if vu and check > vu:
            continue
        return deepcopy(r)
    return None


def find_active_budget_responsibility_conflict_in_rows(
    rows: dict[str, dict[str, Any]],
    *,
    exercise_id: str,
    module: str,
    user_sub: str,
    cost_center_id: str,
    unit_id: str | None = None,
    exclude_id: str | None = None,
) -> dict[str, Any] | None:
    for rid, r in rows.items():
        if exclude_id and rid == exclude_id:
            continue
        if not r.get("is_active", True):
            continue
        if (
            r["exercise_id"] == exercise_id
            and r["module"] == module
            and r["user_sub"] == user_sub
            and r["cost_center_id"] == cost_center_id
            and (unit_id is None or r.get("unit_id") == unit_id)
        ):
            return deepcopy(r)
    return None


def get_capex_plan_by_exercise_cc_from_plans(
    plans: dict[str, dict[str, Any]],
    *,
    exercise_id: str,
    cost_center_id: str,
    unit_id: str | None = None,
) -> dict[str, Any] | None:
    for p in plans.values():
        if p["exercise_id"] != exercise_id or p["cost_center_id"] != cost_center_id:
            continue
        if unit_id is not None and p.get("unit_id") != unit_id:
            continue
        return deepcopy(p)
    return None
