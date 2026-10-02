"""Use-case tests for SpecialistInterop — C3-MCP-INTEROP-01.

Proves the first fail-closed boundary: catalog projection projects the
specialist-owned surface with owner-typed classes (UNKNOWN when absent)
and marks every name not invocable under current DÉLIA policy as
blocked; invocation re-reads the owner class from a fresh tools/list
and enforces the governance bindings before tools/call.
"""

from __future__ import annotations

import pytest

from app.application.specialist_interop.contracts import (
    RemoteToolDescriptor,
    RemoteToolOutcome,
    SpecialistCatalogRequest,
    SpecialistInvocationRequest,
)
from app.application.specialist_interop.errors import (
    CAPABILITY_NOT_ALLOWED_IN_PHASE,
    UNKNOWN_CAPABILITY,
    UNKNOWN_SPECIALIST,
    WRITE_CAPABILITY_BLOCKED,
    SpecialistInteropError,
)
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.domain.evidence.model import EpistemicClass
from app.domain.specialist_interop.model import SpecialistOperationClass


TEO_REMOTE_TOOLS = (
    RemoteToolDescriptor(
        remote_name="get_catalog",
        description="catalog",
        operation_class="DISCOVERY",
    ),
    RemoteToolDescriptor(
        remote_name="get_record", description="read", operation_class="READ"
    ),
    RemoteToolDescriptor(
        remote_name="prepare_record_change",
        description="prepare",
        operation_class="PREPARE",
    ),
    RemoteToolDescriptor(
        remote_name="commit_proposal", description="act", operation_class="ACT"
    ),
    RemoteToolDescriptor(remote_name="undocumented_tool", description="?"),
)


class FakePort:
    adapter_kind = "MCP_FAKE"

    def __init__(self, tools=(), outcome=None):
        self._tools = tuple(tools)
        self._outcome = outcome or RemoteToolOutcome(content_text="{}")
        self.listed_for: list[str] = []
        self.calls: list[tuple] = []

    def list_remote_tools(self, specialist, *, timeout_seconds):
        self.listed_for.append(specialist.specialist_id)
        return self._tools

    def call_remote_tool(
        self, specialist, remote_name, arguments, *, correlation_id,
        timeout_seconds,
    ):
        self.calls.append((specialist.specialist_id, remote_name, arguments))
        return self._outcome


def _interop(tools=(), outcome=None):
    return SpecialistInterop(FakePort(tools=tools, outcome=outcome))


def _by_name(result):
    return {c.remote_name: c for c in result.capabilities}


def test_davi_catalog_projects_owner_surface():
    interop = _interop(
        tools=(
            RemoteToolDescriptor(
                remote_name="discover_delpi_information",
                operation_class="DISCOVERY",
            ),
            RemoteToolDescriptor(
                remote_name="execute_delpi_information",
                operation_class="READ",
            ),
        )
    )
    result = interop.discover_catalog(
        SpecialistCatalogRequest(specialist_id="davi", correlation_id="c1")
    )
    # Full owner surface is projected — discovery != invocation.
    assert [c.remote_name for c in result.capabilities] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    assert (
        _by_name(result)["execute_delpi_information"].operation_class
        is SpecialistOperationClass.READ
    )
    # Class gate only — DISCOVERY and READ are both invocable now
    # (specialist-owned availability, §6.118); nothing is blocked here.
    assert result.blocked_remote_names == ()
    assert result.specialist.owner_ref == "api-delpi"


def test_teo_catalog_blocks_reads_prepare_act_and_unknown():
    interop = _interop(tools=TEO_REMOTE_TOOLS)
    result = interop.discover_catalog(
        SpecialistCatalogRequest(specialist_id="teo", correlation_id="c2")
    )
    projected = _by_name(result)
    assert (
        projected["get_catalog"].operation_class
        is SpecialistOperationClass.DISCOVERY
    )
    assert (
        projected["undocumented_tool"].operation_class
        is SpecialistOperationClass.UNKNOWN
    )
    assert set(result.blocked_remote_names) == {
        "prepare_record_change",
        "commit_proposal",
        "undocumented_tool",
    }
    assert "get_catalog" not in result.blocked_remote_names
    assert "get_record" not in result.blocked_remote_names


