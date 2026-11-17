"""W014 — DAVI execute: governed PREPARE/ACT for SI bulk/operational writes.

Unit-level coverage with a fake owner client enforcing the same contracts
the SI API now enforces: digest-bound bulk previews, per-scope
expected_max_version OCC, import expected_counts, single-flight cache
refresh, admission-capped actor-owned jobs — plus the sealed-proposal
single-use/cross-actor/confirmation guarantees from W012/W013.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

import pytest

from strategic_indicators_client import StrategicIndicatorsApiError

from app.application.external_capabilities.governed_writes.errors import (
    CAPABILITY_NOT_ALLOWED,
    CONFIRMATION_REQUIRED,
    PROPOSAL_STALE,
    VALIDATION,
    GovernedWriteError,
)
from app.application.external_capabilities.governed_writes.orchestrator import (
    DaviGovernedWriteOrchestrator,
    WRITE_CAPABILITIES,
)
from app.application.external_capabilities.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from app.application.external_capabilities.governed_writes.si_w014_capabilities import (
    SI_W014_WRITE_CAPABILITIES,
    SiW014WriteStack,
)

AUTH_OK = "Bearer user-a"
AUTH_OTHER = "Bearer user-b"
AUTH_DENIED = "Bearer user-denied"
ACTOR = "user-a@delpi"

_SOURCE_FIELDS = (
    "indicator_id",
    "goal_scope_branch",
    "goal_label",
    "goal_value",
    "goal_periodicity",
    "goal_mode",
)
_EXISTING_FIELDS = ("indicator_id", "goal_scope_branch", "goal_year")


def _digest(rows, fields):
    def _norm(field, value):
        if value is None:
            return ""
        if field == "goal_value":
            return str(float(value))
        return str(value)

    tuples = sorted(
        "|".join(_norm(f, r.get(f)) for f in fields) for r in rows
    )
    return hashlib.sha256("\n".join(tuples).encode("utf-8")).hexdigest()


def _goal(**kw):
    row = {
        "id": kw.pop("id", "g-x"),
        "indicator_id": "ind-1",
        "goal_year": 2025,
        "goal_label": "Meta",
        "goal_value": 100.0,
        "goal_periodicity": "monthly",
        "goal_mode": "standard",
        "goal_scope_branch": "",
        "version": 1,
        "is_active": True,
        "monthly_targets": [],
        "updated_at": "2025-01-01T00:00:00",
    }
    row.update(kw)
    return row


class FakeSiClient:
    """Owner double enforcing the W014 OCC/digest/admission contracts."""

    def __init__(self) -> None:
        self.goals: list[dict] = []
        self.writes: list[str] = []
        self.dept_indicators = {
            "fin": [{"indicator_id": "ind-1", "is_active": True}]
        }
        self.catalog = {
            "departments": [{"department_id": "fin"}],
            "department_indicators": [{"indicator_id": "ind-1"}],
            "indicator_goals": [],
        }
        self.refresh = {
            "running": False,
            "last_started_at": "2025-01-01T00:00:00",
            "last_completed_at": "2025-01-01T01:00:00",
        }
        self.jobs: dict[str, dict] = {}
        self._job_seq = 0

    def _check(self, authorization: str) -> None:
        if authorization == AUTH_DENIED:
            raise StrategicIndicatorsApiError("denied", status_code=403)

    # ---- reads ----------------------------------------------------------
    def list_user_indicator_goals(
        self,
        *,
        authorization: str,
        indicator_id=None,
        goal_year=None,
        department_id=None,
        active_only=None,
    ):
        self._check(authorization)
        items = [
            dict(g)
            for g in self.goals
            if (goal_year is None or g["goal_year"] == goal_year)
            and (indicator_id is None or g["indicator_id"] == indicator_id)
            and (not active_only or g["is_active"])
        ]
        return {"items": items}

    def list_user_admin_department_indicators(
        self, *, authorization: str, department_id: str
    ):
        self._check(authorization)
        return {"items": list(self.dept_indicators.get(department_id, []))}

    def get_user_cache_refresh_status(self, *, authorization: str):
        self._check(authorization)
        return dict(self.refresh)

    def get_user_job_status(self, *, authorization: str, job_id: str):
        self._check(authorization)
        job = self.jobs.get(job_id)
        # Owner binds jobs to the creator — a different actor sees 404.
        if job is None or job["actor"] != authorization:
            raise StrategicIndicatorsApiError("not found", status_code=404)
        return dict(job)

    def export_user_admin_config(self, *, authorization: str):
        self._check(authorization)
        return {
            "schema_version": 1,
            "departments": list(self.catalog["departments"]),
            "department_indicators": list(
                self.catalog["department_indicators"]
            ),
            "indicator_goals": list(self.catalog["indicator_goals"]),
        }

    # ---- bulk goals -----------------------------------------------------
    def bulk_create_user_indicator_goals(
        self, *, authorization: str, body, **kw
    ):
        self._check(authorization)
        self.writes.append("bulk_create")
        created = []
        for item in body["items"]:
            key = (
                item["indicator_id"],
                item.get("goal_scope_branch") or "",
            )
            current_max = max(
                (
                    g["version"]
                    for g in self.goals
                    if g["indicator_id"] == key[0]
                    and g["goal_year"] == body["goal_year"]
                    and (g.get("goal_scope_branch") or "") == key[1]
                ),
                default=0,
            )
            expected = item.get("expected_max_version")
            if expected is not None and current_max != int(expected):
                raise StrategicIndicatorsApiError(
                    "expected_max_version stale", status_code=409
                )
            for g in self.goals:
                if (
                    g["indicator_id"] == key[0]
                    and g["goal_year"] == body["goal_year"]
                    and (g.get("goal_scope_branch") or "") == key[1]
                    and g["is_active"]
                ):
                    g["is_active"] = False
            row = _goal(
                id=f"g-bulk-{len(self.goals)}",
                indicator_id=item["indicator_id"],
                goal_year=body["goal_year"],
                goal_label=item["goal_label"],
                goal_value=item["goal_value"],
                goal_periodicity=item["goal_periodicity"],
                goal_mode=item.get("goal_mode", "standard"),
                goal_scope_branch=key[1],
                version=current_max + 1,
                is_active=True,
            )
            self.goals.append(row)
            created.append(dict(row))
        return {"items": created}

    def duplicate_user_indicator_goals_year(
        self,
        *,
        authorization: str,
        body,
        expected_source_digest=None,
        expected_existing_digest=None,
        **kw,
    ):
        self._check(authorization)
        self.writes.append("duplicate_year")
        source = [
            g
            for g in self.goals
            if g["goal_year"] == body["source_year"] and g["is_active"]
        ]
        existing = [
            g
            for g in self.goals
            if g["goal_year"] == body["target_year"] and g["is_active"]
        ]
        if expected_source_digest is not None and (
            _digest(source, _SOURCE_FIELDS) != expected_source_digest
        ):
            raise StrategicIndicatorsApiError(
                "source digest mismatch", status_code=409
            )
        if expected_existing_digest is not None and (
            _digest(existing, _EXISTING_FIELDS) != expected_existing_digest
        ):
            raise StrategicIndicatorsApiError(
                "existing digest mismatch", status_code=409
            )
        created = []
        for row in source:
            key = (row["indicator_id"], row.get("goal_scope_branch") or "")
            has = any(
                (g["indicator_id"], g.get("goal_scope_branch") or "") == key
                for g in existing
            )
            if has and not body.get("overwrite_existing"):
                continue
            if has:
                for g in self.goals:
                    if (
                        g["indicator_id"] == key[0]
                        and g["goal_year"] == body["target_year"]
                        and (g.get("goal_scope_branch") or "") == key[1]
                        and g["is_active"]
                    ):
                        g["is_active"] = False
            new = dict(row)
            new["id"] = f"g-dup-{len(self.goals)}"
            new["goal_year"] = body["target_year"]
            new["version"] = 1
            new["is_active"] = True
            self.goals.append(new)
            created.append(dict(new))
        return {"items": created}

    def fill_missing_user_indicator_goals(
        self,
        *,
        authorization: str,
        body,
        expected_target_digest=None,
        expected_source_digest=None,
        **kw,
    ):
        self._check(authorization)
        self.writes.append("fill_missing")
        indicator_ids = {
            ind["indicator_id"]
            for dept in (body.get("department_ids") or [])
            for ind in self.dept_indicators.get(dept, [])
        } or None
        target = [
            g
            for g in self.goals
            if g["goal_year"] == body["goal_year"]
            and g["is_active"]
            and (indicator_ids is None or g["indicator_id"] in indicator_ids)
        ]
        if expected_target_digest is not None and (
            _digest(target, _EXISTING_FIELDS) != expected_target_digest
        ):
            raise StrategicIndicatorsApiError(
                "target digest mismatch", status_code=409
            )
        created = []
        copy_from = body.get("copy_from_year")
        if copy_from is not None:
            for ind_id in indicator_ids or set():
                if any(g["indicator_id"] == ind_id for g in target):
                    continue
                sources = [
                    g
                    for g in self.goals
                    if g["goal_year"] == copy_from
                    and g["is_active"]
                    and g["indicator_id"] == ind_id
                ]
                if not sources:
                    continue
                src = max(
                    sources, key=lambda g: (g["version"], g["updated_at"])
                )
                new = dict(src)
                new["id"] = f"g-fill-{len(self.goals)}"
                new["goal_year"] = body["goal_year"]
                new["is_active"] = True
                self.goals.append(new)
                created.append(dict(new))
        return {"items": created}

    # ---- import ---------------------------------------------------------
    def preview_user_admin_config_import(self, *, authorization: str, body):
        self._check(authorization)
        current = {k: len(v) for k, v in self.catalog.items()}
        planned = {
            "departments": {
                "in_file": len(body.get("departments") or []),
                "insert": sum(
                    1
                    for d in (body.get("departments") or [])
                    if d.get("department_id")
                    not in {x["department_id"] for x in self.catalog["departments"]}
                ),
                "update": 0,
                "skip": 0,
                "delete": 0,
            },
            "department_indicators": {
                "in_file": len(body.get("department_indicators") or []),
                "insert": sum(
                    1
                    for i in (body.get("department_indicators") or [])
                    if i.get("indicator_id")
                    not in {
                        x["indicator_id"]
                        for x in self.catalog["department_indicators"]
                    }
                ),
                "update": 0,
                "skip": 0,
                "delete": 0,
            },
            "indicator_goals": {
                "in_file": 0,
                "insert": 0,
                "update": 0,
                "skip": 0,
                "delete": 0,
            },
        }
        return {
            "valid": bool(body.get("schema_version") == 1),
            "errors": []
            if body.get("schema_version") == 1
            else ["schema_version incompatível"],
            "mode": body.get("mode"),
            "current_counts": current,
            "planned": planned,
        }

    def apply_user_admin_config_import(
        self,
        *,
        authorization: str,
        body,
        expected_counts=None,
        **kw,
    ):
        self._check(authorization)
        self.writes.append("import_apply")
        if expected_counts is not None:
            current = {k: len(v) for k, v in self.catalog.items()}
            expected = {
                "departments": int(expected_counts.get("departments") or 0),
                "department_indicators": int(
                    expected_counts.get("department_indicators") or 0
                ),
                "indicator_goals": int(
                    expected_counts.get("indicator_goals") or 0
                ),
            }
            if current != expected:
                raise StrategicIndicatorsApiError(
                    "catalog drifted since preview", status_code=409
                )
        existing_depts = {
            d["department_id"] for d in self.catalog["departments"]
        }
        for dept in body.get("departments") or []:
            if dept.get("department_id") not in existing_depts:
                self.catalog["departments"].append(dict(dept))
        existing_inds = {
            i["indicator_id"] for i in self.catalog["department_indicators"]
        }
        for ind in body.get("department_indicators") or []:
            if ind.get("indicator_id") not in existing_inds:
                self.catalog["department_indicators"].append(dict(ind))
        return {"stats": {"departments": {}, "department_indicators": {}}}

    # ---- cache ----------------------------------------------------------
    def refresh_user_cache(self, *, authorization: str, body=None):
        self._check(authorization)
        self.writes.append("cache_refresh")
        if self.refresh["running"]:
            return {"status": "already_running"}
        self.refresh["running"] = True
        self.refresh["last_started_at"] = "2025-06-01T00:00:00"
        return {"status": "accepted"}

    def invalidate_user_cache(self, *, authorization: str):
        self._check(authorization)
        self.writes.append("cache_invalidate")
        self.refresh["running"] = True
        self.refresh["last_started_at"] = "2025-06-01T00:00:00"
        return {"status": "ok"}

    # ---- jobs -----------------------------------------------------------
    def create_user_tree_load_job(self, *, authorization: str, body):
        self._check(authorization)
        self.writes.append("tree_load")
        active = [
            j for j in self.jobs.values() if j["state"] in ("queued", "running")
        ]
        if len(active) >= 8 or sum(
            1 for j in active if j["actor"] == authorization
        ) >= 2:
            raise StrategicIndicatorsApiError("admission", status_code=429)
        self._job_seq += 1
        job_id = f"job-{self._job_seq}"
        self.jobs[job_id] = {
            "job_id": job_id,
            "actor": authorization,
            "state": "queued",
            "phase": "snapshot",
            "progress_pct": 0,
            "message": "Preparando carregamento...",
        }
        return dict(self.jobs[job_id])


@pytest.fixture()
def orch(monkeypatch):
    monkeypatch.setenv("DAVI_GOVERNED_WRITE_HMAC_SECRET", "w014-test-secret")
    reset_proposal_store_for_tests()
    client = FakeSiClient()
    return (
        DaviGovernedWriteOrchestrator(
            w014_stack=SiW014WriteStack(client=client)
        ),
        client,
    )


def _prepare(orch, cap, args, auth=AUTH_OK):
    return orch.prepare(
        capability=cap,
        args=args,
        actor_id=ACTOR,
        actor_email=ACTOR,
        authorization=auth,
    )


def _act(orch, cap, prep, auth=AUTH_OK, confirm=True):
    return orch.act(
        capability=cap,
        proposal_handle=prep["proposal_handle"],
        proposal_id=None,
        confirm=confirm,
        actor_id=ACTOR,
        authorization=auth,
    )


# --------------------------------------------------------------- gate
def test_w014_capability_set():
    assert len(SI_W014_WRITE_CAPABILITIES) == 7
    assert len(WRITE_CAPABILITIES) == 23
    assert "si.config.import_replace" not in WRITE_CAPABILITIES
    assert "si.job.delete" not in WRITE_CAPABILITIES


def test_unapproved_capability_rejected(orch):
    o, _c = orch
    for bad in ("si.config.import", "si.config.replace", "si.goal.delete"):
        with pytest.raises(GovernedWriteError) as ei:
            _prepare(o, bad, {})
        assert ei.value.code == CAPABILITY_NOT_ALLOWED


# ---------------------------------------------------------- bulk create
def test_bulk_create_full_cycle(orch):
    o, c = orch
    prep = _prepare(
        o,
        "si.goal.bulk_create",
        {
            "goal_year": 2026,
            "items": [
                {
                    "indicator_id": "ind-1",
                    "goal_label": "Meta 2026",
                    "goal_value": 50,
                    "goal_periodicity": "monthly",
                }
            ],
        },
    )
    assert prep["phase"] == "prepare" and prep["act_allowed"]
    assert c.writes == []
    res = _act(o, "si.goal.bulk_create", prep)
    assert res["verified"] and res["data"]["bulk_create"]["created_count"] == 1


def test_bulk_create_supersede_impact(orch):
    o, c = orch
    c.goals.append(_goal(id="g-old", goal_year=2026, version=3))
    prep = _prepare(
        o,
        "si.goal.bulk_create",
        {
            "goal_year": 2026,
            "items": [
                {
                    "indicator_id": "ind-1",
                    "goal_label": "Meta nova",
                    "goal_value": 70,
                    "goal_periodicity": "monthly",
                }
            ],
        },
    )
    summary = prep["confirmation_requirement"]["summary"]
    assert summary["supersedes_active_goals"] == 1
    res = _act(o, "si.goal.bulk_create", prep)
    assert res["verified"]
    assert res["data"]["bulk_create"]["created_count"] == 1


def test_bulk_create_item_cap(orch):
    o, _c = orch
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(
            o,
            "si.goal.bulk_create",
            {
                "goal_year": 2026,
                "items": [
                    {
                        "indicator_id": "ind-1",
                        "goal_label": "x",
                        "goal_value": 1,
                        "goal_periodicity": "monthly",
                    }
                ]
                * 501,
            },
        )
    assert ei.value.code == VALIDATION


def test_bulk_create_stale_fingerprint_refused(orch):
    o, c = orch
    prep = _prepare(
        o,
        "si.goal.bulk_create",
        {
            "goal_year": 2026,
            "items": [
                {
                    "indicator_id": "ind-1",
                    "goal_label": "Meta",
                    "goal_value": 1,
                    "goal_periodicity": "monthly",
                }
            ],
        },
    )
    # Concurrent writer advances the scope version between PREPARE and ACT.
    c.goals.append(_goal(id="g-race", goal_year=2026, version=1))
    with pytest.raises(GovernedWriteError) as ei:
        _act(o, "si.goal.bulk_create", prep)
    assert ei.value.code == PROPOSAL_STALE


# ---------------------------------------------------------- duplicate year
def test_duplicate_year_full_cycle(orch):
    o, c = orch
    c.goals.append(_goal(id="g-2025", goal_year=2025))
    prep = _prepare(
        o,
        "si.goal.duplicate_year",
        {"source_year": 2025, "target_year": 2026},
    )
    summary = prep["confirmation_requirement"]["summary"]
    assert summary["source_goals"] == 1 and summary["creates"] == 1
    assert c.writes == []
    res = _act(o, "si.goal.duplicate_year", prep)
    assert res["verified"] and res["data"]["duplicate_year"]["created_count"] == 1


def test_duplicate_year_overwrite_counts(orch):
    o, c = orch
    c.goals.append(_goal(id="g-2025", goal_year=2025))
    c.goals.append(_goal(id="g-2026", goal_year=2026))
    prep = _prepare(
        o,
        "si.goal.duplicate_year",
        {"source_year": 2025, "target_year": 2026, "overwrite_existing": False},
    )
    summary = prep["confirmation_requirement"]["summary"]
    assert summary["preserved_conflicts"] == 1 and summary["creates"] == 0
    prep2 = _prepare(
        o,
        "si.goal.duplicate_year",
        {"source_year": 2025, "target_year": 2026, "overwrite_existing": True},
    )
    assert prep2["confirmation_requirement"]["summary"]["overwrites"] == 1
    res = _act(o, "si.goal.duplicate_year", prep2)
    assert res["verified"]


def test_duplicate_year_digest_conflict(orch):
    o, c = orch
    c.goals.append(_goal(id="g-2025", goal_year=2025))
    prep = _prepare(
        o,
        "si.goal.duplicate_year",
        {"source_year": 2025, "target_year": 2026},
    )
    # Concurrent source change after PREPARE → fingerprint drift.
    c.goals.append(_goal(id="g-2025-b", goal_year=2025, indicator_id="ind-2"))
    with pytest.raises(GovernedWriteError) as ei:
        _act(o, "si.goal.duplicate_year", prep)
    assert ei.value.code == PROPOSAL_STALE


def test_duplicate_year_same_year_rejected(orch):
    o, _c = orch
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(
            o,
            "si.goal.duplicate_year",
            {"source_year": 2026, "target_year": 2026},
        )
    assert ei.value.code == VALIDATION


# ----------------------------------------------------------- fill missing
def test_fill_missing_full_cycle(orch):
    o, c = orch
    c.goals.append(_goal(id="g-2025", goal_year=2025))
    prep = _prepare(
        o,
        "si.goal.fill_missing",
        {
            "goal_year": 2026,
            "department_ids": ["fin"],
            "copy_from_year": 2025,
        },
    )
    assert prep["confirmation_requirement"]["summary"]["creates"] == 1
    res = _act(o, "si.goal.fill_missing", prep)
    assert res["verified"] and res["data"]["fill_missing"]["created_count"] == 1


def test_fill_missing_noop_when_present(orch):
    o, c = orch
    c.goals.append(_goal(id="g-2025", goal_year=2025))
    c.goals.append(_goal(id="g-2026", goal_year=2026))
    prep = _prepare(
        o,
        "si.goal.fill_missing",
        {
            "goal_year": 2026,
            "department_ids": ["fin"],
            "copy_from_year": 2025,
        },
    )
    assert prep["confirmation_requirement"]["summary"]["creates"] == 0
    res = _act(o, "si.goal.fill_missing", prep)
    assert res["verified"] and res["data"]["fill_missing"]["created_count"] == 0


# -------------------------------------------------------------- import
def _bundle(**kw):
    bundle = {
        "schema_version": 1,
        "mode": "merge",
        "departments": [{"department_id": "ops"}],
        "department_indicators": [{"indicator_id": "ind-9"}],
        "indicator_goals": [],
        "module_settings": {},
    }
    bundle.update(kw)
    return bundle


def test_import_apply_merge_cycle(orch):
    o, c = orch
    prep = _prepare(
        o, "si.config.import_apply", {"bundle": _bundle(), "include_goals": True}
    )
    assert prep["act_allowed"]
    assert c.writes == []
    res = _act(o, "si.config.import_apply", prep)
    assert res["verified"]
    counts = res["data"]["import"]["counts"]
    assert counts["departments"] == 2
    assert counts["department_indicators"] == 2


def test_import_apply_replace_rejected(orch):
    o, _c = orch
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(
            o,
            "si.config.import_apply",
            {"bundle": _bundle(mode="replace")},
        )
    assert ei.value.code == VALIDATION


def test_import_apply_invalid_bundle_not_ready(orch):
    o, _c = orch
    prep = _prepare(
        o,
        "si.config.import_apply",
        {"bundle": _bundle(schema_version=99)},
    )
    assert not prep["ready"]
    with pytest.raises(GovernedWriteError) as ei:
        _act(o, "si.config.import_apply", prep)
    assert ei.value.code == PROPOSAL_STALE


def test_import_apply_catalog_drift_refused(orch):
    o, c = orch
    prep = _prepare(
        o, "si.config.import_apply", {"bundle": _bundle()}
    )
    c.catalog["departments"].append({"department_id": "race"})
    with pytest.raises(GovernedWriteError) as ei:
        _act(o, "si.config.import_apply", prep)
    assert ei.value.code == PROPOSAL_STALE


# --------------------------------------------------------------- cache
def test_cache_refresh_cycle(orch):
    o, c = orch
    prep = _prepare(o, "si.cache.refresh", {"competence": "2025-06"})
    assert c.writes == []
    res = _act(o, "si.cache.refresh", prep)
    assert res["verified"] and res["data"]["cache"]["running"] is True


def test_cache_refresh_already_running_impact(orch):
    o, c = orch
    c.refresh["running"] = True
    prep = _prepare(o, "si.cache.refresh", {})
    assert prep["consequential_impact"]["already_running"] is True


def test_cache_invalidate_cycle(orch):
    o, c = orch
    prep = _prepare(o, "si.cache.invalidate", {})
    res = _act(o, "si.cache.invalidate", prep)
    assert res["verified"]
    assert c.writes == ["cache_invalidate"]


def test_cache_invalidate_extra_arg_rejected(orch):
    o, _c = orch
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(o, "si.cache.invalidate", {"scope": "all"})
    assert ei.value.code == VALIDATION


# ----------------------------------------------------------------- jobs
def test_tree_load_job_cycle(orch):
    o, c = orch
    prep = _prepare(
        o,
        "si.job.tree_load",
        {"view_mode": "consolidated", "months": 6},
    )
    assert c.writes == []
    res = _act(o, "si.job.tree_load", prep)
    assert res["verified"]
    job = res["data"]["job"]
    assert job["job_id"] == "job-1" and job["state"] == "queued"
    # The job is registered and queryable by the dispatching actor.
    assert c.get_user_job_status(
        authorization=AUTH_OK, job_id="job-1"
    )["state"] == "queued"


def test_tree_load_job_view_mode_rejected(orch):
    o, _c = orch
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(o, "si.job.tree_load", {"view_mode": "raw"})
    assert ei.value.code == VALIDATION


# ------------------------------------------------------- shared guarantees
def test_act_without_confirm_rejected(orch):
    o, c = orch
    prep = _prepare(o, "si.cache.invalidate", {})
    with pytest.raises(GovernedWriteError) as ei:
        _act(o, "si.cache.invalidate", prep, confirm=False)
    assert ei.value.code == CONFIRMATION_REQUIRED
    assert c.writes == []


def test_cross_actor_proposal_rejected(orch):
    o, c = orch
    prep = _prepare(o, "si.cache.invalidate", {})
    with pytest.raises(GovernedWriteError):
        o.act(
            capability="si.cache.invalidate",
            proposal_handle=prep["proposal_handle"],
            proposal_id=None,
            confirm=True,
            actor_id="user-b@delpi",
            authorization=AUTH_OTHER,
        )
    assert c.writes == []


def test_denied_owner_authz_maps(orch):
    o, _c = orch
    with pytest.raises(GovernedWriteError):
        _prepare(o, "si.job.tree_load", {}, auth=AUTH_DENIED)


def test_consumed_proposal_cannot_be_replayed(orch):
    """The sealed handle is single-use even after a verified ACT."""
    o, c = orch
    c.goals.append(_goal(id="g-2025", goal_year=2025))
    prep = _prepare(
        o,
        "si.goal.duplicate_year",
        {"source_year": 2025, "target_year": 2026},
    )
    res = _act(o, "si.goal.duplicate_year", prep)
    assert res["verified"]
    with pytest.raises(GovernedWriteError):
        _act(o, "si.goal.duplicate_year", prep)
