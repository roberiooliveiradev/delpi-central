"""G1-API: CRUD e RBAC testados com um repositorio em memoria."""

from datetime import datetime, timezone

import pytest

from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.workstations import format_workstation_code
from it_portal_app.interface.http.dependencies import get_workstation_repository
from it_portal_app.main import app


class InMemoryWorkstationRepository:
    def __init__(self):
        self.items = {}
        self.events = []
        self.next_seq = 1

    def _unique(self, fields, except_id=None):
        for row in self.items.values():
            if row["id"] == except_id or row["archived"]:
                continue
            if row["unit_code"] == fields.unit_code and row["hostname"] == fields.hostname:
                raise ConflictError("workstation_identity_conflict", "Hostname ja cadastrado.")

    def _audit(self, audit, actor):
        self.events.append({
            "id": audit.entity_id,
            "entity_type": audit.entity_type,
            "entity_id": audit.entity_id,
            "event_type": audit.event_type,
            "changes": audit.changes,
            "actor_name": actor.name,
            "occurred_at": datetime.now(timezone.utc),
        })

    def list_workstations(self, query):
        rows = list(self.items.values())
        if query.archived == "active":
            rows = [r for r in rows if not r["archived"]]
        if query.archived == "archived":
            rows = [r for r in rows if r["archived"]]
        for col in ("unit_code", "device_kind", "administrative_status"):
            value = getattr(query, col)
            if value:
                rows = [r for r in rows if r[col] == value]
        if query.q:
            q = query.q.lower()
            rows = [r for r in rows if any(q in str(r.get(k) or "").lower()
                    for k in ("name", "hostname", "department", "ip_address"))]
        rows.sort(
            key=lambda r: (r[query.sort].lower() if isinstance(r[query.sort], str)
                           else r[query.sort], r["code"]),
            reverse=query.direction == "desc",
        )
        return rows[(query.page - 1) * query.page_size:query.page * query.page_size], len(rows)

    def get_workstation(self, workstation_id):
        return dict(self.items[workstation_id]) if workstation_id in self.items else None

    def insert_workstation(self, workstation_id, fields, actor, audit):
        self._unique(fields)
        now = datetime.now(timezone.utc)
        row = {
            **fields.as_dict(), "id": workstation_id,
            "code": format_workstation_code(self.next_seq),
            "revision": 1, "archived": False,
            "archived_at": None, "archived_by_name": None,
            "created_at": now, "created_by_name": actor.name,
            "updated_at": now, "updated_by_name": actor.name,
        }
        self.next_seq += 1
        self.items[workstation_id] = row
        self._audit(audit, actor)
        return dict(row)

    def update_workstation(self, workstation_id, fields, expected_revision, actor, audit):
        row = self.items.get(workstation_id)
        if not row or row["archived"] or row["revision"] != expected_revision:
            return None
        self._unique(fields, except_id=workstation_id)
        row.update(fields.as_dict())
        row.update(revision=expected_revision + 1, updated_by_name=actor.name)
        self._audit(audit, actor)
        return dict(row)

    def set_workstation_archived(self, workstation_id, archived, expected_revision, actor, audit):
        row = self.items.get(workstation_id)
        if not row or row["archived"] == archived or row["revision"] != expected_revision:
            return None
        if not archived:
            class Fields:
                hostname = row["hostname"]
                unit_code = row["unit_code"]
            self._unique(Fields, except_id=workstation_id)
        row.update(
            revision=expected_revision + 1, archived=archived,
            archived_at=datetime.now(timezone.utc) if archived else None,
            archived_by_name=actor.name if archived else None,
            updated_by_name=actor.name,
        )
        self._audit(audit, actor)
        return dict(row)

    def list_history(self, workstation_id, limit):
        return [e for e in reversed(self.events) if e["entity_id"] == workstation_id][:limit]


@pytest.fixture
def workstation_client(client):
    repo = InMemoryWorkstationRepository()
    app.dependency_overrides[get_workstation_repository] = lambda: repo
    yield client, repo
    app.dependency_overrides.pop(get_workstation_repository, None)


def payload(**overrides):
    data = {
        "name": "PC Engenharia", "hostname": "pc-eng-001.delpi.local",
        "ip_address": "192.0.2.10", "unit_code": "01", "device_kind": "desktop",
        "department": "Engenharia", "location": "Predio principal", "responsible": "TI",
        "operating_system": "Windows 11", "administrative_status": "in_operation",
        "description": "Estacao corporativa de teste",
    }
    data.update(overrides)
    return data


def create(client, **overrides):
    return client.post("/workstations", json=payload(**overrides))


