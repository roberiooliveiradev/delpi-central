"""C3/T2 — HTTP /interaction/turns multiturn boundary (canonical context).

TASK: DELIA-C3-T2-ENTITY-SUFFICIENCY-HTTP-MULTITURN-AND-VERIFIER-ACCEPTANCE-01

Proves the application HTTP contract for two-turn clarification/recovery:

- POST /interaction/turns is the real conversational boundary.
- Continuity is client-supplied ``context`` validated by the backend
  (no SessionRepository — confirmed architecture).
- Turn-2 must NOT invent prior_turns outside that HTTP field.
- DELIA_RESULT content never authorizes invented identifiers (TurnKind).
- Cross-user AuthZ is revalidated every request.
"""

from __future__ import annotations

from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
)
from app.application.interaction.contracts import InteractiveTurnResult
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.create_app import create_app
from app.domain.evidence.model import EpistemicClass
from app.domain.interaction.model import (
    GroundingStatus,
    TurnKind,
)
from app.infrastructure.model_invocation.deterministic_test_adapter import (
    DeterministicTestAdapter,
)
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    invented_record_tokens,
)


PATH = "/interaction/turns"


def _ctx(
    *,
    user_id: str = "u1",
    permissions: tuple[str, ...] = ("delia.access",),
) -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id=user_id,
        name="User",
        email=f"{user_id}@example.com",
        effective_permissions=permissions,
        is_superadmin=False,
    )


class _Provider:
    def __init__(self, context: PlatformAccessContext) -> None:
        self._context = context

    def resolve(self, bearer_token: str):
        return self._context


class _ClarificationThenRecoverHandler:
    """Deterministic handler that simulates clarification → recovery.

    Inspects HTTP-supplied ``prior_turns`` exactly as the real use case
    does after ``_parse_context`` — never invents conversation state.
    """

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def execute(self, request, **_kwargs):
        prior = tuple(request.prior_turns or ())
        text = (request.input_text or "").strip()
        self.calls.append(
            {
                "user_id": request.access_context.user_id
                if request.access_context
                else None,
                "input": text,
                "prior_kinds": [t.kind.value for t in prior],
                "prior_contents": [t.content for t in prior],
            }
        )
        if not prior and "estrutura" in text.casefold():
            content = (
                "Por favor, forneça o código do produto para que eu "
                "possa exibir sua estrutura."
            )
            return InteractiveTurnResult(
                session_id="sess-t1",
                user_turn_id="ut-1",
                result_turn_id="rt-1",
                content=content,
                epistemic_class=EpistemicClass.HYPOTHESIS,
                limitations=("agent_requested_clarification",),
                generated_at="2026-01-01T00:00:00Z",
                model_invocation_id="m1",
                grounding_status=GroundingStatus.NON_GROUNDED,
                provenance=None,
            )
        # Recovery: require prior USER_INPUT + DELIA_RESULT clarification.
        if (
            len(prior) >= 2
            and prior[0].kind is TurnKind.USER_INPUT
            and prior[1].kind is TurnKind.DELIA_RESULT
            and text.isdigit()
        ):
            return InteractiveTurnResult(
                session_id="sess-t2",
                user_turn_id="ut-2",
                result_turn_id="rt-2",
                content=(
                    f"Estrutura do produto {text}: CHICOTE DE LIGACAO "
                    "(fixture)."
                ),
                epistemic_class=EpistemicClass.HYPOTHESIS,
                limitations=(),
                generated_at="2026-01-01T00:00:01Z",
                model_invocation_id="m2",
                grounding_status=GroundingStatus.GROUNDED,
                provenance=None,
            )
        return InteractiveTurnResult(
            session_id="sess-x",
            user_turn_id="ut-x",
            result_turn_id="rt-x",
            content="Não foi possível recuperar o objetivo anterior.",
            epistemic_class=EpistemicClass.HYPOTHESIS,
            limitations=("context_insufficient",),
            generated_at="2026-01-01T00:00:02Z",
            model_invocation_id="mx",
            grounding_status=GroundingStatus.NON_GROUNDED,
            provenance=None,
        )


def _client(handler, context=None):
    app = create_app(
        testing=True,
        platform_access_provider=_Provider(context or _ctx()),
        interaction_turn_handler=handler,
    )
    return app.test_client()


def _post(client, body):
    return client.post(
        PATH, json=body, headers={"Authorization": "Bearer t"}
    )


