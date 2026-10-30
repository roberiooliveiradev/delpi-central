"""CAIO 2.0 isolated-DB integration homologation — issue #125 (E2–E6).

Runs the semantic tools end-to-end against a REAL isolated Postgres
(``commercial`` schema, migrations V001–V023 applied). No TOTVS /
api-delpi: gateway-backed operations are covered separately by the
fake-gateway passthrough tests below and marked as boundary evidence.

Environment contract (docker):

    docker run -d --name caio-homolog-pg \\
        -e POSTGRES_PASSWORD=caio_homolog -e POSTGRES_DB=caio_homolog \\
        -p 127.0.0.1:55433:5432 postgres:15-alpine
    for m in commercial-api/migrations/V*.sql: apply in order.

Override via PLUGINS_DB_* env vars. Tests are skipped when the
database is unreachable — unit/contract coverage still applies.
"""

from __future__ import annotations

import os
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest

os.environ.setdefault("PLUGINS_DB_HOST", "127.0.0.1")
os.environ.setdefault("PLUGINS_DB_PORT", "55433")
os.environ.setdefault("PLUGINS_DB_NAME", "caio_homolog")
os.environ.setdefault("PLUGINS_DB_USER", "postgres")
os.environ.setdefault("PLUGINS_DB_PASSWORD", "caio_homolog")
# Production default (infra/docker-compose*.yml) — the legacy
# pedidos_venda_abertos.* source is not part of this isolated DB.
os.environ.setdefault("COMMERCIAL_PORTFOLIO_SOURCE", "commercial")
os.environ.setdefault("COMMERCIAL_AVATAR_UPLOAD_DIR", "/tmp/caio_homolog/avatars")
os.environ.setdefault("COMMERCIAL_USER_AVATAR_UPLOAD_DIR", "/tmp/caio_homolog/user_avatars")
os.environ.setdefault("COMMERCIAL_ATTACHMENT_UPLOAD_DIR", "/tmp/caio_homolog/attachments")

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)

from commercial_app.application.caio import proposal_store
from commercial_app.interface.mcp import semantic_bridge as sem
from commercial_app.interface.mcp import tool_bridge_parity as parity
from commercial_app.infrastructure.providers.database.plugins_postgres_connection import (
    acquire_plugins_connection,
    release_plugins_connection,
)


def _db_available() -> bool:
    try:
        conn = acquire_plugins_connection(timeout_seconds=2)
        release_plugins_connection()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _db_available(),
    reason="isolated plugins Postgres not available (E2 fixture)",
)


def _human(permissions=("commercial.access",), user_id="user-1", **over):
    data = {
        "id": user_id,
        "sub": user_id,
        "email": f"{user_id}@delpi.test",
        "name": f"User {user_id}",
        "principal_type": "user",
        "is_superadmin": False,
        "permissions": list(permissions),
        "access_token": "token-" + user_id,
    }
    data.update(over)
    return SimpleNamespace(**data)


ACCESS_USER = ("commercial.access", "commercial.read",
               "commercial.worklist", "commercial.followups")
MANAGE_USER = tuple(ACCESS_USER) + ("commercial.manage",)


def _act(user):
    set_current_user(user)
    set_request_authorization("Bearer " + user.access_token)