def test_crud_history_and_revision(workstation_client):
    client, repo = workstation_client
    response = create(client, hostname="PC-ENG-001.DELPI.LOCAL")
    assert response.status_code == 201, response.text
    created = response.json()["data"]
    assert created["code"] == "PC-0001"
    assert created["hostname"] == "pc-eng-001.delpi.local"
    assert client.get(f"/workstations/{created['id']}").status_code == 200
    updated = client.put(
        f"/workstations/{created['id']}", json={**payload(name="PC revisado"), "revision": 1}
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["revision"] == 2
    assert client.put(
        f"/workstations/{created['id']}", json={**payload(name="Stale"), "revision": 1}
    ).status_code == 409
    archived = client.post(f"/workstations/{created['id']}/archive", json={"revision": 2})
    assert archived.status_code == 200
    assert archived.json()["data"]["archived"] is True
    assert client.get("/workstations").json()["data"]["total"] == 0
    assert client.get("/workstations?archived=archived").json()["data"]["total"] == 1
    assert client.put(
        f"/workstations/{created['id']}", json={**payload(), "revision": 3}
    ).status_code == 409
    restored = client.post(f"/workstations/{created['id']}/restore", json={"revision": 3})
    assert restored.status_code == 200
    assert restored.json()["data"]["revision"] == 4
    history = client.get(f"/workstations/{created['id']}/history").json()["data"]
    assert [e["event_type"] for e in history] == [
        "workstation_restored", "workstation_archived", "workstation_updated", "workstation_created"
    ]
    assert len(repo.events) == 4


def test_unique_by_unit_and_active_hostname(workstation_client):
    client, _ = workstation_client
    original = create(client).json()["data"]
    assert create(client, hostname="PC-ENG-001.DELPI.LOCAL").status_code == 409
    assert create(client, unit_code="02").status_code == 201
    assert client.post(f"/workstations/{original['id']}/archive", json={"revision": 1}).status_code == 200
    assert create(client).status_code == 201
    assert client.post(f"/workstations/{original['id']}/restore", json={"revision": 2}).status_code == 409


def test_filters_search_and_pagination(workstation_client):
    client, _ = workstation_client
    assert create(client).status_code == 201
    assert create(
        client, hostname="pc-pcp-002", unit_code="02", device_kind="notebook",
        name="PC PCP", department="PCP",
    ).status_code == 201
    assert client.get("/workstations?unit_code=02&device_kind=notebook").json()["data"]["total"] == 1
    assert client.get("/workstations?q=pcp").json()["data"]["total"] == 1
    paged = client.get("/workstations?sort=name&page_size=1&page=2")
    assert paged.status_code == 200
    assert paged.json()["data"]["page"] == 2
    assert paged.json()["data"]["total"] == 2
    assert client.get("/workstations?unit_code=XX").status_code == 422
    assert client.get("/workstations?sort=invalid").status_code == 422


def test_permission_is_independent_of_server_roles(workstation_client, principal):
    client, repo = workstation_client
    principal.permissions = ["it-portal.access", "it-portal.servers.view",
                             "it-portal.servers.manage"]
    assert client.get("/workstations").status_code == 403
    assert create(client).status_code == 403
    assert len(repo.items) == 0
    principal.permissions = ["it-portal.access", "it-portal.computers.manage"]
    assert create(client).status_code == 403
    principal.permissions += ["it-portal.computers.view"]
    assert create(client).status_code == 201


def test_revoked_permission_and_core_outage_fail_closed(workstation_client, principal):
    client, repo = workstation_client
    principal.fresh_permissions = ["it-portal.access", "it-portal.computers.view"]
    assert create(client).status_code == 403
    assert repo.items == {}
    principal.fresh_permissions = None
    principal.fresh_unavailable = True
    assert create(client).status_code == 503
    assert repo.items == {}


def test_rejects_secrets_and_unknown_fields(workstation_client):
    client, repo = workstation_client
    response = create(client, description="senha: secretvalue123")
    assert response.status_code == 422
    assert response.json()["data"]["error"]["code"] == "secret_not_allowed"
    assert create(client, ip_address="bad-ip").status_code == 422
    assert client.post("/workstations", json={**payload(), "remote_access_enabled": True}).status_code == 422
    assert repo.items == {}


def test_capabilities_use_independent_permissions(workstation_client, principal):
    client, _ = workstation_client
    principal.permissions = ["it-portal.access", "it-portal.computers.view"]
    data = client.get("/me/capabilities").json()["data"]
    assert data["can_view_computers"] is True
    assert data["can_manage_computers"] is False
    principal.permissions.append("it-portal.computers.manage")
    data = client.get("/me/capabilities").json()["data"]
    assert data["can_manage_computers"] is True