def test_vista_catalog_blocks_writes_not_reads():
    interop = _interop(
        tools=(
            RemoteToolDescriptor(
                remote_name="get_catalog", operation_class="DISCOVERY"
            ),
            RemoteToolDescriptor(
                remote_name="prepare_change", operation_class="PREPARE"
            ),
            RemoteToolDescriptor(
                remote_name="commit_proposal", operation_class="ACT"
            ),
            RemoteToolDescriptor(
                remote_name="list_playlists", operation_class="READ"
            ),
        )
    )
    result = interop.discover_catalog(
        SpecialistCatalogRequest(specialist_id="vista", correlation_id="c3")
    )
    assert "prepare_change" in result.blocked_remote_names
    assert "commit_proposal" in result.blocked_remote_names
    assert "list_playlists" not in result.blocked_remote_names
    assert "get_catalog" not in result.blocked_remote_names


def test_remote_metadata_cannot_elevate_approval():
    """Discovery != approval (R1B §15/16): remote annotations, descriptions
    and additive schema metadata never change governance — a tool whose
    owner class is PREPARE/ACT stays blocked even when it advertises
    itself as readOnly/safe, and cannot be invoked."""
    interop = _interop(
        tools=(
            RemoteToolDescriptor(
                remote_name="forged_safe_tool",
                title="Read only",
                description="safe read-only lookup",
                input_schema={"type": "object", "properties": {}},
                annotations={"readOnlyHint": True, "title": "safe"},
            ),
            RemoteToolDescriptor(
                remote_name="commit_proposal",
                description="harmless preview",
                annotations={"readOnlyHint": True},
                operation_class="ACT",
            ),
            RemoteToolDescriptor(
                remote_name="get_catalog",
                description="changed description",
                input_schema={"type": "object", "additional": True},
                annotations={"readOnlyHint": True},
                operation_class="DISCOVERY",
            ),
        )
    )
    result = interop.discover_catalog(
        SpecialistCatalogRequest(specialist_id="teo", correlation_id="c5")
    )
    assert set(result.blocked_remote_names) == {
        "forged_safe_tool",
        "commit_proposal",
    }
    assert "get_catalog" not in result.blocked_remote_names
    for name in ("forged_safe_tool", "commit_proposal"):
        with pytest.raises(SpecialistInteropError) as exc:
            interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id="teo",
                    remote_capability=name,
                    correlation_id="c5",
                    arguments={},
                )
            )
        assert exc.value.code in (
            CAPABILITY_NOT_ALLOWED_IN_PHASE,
            WRITE_CAPABILITY_BLOCKED,
        )


def test_catalog_unknown_specialist_rejected():
    interop = _interop()
    with pytest.raises(SpecialistInteropError) as exc:
        interop.discover_catalog(
            SpecialistCatalogRequest(
                specialist_id="unknown-mcp", correlation_id="c4"
            )
        )
    assert exc.value.code == UNKNOWN_SPECIALIST


def test_invoke_discovery_succeeds_and_is_observation():
    interop = _interop(
        tools=(
            RemoteToolDescriptor(
                remote_name="discover_delpi_information",
                operation_class="DISCOVERY",
            ),
        ),
        outcome=RemoteToolOutcome(
            content_text='{"candidates": []}', structured={"ok": True}
        ),
    )
    outcome = interop.invoke(
        SpecialistInvocationRequest(
            specialist_id="davi",
            remote_capability="discover_delpi_information",
            correlation_id="corr-9",
            arguments={"query": "informacao de produto por codigo"},
        )
    )
    assert outcome.epistemic_class is EpistemicClass.OBSERVATION
    assert outcome.provenance.specialist_id == "davi"
    assert outcome.provenance.correlation_id == "corr-9"
    assert outcome.is_complete is True


def test_invoke_discovery_is_class_gated_not_name_bound():
    """ARCH-DRIFT-MCP-CAPABILITY-AUTHORITY-02: any owner-typed
    DISCOVERY capability on an approved specialist is invocable — the
    per-name binding table is superseded."""
    interop = _interop(
        tools=(
            RemoteToolDescriptor(
                remote_name="get_catalog", operation_class="DISCOVERY"
            ),
            RemoteToolDescriptor(
                remote_name="discover_v2", operation_class="DISCOVERY"
            ),
        ),
        outcome=RemoteToolOutcome(content_text="{}"),
    )
    for name in ("get_catalog", "discover_v2"):
        outcome = interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="teo",
                remote_capability=name,
                correlation_id="c",
            )
        )
        assert outcome.provenance.remote_name == name