class _SmartGateway:
    """Recording fake for the api-delpi boundary.

    Owner use cases build gateway adapters at composition time; the
    fake keeps those adapters real while replacing only the HTTP hop.
    ``enrich_portfolio_customers`` echoes unblocked customers so
    eligibility checks behave like a healthy TOTVS."""

    def __init__(self, payload=None):
        self.calls = []
        self.payload = payload

    def enrich_portfolio_customers(self, payload=None, **_):
        self.calls.append(("enrich_portfolio_customers", payload))
        items = [
            {
                "customer_code": c.get("customer_code"),
                "customer_store": c.get("customer_store"),
                "blocked": "0",
            }
            for c in (payload or {}).get("customers", [])
            if isinstance(c, dict)
        ]
        return {"data": {"items": items}}

    def __getattr__(self, name):
        def _call(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            if self.payload is not None:
                return self.payload
            return {"data": {"items": []}}
        return _call


def _reset_composer_singletons():
    """Clear lazily-built composer singletons so patched builders re-run.

    Other test modules may have already instantiated use cases holding
    real gateways; every ``_*`` global in commercial_composer is a lazy
    cache (``= None`` pattern), so resetting them all is safe."""
    from commercial_app.composition import commercial_composer as comp

    for name in list(vars(comp)):
        if name.startswith("_") and not name.startswith("__"):
            value = getattr(comp, name)
            if value is not None and not callable(value):
                setattr(comp, name, None)


@pytest.fixture(scope="module", autouse=True)
def _fake_composer_gateway():
    _reset_composer_singletons()
    fake = _SmartGateway()
    # The Settings object may have been instantiated by an earlier
    # test module before this module's env defaults were applied —
    # pin the values the isolated environment requires.
    from commercial_app.config import settings as _settings

    _settings.COMMERCIAL_PORTFOLIO_SOURCE = "commercial"
    _settings.COMMERCIAL_AVATAR_UPLOAD_DIR = "/tmp/caio_homolog/avatars"
    _settings.COMMERCIAL_USER_AVATAR_UPLOAD_DIR = (
        "/tmp/caio_homolog/user_avatars"
    )
    _settings.COMMERCIAL_ATTACHMENT_UPLOAD_DIR = (
        "/tmp/caio_homolog/attachments"
    )
    _settings.PEDIDOS_VENDA_ABERTOS_AVATAR_UPLOAD_DIR = (
        "/tmp/caio_homolog/pva_avatars"
    )
    with patch(
        "commercial_app.composition.commercial_composer"
        ".build_delpi_commercial_gateway",
        lambda: fake,
    ), patch(
        "commercial_app.interface.mcp.tool_bridge_parity"
        ".build_delpi_commercial_gateway",
        lambda: fake,
    ), patch(
        "commercial_app.interface.mcp.tool_bridge"
        ".build_delpi_commercial_gateway",
        lambda: fake,
    ), patch(
        "commercial_app.interface.http.routes.seller_portfolio_routes"
        ".build_delpi_commercial_gateway",
        lambda: fake,
    ), patch(
        "commercial_app.infrastructure.gateways"
        ".delpi_customer_eligibility_adapter.DelpiCommercialGateway",
        return_value=fake,
    ), patch(
        "commercial_app.composition.commercial_composer"
        ".CoreApiPortalAccessPort",
        return_value=_FakePortalAccess(),
    ):
        yield
    _reset_composer_singletons()


class _FakePortalAccess:
    """Stub for the core-api Portal directory boundary.

    ``user_profile.update`` mirrors profile fields to the Portal via
    CoreApiPortalAccessPort; the isolated E2 environment has no
    reachable core-api, so the mirror hop is stubbed (boundary fake,
    owner use case still real)."""

    def has_commercial_portal_access_batch(self, user_ids):
        return {
            str(user_id): True
            for user_id in user_ids
            if str(user_id or "").strip()
        }

    def __getattr__(self, name):
        def _call(*args, **kwargs):
            if name == "configured":
                return True
            if name.startswith(("has_", "lookup_", "list_")):
                return {}
            if name.startswith("search_"):
                return []
            if name.startswith("get_"):
                return None
            return None
        return _call


@pytest.fixture(autouse=True)
def _ctx():
    clear_current_user()
    clear_request_authorization()
    proposal_store.reset_proposal_store_for_tests()
    yield
    proposal_store.reset_proposal_store_for_tests()
    clear_current_user()
    clear_request_authorization()


def _db(sql: str, params=()):
    conn = acquire_plugins_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()] if cur.description else []
        conn.commit()
        return rows
    finally:
        release_plugins_connection()


@pytest.fixture()
def seeded():
    """Clean commercial schema + canonical synthetic data."""
    tables = [
        "interaction_mentions", "interaction_reactions",
        "interaction_pins", "interaction_messages",
        "interaction_room_members", "interaction_rooms",
        "task_assignee_groups", "task_assignees", "task_customers",
        "tasks", "activities", "attachments", "account_contacts",
        "commercial_user_profiles",
        "commercial_group_members", "commercial_groups",
        "home_favorites", "sla_policies", "customer_avatars",
        "seller_customers",
        "seller_portfolio_members", "seller_portfolios",
        "integration_outbox", "integration_checkpoints",
        "audit_log",
    ]
    for table in tables:
        _db(f"TRUNCATE commercial.{table} CASCADE")
    pid = _db(
        "INSERT INTO commercial.seller_portfolios "
        "(user_id, display_name) VALUES (%s, %s) RETURNING id",
        ("user-1", "Carteira Homolog"),
    )[0]["id"]
    _db(
        "INSERT INTO commercial.seller_portfolio_members "
        "(seller_portfolio_id, user_id, role) VALUES (%s,%s,%s)",
        (str(pid), "user-1", "owner"),
    )
    _db(
        "INSERT INTO commercial.seller_portfolio_members "
        "(seller_portfolio_id, user_id, role) VALUES (%s,%s,%s)",
        (str(pid), "user-2", "member"),
    )
    for code in ("000001", "000002"):
        _db(
            "INSERT INTO commercial.seller_customers "
            "(seller_portfolio_id, customer_code, customer_store, "
            "customer_name) VALUES (%s,%s,%s,%s)",
            (str(pid), code, "01", f"Cliente {code}"),
        )
    return {"portfolio_id": str(pid)}


def _data(result):
    return result.structured_content["data"]


