"""TÉO canonical write-execution policy — contract tests.

TEO-CANONICAL-WRITE-EXECUTION-POLICY-04:

- NON_DESTRUCTIVE WRITE = ``auto_act`` (execute directly after governed
  PREPARE; user request is the intent — no extra confirmation round-trip).
- DESTRUCTIVE WRITE = ``confirm_before_act`` (ONE explicit confirmation
  before ACT).
- The policy is classified per capability in
  ``application/governed_writes/confirmation_policy.py`` — never inferred
  from verbs and never duplicated per transport.
- ``commit_now`` is only the GPT Actions transport mechanism implementing
  ``auto_act``; MCP PREPARE stays pure and ``commit_proposal`` is the ACT
  path on both surfaces.
- AUTO_ACT does not bypass AuthZ, validation, proposal integrity, audit,
  read-back or verification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.governed_writes.confirmation_policy import (
    AUTO_ACT,
    CONFIRM_BEFORE_ACT,
    allows_commit_now_for_capability,
    classified_write_capabilities,
    confirmation_kind_for_entity_operation,
    confirmation_kind_for_workflow,
    execution_policy_for_capability,
    execution_policy_for_entity_operation,
    execution_policy_for_workflow,
    requires_user_confirmation,
)
from tm_app.application.governed_writes.errors import (
    FORBIDDEN,
    GovernedWriteError,
)
from tm_app.application.governed_writes.orchestrator import (
    WRITE_CAPABILITIES,
)
from tm_app.application.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from tm_app.application.gpt_actions.capability_descriptors import (
    build_capability_surface_catalog,
)
from tm_app.application.gpt_actions.governed_actions_facade import (
    GovernedActionsFacade,
)
from tm_app.domain.entities.process_document import ProcessDocument


@pytest.fixture(autouse=True)
def _reset_proposals():
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()


def _user(uid="u1", permissions=None):
    return SimpleNamespace(
        id=uid,
        email=f"{uid}@example.com",
        name="User",
        permissions=permissions or ["transformometro.access"],
        roles=[],
        groups=[],
        is_superadmin=False,
    )


def _request(uid="u1", permissions=None):
    req = MagicMock()
    req.state.user = _user(uid, permissions)
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


# ---------------------------------------------------------------------------
# A. Canonical classification table
# ---------------------------------------------------------------------------

EXPECTED_CAPABILITY_POLICY = {
    "create_record": AUTO_ACT,
    "update_record": AUTO_ACT,
    "duplicate_record": AUTO_ACT,
    "delete_record": CONFIRM_BEFORE_ACT,
    "commit_improvement_package": CONFIRM_BEFORE_ACT,
    "adjust_shared_resource_cost": AUTO_ACT,
    "activate_revision": CONFIRM_BEFORE_ACT,
    "recalculate_dashboard": CONFIRM_BEFORE_ACT,
    "meeting_minute_workflow": CONFIRM_BEFORE_ACT,
    "manage_evidence": CONFIRM_BEFORE_ACT,
    "meeting_minute_manage": CONFIRM_BEFORE_ACT,
    "create_diagnostic": AUTO_ACT,
    "manage_diagnostic": CONFIRM_BEFORE_ACT,
}


def test_every_exposed_write_capability_is_classified():
    """No production material-write capability may be unclassified."""
    exposed = set(WRITE_CAPABILITIES)
    classified = set(classified_write_capabilities())
    missing = exposed - classified
    assert not missing, f"unclassified write capabilities: {missing}"
    for cap in exposed:
        assert execution_policy_for_capability(cap) in (AUTO_ACT, CONFIRM_BEFORE_ACT)


def test_capability_classification_values():
    for cap, expected in EXPECTED_CAPABILITY_POLICY.items():
        assert execution_policy_for_capability(cap) == expected, cap


def test_entity_operation_classification():
    assert execution_policy_for_entity_operation("create") == AUTO_ACT
    assert execution_policy_for_entity_operation("update") == AUTO_ACT
    assert execution_policy_for_entity_operation("duplicate") == AUTO_ACT
    assert execution_policy_for_entity_operation("delete") == CONFIRM_BEFORE_ACT


def test_unknown_capability_fails_closed_to_confirm():
    assert execution_policy_for_capability("never_heard_of") == CONFIRM_BEFORE_ACT
    assert execution_policy_for_entity_operation("transmogrify") == CONFIRM_BEFORE_ACT
    assert execution_policy_for_workflow("not_a_workflow") == CONFIRM_BEFORE_ACT
    assert requires_user_confirmation("never_heard_of") is True
    assert allows_commit_now_for_capability("never_heard_of") is False


# ---------------------------------------------------------------------------
# B. Proposals carry the canonical policy
# ---------------------------------------------------------------------------

def _prepare(facade, request, entity, operation, changes=None, record_id=None):
    with (
        patch.object(facade._dispatch, "_require_capability"),
        patch(
            "tm_app.interface.http.branch_access_http."
            "require_transformometro_view_access",
            return_value=None,
        ),
        patch.object(
            facade._dispatch,
            "get_record",
            return_value=_doc().to_dict(),
        ),
    ):
        return facade.prepare_record_change(
            request,
            entity=entity,
            operation=operation,
            changes=changes or {},
            record_id=record_id,
        )


def test_prepare_seals_auto_act_policy_on_create():
    facade = GovernedActionsFacade()
    prepared = _prepare(
        facade,
        _request(),
        "process_document",
        "create",
        changes={"processo_id": "p1", "title": "x", "content_md": "#"},
    )
    prop = prepared["proposal"]
    assert prop["execution_policy"] == "auto_act"
    assert prop["confirmation_requirement"]["explicit_user_confirmation"] is False
    assert prepared["persisted"] is False


def test_prepare_seals_confirm_policy_on_delete():
    facade = GovernedActionsFacade()
    prepared = _prepare(
        facade,
        _request(),
        "process_document",
        "delete",
        record_id="doc-1",
    )
    prop = prepared["proposal"]
    assert prop["execution_policy"] == "confirm_before_act"
    assert prop["confirmation_requirement"]["explicit_user_confirmation"] is True
    assert prepared["persisted"] is False


# ---------------------------------------------------------------------------
# C. Actions transport: commit_now implements auto_act only
# ---------------------------------------------------------------------------

def test_actions_commit_now_executes_auto_act_capability():
    facade = GovernedActionsFacade()
    req = _request()
    created = _doc()
    with (
        patch.object(facade._dispatch, "_require_capability"),
        patch(
            "tm_app.interface.http.branch_access_http."
            "require_transformometro_view_access",
            return_value=None,
        ),
        patch.object(
            facade._dispatch,
            "create_record",
            return_value=(created.to_dict(), "ok", 201),
        ),
        patch.object(
            facade._dispatch,
            "get_record",
            return_value=created.to_dict(),
        ),
    ):
        result = facade.prepare_record_change(
            req,
            entity="process_document",
            operation="create",
            changes={"processo_id": "p1", "title": "x", "content_md": "#"},
            commit_now=True,
            confirmation=True,
            idempotency_key="idem-1",
        )
    assert result.get("persisted") is True
    assert result.get("postcondition", {}).get("verified") is True


def test_actions_commit_now_ignored_for_confirm_before_act_capability():
    facade = GovernedActionsFacade()
    req = _request()
    with (
        patch.object(facade._dispatch, "_require_capability"),
        patch(
            "tm_app.interface.http.branch_access_http."
            "require_transformometro_view_access",
            return_value=None,
        ),
        patch.object(
            facade._dispatch,
            "get_record",
            return_value=_doc().to_dict(),
        ),
        patch.object(facade._dispatch, "delete_record") as deleter,
    ):
        prepared = facade.prepare_record_change(
            req,
            entity="process_document",
            operation="delete",
            record_id="doc-1",
            commit_now=True,
            confirmation=True,
            idempotency_key="idem-del",
        )
    # Destructive proposals must NOT auto-execute even if the caller passes
    # commit_now=true — the canonical policy ignores the mechanism.
    deleter.assert_not_called()
    assert prepared["persisted"] is False
    assert prepared["proposal"]["execution_policy"] == "confirm_before_act"


def test_actions_commit_now_for_package_no_longer_atomic():
    """commit_improvement_package reclassified CONFIRM_BEFORE_ACT.

    The compound write can supersede the active scenario and recalculate
    materialized state — the additive ``commit_now`` mechanism no longer
    applies to it.
    """
    assert (
        execution_policy_for_capability("commit_improvement_package")
        == CONFIRM_BEFORE_ACT
    )
    assert allows_commit_now_for_capability("commit_improvement_package") is False


def test_commit_auto_act_proposal_accepts_confirmation_false():
    """AUTO_ACT: user request is the intent — no confirmation required."""
    facade = GovernedActionsFacade()
    req = _request()
    created = _doc()
    prepared = _prepare(
        facade,
        req,
        "process_document",
        "create",
        changes={"processo_id": "p1", "title": "x", "content_md": "#"},
    )
    handle = prepared["proposal"]["handle"]
    with (
        patch.object(
            facade._dispatch,
            "create_record",
            return_value=(created.to_dict(), "ok", 201),
        ),
        patch.object(
            facade._dispatch,
            "get_record",
            return_value=created.to_dict(),
        ),
    ):
        committed = facade.commit_proposal(
            req, proposal_handle=handle, confirmation=False
        )
    assert committed["status"] == "ok"
    assert committed["postcondition"]["verified"] is True


def test_commit_confirm_before_act_proposal_requires_confirmation():
    facade = GovernedActionsFacade()
    req = _request()
    prepared = _prepare(
        facade, req, "process_document", "delete", record_id="doc-1"
    )
    handle = prepared["proposal"]["handle"]
    with pytest.raises(GovernedWriteError) as exc:
        facade.commit_proposal(req, proposal_handle=handle, confirmation=False)
    assert exc.value.data.get("error_code") == "CONFIRMATION_REQUIRED"


# ---------------------------------------------------------------------------
# D. AUTO_ACT is not an authorization bypass
# ---------------------------------------------------------------------------

def test_auto_act_does_not_bypass_authz():
    """AUTO_ACT still re-runs backend authorization inside ACT.

    Prepare succeeds while AuthZ is open; the capability check is then
    revoked at commit time — dispatch enforces it inside create_record
    itself, so the write never reaches the backend.
    """
    facade = GovernedActionsFacade()
    req = _request()
    prepared = _prepare(
        facade,
        req,
        "process_document",
        "create",
        changes={"processo_id": "p1", "title": "x", "content_md": "#"},
    )
    handle = prepared["proposal"]["handle"]
    with (
        patch.object(
            facade._dispatch,
            "_require_capability",
            side_effect=GovernedWriteError(
                "forbidden", code=FORBIDDEN, status_code=403
            ),
        ),
        pytest.raises(GovernedWriteError) as exc,
    ):
        facade.commit_proposal(req, proposal_handle=handle, confirmation=False)
    assert exc.value.code == FORBIDDEN


# ---------------------------------------------------------------------------
# E. Catalog / intelligence projection
# ---------------------------------------------------------------------------

def test_catalog_exposes_execution_policy_both_transports():
    for transport in ("gpt_actions", "mcp"):
        catalog = build_capability_surface_catalog(transport)
        entity = next(
            e for e in catalog["entities"] if "create" in e.get("write_operations", ())
        )
        assert entity["execution_policy"]["create"] == "auto_act"
        assert entity["execution_policy"]["delete"] == "confirm_before_act"
        assert "auto_act" in catalog["proposal_model"]["write_execution_policy"]
        workflows = {w["id"]: w for w in catalog["workflows"]}
        assert workflows["activate_revision"]["execution_policy"] == "confirm_before_act"
        assert workflows["activate_revision"]["confirmation_requirement"] is True
        assert (
            workflows["adjust_shared_resource_cost"]["execution_policy"]
            == "auto_act"
        )
        assert (
            workflows["adjust_shared_resource_cost"]["confirmation_requirement"]
            is False
        )


def test_mcp_catalog_never_leaks_commit_now():
    import json

    catalog = build_capability_surface_catalog("mcp")
    blob = json.dumps(catalog, ensure_ascii=False)
    assert "commit_now" not in blob
    assert "gpt_" not in blob


def test_one_change_policy_flip_updates_all_surfaces():
    """Flipping ONE canonical classification must propagate everywhere."""
    flipped = {"activate_revision": "auto_act"}
    assert (
        execution_policy_for_workflow("activate_revision", policies=flipped)
        == "auto_act"
    )
    # Same canonical source drives entity op checks and commit-now compat.
    flipped_ops = {"create": "confirm_before_act"}
    assert (
        execution_policy_for_entity_operation("create", policies=flipped_ops)
        == "confirm_before_act"
    )
    # Kind renderers consume the same policy — no second registry needed.
    assert confirmation_kind_for_entity_operation("create") == "auto_act"
    assert confirmation_kind_for_workflow("activate_revision") == "confirm_before_act"


def test_policy_is_transport_independent():
    """The same capability resolves identically for Actions and MCP."""
    for cap in classified_write_capabilities():
        policy = execution_policy_for_capability(cap)
        assert policy in (AUTO_ACT, CONFIRM_BEFORE_ACT)
        # compat helpers agree with the canonical classification
        assert allows_commit_now_for_capability(cap) == (policy == AUTO_ACT)
