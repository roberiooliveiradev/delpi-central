"""Domain contract tests for C3-MCP-INTEROP-01.

Locks: the approved specialist set (DAVI/TÉO/VISTA only), the
provider-neutral owner-class mapping, the DÉLIA governance bindings
(DISCOVERY + governed READ tuples — policy, not catalog), the C3
invocation gate, and the epistemic pin (specialist outcome ==
OBSERVATION, never auto-FACT).

ARCH-DRIFT-MCP-FEDERATION-CATALOG-OWNER-01 (ledger §6.109): the local
full-tool mirror (SPECIALIST_CAPABILITY_CLASSES) is superseded — the
remote specialist owns its catalog; these tests guard against its
re-creation.
"""

from __future__ import annotations

import inspect
from dataclasses import fields

import pytest

from app.domain.evidence.model import EpistemicClass
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistCapabilityDescriptor,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from app.domain.specialist_interop import rules
from app.domain.specialist_interop.rules import (
    APPROVED_SPECIALIST_IDS,
    GOVERNED_DISCOVERY_BINDINGS,
    GOVERNED_READ_ACTIONS,
    discovery_binding_allowed,
    invocable_in_foundation,
    operation_class_from_owner,
    specialist_ref_or_none,
)


def test_approved_specialist_set_is_exactly_davi_teo_vista():
    assert APPROVED_SPECIALIST_IDS == frozenset({"davi", "teo", "vista"})


def test_specialist_ref_for_each_approved_specialist():
    owners = {
        "davi": "api-delpi",
        "teo": "transformometro-api",
        "vista": "tv-dashboard-api",
    }
    for specialist_id, owner in owners.items():
        ref = specialist_ref_or_none(specialist_id)
        assert ref is not None
        assert ref.specialist_id == specialist_id
        assert ref.owner_ref == owner
        assert ref.protocol is InteropProtocol.MCP


def test_unknown_specialist_fails_closed():
    for unknown in ("", "chatgpt", "unknown-mcp", "DAVI2", " openai "):
        assert specialist_ref_or_none(unknown) is None
        assert discovery_binding_allowed(unknown, "get_catalog") is False


def test_no_local_full_tool_mirror():
    """Regression guard: the superseded per-specialist tool-name mirror
    must not be recreated — the remote specialist owns its catalog."""
    assert not hasattr(rules, "SPECIALIST_CAPABILITY_CLASSES")
    assert not hasattr(rules, "operation_class_for")
    source = inspect.getsource(rules)
    assert "SPECIALIST_CAPABILITY_CLASSES" not in source
    # No per-specialist dict of remote tool names may exist: the only
    # remote names in this module are the bounded governance bindings.
    assert "commit_proposal" not in source
    assert "prepare_" not in source
    assert "execute_delpi_information" in source  # governed READ policy
    assert "get_catalog" in source  # DISCOVERY binding policy


def test_governance_bindings_are_bounded_policy_not_catalog():
    """The only remote names DÉLIA lists are its own invocation policy —
    3 DISCOVERY bindings + the 2 authorized C4 READ tuples."""
    assert GOVERNED_DISCOVERY_BINDINGS == frozenset(
        {
            ("davi", "discover_delpi_information"),
            ("teo", "get_catalog"),
            ("vista", "get_catalog"),
        }
    )
    assert set(GOVERNED_READ_ACTIONS) == {
        ("davi", "execute_delpi_information"),
        ("teo", "analyze"),
    }
    for specialist_id, _ in GOVERNED_DISCOVERY_BINDINGS:
        assert specialist_id in APPROVED_SPECIALIST_IDS


def test_owner_class_mapping_is_provider_neutral():
    assert (
        operation_class_from_owner("DISCOVERY")
        is SpecialistOperationClass.DISCOVERY
    )
    assert (
        operation_class_from_owner("READ") is SpecialistOperationClass.READ
    )
    # Owner ANALYSIS (non-persisting analysis) projects as READ.
    assert (
        operation_class_from_owner("ANALYSIS")
        is SpecialistOperationClass.READ
    )
    assert (
        operation_class_from_owner("PREPARE")
        is SpecialistOperationClass.PREPARE
    )
    assert operation_class_from_owner("ACT") is SpecialistOperationClass.ACT


def test_owner_class_mapping_fail_closed():
    """Missing/invalid/untrusted owner typing -> UNKNOWN: discoverable,
    never invocable."""
    for raw in (None, "", "  ", "read-only", "SAFE", 42, {"x": 1}, []):
        assert (
            operation_class_from_owner(raw) is SpecialistOperationClass.UNKNOWN
        )
    # Case-insensitive tolerance is fine — the vocabulary is bounded.
    assert (
        operation_class_from_owner(" read ") is SpecialistOperationClass.READ
    )


def test_c3_invocation_gate_is_discovery_only():
    assert invocable_in_foundation(SpecialistOperationClass.DISCOVERY) is True
    for cls in (
        SpecialistOperationClass.READ,
        SpecialistOperationClass.PREPARE,
        SpecialistOperationClass.ACT,
        SpecialistOperationClass.UNKNOWN,
    ):
        assert invocable_in_foundation(cls) is False


def test_discovery_binding_policy_exact():
    assert discovery_binding_allowed("davi", "discover_delpi_information")
    assert discovery_binding_allowed("teo", "get_catalog")
    assert discovery_binding_allowed("vista", "get_catalog")
    assert not discovery_binding_allowed("davi", "get_catalog")
    assert not discovery_binding_allowed("teo", "discover_delpi_information")
    assert not discovery_binding_allowed("vista", "preview_data_model")


def test_capability_descriptor_grants_nothing():
    descriptor = SpecialistCapabilityDescriptor(
        capability_id="davi.discover_delpi_information",
        specialist_id="davi",
        remote_name="discover_delpi_information",
        operation_class=SpecialistOperationClass.DISCOVERY,
        protocol=InteropProtocol.MCP,
        observed_at="2026-01-01T00:00:00+00:00",
    )
    assert descriptor.grants_authorization() is False
    assert descriptor.grants_execution() is False
    assert descriptor.is_authoritative_fact() is False


def test_outcome_epistemic_class_is_pinned_observation():
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="davi",
            remote_name="discover_delpi_information",
            protocol=InteropProtocol.MCP,
            correlation_id="corr-1",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text="{}",
    )
    assert outcome.epistemic_class is EpistemicClass.OBSERVATION
    with pytest.raises((AttributeError, TypeError)):
        outcome.epistemic_class = EpistemicClass.FACT  # type: ignore[misc]


def test_outcome_carries_no_secret_fields():
    names = {f.name for f in fields(SpecialistOutcome)} | {
        f.name for f in fields(SpecialistResultProvenance)
    }
    for leaked in ("token", "credential", "secret", "authorization", "key"):
        assert not any(leaked in n for n in names)