# --- portfolio (plugin DB — real integration) ---------------------------------------


def test_portfolio_me_member_sees_portfolio(seeded):
    _act(_human(ACCESS_USER))
    r = sem.tool_read(entity="portfolio", action="me")
    assert r.is_error is False, r.structured_content
    d = _data(r)
    text = str(d)
    assert seeded["portfolio_id"] in text or "Carteira Homolog" in text


def test_portfolio_me_no_membership_empty_scope(seeded):
    _act(_human(ACCESS_USER, user_id="user-9"))
    r = sem.tool_read(entity="portfolio", action="me")
    assert r.is_error is False
    assert seeded["portfolio_id"] not in str(_data(r))


def test_portfolio_list_and_get(seeded):
    _act(_human(MANAGE_USER))
    r = sem.tool_read(entity="portfolio", action="list")
    assert r.is_error is False
    assert "Carteira Homolog" in str(_data(r))
    g = sem.tool_read(
        entity="portfolio", action="get",
        ref=seeded["portfolio_id"],
    )
    assert g.is_error is False
    d = _data(g)
    assert seeded["portfolio_id"] == str(d.get("id"))
    assert "Carteira Homolog" in str(d)


def test_portfolio_lifecycle_create_update_audit(seeded):
    _act(_human(MANAGE_USER))
    r = sem.tool_execute(
        entity="portfolio", action="create",
        payload={
            "display_name": "Carteira Nova",
            "user_id": "user-5",
            "owner_user_id": "user-5",
        },
    )
    assert r.is_error is False, r.structured_content
    rows = _db(
        "SELECT id FROM commercial.seller_portfolios "
        "WHERE display_name = %s", ("Carteira Nova",)
    )
    assert rows
    new_id = str(rows[0]["id"])
    upd = sem.tool_execute(
        entity="portfolio", action="update",
        target_ref=new_id, payload={"display_name": "Carteira Renamed"},
    )
    assert upd.is_error is False, upd.structured_content
    assert _db(
        "SELECT display_name FROM commercial.seller_portfolios "
        "WHERE id = %s", (new_id,)
    )[0]["display_name"] == "Carteira Renamed"
    audit = sem.tool_read(
        entity="portfolio", action="audit", ref=new_id
    )
    assert audit.is_error is False
    assert "audit" in str(_data(audit)).lower() or _data(audit)


def test_portfolio_customer_add_remove_with_audit(seeded):
    _act(_human(MANAGE_USER))
    r = sem.tool_execute(
        entity="portfolio", action="customer_add",
        target_ref=seeded["portfolio_id"],
        payload={
            "customer_code": "000003",
            "customer_store": "01",
            "customer_name": "Cliente C",
        },
    )
    assert r.is_error is False, r.structured_content
    assert _db(
        "SELECT 1 FROM commercial.seller_customers "
        "WHERE customer_code='000003'"
    )
    rem = sem.tool_execute(
        entity="portfolio", action="customer_remove",
        target_ref=seeded["portfolio_id"],
        payload={"customer_code": "000003", "customer_store": "01"},
    )
    assert rem.is_error is False
    assert not _db(
        "SELECT 1 FROM commercial.seller_customers "
        "WHERE customer_code='000003'"
    )
    audit_rows = _db(
        "SELECT action FROM commercial.audit_log "
        "WHERE entity_id = %s", (seeded["portfolio_id"],)
    )
    assert audit_rows


def test_portfolio_member_add_remove(seeded):
    _act(_human(MANAGE_USER))
    r = sem.tool_execute(
        entity="portfolio", action="member_add",
        target_ref=seeded["portfolio_id"],
        payload={"user_id": "user-7", "role": "member"},
    )
    assert r.is_error is False, r.structured_content
    assert _db(
        "SELECT 1 FROM commercial.seller_portfolio_members "
        "WHERE user_id='user-7'"
    )
    rem = sem.tool_execute(
        entity="portfolio", action="member_remove",
        target_ref=seeded["portfolio_id"],
        payload={"user_id": "user-7"},
    )
    assert rem.is_error is False
    assert not _db(
        "SELECT 1 FROM commercial.seller_portfolio_members "
        "WHERE user_id='user-7'"
    )


def test_portfolio_transfer_real(seeded):
    _act(_human(MANAGE_USER))
    c = sem.tool_execute(
        entity="portfolio", action="create",
        payload={"display_name": "Carteira Destino",
                 "user_id": "user-6"},
    )
    assert c.is_error is False, c.structured_content
    target = str(_db(
        "SELECT id FROM commercial.seller_portfolios "
        "WHERE display_name='Carteira Destino'"
    )[0]["id"])
    r = sem.tool_execute(
        entity="portfolio", action="transfer",
        payload={
            "source_portfolio_id": seeded["portfolio_id"],
            "target_portfolio_id": target,
            "customers": [{"customer_code": "000002",
                           "customer_store": "01"}],
            "reason_note": "rebalanceamento de carteira",
        },
    )
    assert r.is_error is False, r.structured_content
    moved = _db(
        "SELECT seller_portfolio_id FROM commercial.seller_customers "
        "WHERE customer_code='000002'"
    )
    assert moved and str(moved[0]["seller_portfolio_id"]) == target


