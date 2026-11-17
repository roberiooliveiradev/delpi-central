"""W013-ACT — get_context(action="schema") serves governed write schemas.

The READ action catalog does not contain write capabilities; the schema
endpoint must still answer for the 14 approved governed writes so the
model can construct valid PREPARE arguments instead of failing closed
on guessed keys. The schemas are descriptive: enforcement stays in the
capability stacks (closed vocabularies).
"""

from __future__ import annotations

import pytest

from app.application.external_capabilities.dynamic_information.context_service import (
    davi_get_context,
)
from app.application.external_capabilities.governed_writes.arg_schemas import (
    WRITE_CAPABILITY_ARG_SCHEMAS,
    get_write_capability_schema,
)
from app.application.external_capabilities.governed_writes.orchestrator import (
    WRITE_CAPABILITIES,
)
from app.application.external_capabilities.governed_writes.si_admin_capabilities import (
    SI_ADMIN_WRITE_CAPABILITIES,
)
from app.application.external_capabilities.governed_writes.si_goal_capabilities import (
    SI_GOAL_WRITE_CAPABILITIES,
)


def test_schema_covers_every_approved_write_capability() -> None:
    assert set(WRITE_CAPABILITY_ARG_SCHEMAS) == set(WRITE_CAPABILITIES)
    assert len(WRITE_CAPABILITY_ARG_SCHEMAS) == 16


def test_schema_endpoint_serves_write_capability() -> None:
    out = davi_get_context(action="schema", capability="si.department.update")
    cap = out["capability"]
    assert out["action"] == "schema" and cap["available"] is True
    assert cap["davi_status"] == "GOVERNED_WRITE"
    assert "confirm_before_act" in cap["confirmation"]
    props = cap["argument_schema"]["properties"]
    assert "department_id" in props and "new_department_id" in props
    assert cap["required_arguments"] == ["department_id"]
    assert cap["argument_schema"]["additionalProperties"] is False


def test_schema_endpoint_serves_all_14_caps() -> None:
    for cap_id in sorted(WRITE_CAPABILITIES):
        out = davi_get_context(action="schema", capability=cap_id)
        assert out["capability"]["available"] is True, cap_id
        assert out["capability"]["argument_schema"]["properties"]


def test_schema_endpoint_unknown_capability_still_unknown() -> None:
    out = davi_get_context(action="schema", capability="si.department.delete")
    assert out["capability"]["available"] is False
    assert out["capability"]["davi_status"] == "UNKNOWN"
    out = davi_get_context(action="schema", capability="si.indicator.delete")
    assert out["capability"]["available"] is False
    out = davi_get_context(action="schema", capability="si.goal.delete")
    assert out["capability"]["available"] is False
    out = davi_get_context(action="schema", capability="http.post")
    assert out["capability"]["available"] is False


def test_read_capability_schema_unchanged() -> None:
    out = davi_get_context(action="schema", capability="list_si_admin_departments")
    cap = out["capability"]
    assert cap["available"] is True
    assert cap["davi_status"] != "GOVERNED_WRITE"


def test_get_write_capability_schema_rejects_non_write() -> None:
    assert get_write_capability_schema("si.department.delete") is None
    assert get_write_capability_schema("list_si_admin_departments") is None
    assert get_write_capability_schema("si.config.import") is None


def test_schema_key_sets_match_closed_vocabularies() -> None:
    """Drift guard: every published argument must be in the stack's
    closed vocabulary (and required args must exist)."""
    from app.application.external_capabilities.governed_writes import (
        si_admin_capabilities as admin,
        si_goal_capabilities as goals,
    )

    vocab = {
        "si.goal.create": goals._CREATE_ARGS,
        "si.goal.update": goals._UPDATE_ARGS,
        "si.goal.activate": goals._GOAL_REF_ARGS,
        "si.goal.deactivate": goals._GOAL_REF_ARGS,
        "si.department.create": admin._DEPT_CREATE_ARGS,
        "si.department.update": admin._DEPT_UPDATE_ARGS,
        "si.department.activate": admin._DEPT_REF_ARGS,
        "si.department.deactivate": admin._DEPT_REF_ARGS,
        "si.settings.update": admin._SETTINGS_UPDATE_ARGS,
        "si.indicator.create": admin._IND_CREATE_ARGS,
        "si.indicator.update": admin._IND_UPDATE_ARGS,
        "si.indicator.activate": admin._IND_REF_ARGS,
        "si.indicator.deactivate": admin._IND_REF_ARGS,
        "si.change_request.create": admin._CR_CREATE_ARGS,
        "si.change_request.comment": admin._CR_COMMENT_ARGS,
        "si.change_request.submit": admin._CR_REF_ARGS,
    }
    for cap_id, allowed in vocab.items():
        props = set(WRITE_CAPABILITY_ARG_SCHEMAS[cap_id]["properties"])
        missing = props - set(allowed)
        assert not missing, f"{cap_id}: schema publishes args outside vocabulary: {missing}"
        required = WRITE_CAPABILITY_ARG_SCHEMAS[cap_id]["required"]
        assert set(required) <= props, f"{cap_id}: required not in properties"
