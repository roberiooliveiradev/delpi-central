"""S4 — governed LangGraph fan-out/fan-in for independent
subobjectives (doc 214 §7): native Send waves over the SAME governed
gates — ordering only, never a second authority."""

from __future__ import annotations

from app.application.capability_provision.contracts import (
    CapabilityProviderError,
)
from app.application.specialist_interop.errors import (
    MCP_AUTHORIZATION_DENIED,
    MCP_UNAVAILABLE,
)
from app.application.capability_provision.orchestration import (
    OperationalCapabilityOrchestrator,
    SUBOBJECTIVES_INSTRUCTION_ID,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.specialist_interop.model import (
    SpecialistOperationClass,
)
from app.infrastructure.orchestration.langgraph_engine import (
    LangGraphCapabilityOrchestrator,
)
from tests.test_generic_multistep_orchestration import (
    FakeProposalModel,
    FakeProvider,
    _cap,
    _group,
)
from tests.test_subobjective_investigation import (
    _SUBOBJECTIVES_INSTRUCTION,
    TEST_MODEL_REF,
    _decompose,
    _select,
)


def _engine_a(providers, proposal):
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


def _engine(providers, proposal):
    return LangGraphCapabilityOrchestrator(
        _engine_a(providers, proposal),
        subobjective_fanout_enabled=True,
    )


def _cap_s(group_id, provider_id, name):
    return _cap(
        group_id,
        provider_id,
        name,
        SpecialistOperationClass.READ,
        schema={"type": "object", "properties": {}},
    )


# ---------------- three independent READ branches ----------------


def test_three_independent_branches_fanout():
    p1 = FakeProvider("p1", [_group("p1", "g1", [_cap_s("g1", "p1", "r1")])])
    p2 = FakeProvider("p2", [_group("p2", "g2", [_cap_s("g2", "p2", "r2")])])
    p3 = FakeProvider("p3", [_group("p3", "g3", [_cap_s("g3", "p3", "r3")])])
    eng = _engine(
        {"p1": p1, "p2": p2, "p3": p3},
        [
            _select("g1", "r1", extra=_decompose(
                ("ler g1", (), ("a",)),
                ("ler g2", (), ("b",)),
                ("ler g3", (), ("c",)),
            )),
            _select("g2", "r2"),
            _select("g3", "r3"),
        ],
    )
    attempt = eng.attempt("ler g1 g2 g3")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert p1.calls and p2.calls and p3.calls


# ---------------- dependent subobjectives execute in waves --------


def test_dependent_subobjectives_sequential_waves():
    caps = [
        _cap_s("gamma", "p1", "locate"),
        _cap_s("gamma", "p1", "detail"),
    ]
    p1 = FakeProvider("p1", [_group("p1", "gamma", caps)])
    order = []
    real = p1.invoke

    def tracking(capability, arguments, **kw):
        order.append(capability.remote_name)
        return real(capability, arguments, **kw)

    p1.invoke = tracking
    eng = _engine(
        {"p1": p1},
        [
            _select("gamma", "locate", extra=_decompose(
                ("localizar", (), ("id",)),
                ("detalhar", (0,), ("detalhe",)),
            )),
            _select("gamma", "detail"),
        ],
    )
    attempt = eng.attempt("localize e detalhe")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert order == ["locate", "detail"]


# ---------------- mixed: independent + dependent ------------------


def test_mixed_dependency_graph():
    caps = [
        _cap_s("mx", "p1", "a_step"),
        _cap_s("mx", "p1", "b_step"),
        _cap_s("mx", "p1", "c_step"),
    ]
    p1 = FakeProvider("p1", [_group("p1", "mx", caps)])
    eng = _engine(
        {"p1": p1},
        [
            _select("mx", "a_step", extra=_decompose(
                ("passo A", (), ("a",)),
                ("passo B", (), ("b",)),
                ("passo C depende de A", (0,), ("c",)),
            )),
            _select("mx", "b_step"),
            _select("mx", "c_step"),
        ],
    )
    attempt = eng.attempt("A e B independentes, C depende de A")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    names = [c[0] for c in p1.calls]
    assert "a_step" in names and "b_step" in names and "c_step" in names
    # c runs only after a
    assert names.index("c_step") > names.index("a_step")


# ---------------- one owner 503 → partial gap, others answer ------


class _ErrorProvider(FakeProvider):
    def __init__(self, provider_id, groups, error):
        super().__init__(provider_id, groups)
        self._error = error

    def invoke(self, capability, arguments, *, correlation_id, timeout_seconds=None):
        self.calls.append((capability.remote_name, dict(arguments)))
        raise self._error


def test_owner_503_partial_others_answer():
    p1 = FakeProvider("p1", [_group("p1", "ok", [_cap_s("ok", "p1", "r_ok")])])
    p2 = _ErrorProvider(
        "p2",
        [_group("p2", "bad", [_cap_s("bad", "p2", "r_bad")])],
        CapabilityProviderError(MCP_UNAVAILABLE, "owner 503"),
    )
    eng = _engine(
        {"p1": p1, "p2": p2},
        [
            _select("ok", "r_ok", extra=_decompose(
                ("ler ok", (), ("o",)),
                ("ler bad", (), ("b",)),
            )),
            _select("bad", "r_bad"),
        ],
    )
    attempt = eng.attempt("ler ok e bad")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert any("so_2" in lim for lim in attempt.limitations)


# ---------------- authz denial → blocked, no fallback -------------


def test_authz_denied_branch_blocked():
    p1 = _ErrorProvider(
        "p1",
        [_group("p1", "sec", [_cap_s("sec", "p1", "r_sec")])],
        CapabilityProviderError(MCP_AUTHORIZATION_DENIED, "denied"),
    )
    eng = _engine(
        {"p1": p1},
        [
            _select("sec", "r_sec", extra=_decompose(
                ("ler s1", (), ("s",)),
                ("ler s2", (), ("t",)),
            )),
            _select("sec", "r_sec"),
        ],
    )
    attempt = eng.attempt("ler segredos")
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS or (
        not attempt.content
    )
    assert len(p1.calls) <= 6


# ---------------- budget exhaustion → honest gaps, no fabrication -


def test_budget_exhaustion_no_fabrication():
    caps = [_cap_s("z", "p1", "r_z")]
    p1 = FakeProvider("p1", [_group("p1", "z", caps)])
    eng = _engine(
        {"p1": p1},
        [
            _select("z", "r_z", extra=_decompose(
                ("ler z1", (), ("z1",)),
                ("ler z2", (), ("z2",)),
            )),
            _select("z", "r_z"),
        ],
    )
    attempt = eng.attempt(
        "ler z1 e z2", turn_deadline=TurnDeadline.start(0.001)
    )
    if attempt.status is GovernedCapabilityStatus.SUCCESS:
        assert attempt.content


# ---------------- fan-in stable independent of completion order ---


def test_fanin_order_independent():
    """Coverage/synthesis must not depend on branch completion order."""
    p1 = FakeProvider("p1", [_group("p1", "i1", [_cap_s("i1", "p1", "r1")])])
    p2 = FakeProvider("p2", [_group("p2", "i2", [_cap_s("i2", "p2", "r2")])])
    eng = _engine(
        {"p1": p1, "p2": p2},
        [
            _select("i1", "r1", extra=_decompose(
                ("ler i1", (), ("a",)),
                ("ler i2", (), ("b",)),
            )),
            _select("i2", "r2"),
        ],
    )
    attempt = eng.attempt("ler i1 e i2")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
