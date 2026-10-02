"""Domain contract tests for the specialist-interop boundary.

Locks: the approved specialist set (DAVI/TÉO/VISTA only), the
provider-neutral owner-class mapping, the interactive phase class gate
(DISCOVERY|READ invocable; PREPARE/ACT/UNKNOWN never), and the
epistemic pin (specialist outcome == OBSERVATION, never auto-FACT).

ARCH-DRIFT-MCP-FEDERATION-CATALOG-OWNER-01 (§6.109) superseded the
local full-tool mirror; ARCH-DRIFT-MCP-CAPABILITY-AUTHORITY-02 (§6.118)
superseded the remaining second capability authority — the per-name
DISCOVERY bindings, the per-tuple READ actions, the enabled-tuple
config plumbing and the DELIA_C4_*_ENABLED flags. These tests guard
against their re-creation: no remote tool name may appear in this
module as DÉLIA policy.
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
    INTERACTIVE_INVOCABLE_CLASSES,
    invocable_in_interactive_phase,
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


def test_no_local_tool_authority():
    """Regression guard: no per-tool catalog or availability table may
    be recreated — the remote specialist owns its capability surface."""
    assert not hasattr(rules, "SPECIALIST_CAPABILITY_CLASSES")
    assert not hasattr(rules, "GOVERNED_DISCOVERY_BINDINGS")
    assert not hasattr(rules, "GOVERNED_READ_ACTIONS")
    assert not hasattr(rules, "enabled_governed_read_tuples")
    assert not hasattr(rules, "governed_read_action_allowed")
    assert not hasattr(rules, "discovery_binding_allowed")
    source = inspect.getsource(rules)
    for leaked_remote_name in (
        "execute_delpi_information",
        "discover_delpi_information",
        "get_catalog",
        "search_products",
        "gpt_analyze",
        "list_playlists",
        "prepare_",
        "commit_proposal",
    ):
        assert leaked_remote_name not in source


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


def test_interactive_gate_allows_all_known_owner_classes():
    """ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03 class gate —
    every owner-typed known class is orchestration-eligible; no
    per-name or per-flag narrowing exists. Eligibility is never
    permission — the governed-write chain and live AuthZ apply
    downstream."""
    assert INTERACTIVE_INVOCABLE_CLASSES == frozenset(
        {
            SpecialistOperationClass.DISCOVERY,
            SpecialistOperationClass.READ,
            SpecialistOperationClass.PREPARE,
            SpecialistOperationClass.ACT,
        }
    )
    for cls in (
        SpecialistOperationClass.DISCOVERY,
        SpecialistOperationClass.READ,
        SpecialistOperationClass.PREPARE,
        SpecialistOperationClass.ACT,
    ):
        assert invocable_in_interactive_phase(cls) is True


def test_interactive_gate_blocks_unknown_class():
    """UNKNOWN (absent/invalid owner typing) is discoverable but never
    invocable — the only class excluded from orchestration."""
    assert invocable_in_interactive_phase(
        SpecialistOperationClass.UNKNOWN
    ) is False


def test_capability_descriptor_grants_nothing():
    descriptor = SpecialistCapabilityDescriptor(
        capability_id="davi.some_read",
        specialist_id="davi",
        remote_name="some_read",
        operation_class=SpecialistOperationClass.READ,
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
            remote_name="some_read",
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
