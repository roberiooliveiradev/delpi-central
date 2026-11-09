"""Final closure: MCP eligibility before resume outcome replay.

Doc 293 §2A.12 residual — stored READ outcomes must not bypass Core
approval revalidation on investigation resume.
"""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Iterator
from unittest.mock import MagicMock

import pytest

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    CapabilityProviderError,
    ProviderCapability,
)
from app.application.capability_provision.governed_capability_orchestrator import (
    OperationalCapabilityOrchestrator,
)
from app.application.capability_provision.semantic_capability_support import (
    _AttemptCheckpoint,
    _CANCEL_CHECK,
    _RESUME_STATE,
    _TurnCancelled,
    _resume_invoke_key,
)
from app.application.interaction.turn_budget import (
    TurnBudgetExhausted,
    TurnDeadline,
)
from app.application.ports.mcp_provider_eligibility_port import (
    McpProviderEligibilityError,
)
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)


def _mcp_group(
    *,
    group_id: str = "davi",
    remote_name: str = "execute_delpi_information",
    operation_class: SpecialistOperationClass = SpecialistOperationClass.READ,
) -> CapabilityGroup:
    return CapabilityGroup(
        provider_id="mcp",
        group_id=group_id,
        owner_ref="api-delpi",
        display_name=group_id.upper(),
        capabilities=(
            ProviderCapability(
                capability_id=f"{group_id}.{remote_name}",
                group_id=group_id,
                provider_id="mcp",
                remote_name=remote_name,
                owner="api-delpi",
                operation_class=operation_class,
                description="x",
                input_schema={"type": "object"},
                binding={
                    "specialist_id": group_id,
                    "remote_name": remote_name,
                },
            ),
        ),
        source=SourceRef(
            source_id="api-delpi",
            source_system="api-delpi",
            provider_name=group_id.upper(),
        ),
    )


def _non_mcp_group() -> CapabilityGroup:
    return CapabilityGroup(
        provider_id="http",
        group_id="internal-ops",
        owner_ref="ops",
        display_name="OPS",
        capabilities=(
            ProviderCapability(
                capability_id="internal-ops.read",
                group_id="internal-ops",
                provider_id="http",
                remote_name="read",
                owner="ops",
                operation_class=SpecialistOperationClass.READ,
                description="x",
                input_schema={"type": "object"},
                binding={"remote_name": "read"},
            ),
        ),
        source=SourceRef(
            source_id="ops",
            source_system="ops",
            provider_name="OPS",
        ),
    )


def _stored_outcome(group_id: str = "davi", remote_name: str = "execute_delpi_information") -> SpecialistOutcome:
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id=group_id,
            remote_name=remote_name,
            protocol=InteropProtocol.MCP,
            correlation_id="corr-stored",
            observed_at="2026-11-09T12:00:00Z",
        ),
        content_text="stored-read-evidence",
    )


@contextmanager
def _resume_checkpoint(
    outcomes: dict[str, SpecialistOutcome],
) -> Iterator[_AttemptCheckpoint]:
    checkpoint = _AttemptCheckpoint(invoke_outcomes=dict(outcomes))
    token = _RESUME_STATE.set(checkpoint)
    try:
        yield checkpoint
    finally:
        _RESUME_STATE.reset(token)


class _TrackingEligibility:
    def __init__(self, *, allow: set[str] | None = None, error: McpProviderEligibilityError | None = None):
        self.allow = allow
        self.error = error
        self.calls: list[str] = []

    def require_eligible(self, provider_ref: str) -> None:
        self.calls.append(provider_ref)
        if self.error is not None:
            raise self.error
        if self.allow is not None and provider_ref not in self.allow:
            raise McpProviderEligibilityError(
                "mcp_provider_not_eligible",
                f"{provider_ref} not eligible",
            )


class _WireProv:
    provider_id = "mcp"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def list_groups(self, **_kwargs):
        raise AssertionError("list_groups unused")

    def invoke(self, capability, arguments, **_kwargs):
        self.calls.append(capability.remote_name)
        raise AssertionError("wire must not run on blocked/replay paths")


def _orch(eligibility, providers=None):
    return OperationalCapabilityOrchestrator(
        providers or [_WireProv()],
        orchestration_instructions={"x": "y"},
        mcp_provider_eligibility=eligibility,
    )