def test_portfolio_deactivate_real_delete_cycle(seeded):
    _act(_human(MANAGE_USER))
    prep = sem.tool_delete(
        entity="portfolio", action="deactivate",
        target_ref=seeded["portfolio_id"], phase="prepare",
    )
    assert prep.is_error is False, prep.structured_content
    ref = _data(prep)["proposal_ref"]
    commit = sem.tool_delete(
        entity="portfolio", action="deactivate",
        target_ref=seeded["portfolio_id"], phase="commit",
        proposal_ref=ref,
    )
    assert commit.is_error is False, commit.structured_content
    assert _db(
        "SELECT active FROM commercial.seller_portfolios "
        "WHERE id=%s", (seeded["portfolio_id"],)
    )[0]["active"] is False


def test_portfolio_purge_real_delete_cycle(seeded):
    _act(_human(MANAGE_USER))
    prep = sem.tool_delete(
        entity="portfolio", action="purge",
        target_ref=seeded["portfolio_id"], phase="prepare",
    )
    assert prep.is_error is False, prep.structured_content
    ref = _data(prep)["proposal_ref"]
    commit = sem.tool_delete(
        entity="portfolio", action="purge",
        target_ref=seeded["portfolio_id"], phase="commit",
        proposal_ref=ref,
    )
    assert commit.is_error is False, commit.structured_content
    assert not _db(
        "SELECT 1 FROM commercial.seller_portfolios WHERE id=%s",
        (seeded["portfolio_id"],),
    )


# --- worklist / tasks / activities ---------------------------------------------------


def _create_task(**over):
    payload = {"title": "Tarefa homolog", "task_type": "follow_up",
               "priority": "normal",
               "customer_code": "000001", "customer_store": "01"}
    payload.update(over)
    r = sem.tool_execute(entity="task", action="create",
                         payload=payload)
    assert r.is_error is False, r.structured_content
    rows = _db(
        "SELECT id FROM commercial.tasks ORDER BY created_at DESC "
        "LIMIT 1"
    )
    return str(rows[0]["id"])


def test_task_full_lifecycle(seeded):
    _act(_human(ACCESS_USER))
    task_id = _create_task()
    mine = sem.tool_read(entity="worklist", action="mine")
    assert mine.is_error is False
    assert task_id in str(_data(mine))
    upd = sem.tool_execute(
        entity="task", action="update", target_ref=task_id,
        payload={"title": "Tarefa renomeada"},
    )
    assert upd.is_error is False
    assert _db(
        "SELECT title FROM commercial.tasks WHERE id=%s",
        (task_id,),
    )[0]["title"] == "Tarefa renomeada"
    de = sem.tool_execute(
        entity="task", action="defer", target_ref=task_id,
        payload={"due_at": "2030-01-01"},
    )
    assert de.is_error is False, de.structured_content
    comp = sem.tool_execute(
        entity="task", action="complete", target_ref=task_id
    )
    assert comp.is_error is False, comp.structured_content
    done = sem.tool_read(entity="worklist", action="done")
    assert task_id in str(_data(done))


def test_task_reassign_requires_manager_and_scope(seeded):
    _act(_human(ACCESS_USER))
    task_id = _create_task()
    denied = sem.tool_execute(
        entity="task", action="reassign", target_ref=task_id,
        payload={"assignee_user_ids": ["user-2"]},
    )
    # Owner rule: only portfolio managers can reassign tasks.
    assert denied.is_error is True
    assert denied.structured_content["status_code"] == 403
    _act(_human(MANAGE_USER))
    re = sem.tool_execute(
        entity="task", action="reassign", target_ref=task_id,
        payload={"assignee_user_ids": ["user-2"]},
    )
    assert re.is_error is False, re.structured_content
    _act(_human(ACCESS_USER, user_id="user-9"))
    mine = sem.tool_read(entity="worklist", action="mine")
    assert task_id not in str(_data(mine))


def test_task_delete_real_cycle(seeded):
    _act(_human(ACCESS_USER))
    task_id = _create_task()
    prep = sem.tool_delete(
        entity="task", target_ref=task_id, phase="prepare"
    )
    assert prep.is_error is False, prep.structured_content
    ref = _data(prep)["proposal_ref"]
    commit = sem.tool_delete(
        entity="task", target_ref=task_id, phase="commit",
        proposal_ref=ref,
    )
    assert commit.is_error is False
    rows = _db("SELECT deleted_at FROM commercial.tasks WHERE id=%s",
               (task_id,))
    assert rows and (
        rows[0].get("deleted_at") is not None or not rows
    ) or not _db("SELECT 1 FROM commercial.tasks WHERE id=%s",
                 (task_id,))


