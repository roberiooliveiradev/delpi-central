"""Generic bounded multi-step orchestration — ARCH-DRIFT-DELIA-
GENERIC-MCP-MULTISTEP-ORCHESTRATION-R1 (ledger §6.140).

Proves the R1 contract on a fake FOURTH owner whose vocabulary is
deliberately unrelated to VISTA/TÉO/DAVI:

- RESOLVER is a role, not a tool class — a same-owner non-mutating
  capability resolves a missing target input (name -> id);
- ambiguity returns a bounded CLARIFICATION_REQUIRED, never a silent
  pick and never an invented id;
- ANALYSIS is first-class and may feed PREPARE generically — never a
  direct ACT;
- the structural confirmation_requirement on the PREPARE proposal is
  the sole write-policy authority;
- opaque proposal handles never reach user-visible surfaces.

No owner-name or tool-name branch is exercised — the fixture names
are meaningless to the runtime.
"""

from __future__ import annotations

import json

from app.application.capability_provision.contracts import (
    CapabilityGroup,
    ProviderCapability,
    ProviderSurface,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    CONTINUATION_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    RESOLVER_SELECTION_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    ProviderInvocationPayload,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import ModelRef, SourceRef
from app.domain.interaction.model import TurnKind
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

PURPOSE_IDS = frozenset(
    {
        GROUP_SELECTION_INSTRUCTION_ID,
        CAPABILITY_SELECTION_INSTRUCTION_ID,
        ARGUMENTS_INSTRUCTION_ID,
        RESOLVER_SELECTION_INSTRUCTION_ID,
        CONTINUATION_INSTRUCTION_ID,
    }
)


class FakeProposalModel:
    """Selection model stub — routes proposals by task_purpose_id."""

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
            if isinstance(item, dict) and set(item) & PURPOSE_IDS:
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


class FakeProvider:
    """Provider stub: fixed group surface, recorded invocations."""

    def __init__(self, provider_id: str, groups, outcomes=None):
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
        if key in self._outcomes:
            return self._outcomes[key]
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


def _outcome(group_id, remote_name, text, structured=None):
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
        structured=structured,
    )


def _select(
    group_key, remote_name, arguments=None, extra=None,
    arg_payload=None,
):
    proposal = {
        GROUP_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "capability_group_id": group_key,
        },
        CAPABILITY_SELECTION_INSTRUCTION_ID: {
            "applicable": True,
            "remote_name": remote_name,
        },
        ARGUMENTS_INSTRUCTION_ID: (
            arg_payload
            if arg_payload is not None
            else {"arguments": arguments or {}}
        ),
    }
    if extra:
        proposal.update(extra)
    return proposal


def _orchestrator(providers, proposal):
    return OperationalCapabilityOrchestrator(
        providers,
        invoke_model=InvokeModel(FakeProposalModel(proposal)),
        model_ref=TEST_MODEL_REF,
    )


# --- fake fourth owner: neutral vocabulary, unrelated to any real owner

_HANDLE = "opaque-stage-handle-77"
GROUP_KEY = "fake-mcp:quarto"


def _quarto_caps():
    return [
        _cap(
            "quarto", "fake-mcp", "find_fixture",
            SpecialistOperationClass.READ,
            schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            desc="locate fixtures by human-readable name",
        ),
        _cap(
            "quarto", "fake-mcp", "fixture_detail",
            SpecialistOperationClass.READ,
            schema={
                "type": "object",
                "properties": {"fixture_id": {"type": "string"}},
                "required": ["fixture_id"],
            },
            desc="read the full record of one fixture",
        ),
        _cap(
            "quarto", "fake-mcp", "evaluate_fixture",
            SpecialistOperationClass.ANALYSIS,
            schema={
                "type": "object",
                "properties": {"topic": {"type": "string"}},
            },
            desc="owner-side assessment of a fixture request",
        ),
        _cap(
            "quarto", "fake-mcp", "draft_adjustment",
            SpecialistOperationClass.PREPARE,
            schema={
                "type": "object",
                "properties": {
                    "fixture_id": {"type": "string"},
                    "note": {"type": "string"},
                },
            },
            desc="stage a fixture mutation for review",
        ),
        _cap(
            "quarto", "fake-mcp", "apply_adjustment",
            SpecialistOperationClass.ACT,
            schema={
                "type": "object",
                "properties": {
                    "proposal_handle": {"type": "string"},
                    "confirmation": {"type": "boolean"},
                    "idempotency_key": {"type": "string"},
                },
                "required": ["proposal_handle", "confirmation"],
            },
            desc="execute a staged fixture adjustment",
        ),
    ]