def test_a_revoked_provider_blocks_resume_replay_without_wire():
    group = _mcp_group()
    stored = _stored_outcome()
    key = _resume_invoke_key(group.group_id, "execute_delpi_information", {})
    eligibility = _TrackingEligibility(
        error=McpProviderEligibilityError(
            "mcp_provider_not_eligible", "revoked"
        )
    )
    wire = _WireProv()
    orch = _orch(eligibility, [wire])
    with _resume_checkpoint({key: stored}):
        with pytest.raises(CapabilityProviderError) as exc:
            orch._invoke(group, "execute_delpi_information", {}, "c-a")
    assert exc.value.code == "mcp_provider_not_eligible"
    assert eligibility.calls == ["davi"]
    assert wire.calls == []


def test_b_disabled_provider_blocks_resume_replay():
    # Same typed denial path as revoke — Core eligible projection omits it.
    group = _mcp_group()
    stored = _stored_outcome()
    key = _resume_invoke_key(group.group_id, "execute_delpi_information", {})
    eligibility = _TrackingEligibility(allow=set())  # disabled/missing
    with _resume_checkpoint({key: stored}):
        with pytest.raises(CapabilityProviderError) as exc:
            _orch(eligibility)._invoke(
                group, "execute_delpi_information", {}, "c-b"
            )
    assert exc.value.code == "mcp_provider_not_eligible"


def test_c_core_unavailable_fail_closed_no_stored_fallback():
    group = _mcp_group()
    stored = _stored_outcome()
    key = _resume_invoke_key(group.group_id, "execute_delpi_information", {})
    eligibility = _TrackingEligibility(
        error=McpProviderEligibilityError(
            "mcp_provider_registry_unavailable", "core down"
        )
    )
    wire = _WireProv()
    with _resume_checkpoint({key: stored}):
        with pytest.raises(CapabilityProviderError) as exc:
            _orch(eligibility, [wire])._invoke(
                group, "execute_delpi_information", {}, "c-c"
            )
    assert exc.value.code == "mcp_provider_registry_unavailable"
    assert wire.calls == []


def test_d_approved_provider_replays_without_second_wire_call():
    group = _mcp_group()
    stored = _stored_outcome()
    key = _resume_invoke_key(group.group_id, "execute_delpi_information", {})
    eligibility = _TrackingEligibility(allow={"davi"})
    wire = _WireProv()
    orch = _orch(eligibility, [wire])
    with _resume_checkpoint({key: stored}):
        outcome = orch._invoke(
            group, "execute_delpi_information", {}, "c-d"
        )
    assert outcome is stored
    assert outcome.content_text == "stored-read-evidence"
    assert eligibility.calls == ["davi"]
    assert wire.calls == []


def test_e_multi_owner_isolation_teo_unaffected_by_davi_revoke():
    davi = _mcp_group(group_id="davi")
    teo = _mcp_group(
        group_id="teo",
        remote_name="analyze",
    )
    davi_stored = _stored_outcome("davi")
    teo_stored = _stored_outcome("teo", "analyze")
    davi_key = _resume_invoke_key("davi", "execute_delpi_information", {})
    teo_key = _resume_invoke_key("teo", "analyze", {})
    eligibility = _TrackingEligibility(allow={"teo"})  # davi revoked
    wire = _WireProv()
    orch = _orch(eligibility, [wire])
    with _resume_checkpoint({davi_key: davi_stored, teo_key: teo_stored}):
        with pytest.raises(CapabilityProviderError) as blocked:
            orch._invoke(davi, "execute_delpi_information", {}, "c-e1")
        teo_out = orch._invoke(teo, "analyze", {}, "c-e2")
    assert blocked.value.code == "mcp_provider_not_eligible"
    assert teo_out is teo_stored
    assert wire.calls == []
    assert eligibility.calls == ["davi", "teo"]


