"""Shared governed-capability test fixtures (doc 241 — native-first).

Extracted from the retired Application-sequencer suites; only
fixtures consumed by the surviving native-path suites remain.
"""

from __future__ import annotations

from tests.conftest import load_test_orchestration_instructions  # noqa: F401

import json
from app.application.capability_provision.orchestration import (
    EVIDENCE_COMPOSITION_INSTRUCTION_ID,
    INTERACTION_ADMISSION_INSTRUCTION_ID,
)
from pathlib import (
    Path,
)
from app.application.capability_provision.contracts import (
    CapabilityGroup,
    ProviderCapability,
    ProviderSurface,
)
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.domain.evidence.model import (
    ModelRef,
    SourceRef,
)
from app.domain.model_invocation.model import (
    ProviderExposureClass,
)
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)


TEST_MODEL_REF = ModelRef(
    model_id="test-model", version="1", owner_ref="DELPI"
)


class FakeProposalModel:
    """Selection model stub — queues proposals per task_purpose_id."""

    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, proposal):
        items = list(proposal) if isinstance(proposal, list) else [proposal]
        self._queues: dict[str, list] = {}
        self.requests = []
        self._generic: list = []
        routed = {
            INTERACTION_ADMISSION_INSTRUCTION_ID,
            EVIDENCE_COMPOSITION_INSTRUCTION_ID,
        }
        for item in items:
            if isinstance(item, dict) and set(item) & routed:
                for purpose, payload in item.items():
                    self._queues.setdefault(purpose, []).append(payload)
            else:
                self._generic.append(item)
        self._last: dict[str, object] = {}

    def invoke(self, request):
        self.requests.append(request)
        purpose = request.task_purpose_id
        queue = self._queues.get(purpose)
        if queue:
            resolved = queue.pop(0)
        elif purpose == "delia.capability_orchestration.interaction_admission":
            resolved = self._last.get(purpose)
        elif self._generic:
            resolved = self._generic.pop(0)
        else:
            resolved = self._last.get(purpose)
        if resolved is not None:
            self._last[purpose] = resolved
        return ProviderInvocationPayload(
            structured_output=resolved,
            generated_at="2026-01-01T00:00:00+00:00",
        )

    def purposes(self) -> list[str]:
        return [request.task_purpose_id for request in self.requests]


def _outcome(
    text: str,
    structured=None,
    is_complete: bool = True,
    limitations: tuple[str, ...] = (),
) -> SpecialistOutcome:
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="provider_alpha:guide",
            remote_name="read_items",
            protocol=InteropProtocol.MCP,
            correlation_id="corr-rel",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text=text,
        is_complete=is_complete,
        structured=structured,
        limitations=limitations,
    )


class FakeProvider:
    """Outcomes may be a single value or a queue per capability key."""

    def __init__(self, provider_id, groups, outcomes=None):
        self.provider_id = provider_id
        self._groups = list(groups)
        self.calls = []
        self._outcomes = dict(outcomes or {})

    def list_groups(self, *, correlation_id, timeout_seconds=None):
        return ProviderSurface(groups=tuple(self._groups))

    def invoke(self, capability, arguments, *, correlation_id,
               timeout_seconds=None):
        self.calls.append((capability.remote_name, dict(arguments)))
        key = (capability.group_id, capability.remote_name)
        queued = self._outcomes[key]
        if isinstance(queued, list):
            item = queued.pop(0)
            if isinstance(item, BaseException):
                raise item
            return item
        if isinstance(queued, BaseException):
            raise queued
        return queued

    def native_toolset_config(self, group_id, *, timeout_seconds=None):
        """Same public contract seam as the real MCP provider — the
        endpoint marks the test transport substituted by
        ``native_toolset_stub``; no private-attribute traversal."""
        from app.application.specialist_interop.contracts import (
            SpecialistToolsetConfig,
        )

        return SpecialistToolsetConfig(
            endpoint=f"mcp-test://{group_id}",
            headers={},
            timeout_seconds=5.0,
        )


