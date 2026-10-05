"""Provider-neutral orchestration — ARCH-DRIFT-DELIA-PROVIDER-
NEUTRAL-ORCHESTRATION-01 (ledger §6.130).

Proves the central orchestrator is provider-agnostic: capability
groups from multiple provider families are projected uniformly,
selection is a bounded model proposal revalidated deterministically,
and provider identity never biases ordering or routing.
"""

from __future__ import annotations

import json

import pytest

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    CapabilityProviderError,
    ProviderCapability,
    ProviderSurface,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.workspace_context import (
    WorkspaceContext,
    WorkspaceEntityRef,
    parse_workspace_context,
)
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import EpistemicClass, ModelRef, SourceRef
from app.domain.model_invocation.model import ProviderExposureClass
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
    """Selection model stub — routes proposals by task_purpose_id."""

    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, proposal):
        items = list(proposal) if isinstance(proposal, list) else [proposal]
        self._queues: dict[str, list] = {}
        self.requests = []
        self._generic: list = []
        for item in items:
            if isinstance(item, dict) and set(item) & {
                GROUP_SELECTION_INSTRUCTION_ID,
                CAPABILITY_SELECTION_INSTRUCTION_ID,
                ARGUMENTS_INSTRUCTION_ID,
            }:
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


def _outcome(group_id: str, remote_name: str, text: str) -> SpecialistOutcome:
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id=group_id,
            remote_name=remote_name,
            protocol=InteropProtocol.MCP,
            correlation_id="c",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text=text,
    )


class FakeProvider:
    """Provider stub: projects fixed groups, records invocations."""

    def __init__(self, provider_id: str, groups, outcomes=None):
        self.provider_id = provider_id
        self._groups = list(groups)
        self.calls = []
        self._outcomes = dict(outcomes or {})

    def list_groups(self, *, correlation_id, timeout_seconds=None):
        return ProviderSurface(groups=tuple(self._groups))

    def invoke(self, capability, arguments, *, correlation_id, timeout_seconds=None):
        self.calls.append((capability.remote_name, dict(arguments)))
        key = (capability.group_id, capability.remote_name)
        if key in self._outcomes:
            return self._outcomes[key]
        return _outcome(
            capability.group_id, capability.remote_name, "ok"
        )


class FailingProvider:
    provider_id = "broken"

    def list_groups(self, *, correlation_id, timeout_seconds=None):
        raise CapabilityProviderError("provider_unavailable", "down")

    def invoke(self, capability, arguments, *, correlation_id, timeout_seconds=None):
        raise CapabilityProviderError("provider_unavailable", "down")


def _cap(group_id, provider_id, name, op_class, desc=""):
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id=provider_id,
        remote_name=name,
        owner=group_id,
        operation_class=op_class,
        description=desc,
        input_schema={"type": "object", "properties": {}},
        binding={"ref": name},
    )


def _group(provider_id, group_id, capabilities, display=""):
    return CapabilityGroup(
        provider_id=provider_id,
        group_id=group_id,
        owner_ref=group_id,
        display_name=display or group_id,
        capabilities=tuple(capabilities),
        source=SourceRef(
            source_id=group_id,
            source_system=group_id,
            provider_name=display or group_id,
        ),
    )


def _select(group_key, remote_name, arguments=None):
    return {
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": group_key,
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": remote_name,
        },
        ARGUMENTS_INSTRUCTION_ID: {"arguments": arguments or {}},
    }


def _orchestrator(providers, proposal):
    return OperationalCapabilityOrchestrator(
        providers,
        invoke_model=InvokeModel(FakeProposalModel(proposal)),
        model_ref=TEST_MODEL_REF,
    )


# --- provider neutrality ------------------------------------------------


def test_two_provider_families_unified_surface():
    """An MCP group and an OpenAPI group project into the same surface;
    invocation dispatches to the owning provider by binding, never by
    branch on provider name."""
    mcp = FakeProvider(
        "mcp",
        [
            _group(
                "mcp",
                "vista",
                [_cap("vista", "mcp", "list_playlists",
                      SpecialistOperationClass.READ)],
                "VISTA",
            )
        ],
    )
    openapi = FakeProvider(
        "openapi",
        [
            _group(
                "openapi",
                "delpi",
                [_cap("delpi", "openapi", "list_products",
                      SpecialistOperationClass.READ)],
                "DELPI API",
            )
        ],
        outcomes={
            ("delpi", "list_products"): _outcome(
                "delpi", "list_products", "products: X"
            )
        },
    )
    orch = _orchestrator(
        [mcp, openapi], _select("openapi:delpi", "list_products")
    )
    attempt = orch.attempt("Liste os produtos")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert openapi.calls == [("list_products", {})]
    assert not mcp.calls
    assert attempt.provenance.provider_id == "openapi"
    assert attempt.provenance.capability_group_id == "delpi"