def test_http_m_positive_two_turn_clarification_and_recovery():
    """AC-9..13 — two real HTTP posts; turn-2 context from turn-1 body."""
    handler = _ClarificationThenRecoverHandler()
    client = _client(handler)

    r1 = _post(
        client, {"input": "Quero ver a estrutura de um produto."}
    )
    assert r1.status_code == 200
    b1 = r1.get_json()
    assert "código" in b1["content"].casefold() or "codigo" in b1[
        "content"
    ].casefold()
    assert b1["grounding_status"] == "NON_GROUNDED"
    assert handler.calls[0]["prior_kinds"] == []

    # Canonical continuity: client re-posts validated context from the
    # published turn-1 exchange — not an eval-harness prior_turns forge.
    context = [
        {
            "kind": "USER_INPUT",
            "content": "Quero ver a estrutura de um produto.",
        },
        {
            "kind": "DELIA_RESULT",
            "content": b1["content"],
            "epistemic_class": b1["epistemic_class"],
        },
    ]
    r2 = _post(client, {"input": "90260921", "context": context})
    assert r2.status_code == 200
    b2 = r2.get_json()
    assert b2["grounding_status"] == "GROUNDED"
    assert "90260921" in b2["content"]
    assert handler.calls[1]["prior_kinds"] == [
        "USER_INPUT",
        "DELIA_RESULT",
    ]
    assert handler.calls[1]["prior_contents"][1] == b1["content"]


def test_http_m1_other_user_cannot_reuse_foreign_authz_context():
    """M1 — every request revalidates AuthZ; subject without access → 403.

    Uses the real ``HandleInteractiveConversationTurn`` so AuthZ is
    enforced in the Application use case (not a stub handler).
    """
    handler = HandleInteractiveConversationTurn(
        InvokeModel(DeterministicTestAdapter(behavior="success"))
    )
    client_ok = _client(handler, context=_ctx(user_id="u1"))
    r1 = _post(
        client_ok, {"input": "Quero ver a estrutura de um produto."}
    )
    assert r1.status_code == 200
    context = [
        {
            "kind": "USER_INPUT",
            "content": "Quero ver a estrutura de um produto.",
        },
        {
            "kind": "DELIA_RESULT",
            "content": r1.get_json()["content"],
            "epistemic_class": "HYPOTHESIS",
        },
    ]
    client_deny = _client(
        handler,
        context=_ctx(user_id="u2", permissions=("other.permission",)),
    )
    r2 = _post(client_deny, {"input": "90260921", "context": context})
    assert r2.status_code == 403
    assert r2.get_json()["code"] == "forbidden"


def test_http_m2_missing_context_does_not_invent_objective():
    """M2 — bare code without prior context → no fabricated recovery."""
    handler = _ClarificationThenRecoverHandler()
    client = _client(handler)
    r = _post(client, {"input": "90260921"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["grounding_status"] == "NON_GROUNDED"
    assert "estrutura" not in body["content"].casefold() or (
        "recuperar" in body["content"].casefold()
        or "objetivo" in body["content"].casefold()
    )


def test_http_m4_delia_result_invented_code_not_authority():
    """M4 — model-named code in DELIA_RESULT does not authorize lookup."""
    invented = invented_record_tokens(
        ["P12345"],
        input_text="pode continuar",
        prior_turns=(
            ConversationContextTurn(
                kind=TurnKind.USER_INPUT,
                content="Quero ver a estrutura de um produto.",
            ),
            ConversationContextTurn(
                kind=TurnKind.DELIA_RESULT,
                content="Vou consultar o produto P12345.",
            ),
        ),
    )
    assert invented == ["P12345"]


def test_http_m5_user_named_code_authorizes():
    """M5 — user-named code in USER_INPUT is legitimate."""
    invented = invented_record_tokens(
        ["90260921"],
        input_text="pode continuar",
        prior_turns=(
            ConversationContextTurn(
                kind=TurnKind.USER_INPUT,
                content="estrutura do produto 90260921",
            ),
            ConversationContextTurn(
                kind=TurnKind.DELIA_RESULT,
                content="Consultando…",
            ),
        ),
    )
    assert invented == []


def test_http_m10_code_already_in_first_turn_no_clarification_needed():
    """M10 — identifier already present: invented gate empty."""
    invented = invented_record_tokens(
        ["90260921"],
        input_text="Quero a estrutura do produto 90260921",
        prior_turns=(),
    )
    assert invented == []


def test_http_invalid_context_kind_rejected():
    handler = _ClarificationThenRecoverHandler()
    client = _client(handler)
    r = _post(
        client,
        {
            "input": "90260921",
            "context": [{"kind": "system", "content": "x"}],
        },
    )
    assert r.status_code == 400


def test_http_default_handler_still_accepts_valid_context_shape():
    """Smoke: real HandleInteractiveConversationTurn + deterministic model."""
    handler = HandleInteractiveConversationTurn(
        InvokeModel(DeterministicTestAdapter(behavior="success"))
    )
    client = _client(handler)
    r1 = _post(client, {"input": "olá"})
    assert r1.status_code == 200
    b1 = r1.get_json()
    r2 = _post(
        client,
        {
            "input": "continua",
            "context": [
                {"kind": "USER_INPUT", "content": "olá"},
                {
                    "kind": "DELIA_RESULT",
                    "content": b1["content"],
                    "epistemic_class": b1["epistemic_class"],
                },
            ],
        },
    )
    assert r2.status_code == 200