def _quarto_provider(outcomes=None):
    return FakeProvider(
        "fake-mcp",
        [_group("fake-mcp", "quarto", _quarto_caps())],
        outcomes=outcomes or {},
    )


def _prepare_outcome(*, confirmation: bool | None, handle=_HANDLE):
    requirement = (
        {"explicit_user_confirmation": confirmation}
        if confirmation is not None
        else None
    )
    data = {
        "capability": "draft_adjustment",
        "proposal_handle": handle,
        "exact_change": {"field": "label", "to": "Novo rotulo"},
        "validation_result": {"ready": True},
        "ready": True,
    }
    if requirement is not None:
        data["confirmation_requirement"] = requirement
    return _outcome(
        "quarto", "draft_adjustment", "Ajuste preparado.",
        structured={"data": data},
    )


_COMMIT = _outcome(
    "quarto",
    "apply_adjustment",
    "Ajuste aplicado.",
    structured={
        "data": {
            "capability": "apply_adjustment",
            "success": True,
            "verified": True,
            "postcondition": {"field": "label", "value": "Novo rotulo"},
        }
    },
)


def _confirmation(attempt):
    ctx = attempt.confirmation_context
    return {
        "decision": "CONFIRM",
        "proposal_digest": ctx["proposal_digest"],
        "preview_fingerprint": ctx["preview_fingerprint"],
        "session_id": ctx["session_id"],
    }


# --- RESOLVER: name -> id -------------------------------------------------


def test_resolver_resolves_name_to_unique_id():
    """Target requires an owner id absent from the turn; one generic
    same-owner READ resolver supplies exactly one candidate and the
    target is invoked with the owner-returned id."""
    provider = _quarto_provider(
        {
            ("quarto", "find_fixture"): _outcome(
                "quarto", "find_fixture", "1 registro",
                structured={
                    "matches": [
                        {
                            "fixture_id": "FX-0042",
                            "name": "Bomba hidraulica",
                        }
                    ]
                },
            ),
            ("quarto", "fixture_detail"): _outcome(
                "quarto", "fixture_detail", "detalhe do ativo"
            ),
        }
    )
    orch = _orchestrator(
        [provider],
        [
            _select(
                GROUP_KEY,
                "fixture_detail",
                arg_payload={
                    "arguments": {},
                    "missing_inputs": ["fixture_id"],
                },
            ),
            {
                RESOLVER_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "find_fixture",
                }
            },
            {ARGUMENTS_INSTRUCTION_ID: {"arguments": {"query": "Bomba"}}},
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"fixture_id": "FX-0042"}
                }
            },
        ],
    )
    attempt = orch.attempt(
        "me mostre o ativo Bomba hidraulica",
        actor_user_id="u1",
        session_id="s1",
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    names = [c[0] for c in provider.calls]
    assert names == ["find_fixture", "fixture_detail"]
    assert provider.calls[-1][1]["fixture_id"] == "FX-0042"


def test_resolver_ambiguity_yields_bounded_clarification():
    """Two plausible owner candidates -> CLARIFICATION_REQUIRED with
    both bounded entries; target, PREPARE and ACT never run."""
    provider = _quarto_provider(
        {
            ("quarto", "find_fixture"): _outcome(
                "quarto", "find_fixture", "2 registros",
                structured={
                    "matches": [
                        {"fixture_id": "FX-0057", "name": "Bomba A"},
                        {"fixture_id": "FX-0039", "name": "Bomba A"},
                    ]
                },
            ),
        }
    )
    orch = _orchestrator(
        [provider],
        [
            _select(
                GROUP_KEY,
                "fixture_detail",
                arg_payload={
                    "arguments": {},
                    "missing_inputs": ["fixture_id"],
                },
            ),
            {
                RESOLVER_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "find_fixture",
                }
            },
            {ARGUMENTS_INSTRUCTION_ID: {"arguments": {"query": "Bomba A"}}},
        ],
    )
    attempt = orch.attempt(
        "me mostre a Bomba A", actor_user_id="u1", session_id="s1"
    )
    assert (
        attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    )
    assert "FX-0057" in attempt.content
    assert "FX-0039" in attempt.content
    names = [c[0] for c in provider.calls]
    assert names == ["find_fixture"]


