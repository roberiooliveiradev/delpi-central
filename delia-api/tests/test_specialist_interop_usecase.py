"""Use-case tests for SpecialistInterop — C3-MCP-INTEROP-01.

Proves the first fail-closed boundary: catalog projection exposes only
DISCOVERY-class capabilities, everything else is recorded as blocked;
invocation enforces the registry + phase gate before any wire activity.
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
    RemoteToolDescriptor(remote_name="get_catalog", description="catalog"),
    RemoteToolDescriptor(remote_name="get_record", description="read"),
    RemoteToolDescriptor(
        remote_name="prepare_record_change", description="prepare"
    ),
    RemoteToolDescriptor(remote_name="commit_proposal", description="act"),
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


def test_davi_catalog_projects_only_discovery():
    interop = _interop(
        tools=(
            RemoteToolDescriptor(remote_name="discover_delpi_information"),
            RemoteToolDescriptor(remote_name="execute_delpi_information"),
        )
    )
    result = interop.discover_catalog(
        SpecialistCatalogRequest(specialist_id="davi", correlation_id="c1")
    )
    assert [c.remote_name for c in result.capabilities] == [
        "discover_delpi_information"
    ]
    assert result.blocked_remote_names == ("execute_delpi_information",)
    assert result.specialist.owner_ref == "api-delpi"


def test_teo_catalog_blocks_reads_prepare_act_and_unknown():
    interop = _interop(tools=TEO_REMOTE_TOOLS)
    result = interop.discover_catalog(
        SpecialistCatalogRequest(specialist_id="teo", correlation_id="c2")
    )
    assert [c.remote_name for c in result.capabilities] == ["get_catalog"]
    assert set(result.blocked_remote_names) == {
        "get_record",
        "prepare_record_change",
        "commit_proposal",
        "undocumented_tool",
    }


def test_vista_catalog_blocks_writes_and_reads():
    interop = _interop(
        tools=(
            RemoteToolDescriptor(remote_name="get_catalog"),
            RemoteToolDescriptor(remote_name="prepare_change"),
            RemoteToolDescriptor(remote_name="commit_proposal"),
            RemoteToolDescriptor(remote_name="list_playlists"),
        )
    )
    result = interop.discover_catalog(
        SpecialistCatalogRequest(specialist_id="vista", correlation_id="c3")
    )
    assert [c.remote_name for c in result.capabilities] == ["get_catalog"]
    assert "prepare_change" in result.blocked_remote_names
    assert "commit_proposal" in result.blocked_remote_names
    assert "list_playlists" in result.blocked_remote_names


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
        outcome=RemoteToolOutcome(
            content_text='{"candidates": []}', structured={"ok": True}
        )
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


def test_invoke_read_capability_phase_gated():
    interop = _interop()
    for specialist_id, name in (
        ("davi", "execute_delpi_information"),
        ("teo", "get_record"),
        ("vista", "list_playlists"),
    ):
        with pytest.raises(SpecialistInteropError) as exc:
            interop.invoke(
                SpecialistInvocationRequest(
                    specialist_id=specialist_id,
                    remote_capability=name,
                    correlation_id="c",
                )
            )
        assert exc.value.code == CAPABILITY_NOT_ALLOWED_IN_PHASE


def test_invoke_prepare_and_act_rejected():
    interop = _interop()
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
    interop = _interop()
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


def test_invoke_arguments_bounded():
    interop = _interop()
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
        outcome=RemoteToolOutcome(content_text="denied", is_error=True)
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