def _cap(group_id, provider_id, name, *, schema=None, op_class=None):
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id=provider_id,
        remote_name=name,
        owner=group_id,
        operation_class=op_class or SpecialistOperationClass.READ,
        description="read items",
        input_schema=schema or {"type": "object", "properties": {}},
        binding={"ref": name},
    )


_QUERY_SCHEMA = {
    "type": "object",
    "properties": {"query": {"type": "string"}},
}


def _group(provider_id, group_id, capabilities):
    return CapabilityGroup(
        provider_id=provider_id,
        group_id=group_id,
        owner_ref=group_id,
        display_name=group_id,
        capabilities=tuple(capabilities),
        source=SourceRef(
            source_id=group_id,
            source_system=group_id,
            provider_name=group_id,
        ),
    )



def _query_cap():
    return _cap(
        "alpha",
        "mcp",
        "search_items",
        schema=_QUERY_SCHEMA,
    )


def _doc_cap():
    return _cap("beta", "mcp", "read_guidance")


def _doc_outcome():
    return _outcome(
        "knowledge",
        structured={
            "items": [
                {
                    "section": "s0055",
                    "content": "Ex.: TERM. BALA 2,50-6,00MM2 NU GRANEL",
                }
            ]
        },
    )




_IRRELEVANT = _outcome(
    "ok", structured={"items": [{"name": "BALANCA 1"}]}
)
_RELEVANT = _outcome(
    "ok",
    structured={
        "items": [
            {"name": "TERM. BALA 0,50-2,27MM2"},
            {"name": "TERM. BALA 1,00-2,50MM2"},
        ]
    },
)

def _providers(alpha_outcomes=None, beta_outcome=None):
    pa = FakeProvider(
        "pa",
        [_group("pa", "alpha", [_query_cap()])],
        outcomes={
            ("alpha", "search_items"): (
                alpha_outcomes
                if alpha_outcomes is not None
                else [_IRRELEVANT, _RELEVANT]
            )
        },
    )
    pb = FakeProvider(
        "pb",
        [_group("pb", "beta", [_doc_cap()])],
        outcomes={
            ("beta", "read_guidance"): (
                beta_outcome
                if beta_outcome is not None
                else _doc_outcome()
            )
        },
    )
    return [pa, pb]


def _reuse_proposal(
    *,
    first_status="foreign_evidence_required",
    reselect_capability="search_items",
    foreign_capability_id="beta.read_guidance",
    final_correspondence="corresponds",
):
    """Two-group recovery scenario exercising the redundant second
    ``native_assessment`` (H5).

    Call order per unrouted purpose (generic queue):
      admission, turn_goal, native_assessment#1, foreign_selection#1,
      index_probe, native_assessment#2 | foreign_selection#2.

    The assessment/foreign pair is a SINGLE dual-key item so it feeds
    whichever of the two stages consumes it first: a reassessing
    engine pops it as the assessment decision; a reusing engine skips
    the assessment and the same item feeds the foreign selection that
    still runs under the reused decision. Argument slots:
    foreign#1 -> {}, owner#1 -> literal, foreign#2 -> {}, owner#2 ->
    reformulated.
    """
    foreign_round1 = first_status == "foreign_evidence_required"
    select1_args = {} if foreign_round1 else {"query": "terminal bala"}
    proposal = [
        _select(
            "pa:alpha",
            "search_items",
            **_args(select1_args),
            **_rel("irrelevant", "records are scales, not terminals"),
        ),
        _args({"query": "terminal bala"}) if foreign_round1 else None,
        {"goal_class": "record_lookup"},
        {"status": first_status},
        {"foreign_capability_id": foreign_capability_id}
        if foreign_round1
        else {"probe_index": False},
        {"probe_index": False} if foreign_round1 else None,
        _select(
            "pa:alpha",
            reselect_capability,
            **_args({}),
        ),
        {
            "status": "foreign_evidence_required",
            "foreign_capability_id": foreign_capability_id,
        },
        {"foreign_capability_id": foreign_capability_id},
        _args({"query": "TERM. BALA"}),
        _rel(final_correspondence, "still scales" if final_correspondence == "irrelevant" else None),
    ]
    return [item for item in proposal if item is not None]