def test_invoke_read_capabilities_invocable_on_all_specialists():
    """READ class is invocable for every approved specialist without a
    per-tool tuple or env flag (§6.118)."""
    interop = _interop(
        tools=(
            RemoteToolDescriptor(
                remote_name="execute_delpi_information",
                operation_class="READ",
            ),
            RemoteToolDescriptor(
                remote_name="get_record", operation_class="READ"
            ),
            RemoteToolDescriptor(
                remote_name="list_playlists", operation_class="READ"
            ),
        ),
        outcome=RemoteToolOutcome(content_text="{}"),
    )
    for specialist_id, name in (
        ("davi", "execute_delpi_information"),
        ("teo", "get_record"),
        ("vista", "list_playlists"),
    ):
        outcome = interop.invoke(
            SpecialistInvocationRequest(
                specialist_id=specialist_id,
                remote_capability=name,
                correlation_id="c",
            )
        )
        assert outcome.provenance.remote_name == name


def test_invoke_read_class_invocable_without_tuple():
    """READ-class capabilities are invocable on approval — no
    per-tuple gate remains (§6.118)."""
    interop = _interop(
        tools=(
            RemoteToolDescriptor(
                remote_name="execute_delpi_information",
                operation_class="READ",
            ),
        ),
        outcome=RemoteToolOutcome(content_text='{"ok": true}'),
    )
    outcome = interop.invoke(
        SpecialistInvocationRequest(
            specialist_id="davi",
            remote_capability="execute_delpi_information",
            correlation_id="c",
            arguments={"candidate_token": "t", "arguments": {}},
        )
    )
    assert outcome.provenance.remote_name == "execute_delpi_information"


def test_invoke_prepare_and_act_rejected():
    interop = _interop(
        tools=(
            RemoteToolDescriptor(
                remote_name="prepare_record_change",
                operation_class="PREPARE",
            ),
            RemoteToolDescriptor(
                remote_name="commit_proposal", operation_class="ACT"
            ),
            RemoteToolDescriptor(
                remote_name="prepare_change", operation_class="PREPARE"
            ),
        )
    )
    for specialist_id, name in (
        ("teo", "prepare_record_change"),
        ("teo", "commit_proposal"),
        ("vista", "prepare_change"),
        ("vista", "commit_proposal"),
    ):
        with pytest.raises(SpecialistInteropError) as exc:
            interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id=specialist_id,
                    remote_capability=name,
                    correlation_id="c",
                )
            )
        assert exc.value.code == WRITE_CAPABILITY_BLOCKED


def test_invoke_unknown_capability_and_specialist_rejected():
    interop = _interop(
        tools=(
            RemoteToolDescriptor(
                remote_name="execute_delpi_information",
                operation_class="READ",
            ),
        )
    )
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="davi",
                remote_capability="commit_proposal",
                correlation_id="c",
            )
        )
    assert exc.value.code == UNKNOWN_CAPABILITY
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="rogue", remote_capability="x", correlation_id="c"
            )
        )
    assert exc.value.code == UNKNOWN_SPECIALIST


def test_invoke_unclassifiable_capability_not_invocable():
    """Advertised but owner-untyped -> UNKNOWN -> discoverable, not
    invocable (no stale mirror may rescue it)."""
    interop = _interop(
        tools=(RemoteToolDescriptor(remote_name="mystery_tool"),)
    )
    catalog = interop.discover_catalog(
        SpecialistCatalogRequest(specialist_id="teo", correlation_id="c")
    )
    assert [c.remote_name for c in catalog.capabilities] == ["mystery_tool"]
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="teo",
                remote_capability="mystery_tool",
                correlation_id="c",
            )
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED_IN_PHASE


def test_invoke_arguments_bounded():
    interop = _interop(
        tools=(
            RemoteToolDescriptor(
                remote_name="discover_delpi_information",
                operation_class="DISCOVERY",
            ),
        )
    )
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="davi",
                remote_capability="discover_delpi_information",
                correlation_id="c",
                arguments={"query": "x" * 5000},
            )
        )
    assert exc.value.code == "mcp_invalid_response"


def test_request_contracts_carry_no_context_or_credentials():
    from dataclasses import fields

    request_fields = {
        f.name for f in fields(SpecialistInvocationRequest)
    } | {f.name for f in fields(SpecialistCatalogRequest)}
    for leaked in (
        "history",
        "prior_turns",
        "instruction",
        "token",
        "credential",
        "conversation",
        "system_prompt",
        "authorization",
    ):
        assert not any(leaked in name for name in request_fields)


def test_remote_error_is_truthful_failure():
    interop = _interop(
        tools=(
            RemoteToolDescriptor(
                remote_name="discover_delpi_information",
                operation_class="DISCOVERY",
            ),
        ),
        outcome=RemoteToolOutcome(content_text="denied", is_error=True),
    )
    with pytest.raises(SpecialistInteropError):
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="davi",
                remote_capability="discover_delpi_information",
                correlation_id="c",
                arguments={"query": "x"},
            )
        )