def test_resolver_never_invents_identifier():
    """A rebuilt id that does not occur in the owner resolver payload
    is an invention — fail closed to clarification, never invoke."""
    provider = _quarto_provider(
        {
            ("quarto", "find_fixture"): _outcome(
                "quarto", "find_fixture", "1 registro",
                structured={
                    "matches": [
                        {"fixture_id": "FX-0042", "name": "Bomba"}
                    ]
                },
            ),
        }
    )
    orch = _orchestrator(
        [provider],
        [
            _select(
                GROUP_KEY,
                "fixture_detail",
                arg_payload={
                    "arguments": {},
                    "missing_inputs": ["fixture_id"],
                },
            ),
            {
                RESOLVER_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "find_fixture",
                }
            },
            {ARGUMENTS_INSTRUCTION_ID: {"arguments": {"query": "Bomba"}}},
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"fixture_id": "FX-9999"}
                }
            },
        ],
    )
    attempt = orch.attempt(
        "me mostre a Bomba", actor_user_id="u1", session_id="s1"
    )
    assert (
        attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    )
    assert "fixture_detail" not in [c[0] for c in provider.calls]


def test_invented_identifier_demoted_to_resolver():
    """The model proposes a complete argument set whose identifier has
    no provenance (absent from the user message, workspace, evidence
    and owner schema literals). The invented value is demoted to a
    missing input: the generic resolver resolves the real id and the
    target is invoked with owner evidence — the invented value never
    reaches the owner."""
    provider = _quarto_provider(
        {
            ("quarto", "find_fixture"): _outcome(
                "quarto", "find_fixture", "1 registro",
                structured={
                    "matches": [
                        {"fixture_id": "FX-0042", "name": "Bomba"}
                    ]
                },
            ),
            ("quarto", "fixture_detail"): _outcome(
                "quarto", "fixture_detail", "detalhe"
            ),
        }
    )
    orch = _orchestrator(
        [provider],
        [
            _select(
                GROUP_KEY,
                "fixture_detail",
                # no missing_inputs declared — the model 'filled' the
                # id itself, with a value present in no trusted source
                arg_payload={"arguments": {"fixture_id": "FX-9999"}},
            ),
            {
                RESOLVER_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "find_fixture",
                }
            },
            {ARGUMENTS_INSTRUCTION_ID: {"arguments": {"query": "Bomba"}}},
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"fixture_id": "FX-0042"}
                }
            },
        ],
    )
    attempt = orch.attempt(
        "me mostre a Bomba", actor_user_id="u1", session_id="s1"
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    names = [c[0] for c in provider.calls]
    assert names == ["find_fixture", "fixture_detail"]
    # only the owner-evidence id reaches the wire
    assert provider.calls[-1][1]["fixture_id"] == "FX-0042"
    assert "FX-9999" not in json.dumps(provider.calls)


def test_invented_identifier_unresolved_asks_user():
    """When the resolver cannot produce evidence for the demoted id,
    the turn fails closed to clarification — the invented identifier
    is never invoked and never asked back as a fabricated value."""
    provider = _quarto_provider(
        {
            ("quarto", "find_fixture"): _outcome(
                "quarto", "find_fixture", "0 registros",
                structured={"matches": []},
            ),
        }
    )
    orch = _orchestrator(
        [provider],
        [
            _select(
                GROUP_KEY,
                "fixture_detail",
                arg_payload={"arguments": {"fixture_id": "FX-9999"}},
            ),
            {
                RESOLVER_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "find_fixture",
                }
            },
            {ARGUMENTS_INSTRUCTION_ID: {"arguments": {"query": "Bomba"}}},
        ],
    )
    attempt = orch.attempt(
        "me mostre a Bomba", actor_user_id="u1", session_id="s1"
    )
    assert (
        attempt.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    )
    assert "fixture_detail" not in [c[0] for c in provider.calls]
    assert "FX-9999" not in (attempt.content or "")