def test_activity_create_and_list(seeded):
    _act(_human(ACCESS_USER))
    r = sem.tool_execute(
        entity="activity", action="create",
        payload={
            "activity_type": "call", "subject": "Ligação homolog",
            "customer_code": "000001", "customer_store": "01",
        },
    )
    assert r.is_error is False, r.structured_content
    lst = sem.tool_read(
        entity="activity", action="list",
        filters={"customer_code": "000001", "customer_store": "01"},
    )
    assert lst.is_error is False
    assert "Ligação homolog" in str(_data(lst))


# --- groups / sla / contacts / favorites / profile -------------------------------------


def test_group_lifecycle_and_real_delete(seeded):
    _act(_human(MANAGE_USER))
    r = sem.tool_execute(
        entity="group", action="create",
        payload={"name": "Grupo H", "user_ids": ["user-1"]},
    )
    assert r.is_error is False, r.structured_content
    gid = str(_db(
        "SELECT id FROM commercial.commercial_groups "
        "WHERE name='Grupo H'"
    )[0]["id"])
    assert sem.tool_read(
        entity="group", action="list"
    ).is_error is False
    g = sem.tool_read(entity="group", action="get", ref=gid)
    assert g.is_error is False
    rn = sem.tool_execute(
        entity="group", action="rename", target_ref=gid,
        payload={"name": "Grupo H2"},
    )
    assert rn.is_error is False
    mr = sem.tool_execute(
        entity="group", action="members_replace", target_ref=gid,
        payload={"user_ids": ["user-2"]},
    )
    assert mr.is_error is False, mr.structured_content
    assert not _db(
        "SELECT 1 FROM commercial.commercial_group_members "
        "WHERE user_id='user-1' AND group_id=%s", (gid,)
    )
    prep = sem.tool_delete(
        entity="group", target_ref=gid, phase="prepare"
    )
    assert prep.is_error is False
    commit = sem.tool_delete(
        entity="group", target_ref=gid, phase="commit",
        proposal_ref=_data(prep)["proposal_ref"],
    )
    assert commit.is_error is False
    assert not _db(
        "SELECT 1 FROM commercial.commercial_groups WHERE id=%s",
        (gid,),
    )


def test_sla_policy_lifecycle(seeded):
    _act(_human(MANAGE_USER))
    r = sem.tool_execute(
        entity="sla_policy", action="create",
        payload={"code": "SLA-H", "name": "SLA Homolog",
                 "appliesTo": "task", "durationHours": 24},
    )
    assert r.is_error is False, r.structured_content
    pid = str(_db(
        "SELECT id FROM commercial.sla_policies WHERE code='SLA-H'"
    )[0]["id"])
    lst = sem.tool_read(entity="sla_policy", action="list")
    assert lst.is_error is False and "SLA-H" in str(_data(lst))
    upd = sem.tool_execute(
        entity="sla_policy", action="update", target_ref=pid,
        payload={"name": "SLA Homolog v2"},
    )
    assert upd.is_error is False
    prep = sem.tool_delete(
        entity="sla_policy", action="deactivate",
        target_ref=pid, phase="prepare",
    )
    assert prep.is_error is False
    commit = sem.tool_delete(
        entity="sla_policy", action="deactivate",
        target_ref=pid, phase="commit",
        proposal_ref=_data(prep)["proposal_ref"],
    )
    assert commit.is_error is False


def test_contact_lifecycle_and_real_delete(seeded):
    _act(_human(MANAGE_USER))
    r = sem.tool_execute(
        entity="contact", action="create",
        payload={
            "customer_code": "000001", "customer_store": "01",
            "full_name": "Contato H", "channel": "email",
            "email": "c@h.test",
        },
    )
    assert r.is_error is False, r.structured_content
    cid = str(_db(
        "SELECT id FROM commercial.account_contacts "
        "WHERE full_name='Contato H'"
    )[0]["id"])
    upd = sem.tool_execute(
        entity="contact", action="update", target_ref=cid,
        payload={"customer_code": "000001", "customer_store": "01",
                 "full_name": "Contato H2"},
    )
    assert upd.is_error is False, upd.structured_content
    target = f"contact_id={cid}&customer_code=000001&customer_store=01"
    prep = sem.tool_delete(
        entity="contact", target_ref=target, phase="prepare"
    )
    assert prep.is_error is False, prep.structured_content
    commit = sem.tool_delete(
        entity="contact", target_ref=target, phase="commit",
        proposal_ref=_data(prep)["proposal_ref"],
    )
    assert commit.is_error is False, commit.structured_content
    assert _db(
        "SELECT deleted_at FROM commercial.account_contacts "
        "WHERE id=%s AND deleted_at IS NOT NULL",
        (cid,),
    )