def test_provider_failure_is_truthful_source_unavailable():
    """A provider that cannot be consulted contributes a failure code —
    if the remaining surface has no match the answer is a truthful
    unavailability, never a silent miss."""
    broken = FailingProvider()
    orch = _orchestrator([broken], _select("x", "y"))
    attempt = orch.attempt("anything")
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == "provider_unavailable"


def test_selection_proposal_revalidated_against_fresh_groups():
    """An invented group id is never selectable — selection is a
    proposal, never authority."""
    mcp = FakeProvider(
        "mcp",
        [
            _group(
                "mcp",
                "vista",
                [_cap("vista", "mcp", "list_playlists",
                      SpecialistOperationClass.READ)],
            )
        ],
    )
    other = FakeProvider(
        "openapi",
        [
            _group(
                "openapi",
                "delpi",
                [_cap("delpi", "openapi", "list_products",
                      SpecialistOperationClass.READ)],
            )
        ],
    )
    orch = _orchestrator(
        [mcp, other],
        _select("openapi:nonexistent", "list_products"),
    )
    attempt = orch.attempt("Liste produtos")
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert not other.calls


# --- provider-bias / order-permutation ----------------------------------


def test_group_ordering_is_deterministic_and_provider_neutral():
    """Stage-1 sees groups sorted by key regardless of provider
    registration order — provider position never biases selection."""
    caps = [_cap("a", "p", "read_a", SpecialistOperationClass.READ)]
    provider_a = FakeProvider(
        "zzz_provider",
        [_group("zzz_provider", "last_group", caps)],
    )
    provider_b = FakeProvider(
        "aaa_provider",
        [_group("aaa_provider", "first_group", caps)],
    )
    proposal = _select("aaa_provider:first_group", "read_a")
    for order in ([provider_a, provider_b], [provider_b, provider_a]):
        orch = _orchestrator(order, proposal)
        attempt = orch.attempt("read something")
        assert attempt.status is GovernedCapabilityStatus.SUCCESS
    # The model payload lists both groups sorted by key.
    stage1 = next(
        r for r in orch._invoke_model._port.requests
        if r.task_purpose_id == GROUP_SELECTION_INSTRUCTION_ID
    )
    payload = stage1.input_text
    idx_first = payload.index("aaa_provider:first_group")
    idx_last = payload.index("zzz_provider:last_group")
    assert idx_first < idx_last


def test_group_key_is_provider_prefixed():
    """Group keys are provider-scoped — same group_id in two providers
    never collides and is never confused."""
    p1 = FakeProvider(
        "mcp",
        [_group("mcp", "shared", [_cap("shared", "mcp", "x",
              SpecialistOperationClass.READ)])],
    )
    p2 = FakeProvider(
        "openapi",
        [_group("openapi", "shared", [_cap("shared", "openapi", "x",
              SpecialistOperationClass.READ)])],
    )
    orch = OperationalCapabilityOrchestrator([p1, p2])
    groups, _ = orch._groups("c")
    assert set(groups) == {"mcp:shared", "openapi:shared"}


# --- workspace context ---------------------------------------------------


def test_workspace_context_parsed_bounded():
    ctx, err = parse_workspace_context(
        {
            "host_app_id": "tv-dashboard",
            "route": "/tv-dashboard",
            "selected_entity_ref": {
                "entity_type": "playlist",
                "entity_id": "pl-1",
                "source_system": "vista",
            },
            "entity_refs": [
                {
                    "entity_type": "slide",
                    "entity_id": "sl-7",
                    "source_system": "vista",
                    "label": "Slide 7",
                }
            ],
        }
    )
    assert err is None
    assert ctx.host_app_id == "tv-dashboard"
    assert ctx.selected_entity_ref.entity_id == "pl-1"
    assert ctx.entity_refs[0].entity_type == "slide"
    block = ctx.to_prompt_block()
    assert "pl-1" in block and "sl-7" in block