def test_f_non_mcp_resume_skips_mcp_registry_gate():
    group = _non_mcp_group()
    stored = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="internal-ops",
            remote_name="read",
            protocol=InteropProtocol.HTTP,
            correlation_id="corr-http",
            observed_at="2026-11-09T12:00:00Z",
        ),
        content_text="http-stored",
    )
    key = _resume_invoke_key("internal-ops", "read", {})
    eligibility = _TrackingEligibility(
        error=McpProviderEligibilityError(
            "mcp_provider_not_eligible", "should not be consulted"
        )
    )
    wire_calls: list[str] = []

    class _HttpProv:
        provider_id = "http"

        def invoke(self, capability, arguments, **_kwargs):
            wire_calls.append(capability.remote_name)
            raise AssertionError("wire must not run on resume")

    orch = OperationalCapabilityOrchestrator(
        [_HttpProv()],
        orchestration_instructions={"x": "y"},
        mcp_provider_eligibility=eligibility,
    )
    with _resume_checkpoint({key: stored}):
        outcome = orch._invoke(group, "read", {}, "c-f")
    assert outcome is stored
    assert eligibility.calls == []
    assert wire_calls == []


def test_g_prepare_act_not_replayed_from_read_store():
    group = _mcp_group(
        operation_class=SpecialistOperationClass.PREPARE,
        remote_name="prepare_write",
    )
    # Even if a key collision somehow stored a READ-shaped outcome,
    # PREPARE is not resumable — mutating frontier is marked and wire
    # path is taken (then blocked by eligibility here).
    stored = _stored_outcome(remote_name="prepare_write")
    key = _resume_invoke_key("davi", "prepare_write", {})
    eligibility = _TrackingEligibility(allow={"davi"})
    wire_calls: list[str] = []

    class _Prov:
        provider_id = "mcp"

        def invoke(self, capability, arguments, **_kwargs):
            wire_calls.append(capability.remote_name)
            return stored

    orch = _orch(eligibility, [_Prov()])
    with _resume_checkpoint({key: stored}) as checkpoint:
        outcome = orch._invoke(group, "prepare_write", {}, "c-g")
        assert checkpoint.mutating_invoke_started is True
    assert outcome is stored
    assert wire_calls == ["prepare_write"]  # not silent replay


def test_h_deadline_blocks_before_resume_or_eligibility():
    group = _mcp_group()
    stored = _stored_outcome()
    key = _resume_invoke_key("davi", "execute_delpi_information", {})
    eligibility = _TrackingEligibility(allow={"davi"})
    wire = _WireProv()
    deadline = TurnDeadline.start(0.0)
    assert deadline.exhausted()
    with _resume_checkpoint({key: stored}):
        with pytest.raises(TurnBudgetExhausted) as exc:
            _orch(eligibility, [wire])._invoke(
                group,
                "execute_delpi_information",
                {},
                "c-h",
                deadline=deadline,
            )
    assert exc.value.stage == "provider_invoke"
    assert eligibility.calls == []
    assert wire.calls == []


def test_h_cancel_blocks_before_resume_or_eligibility():
    group = _mcp_group()
    stored = _stored_outcome()
    key = _resume_invoke_key("davi", "execute_delpi_information", {})
    eligibility = _TrackingEligibility(allow={"davi"})
    wire = _WireProv()
    token = _CANCEL_CHECK.set(lambda: True)
    try:
        with _resume_checkpoint({key: stored}):
            with pytest.raises(_TurnCancelled) as exc:
                _orch(eligibility, [wire])._invoke(
                    group, "execute_delpi_information", {}, "c-h2"
                )
        assert type(exc.value) is _TurnCancelled
    finally:
        _CANCEL_CHECK.reset(token)
    assert eligibility.calls == []
    assert wire.calls == []


def test_h_cancel_assertion_rejects_wrong_exception_type():
    """Mutation evidence: the old ``… or True`` assertion was a false
    positive — it accepted ANY exception. The corrected contract must
    fail when a non-cancel exception is observed instead.
    """
    # Characterization of the defective assertion (always True).
    wrong = ValueError("not-cancel")
    defective = ("Cancel" in type(wrong).__name__) or True
    assert defective is True

    # Corrected assertion must reject the wrong type.
    with pytest.raises(AssertionError):
        assert type(wrong) is _TurnCancelled

    # And must accept the real cancel type used by the orchestrator.
    assert type(_TurnCancelled()) is _TurnCancelled
