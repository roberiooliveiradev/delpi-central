"""GPT Actions V2 — prepare_record_change + commit_proposal surface."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.governed_writes.errors import (
    PROPOSAL_ACTOR_MISMATCH,
    PROPOSAL_STALE,
    GovernedWriteError,
)
from tm_app.application.governed_writes.proposal_store import reset_proposal_store_for_tests
from tm_app.application.gpt_actions.governed_actions_facade import GovernedActionsFacade
from tm_app.application.gpt_actions.openapi_builder import (
    GPT_ACTIONS_LEGACY_OPERATION_IDS,
    GPT_ACTIONS_OPERATION_IDS,
    build_gpt_actions_openapi,
    count_operations,
)
from tm_app.domain.entities.process_document import ProcessDocument


@pytest.fixture(autouse=True)
def _reset_proposals():
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()


def _user(uid="u1"):
    return SimpleNamespace(
        id=uid,
        email=f"{uid}@example.com",
        name="User",
        permissions=["transformometro.access"],
        roles=[],
        groups=[],
        is_superadmin=False,
    )


def _request(uid="u1"):
    req = MagicMock()
    req.state.user = _user(uid)
    return req


def _doc(**overrides) -> ProcessDocument:
    now = datetime.now(timezone.utc)
    base = dict(
        id="doc-1",
        processo_id="proc-1",
        title="AS-IS",
        content_md="# hi",
        created_by_user_id="u1",
        updated_by_user_id="u1",
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return ProcessDocument(**base)


def test_builder_surface_budget_reduced_and_no_legacy_crud():
    doc = build_gpt_actions_openapi()
    assert count_operations(doc) == len(GPT_ACTIONS_OPERATION_IDS) == 18
    assert count_operations(doc) <= 30
    found = []
    for methods in doc["paths"].values():
        for method, op in methods.items():
            if method.lower() in {"get", "post", "put", "patch", "delete"}:
                found.append(op["operationId"])
    assert "gpt_prepare_record_change" in found
    assert "gpt_commit_proposal" in found
    for legacy in GPT_ACTIONS_LEGACY_OPERATION_IDS:
        assert legacy not in found
    blob = str(doc)
    assert "gpt_call_any_route" not in blob
    assert "gpt_run_sql" not in blob
    assert "gpt_http_proxy" not in blob


def test_prepare_rejects_server_owned_fields():
    facade = GovernedActionsFacade()
    with pytest.raises(GovernedWriteError) as exc:
        facade.prepare_record_change(
            _request(),
            entity="process_document",
            operation="create",
            changes={
                "processo_id": "proc-1",
                "title": "x",
                "created_by_user_id": "evil",
            },
        )
    assert exc.value.data.get("error_code") == "INVALID_FIELD"


def test_prepare_create_process_document_no_write_then_commit():
    facade = GovernedActionsFacade()
    req = _request()
    created = _doc()

    with (
        patch.object(facade._dispatch, "_require_capability"),
        patch(
            "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
            return_value=None,
        ),
    ):
        prepared = facade.prepare_record_change(
            req,
            entity="process_document",
            operation="create",
            changes={
                "processo_id": "proc-1",
                "title": "AS-IS",
                "content_md": "# hi",
            },
        )
    assert prepared["status"] == "proposal_ready"
    handle = prepared["proposal"]["handle"]
    assert handle

    with (
        patch.object(
            facade._dispatch,
            "create_record",
            return_value=(created.to_dict(), "ok", 201),
        ) as creator,
        patch.object(
            facade._dispatch,
            "get_record",
            return_value=created.to_dict(),
        ),
    ):
        committed = facade.commit_proposal(
            req, proposal_handle=handle, confirmation=True
        )
    creator.assert_called_once()
    assert committed["status"] == "ok"
    assert committed["postcondition"]["verified"] is True


def test_commit_requires_confirmation():
    facade = GovernedActionsFacade()
    with pytest.raises(GovernedWriteError) as exc:
        facade.commit_proposal(
            _request(), proposal_handle="x.y", confirmation=False
        )
    assert exc.value.data.get("error_code") == "CONFIRMATION_REQUIRED"


def test_wrong_user_cannot_commit():
    facade = GovernedActionsFacade()
    with (
        patch(
            "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
            return_value=None,
        ),
        patch.object(facade._dispatch, "_require_capability"),
    ):
        prepared = facade.prepare_record_change(
            _request("u1"),
            entity="process_document",
            operation="create",
            changes={"processo_id": "proc-1", "title": "A"},
        )
    handle = prepared["proposal"]["handle"]
    with pytest.raises(GovernedWriteError) as exc:
        facade.commit_proposal(
            _request("u2"), proposal_handle=handle, confirmation=True
        )
    assert exc.value.code == PROPOSAL_ACTOR_MISMATCH


def test_capability_surface_in_catalog_payload_shape():
    from tm_app.application.gpt_actions.capability_descriptors import (
        build_capability_surface_catalog,
    )

    surface = build_capability_surface_catalog()
    assert surface["surface_version"] == "teo-gpt-actions-v2"
    assert any(e["id"] == "process_document" for e in surface["entities"])
    assert surface["proposal_model"]["commit_operation"] == "gpt_commit_proposal"
    assert "tm_task" in surface["not_exposed_by_design"]


def test_search_rejects_disallowed_filter(tm_client):
    response = tm_client.get(
        "/transformometro/gpt-actions/v1/records/branch",
        params={"q": "nope"},
    )
    assert response.status_code == 400
    assert response.json()["success"] is False
