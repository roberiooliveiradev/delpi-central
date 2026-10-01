"""Domain contract tests for C3-MCP-INTEROP-01.

Locks: the approved specialist set (DAVI/TÉO/VISTA only), the DÉLIA-owned
operation classification, the C3 invocation gate (DISCOVERY only), and
the epistemic pin (specialist outcome == OBSERVATION, never auto-FACT).
"""

from __future__ import annotations

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
from app.domain.specialist_interop.rules import (
    APPROVED_SPECIALIST_IDS,
    SPECIALIST_CAPABILITY_CLASSES,
    invocable_in_foundation,
    operation_class_for,
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
        assert operation_class_for(unknown, "get_catalog") is None


def test_davi_classification():
    assert (
        operation_class_for("davi", "discover_delpi_information")
        is SpecialistOperationClass.DISCOVERY
    )
    assert (
        operation_class_for("davi", "execute_delpi_information")
        is SpecialistOperationClass.READ
    )


def test_teo_classification_covers_full_surface():
    teo = SPECIALIST_CAPABILITY_CLASSES["teo"]
    assert len(teo) == 24
    assert teo["get_catalog"] is SpecialistOperationClass.DISCOVERY
    assert teo["generate_from_transcript"] is SpecialistOperationClass.READ
    assert teo["prepare_record_change"] is SpecialistOperationClass.PREPARE
    assert teo["commit_proposal"] is SpecialistOperationClass.ACT


def test_vista_classification_covers_full_surface():
    vista = SPECIALIST_CAPABILITY_CLASSES["vista"]
    assert len(vista) == 8
    assert vista["get_catalog"] is SpecialistOperationClass.DISCOVERY
    assert vista["list_playlists"] is SpecialistOperationClass.READ
    assert vista["prepare_change"] is SpecialistOperationClass.PREPARE
    assert vista["commit_proposal"] is SpecialistOperationClass.ACT


def test_unknown_capability_fails_closed():
    assert operation_class_for("davi", "commit_proposal") is None
    assert operation_class_for("teo", "drop_table") is None
    assert operation_class_for("vista", "execute_sql") is None


def test_c3_invocation_gate_is_discovery_only():
    assert invocable_in_foundation(SpecialistOperationClass.DISCOVERY) is True
    for cls in (
        SpecialistOperationClass.READ,
        SpecialistOperationClass.PREPARE,
        SpecialistOperationClass.ACT,
    ):
        assert invocable_in_foundation(cls) is False


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