def test_home_favorite_put_and_list(seeded):
    _act(_human(ACCESS_USER))
    r = sem.tool_execute(
        entity="home_favorite", action="put",
        payload={"items": [{"viewId": "open_orders"}]},
    )
    assert r.is_error is False, r.structured_content
    lst = sem.tool_read(entity="home_favorite", action="list")
    assert lst.is_error is False
    assert "open_orders" in str(_data(lst))


def test_user_profile_update_get(seeded):
    _act(_human(ACCESS_USER))
    r = sem.tool_execute(
        entity="user_profile", action="update",
        payload={"user_id": "user-1", "job_title": "Vendedor"},
    )
    assert r.is_error is False, r.structured_content
    g = sem.tool_read(
        entity="user_profile", action="get", ref="user-1"
    )
    assert g.is_error is False
    assert "Vendedor" in str(_data(g))


def test_team_roster(seeded):
    _act(_human(MANAGE_USER))
    r = sem.tool_read(entity="team", action="roster")
    assert r.is_error is False
    assert "user-1" in str(_data(r))


def test_attachment_list_empty(seeded):
    _act(_human(ACCESS_USER))
    task_id = _create_task()
    r = sem.tool_read(
        entity="attachment", action="list",
        filters={"owner_type": "task", "owner_id": task_id},
    )
    assert r.is_error is False
    assert _data(r)["items"] == [] or not _data(r).get("items")


def test_customer_center_assignments(seeded):
    # center_assignments resolves via the api-delpi analytics endpoint
    # (not the plugins DB) — the boundary fake records the call.
    _act(_human(ACCESS_USER))
    r = sem.tool_read(
        entity="customer", action="center_assignments",
        filters={"customers": [{"customer_code": "000001",
                               "customer_store": "01"}]},
    )
    assert r.is_error is False, r.structured_content


# --- interaction rooms / messages (real DB flow) --------------------------------------


def test_interaction_room_full_flow(seeded):
    _act(_human(ACCESS_USER))
    res = sem.tool_execute(
        entity="interaction_room", action="resolve",
        payload={"kind": "entity", "entity_type": "customer",
                 "entity_key": "000001:01"},
    )
    assert res.is_error is False, res.structured_content
    room_id = _room_id_from(res)
    assert room_id
    post = sem.tool_execute(
        entity="interaction_message", action="post",
        target_ref=room_id, payload={"body_text": "msg homolog"},
    )
    assert post.is_error is False, post.structured_content
    mid = _message_id_from(post)
    msgs = sem.tool_read(
        entity="interaction_room", action="messages",
        ref=room_id,
    )
    assert msgs.is_error is False
    assert "msg homolog" in str(_data(msgs))
    if mid:
        rx = sem.tool_execute(
            entity="interaction_message", action="reaction_set",
            payload={"room_id": room_id, "message_id": mid,
                     "code": "thumbs_up"},
        )
        assert rx.is_error is False, rx.structured_content
        pin = sem.tool_execute(
            entity="interaction_message", action="pin",
            payload={"room_id": room_id, "message_id": mid},
        )
        assert pin.is_error is False, pin.structured_content
        pins = sem.tool_read(
            entity="interaction_room", action="pins", ref=room_id
        )
        assert mid in str(_data(pins))
        sem.tool_execute(
            entity="interaction_message", action="unpin",
            payload={"room_id": room_id, "message_id": mid},
        )
        fm = sem.tool_execute(
            entity="task", action="from_message",
            payload={"room_id": room_id, "message_id": mid,
                     "description": "task-from-msg"},
        )
        assert fm.is_error is False, fm.structured_content
        mdel = sem.tool_delete(
            entity="interaction_message",
            target_ref=f"room_id={room_id}&message_id={mid}",
            phase="prepare",
        )
        assert mdel.is_error is False, mdel.structured_content
        mcommit = sem.tool_delete(
            entity="interaction_message",
            target_ref=f"room_id={room_id}&message_id={mid}",
            phase="commit",
            proposal_ref=_data(mdel)["proposal_ref"],
        )
        assert mcommit.is_error is False, mcommit.structured_content
    sem.tool_execute(
        entity="interaction_room", action="mark_read",
        target_ref=room_id,
    )
    lst = sem.tool_read(entity="interaction_room", action="list")
    assert lst.is_error is False
    _act(_human(MANAGE_USER))
    prep = sem.tool_delete(
        entity="interaction_room", target_ref=room_id,
        phase="prepare",
    )
    assert prep.is_error is False, prep.structured_content
    commit = sem.tool_delete(
        entity="interaction_room", target_ref=room_id,
        phase="commit",
        proposal_ref=_data(prep)["proposal_ref"],
    )
    assert commit.is_error is False, commit.structured_content