# --- ANALYSIS --------------------------------------------------------------


def test_analysis_to_prepare_continuation():
    """ANALYSIS evidence feeds a semantically selected same-owner
    PREPARE — never a direct ACT."""
    provider = _quarto_provider(
        {
            ("quarto", "evaluate_fixture"): _outcome(
                "quarto", "evaluate_fixture", "avaliacao",
                structured={
                    "data": {
                        "assessment": "label inconsistente",
                        "candidate": {"fixture_id": "FX-0042"},
                    }
                },
            ),
            ("quarto", "draft_adjustment"): _prepare_outcome(
                confirmation=True
            ),
        }
    )
    orch = _orchestrator(
        [provider],
        [
            _select(GROUP_KEY, "evaluate_fixture"),
            {
                CONTINUATION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "draft_adjustment",
                }
            },
            {
                ARGUMENTS_INSTRUCTION_ID: {
                    "arguments": {"fixture_id": "FX-0042"}
                }
            },
        ],
    )
    attempt = orch.attempt(
        "avalie e prepare a correcao do ativo",
        actor_user_id="u1",
        session_id="s1",
    )
    assert (
        attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    )
    names = [c[0] for c in provider.calls]
    assert names == ["evaluate_fixture", "draft_adjustment"]
    assert "apply_adjustment" not in names


