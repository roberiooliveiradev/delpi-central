"""I02-R1 characterization — pre-synthesis latency critical path.

Documents proven live failure modes without implementing a performance
fix. Fake model / fake provider. MESSAGE ≠ ACT. Budget = 30s.
"""

from __future__ import annotations

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    ProviderCapability,
    ProviderSurface,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GOAL_INSTRUCTION_ID,
    INDEX_PROBE_INSTRUCTION_ID,
    INDEX_SELECT_INSTRUCTION_ID,
    MIN_VIABLE_MODEL_STAGE_SECONDS,
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import (
    DEFAULT_TURN_BUDGET_SECONDS,
    TurnDeadline,
)
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.errors import (
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import ModelRef, SourceRef
from app.domain.model_invocation.model import ProviderExposureClass
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)

TEST_MODEL_REF = ModelRef(
    model_id="i02r1-latency", version="1", owner_ref="DELPI"
)

# Optional unconstrained string → self-index eligible (VISTA-like).
_GUIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
    },
}


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += float(seconds)


class FakeProposalModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(
        self,
        proposal,
        *,
        clock=None,
        timeout_purposes=frozenset(),
        advance_on=None,
    ):
        items = (
            list(proposal) if isinstance(proposal, list) else [proposal]
        )
        self._queues: dict[str, list] = {}
        self.requests = []
        self._generic: list = []
        self._last: dict[str, object] = {}
        self._clock = clock
        self._timeout_purposes = frozenset(timeout_purposes)
        self._advance_on = dict(advance_on or {})
        purpose_ids = {
            GOAL_INSTRUCTION_ID,
            CAPABILITY_SELECTION_INSTRUCTION_ID,
            ARGUMENTS_INSTRUCTION_ID,
            NATIVE_ASSESSMENT_INSTRUCTION_ID,
            INDEX_PROBE_INSTRUCTION_ID,
            INDEX_SELECT_INSTRUCTION_ID,
        }
        for item in items:
            if isinstance(item, dict) and set(item) & purpose_ids:
                for purpose, payload in item.items():
                    self._queues.setdefault(purpose, []).append(payload)
            else:
                self._generic.append(item)

    def invoke(self, request):
        self.requests.append(request)
        purpose = request.task_purpose_id
        if purpose in self._timeout_purposes:
            if self._clock is not None:
                # Consume remaining budget like a hung model stage.
                self._clock.advance(
                    max(0.0, request.timeout_seconds or 10.0)
                )
            raise ModelInvocationError(
                TIMEOUT, "simulated index_probe timeout"
            )
        advance = self._advance_on.get(purpose)
        if self._clock is not None and advance:
            self._clock.advance(float(advance))
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


class FakeProvider:
    def __init__(self, provider_id, groups, outcomes=None):
        self.provider_id = provider_id
        self._groups = list(groups)
        self.calls = []
        self._outcomes = dict(outcomes or {})

    def list_groups(self, *, correlation_id, timeout_seconds=None):
        return ProviderSurface(groups=tuple(self._groups))

    def invoke(
        self, capability, arguments, *, correlation_id,
        timeout_seconds=None,
    ):
        self.calls.append((capability.remote_name, dict(arguments)))
        key = (capability.group_id, capability.remote_name)
        outcome = self._outcomes.get(key)
        if outcome is not None:
            return outcome
        return SpecialistOutcome(
            status=SpecialistResultStatus.COMPLETED,
            provenance=SpecialistResultProvenance(
                specialist_id=capability.group_id,
                remote_name=capability.remote_name,
                protocol=InteropProtocol.MCP,
                correlation_id=correlation_id,
                observed_at="2026-01-01T00:00:00+00:00",
            ),
            content_text="ok",
            structured={
                "guide": {
                    "purpose": "design guidance",
                    "use_when": ["legibility"],
                    "how_to_use": ["contrast"],
                    "limitations": "no panel inspection",
                }
            },
        )


def _cap(group_id, provider_id, name, op_class, schema=None):
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id=provider_id,
        remote_name=name,
        owner=group_id,
        operation_class=op_class,
        description="product guide",
        input_schema=schema or {"type": "object", "properties": {}},
        binding={"ref": name},
    )


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


def test_index_probe_model_timeout_never_reaches_owner_read():
    """When optional probe is allowed to start and times out → no owner READ.

    I02-R1 characterization of fail-closed timeout (never catch exhausted
    deadline to continue). I02-R2 headroom skip is covered separately in
    ``test_i02r2_index_probe_headroom``; this keeps remaining above the
    optional-probe floor so the timeout path is still exercised.
    """
    clock = FakeClock()
    deadline = TurnDeadline.start(30.0, clock=clock)
    # Remaining must stay >= 2*MODEL_STAGE + MIN_VIABLE*3 (26s default)
    # so the optional probe is eligible to start, then times out.
    clock.advance(2.0)
    provider = FakeProvider(
        "specialist_alpha",
        [
            _group(
                "specialist_alpha",
                "specialist_alpha",
                [
                    _cap(
                        "specialist_alpha",
                        "specialist_alpha",
                        "get_product_guide",
                        SpecialistOperationClass.READ,
                        schema=_GUIDE_SCHEMA,
                    )
                ],
            )
        ],
    )
    model = FakeProposalModel(
        {
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "get_product_guide",
            },
            GOAL_INSTRUCTION_ID: {
                "goal_class": "read",
                "prior_evidence_sufficient": False,
            },
            NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
            # Probe would be proposed true if it completed; it times out.
            INDEX_PROBE_INSTRUCTION_ID: {"probe_index": True},
        },
        clock=clock,
        timeout_purposes=frozenset({INDEX_PROBE_INSTRUCTION_ID}),
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    attempt = orch.attempt(
        "Que critérios de legibilidade devo considerar para um painel?",
        turn_deadline=deadline,
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code in {
        "model_timeout",
        "turn_budget_exhausted",
    }
    # Proven critical gap: owner READ never runs after probe timeout.
    assert provider.calls == []
    assert INDEX_PROBE_INSTRUCTION_ID in {
        r.task_purpose_id for r in model.requests
    }
    assert DEFAULT_TURN_BUDGET_SECONDS == 30.0
    assert MIN_VIABLE_MODEL_STAGE_SECONDS == 2.0


def test_budget_constant_unchanged_by_characterization():
    assert DEFAULT_TURN_BUDGET_SECONDS == 30.0