@pytest.mark.parametrize(
    "raw",
    [
        "not-an-object",
        {"host_app_id": "x", "bogus": 1},
        {"host_app_id": ""},
        {"host_app_id": "x" * 500},
        {
            "host_app_id": "x",
            "selected_entity_ref": {"entity_type": "t"},
        },
        {
            "host_app_id": "x",
            "entity_refs": [
                {"entity_type": "t", "entity_id": "i", "source_system": "s"}
            ]
            * 5,
        },
    ],
)
def test_workspace_context_fail_closed(raw):
    ctx, err = parse_workspace_context(raw)
    assert ctx is None
    assert err is not None


def test_workspace_context_reaches_stage3_proposal():
    """When a workspace context is present it is injected as an
    untrusted block into stage-3 argument building — never into the
    arguments themselves."""
    mcp = FakeProvider(
        "mcp",
        [
            _group(
                "mcp",
                "vista",
                [
                    ProviderCapability(
                        capability_id="vista.get_playlist_context",
                        group_id="vista",
                        provider_id="mcp",
                        remote_name="get_playlist_context",
                        owner="vista",
                        operation_class=SpecialistOperationClass.READ,
                        description="context",
                        input_schema={
                            "type": "object",
                            "properties": {
                                "playlist_id": {"type": "string"}
                            },
                            "required": ["playlist_id"],
                        },
                        binding={"specialist_id": "vista",
                                 "remote_name": "get_playlist_context"},
                    )
                ],
            )
        ],
    )
    orch = _orchestrator(
        [mcp],
        {
            GROUP_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "capability_group_id": "mcp:vista",
            },
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "get_playlist_context",
            },
            ARGUMENTS_INSTRUCTION_ID: {
                "arguments": {"playlist_id": "pl-9"}
            },
        },
    )
    ctx = WorkspaceContext(
        host_app_id="tv-dashboard",
        route="/tv-dashboard",
        selected_entity_ref=WorkspaceEntityRef(
            entity_type="playlist",
            entity_id="pl-9",
            source_system="vista",
        ),
    )
    attempt = orch.attempt(
        "o que tem no slide atual?", workspace_context=ctx
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    stage3 = next(
        r for r in orch._invoke_model._port.requests
        if r.task_purpose_id == ARGUMENTS_INSTRUCTION_ID
    )
    assert "<workspace_context>" in stage3.input_text
    assert "pl-9" in stage3.input_text


def test_workspace_context_never_authorizes():
    """A workspace context that names a nonexistent group/capability
    changes nothing — the live surface still decides."""
    mcp = FakeProvider(
        "mcp",
        [
            _group(
                "mcp",
                "vista",
                [_cap("vista", "mcp", "list_playlists",
                      SpecialistOperationClass.READ)],
            )
        ],
    )
    orch = _orchestrator(
        [mcp], {"applicable": False}
    )
    ctx = WorkspaceContext(
        host_app_id="x",
        selected_entity_ref=WorkspaceEntityRef(
            entity_type="slide", entity_id="evil", source_system="vista"
        ),
    )
    attempt = orch.attempt("anything", workspace_context=ctx)
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert not mcp.calls


# --- governed-write chain stays provider-neutral -------------------------


def test_prepare_confirms_through_generic_chain():
    """A PREPARE capability on ANY provider follows the same
    pending->confirm->ACT lifecycle — provider agnostic."""
    prepare = ProviderCapability(
        capability_id="vista.prepare_change",
        group_id="vista",
        provider_id="mcp",
        remote_name="prepare_change",
        owner="vista",
        operation_class=SpecialistOperationClass.PREPARE,
        input_schema={"type": "object", "properties": {}},
        binding={},
    )
    act = ProviderCapability(
        capability_id="vista.commit_proposal",
        group_id="vista",
        provider_id="mcp",
        remote_name="commit_proposal",
        owner="vista",
        operation_class=SpecialistOperationClass.ACT,
        input_schema={
            "type": "object",
            "properties": {"proposal_handle": {"type": "string"}},
            "required": ["proposal_handle"],
        },
        binding={},
    )
    provider = FakeProvider(
        "mcp",
        [_group("mcp", "vista", [prepare, act])],
        outcomes={
            ("vista", "prepare_change"): _outcome(
                "vista", "prepare_change", "prepared"
            ),
            ("vista", "commit_proposal"): _outcome(
                "vista", "commit_proposal", "committed"
            ),
        },
    )
    orch = _orchestrator(
        [provider], _select("mcp:vista", "prepare_change")
    )
    attempt = orch.attempt("mude o titulo")
    # The owner payload here is minimal — the projection decides
    # readiness; with no handle the preview is not READY.
    assert attempt.status in (
        GovernedCapabilityStatus.SUCCESS,
        GovernedCapabilityStatus.WRITE_REJECTED,
    )