def test_analysis_terminal_when_no_prepare_applies():
    """An analysis-only goal renders the owner analysis terminally —
    no PREPARE is triggered."""
    provider = _quarto_provider(
        {
            ("quarto", "evaluate_fixture"): _outcome(
                "quarto",
                "evaluate_fixture",
                "Recomendacao do owner: revisar rotulo.",
            ),
        }
    )
    orch = _orchestrator(
        [provider],
        [
            _select(GROUP_KEY, "evaluate_fixture"),
            {CONTINUATION_INSTRUCTION_ID: {"applicable": False}},
        ],
    )
    attempt = orch.attempt(
        "qual avaliacao voce recomenda?",
        actor_user_id="u1",
        session_id="s1",
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert "Recomendacao" in attempt.content
    names = [c[0] for c in provider.calls]
    assert names == ["evaluate_fixture"]


# --- write policy ------------------------------------------------------------


def test_direct_write_executes_act_same_turn():
    """Structural explicit_user_confirmation=False -> governed ACT in
    the same turn, postcondition-verified."""
    provider = _quarto_provider(
        {
            ("quarto", "draft_adjustment"): _prepare_outcome(
                confirmation=False
            ),
            ("quarto", "apply_adjustment"): _COMMIT,
        }
    )
    orch = _orchestrator(
        [provider],
        [_select(GROUP_KEY, "draft_adjustment", {"fixture_id": "FX-1"})],
    )
    attempt = orch.attempt(
        "corrija o rotulo do ativo FX-1",
        actor_user_id="u1",
        session_id="s1",
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    names = [c[0] for c in provider.calls]
    assert names == ["draft_adjustment", "apply_adjustment"]
    assert provider.calls[-1][1]["proposal_handle"] == _HANDLE


def test_confirm_policy_gates_act_until_confirmation():
    """explicit_user_confirmation=True -> CONFIRMATION_REQUIRED; ACT
    runs exactly once after a bound confirmation."""
    provider = _quarto_provider(
        {
            ("quarto", "draft_adjustment"): _prepare_outcome(
                confirmation=True
            ),
            ("quarto", "apply_adjustment"): _COMMIT,
        }
    )
    orch = _orchestrator(
        [provider],
        [_select(GROUP_KEY, "draft_adjustment", {"fixture_id": "FX-1"})],
    )
    pending = orch.attempt(
        "corrija o rotulo do ativo FX-1",
        actor_user_id="u1",
        session_id="s1",
    )
    assert (
        pending.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    )
    assert "apply_adjustment" not in [c[0] for c in provider.calls]

    result = orch.attempt(
        "",
        actor_user_id="u1",
        confirmation=_confirmation(pending),
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    commits = [
        c for c in provider.calls if c[0] == "apply_adjustment"
    ]
    assert len(commits) == 1
    assert commits[0][1]["proposal_handle"] == _HANDLE
    assert commits[0][1]["confirmation"] is True


def test_unknown_policy_fails_closed():
    """No structural confirmation_requirement on the PREPARE proposal
    -> WRITE_REJECTED owner_policy_invalid; ACT never runs."""
    provider = _quarto_provider(
        {("quarto", "draft_adjustment"): _prepare_outcome(
            confirmation=None
        )}
    )
    orch = _orchestrator(
        [provider],
        [_select(GROUP_KEY, "draft_adjustment", {"fixture_id": "FX-1"})],
    )
    attempt = orch.attempt(
        "corrija o rotulo do FX-1", actor_user_id="u1", session_id="s1"
    )
    assert attempt.status is GovernedCapabilityStatus.WRITE_REJECTED
    assert attempt.error_code == "owner_policy_invalid"
    assert "apply_adjustment" not in [c[0] for c in provider.calls]


def test_opaque_handle_never_reaches_user_surface():
    """The owner leaks its opaque handle into content_text and nested
    fields — every user-visible surface shows digests only."""
    provider = _quarto_provider(
        {
            ("quarto", "draft_adjustment"): _outcome(
                "quarto",
                "draft_adjustment",
                f"Proposta {_HANDLE} pronta para confirmar.",
                structured={
                    "data": {
                        "capability": "draft_adjustment",
                        "proposal_handle": _HANDLE,
                        "proposal": {"handle": _HANDLE},
                        "exact_change": {"field": "label", "to": "X"},
                        "validation_result": {"ready": True},
                        "ready": True,
                        "confirmation_requirement": {
                            "explicit_user_confirmation": True,
                        },
                    }
                },
            ),
        }
    )
    orch = _orchestrator(
        [provider],
        [_select(GROUP_KEY, "draft_adjustment", {"fixture_id": "FX-1"})],
    )
    attempt = orch.attempt(
        "corrija o rotulo do FX-1", actor_user_id="u1", session_id="s1"
    )
    assert (
        attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    )
    assert _HANDLE not in (attempt.content or "")
    assert _HANDLE not in json.dumps(
        attempt.confirmation_context or {}, default=str
    )


# --- prior context ------------------------------------------------------------


def test_prior_turns_reach_selection_proposals():
    """Bounded request-scoped prior turns are forwarded to the model
    proposal stage — transient context, never persisted state."""
    provider = _quarto_provider(
        {
            ("quarto", "fixture_detail"): _outcome(
                "quarto", "fixture_detail", "detalhe"
            ),
        }
    )
    model = FakeProposalModel(
        [
            _select(
                GROUP_KEY, "fixture_detail", {"fixture_id": "FX-0057"}
            )
        ]
    )
    orch = OperationalCapabilityOrchestrator(
        [provider],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    turns = (
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content="Encontrei FX-0057 e FX-0039.",
        ),
    )
    attempt = orch.attempt(
        "o primeiro",
        actor_user_id="u1",
        session_id="s1",
        prior_turns=turns,
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert model.requests
    assert model.requests[0].prior_context == turns
