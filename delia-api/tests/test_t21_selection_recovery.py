"""Task 21 — bounded selection recovery contracts.

Covers the two governed recoveries added to the hierarchical
selection stage:

1. Reconcile retry — group judged applicable but no listed
   capability bound → ONE re-proposal with typed feedback inside the
   same group (refusal remains a valid outcome; fail-closed).
2. Group fallback — a tried group that bound nothing is excluded and
   group selection re-runs over the remaining live groups with a
   typed unbound signal (named-provider constraint preserved).

Positive + sibling + negative coverage per root-cause rule. All
providers are fake ports; no owner is ever invoked for real.
"""

from __future__ import annotations

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
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
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
    model_id="t21-model", version="1", owner_ref="DELPI"
)


class FakeProposalModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, proposal):
        items = (
            list(proposal) if isinstance(proposal, list) else [proposal]
        )
        self._queues: dict[str, list] = {}
        self.requests = []
        self._generic: list = []
        for item in items:
            if isinstance(item, dict) and set(item) & _PURPOSE_IDS:
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


_PURPOSE_IDS = frozenset(
    {
        GROUP_SELECTION_INSTRUCTION_ID,
        CAPABILITY_SELECTION_INSTRUCTION_ID,
        ARGUMENTS_INSTRUCTION_ID,
    }
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
        if isinstance(outcome, CapabilityProviderError):
            raise outcome
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
        )


def _cap(group_id, provider_id, name, op_class, schema=None, desc=""):
    return ProviderCapability(
        capability_id=f"{group_id}.{name}",
        group_id=group_id,
        provider_id=provider_id,
        remote_name=name,
        owner=group_id,
        operation_class=op_class,
        description=desc,
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


def _orchestrator(providers, proposal):
    model = FakeProposalModel(proposal)
    return (
        OperationalCapabilityOrchestrator(
            providers,
            invoke_model=InvokeModel(model),
            model_ref=TEST_MODEL_REF,
        ),
        model,
    )


def _requests(model, purpose):
    return [
        r for r in model.requests if r.task_purpose_id == purpose
    ]


_READ = SpecialistOperationClass.READ


# ---------------------------------------------------------------------
# Reconcile retry — same group, bounded re-proposal
# ---------------------------------------------------------------------


def _single_group_provider(cap_name="read_things"):
    return FakeProvider(
        "acme-x",
        [
            _group(
                "acme-x",
                "g1",
                [
                    _cap(
                        "g1", "acme-x", cap_name, _READ,
                        desc="read the things register",
                    ),
                ],
            )
        ],
    )


def test_t21_unbound_capability_reconciles_inside_same_group():
    """Positive: group applicable + capability unbound → one typed
    re-proposal binds the listed capability; selection proceeds."""
    provider = _single_group_provider()
    orch, model = _orchestrator(
        [provider],
        [
            {
                GROUP_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "capability_group_id": "g1",
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "read_things",
                }
            },
            {ARGUMENTS_INSTRUCTION_ID: {"arguments": {}}},
        ],
    )
    attempt = orch.attempt("liste os registros")
    assert provider.calls == [("read_things", {})]
    cap_requests = _requests(model, CAPABILITY_SELECTION_INSTRUCTION_ID)
    assert len(cap_requests) == 2
    assert "group_applicable_capability_unbound" in (
        cap_requests[1].input_text
    )