def _room_id_from(result):
    d = _data(result)
    for key in ("room_id", "id"):
        if isinstance(d, dict) and d.get(key):
            return str(d[key])
    rows = _db(
        "SELECT id FROM commercial.interaction_rooms "
        "ORDER BY created_at DESC LIMIT 1"
    )
    return str(rows[0]["id"]) if rows else None


def _message_id_from(result):
    d = _data(result)
    for key in ("message_id", "id"):
        if isinstance(d, dict) and d.get(key):
            return str(d[key])
    rows = _db(
        "SELECT id FROM commercial.interaction_messages "
        "ORDER BY created_at DESC LIMIT 1"
    )
    return str(rows[0]["id"]) if rows else None


# --- gateway boundary passthrough (api-delpi/TOTVS ops) --------------------------------
# Owner services/TOTVS are not part of this isolated DB. A recording
# fake gateway proves the adapter resolves scope and calls the
# official downstream path with the forwarded params — real evidence
# up to the integration boundary, honestly marked as such.


class _FakeGateway:
    def __init__(self, payload=None):
        self.calls = []
        self.payload = payload if payload is not None else {
            "data": {"items": []}
        }

    def __getattr__(self, name):
        def _call(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return self.payload
        return _call


GATEWAY_READS = {
    "customer.search": {"q": "cliente"},
    "customer.enrichment": {
        "customers": [{"customer_code": "000001",
                       "customer_store": "01"}],
    },
    "customer.open_orders": {"customer_code": "000001",
                             "customer_store": "01"},
    "customer.outbound_invoices": {"customer_code": "000001",
                                   "customer_store": "01"},
    "customer.contacts": {"customer_code": "000001",
                          "customer_store": "01"},
    "customer_center.list": {},
    "open_order.list": {},
    "open_order.recently_closed": {},
    "open_order.open_ops": {},
    "production.appointments": {"op": "123"},
}


@pytest.mark.parametrize("cap", sorted(GATEWAY_READS))
def test_read_reaches_official_gateway(cap, seeded):
    entity, action = cap.split(".", 1)
    fake = _FakeGateway()
    _act(_human(MANAGE_USER + ("commercial.analytics",
                               "commercial.proposals.view")))
    with patch(
        "commercial_app.interface.mcp.tool_bridge_parity"
        ".build_delpi_commercial_gateway", return_value=fake
    ), patch(
        "commercial_app.interface.mcp.tool_bridge"
        ".build_delpi_commercial_gateway", return_value=fake
    ):
        r = sem.tool_read(entity=entity, action=action,
                          filters=GATEWAY_READS[cap])
    assert fake.calls, f"{cap}: adapter never reached the gateway"
    assert r.is_error is False, (cap, r.structured_content)


def test_proposal_detail_forwards_upstream_contract(seeded):
    """issue CAIO-2 F1.1 — upstream /proposals/{n} requires ``branch``
    and accepts ``revision``; the adapter must forward both."""
    fake = _FakeGateway({"data": {"proposal": "ok"}})
    _act(_human(MANAGE_USER + ("commercial.analytics",
                               "commercial.proposals.view")))
    with patch.object(
        parity, "build_delpi_commercial_gateway",
        return_value=fake,
    ):
        r = sem.tool_read(
            entity="proposal", action="analytics_get",
            ref="000123",
            filters={"branch": "01", "revision": "2"},
        )
    assert r.is_error is False, r.structured_content
    assert fake.calls
    name, args, kwargs = fake.calls[0]
    assert name == "get_commercial_analytics"
    assert args[0] == "/proposals/000123"
    sent = kwargs.get("params") or {}
    assert sent.get("branch") == "01"
    assert sent.get("revision") == "2"


def test_proposal_history_forwards_period_and_revision(seeded):
    fake = _FakeGateway({"data": {"items": []}})
    _act(_human(MANAGE_USER + ("commercial.analytics",
                               "commercial.proposals.view")))
    with patch.object(
        parity, "build_delpi_commercial_gateway",
        return_value=fake,
    ):
        r = sem.tool_read(
            entity="proposal", action="history_events",
            ref="000123",
            filters={
                "branch": "02",
                "revision": "1",
                "start_date": "2026-01-01",
                "end_date": "2026-10-30",
            },
        )
    assert r.is_error is False, r.structured_content
    name, args, kwargs = fake.calls[0]
    assert name == "get_commercial_analytics"
    assert args[0] == "/proposals/000123/history/events"
    sent = kwargs.get("params") or {}
    assert sent.get("branch") == "02"
    assert sent.get("revision") == "1"
    assert sent.get("start_date") == "2026-01-01"
    assert sent.get("end_date") == "2026-10-30"


def test_proposal_detail_without_branch_is_validation(seeded):
    fake = _FakeGateway()
    _act(_human(MANAGE_USER + ("commercial.analytics",
                               "commercial.proposals.view")))
    with patch.object(
        parity, "build_delpi_commercial_gateway",
        return_value=fake,
    ):
        for action in ("analytics_get", "history_events"):
            r = sem.tool_read(
                entity="proposal", action=action, ref="000123"
            )
            assert r.is_error is True
            payload = r.structured_content
            assert payload["status_code"] == 400
            assert payload["error_code"] == "validation"
            assert "branch" in payload["data"]["missing_fields"]
    assert not fake.calls


def test_proposal_investigation_multistep_chain(seeded):
    """Multi-step scenario (F3): analytics_list → analytics_get →
    history_events → get(document_url) — the ChatGPT investigation
    flow, scoped and authorized."""
    fake = _FakeGateway({"data": {"items": [], "proposal": "ok"}})
    _act(_human(MANAGE_USER + ("commercial.analytics",
                               "commercial.proposals.view")))
    with patch.object(
        parity, "build_delpi_commercial_gateway",
        return_value=fake,
    ):
        r1 = sem.tool_read(entity="proposal", action="analytics_list",
                           filters={"branch": "01"})
        r2 = sem.tool_read(entity="proposal", action="analytics_get",
                           ref="000123",
                           filters={"branch": "01", "revision": "2"})
        r3 = sem.tool_read(entity="proposal", action="history_events",
                           ref="000123",
                           filters={"branch": "01"})
        r4 = sem.tool_read(entity="proposal", action="get",
                           ref="INT-1")
    for r in (r1, r2, r3, r4):
        assert r.is_error is False, r.structured_content
    paths = [c[1][0] if c[1] else "" for c in fake.calls]
    assert "/proposals" in paths or any(
        p.startswith("/proposals") for p in paths
    )
    assert any(p == "/proposals/000123" for p in paths)
    assert any(
        p == "/proposals/000123/history/events" for p in paths
    )
    doc = r4.structured_content["data"]
    assert doc.get("document_url") == "/proposal-documents/INT-1/pdf"


def test_entity_preview_requires_ref_object(seeded):
    _act(_human(MANAGE_USER))
    r = sem.tool_read(
        entity="interaction_room", action="entity_preview",
        filters={"kind": "customer"},
    )
    assert r.is_error is True
    payload = r.structured_content
    assert payload["status_code"] == 400
    assert payload["error_code"] == "validation"
    assert "ref" in payload["data"]["missing_fields"]


def test_analyze_all_reach_owner_path(seeded):
    from commercial_app.interface.mcp.tool_bridge_parity import (
        ANALYZE_PROXY_MAP,
    )
    fake = _FakeGateway({"data": {"value": 1}})
    _act(_human(MANAGE_USER + ("commercial.analytics",
                               "commercial.portfolio_billing_share")))
    failures = []
    for kind, (path, _, required) in ANALYZE_PROXY_MAP.items():
        params = {}
        for field in required:
            if field == "granularity":
                params[field] = "month"
            elif field in ("start_date", "end_date"):
                params[field] = "2026-10-01" if "start" in field \
                    else "2026-10-30"
            else:
                params[field] = "v"
        with patch.object(
            parity, "build_delpi_commercial_gateway",
            return_value=fake,
        ):
            fake.calls.clear()
            r = sem.tool_analyze(analysis_type=kind,
                                 parameters=params)
        if r.is_error or not fake.calls:
            failures.append((kind, r.structured_content))
            continue
        name, args, kwargs = fake.calls[0]
        if name != "get_commercial_analytics" or (
            args and args[0] != path
        ):
            failures.append((kind, fake.calls))
    assert failures == [], failures


def test_analyze_scope_params_forwarded(seeded):
    from commercial_app.interface.mcp import tool_bridge as bridge_mod

    fake = _FakeGateway({"data": {"value": 1}})
    _act(_human(MANAGE_USER + ("commercial.analytics",)))
    with patch.object(
        parity, "build_delpi_commercial_gateway",
        return_value=fake,
    ), patch.object(
        bridge_mod, "build_delpi_commercial_gateway",
        return_value=fake,
    ):
        r = sem.tool_analyze(
            analysis_type="rol.summary",
            parameters={"start_date": "2026-10-01",
                        "end_date": "2026-10-30",
                        "portfolio_id": seeded["portfolio_id"]},
        )
    assert fake.calls, r.structured_content
    name, args, kwargs = fake.calls[0]
    assert name == "get_commercial_analytics"
    sent = kwargs.get("params") or (args[1] if len(args) > 1 else {})
    assert sent.get("start_date") == "2026-10-01"
    assert sent.get("end_date") == "2026-10-30"
