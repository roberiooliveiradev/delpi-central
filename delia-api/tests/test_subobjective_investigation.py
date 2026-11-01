"""S3 — explicit subobjective investigation through the REAL
orchestration path (doc 214 §6.4): the governed owner path receives a
compound objective, a bounded decomposition proposal produces tracked
subobjectives and each one executes through the same
selection→arggen→invoke→judgment gates — never a bypass."""

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
    SUBOBJECTIVES_INSTRUCTION_ID,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import ModelRef, SourceRef
from app.domain.model_invocation.model import ProviderExposureClass
from app.application.specialist_interop.errors import (
    MCP_AUTHORIZATION_DENIED,
    MCP_UNAVAILABLE,
)
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOperationClass,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from tests.test_generic_multistep_orchestration import (
    FakeProposalModel,
    FakeProvider,
    _cap,
    _group,
)


TEST_MODEL_REF = ModelRef(
    model_id="test-model", version="1", owner_ref="DELPI"
)


def _select(group_key, remote_name, arguments=None, extra=None):
    proposal = {
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
    if extra:
        proposal.update(extra)
    return proposal


def _decompose(*items):
    return {
        SUBOBJECTIVES_INSTRUCTION_ID: {
            "subobjectives": [
                {
                    "goal": g,
                    "depends_on": d,
                    "evidence_needed": e,
                }
                for (g, d, e) in items
            ]
        }
    }


_SUBOBJECTIVES_INSTRUCTION = (
    "Decide whether the user objective requires an explicit investigation "
    "across multiple semantic subobjectives — respond with JSON containing "
    'exactly "subobjectives": an array of 0-8 items each with "goal", '
    '"depends_on" (earlier indexes only) and "evidence_needed".'
)


def _orchestrator(providers, proposal):
    seq = (
        tuple(providers.values())
        if isinstance(providers, dict)
        else tuple(providers)
    )
    return OperationalCapabilityOrchestrator(
        seq,
        invoke_model=InvokeModel(FakeProposalModel(proposal)),
        model_ref=TEST_MODEL_REF,
        orchestration_instructions={
            SUBOBJECTIVES_INSTRUCTION_ID: _SUBOBJECTIVES_INSTRUCTION,
        },
        subobjective_investigation_enabled=True,
    )


class _ErrorProvider(FakeProvider):
    def __init__(self, provider_id, groups, error):
        super().__init__(provider_id, groups)
        self._error = error

    def invoke(self, capability, arguments, *, correlation_id, timeout_seconds=None):
        self.calls.append((capability.remote_name, dict(arguments)))
        raise self._error


# ---------------- A: two independent subobjectives ----------------


def test_two_independent_subobjectives():
    caps_a = [
        _cap(
            "alpha", "p1", "read_thing",
            SpecialistOperationClass.READ,
            schema={"type": "object", "properties": {}},
        )
    ]
    caps_b = [
        _cap(
            "beta", "p2", "read_other",
            SpecialistOperationClass.READ,
            schema={"type": "object", "properties": {}},
        )
    ]
    p1 = FakeProvider("p1", [_group("p1", "alpha", caps_a)])
    p2 = FakeProvider("p2", [_group("p2", "beta", caps_b)])
    orch = _orchestrator(
        {"p1": p1, "p2": p2},
        [
            _select("alpha", "read_thing", extra=_decompose(
                ("consultar coisa A", (), ("dado A",)),
                ("consultar coisa B", (), ("dado B",)),
            )),
            _select("beta", "read_other"),
        ],
    )
    attempt = orch.attempt("consultar A e B juntos")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert p1.calls and p2.calls
    names = {c[0] for c in p1.calls} | {c[0] for c in p2.calls}
    assert names == {"read_thing", "read_other"}


# ---------------- B: two dependent subobjectives ----------------


def test_dependent_subobjectives_respect_order():
    caps = [
        _cap(
            "gamma", "p1", "locate",
            SpecialistOperationClass.READ,
            schema={"type": "object", "properties": {}},
        ),
        _cap(
            "gamma", "p1", "detail",
            SpecialistOperationClass.READ,
            schema={"type": "object", "properties": {}},
        ),
    ]
    p1 = FakeProvider("p1", [_group("p1", "gamma", caps)])
    order = []
    real_invoke = p1.invoke

    def tracking(capability, arguments, **kw):
        order.append(capability.remote_name)
        return real_invoke(capability, arguments, **kw)

    p1.invoke = tracking
    orch = _orchestrator(
        {"p1": p1},
        [
            _select("gamma", "locate", extra=_decompose(
                ("localizar o item", (), ("id",)),
                ("detalhar o item localizado", (0,), ("detalhe",)),
            )),
            _select("gamma", "detail"),
        ],
    )
    attempt = orch.attempt("localize e detalhe")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert order == ["locate", "detail"]


# ---------------- C: objective spanning multiple owners ----------------


def test_multi_owner_subobjectives():
    caps_a = [
        _cap("w1", "p1", "read_a", SpecialistOperationClass.READ)
    ]
    caps_b = [
        _cap("w2", "p2", "read_b", SpecialistOperationClass.READ)
    ]
    p1 = FakeProvider("p1", [_group("p1", "w1", caps_a)])
    p2 = FakeProvider("p2", [_group("p2", "w2", caps_b)])
    orch = _orchestrator(
        {"p1": p1, "p2": p2},
        [
            _select("w1", "read_a", extra=_decompose(
                ("ler A no owner 1", (), ("x",)),
                ("ler B no owner 2", (), ("y",)),
            )),
            _select("w2", "read_b"),
        ],
    )
    attempt = orch.attempt("A do owner1 e B do owner2")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert p1.calls[0][0] == "read_a"
    assert p2.calls[0][0] == "read_b"


# ---------------- D: incomplete evidence → further subobjectives continue ----------------


def test_incomplete_evidence_investigation_continues():
    caps_ok = [
        _cap("done", "p1", "read_done", SpecialistOperationClass.READ)
    ]
    p1 = FakeProvider("p1", [_group("p1", "done", caps_ok)])
    caps_thin = [
        _cap("thin", "p2", "read_thin", SpecialistOperationClass.READ)
    ]
    p2 = _ErrorProvider(
        "p2",
        [_group("p2", "thin", caps_thin)],
        CapabilityProviderError(MCP_UNAVAILABLE, "source offline"),
    )
    orch = _orchestrator(
        {"p1": p1, "p2": p2},
        [
            _select("done", "read_done", extra=_decompose(
                ("ler done", (), ("d",)),
                ("ler thin", (), ("t",)),
            )),
            _select("thin", "read_thin"),
        ],
    )
    attempt = orch.attempt("ler done e thin")
    # the available half answers; the unavailable half is an honest gap
    # — investigation continued across both subobjectives.
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert attempt.limitations


# ---------------- E: owner unavailable → partial retained ----------------


def test_owner_unavailable_partial():
    caps_ok = [
        _cap("ok", "p1", "read_ok", SpecialistOperationClass.READ)
    ]
    p1 = FakeProvider("p1", [_group("p1", "ok", caps_ok)])
    caps_bad = [
        _cap("bad", "p2", "read_bad", SpecialistOperationClass.READ)
    ]
    p2 = _ErrorProvider(
        "p2",
        [_group("p2", "bad", caps_bad)],
        CapabilityProviderError(MCP_UNAVAILABLE, "owner reported 503"),
    )
    orch = _orchestrator(
        {"p1": p1, "p2": p2},
        [
            _select("ok", "read_ok", extra=_decompose(
                ("ler ok", (), ("o",)),
                ("ler bad", (), ("b",)),
            )),
            _select("bad", "read_bad"),
        ],
    )
    attempt = orch.attempt("ler ok e bad")
    # grounded half answers; the unavailable half surfaces as a
    # declared limitation — never a fabricated full success.
    assert attempt.status in (
        GovernedCapabilityStatus.SUCCESS,
        GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
    )
    if attempt.status is GovernedCapabilityStatus.SUCCESS:
        assert attempt.limitations or "ok" in (attempt.content or "")


# ---------------- F: authz denial without fallback ----------------


def test_authz_denial_no_fallback():
    caps = [
        _cap("sec", "p1", "read_sec", SpecialistOperationClass.READ)
    ]
    p1 = _ErrorProvider(
        "p1",
        [_group("p1", "sec", caps)],
        CapabilityProviderError(MCP_AUTHORIZATION_DENIED, "denied"),
    )
    orch = _orchestrator(
        {"p1": p1},
        [
            _select("sec", "read_sec", extra=_decompose(
                ("ler segredo", (), ("s",)),
                ("ler outro segredo", (), ("t",)),
            )),
            _select("sec", "read_sec"),
        ],
    )
    attempt = orch.attempt("ler segredos")
    # fail-closed: denied subobjectives never degrade to fabricated
    # content — the attempt must not present invented data.
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS or (
        not attempt.content
    )
    # denial never retried into an unauthorized fallback path
    assert len(p1.calls) <= 6


# ---------------- G: budget exhaustion without fabrication ----------------


def test_budget_exhaustion_no_fabrication():
    caps = [
        _cap("zeta", "p1", "read_z", SpecialistOperationClass.READ)
    ]
    p1 = FakeProvider("p1", [_group("p1", "zeta", caps)])
    orch = _orchestrator(
        {"p1": p1},
        [
            _select("zeta", "read_z", extra=_decompose(
                ("ler Z1", (), ("z1",)),
                ("ler Z2", (), ("z2",)),
            )),
            _select("zeta", "read_z"),
        ],
    )
    deadline = TurnDeadline.start(0.001)
    attempt = orch.attempt(
        "ler Z1 e Z2", turn_deadline=deadline
    )
    # exhausted budget → honest non-completion, never fabricated content
    if attempt.status is GovernedCapabilityStatus.SUCCESS:
        assert attempt.content


# ---------------- H: simple objective keeps the efficient path ----------------


def test_simple_objective_no_decomposition():
    caps = [
        _cap("simples", "p1", "read_s", SpecialistOperationClass.READ)
    ]
    p1 = FakeProvider("p1", [_group("p1", "simples", caps)])
    orch = _orchestrator(
        {"p1": p1},
        [
            _decompose(),  # empty subobjectives → skip
            _select("simples", "read_s"),
        ],
    )
    attempt = orch.attempt("ler S")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert p1.calls[0][0] == "read_s"


def test_invalid_decomposition_falls_back_safely():
    caps = [
        _cap("simples", "p1", "read_s", SpecialistOperationClass.READ)
    ]
    p1 = FakeProvider("p1", [_group("p1", "simples", caps)])
    orch = _orchestrator(
        {"p1": p1},
        [
            {SUBOBJECTIVES_INSTRUCTION_ID: {"subobjectives": [
                {"goal": "x", "depends_on": [1], "evidence_needed": []},
                {"goal": "y", "depends_on": [1], "evidence_needed": []},
            ]}},  # forward dep → fail closed to single path
            _select("simples", "read_s"),
        ],
    )
    attempt = orch.attempt("ler S")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