def test_t21_unbound_capability_still_refuses_when_nothing_owns():
    """Negative sibling: the reconcile re-proposal also refuses →
    deterministic insufficiency; the model is never forced to bind."""
    provider = _single_group_provider()
    orch, model = _orchestrator(
        [provider],
        [
            {
                GROUP_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "capability_group_id": "g1",
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
        ],
    )
    attempt = orch.attempt("consulte o salário dos funcionários")
    assert provider.calls == []
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert len(_requests(model, CAPABILITY_SELECTION_INSTRUCTION_ID)) == 2


# ---------------------------------------------------------------------
# Group fallback — tried group excluded, reselection over the rest
# ---------------------------------------------------------------------


def _two_group_provider():
    return FakeProvider(
        "acme-x",
        [
            _group(
                "acme-x",
                "gA",
                [
                    _cap(
                        "gA", "acme-x", "read_a", _READ,
                        desc="read register A",
                    ),
                ],
            ),
            _group(
                "acme-x",
                "gB",
                [
                    _cap(
                        "gB", "acme-x", "read_b", _READ,
                        desc="read register B",
                    ),
                ],
            ),
        ],
    )


def test_t21_unbound_group_falls_back_to_remaining_group():
    """Positive: gA binds nothing → gA excluded → reselection picks
    gB → its capability binds and executes."""
    provider = _two_group_provider()
    orch, model = _orchestrator(
        [provider],
        [
            {
                GROUP_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "capability_group_id": "gA",
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
            {
                GROUP_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "capability_group_id": "gB",
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "read_b",
                }
            },
            {ARGUMENTS_INSTRUCTION_ID: {"arguments": {}}},
        ],
    )
    attempt = orch.attempt("liste os registros")
    assert provider.calls == [("read_b", {})]
    group_requests = _requests(model, GROUP_SELECTION_INSTRUCTION_ID)
    assert len(group_requests) == 2
    assert "group_capability_unbound" in (
        group_requests[1].input_text
    )


def test_t21_named_provider_never_substituted_by_fallback():
    """Negative: an explicit ``mcp gA`` constraint survives the
    fallback — the remaining pool lacks the named surface, group
    selection fails closed and no other provider is invoked."""
    provider = _two_group_provider()
    orch, model = _orchestrator(
        [provider],
        [
            {
                GROUP_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "capability_group_id": "gA",
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
        ],
    )
    attempt = orch.attempt("use o mcp gA para listar os registros")
    assert provider.calls == []
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE


def test_t21_all_groups_unbound_terminates_insufficiency():
    """Negative: every live group attempted and unbound → terminal
    not_applicable_capability; the loop cannot spin."""
    provider = _two_group_provider()
    orch, model = _orchestrator(
        [provider],
        [
            {
                GROUP_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "capability_group_id": "gA",
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
            {
                GROUP_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "capability_group_id": "gB",
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
        ],
    )
    attempt = orch.attempt("liste os registros")
    assert provider.calls == []
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    # gA: select + reconcile; gB: select + reconcile — bounded.
    assert len(_requests(model, CAPABILITY_SELECTION_INSTRUCTION_ID)) == 4
    assert len(_requests(model, GROUP_SELECTION_INSTRUCTION_ID)) == 2


def test_canonical_subject_args_singularizes_plural_drift():
    from app.application.capability_provision.orchestration import (
        _canonical_subject_args,
    )

    rebound = _canonical_subject_args(
        {"description": "conectores elétricos"},
        "conectores elétricos",
    )
    assert rebound == {"description": "conector elétrico"}

    rebound = _canonical_subject_args(
        {"description": "terminais bala"}, "terminais bala"
    )
    assert rebound == {"description": "terminal bala"}


def test_canonical_subject_args_none_when_already_canonical():
    from app.application.capability_provision.orchestration import (
        _canonical_subject_args,
    )

    # already-canonical multi-token phrase -> head-noun fallback
    assert _canonical_subject_args(
        {"description": "espaguete termorretrátil"},
        "espaguete termorretrátil",
    ) == {"description": "espaguete"}
    # single-token canonical -> nothing to retry
    assert (
        _canonical_subject_args(
            {"description": "espaguete"}, "espaguete"
        )
        is None
    )
    # singular subject, plural merged -> rebound to designation
    rebound = _canonical_subject_args(
        {"description": "conectores elétricos"}, "conector elétrico"
    )
    assert rebound == {"description": "conector elétrico"}


_PREPARE = SpecialistOperationClass.PREPARE


def test_t21_fallback_never_binds_write_class_capability():
    """Negative sibling: a refused write ask must not be revived by
    the group fallback — a foreign CRUD surface that only binds
    through recovery is a cross-domain misbind, so the write-only
    group is spent and the turn fails closed."""
    provider = FakeProvider(
        "acme-x",
        [
            _group(
                "acme-x",
                "gA",
                [
                    _cap(
                        "gA", "acme-x", "read_a", _READ,
                        desc="read register A",
                    ),
                ],
            ),
            _group(
                "acme-x",
                "gB",
                [
                    _cap(
                        "gB", "acme-x", "prepare_change", _PREPARE,
                        desc="conventional entity CRUD prepare",
                    ),
                ],
            ),
        ],
    )
    orch, model = _orchestrator(
        [provider],
        [
            {
                GROUP_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "capability_group_id": "gA",
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
            {
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": False,
                    "remote_name": None,
                }
            },
            {
                GROUP_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "capability_group_id": "gB",
                }
            },
        ],
    )
    attempt = orch.attempt("apague o produto de codigo 10080092")
    # The write-only fallback surface is skipped — no capability
    # proposal inside gB, no invoke, terminal insufficiency.
    assert provider.calls == []
    assert attempt.status in (
        GovernedCapabilityStatus.NOT_APPLICABLE,
        GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
    )
    cap_requests = _requests(model, CAPABILITY_SELECTION_INSTRUCTION_ID)
    # 2 proposals inside gA (initial + reconcile retry) — none in gB.
    assert len(cap_requests) == 2
