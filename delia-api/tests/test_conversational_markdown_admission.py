"""Conversational `markdown_safe` admission (CP-333 remediation).

Decision f09acc8544 (CP-333 evidence): the ordinary governed
conversational COMPOSITION_MODEL result — valid non-empty ``answer``,
``message_kind=RESULT`` — may populate the existing
``InteractiveTurnResult.presentation_markdown`` from exactly that
admitted ``content``. Provider/owner ``content_text``, governed
Category-B projections, errors, denials, confirmations and write
lifecycle text remain v1-plain.

``markdown_safe`` attests safe *display* eligibility only: the v2
consumer still neutralizes links without authorized source, images,
HTML and executable code. It never attests grounding or factuality.
"""

from __future__ import annotations

import dataclasses
import json

from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    InteractiveTurnRequest,
)
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
    serialize_result,
)
from app.application.interaction.presentation import (
    _MAX_BLOCK_TEXT_CHARS,
    compose_presentation,
)
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.domain.model_invocation.model import ProviderExposureClass


SIPOC_ANSWER = (
    "A metodologia SIPOC organiza o processo em cinco etapas:\n\n"
    "**1. Suppliers (Fornecedores)**\n"
    "- Identificam quem fornece os insumos.\n\n"
    "**2. Inputs (Entradas)**\n"
    "- Materia-prima, informacoes e recursos.\n\n"
    "**3. Process (Processo)**\n"
    "1. Recebimento do material.\n"
    "2. Usinagem da peca.\n"
    "3. Inspecao dimensional.\n\n"
    "**4. Outputs (Saidas)**\n"
    "- Peca usinada conforme especificacao.\n\n"
    "**5. Customers (Clientes)**\n"
    "- Linha de montagem e cliente final.\n\n"
    "Exemplo pratico: em uma usinagem, o SIPOC conecta o fornecedor "
    "de barras de aco ate a montagem que recebe a peca conformada."
)


def _context() -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="u1",
        name="User",
        email="u@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def _request(text: str = "pergunta") -> InteractiveTurnRequest:
    return InteractiveTurnRequest(
        access_context=_context(),
        input_text=text,
        prior_turns=(),
    )


class _AnswerAdapter:
    """Test adapter: emits a bounded conversational ``answer`` exactly
    as the governed model contract requires (single JSON object)."""

    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, answer: str, limitations=None):
        self._answer = answer
        self._limitations = limitations or []

    def invoke(self, request):
        output = {"answer": self._answer}
        if self._limitations:
            output["limitations"] = list(self._limitations)
        return ProviderInvocationPayload(
            structured_output=output,
            generated_at="2026-01-01T00:00:00+00:00",
        )


def _conversational_result(answer: str, limitations=None):
    handler = HandleInteractiveConversationTurn(
        InvokeModel(_AnswerAdapter(answer, limitations))
    )
    return handler.execute(_request())


class _Orch:
    def __init__(self, attempt):
        self._attempt = attempt

    def attempt(self, input_text, **kwargs):
        return self._attempt


# ---------------- admitted case ----------------------


def test_conversational_sipoc_like_answer_emits_presentation_v2():
    """RED->GREEN: the SIPOC production incident — governed
    conversational prose organized in topics must reach the consumer
    as v2 ``markdown_safe`` instead of a v1 plain-text block."""
    result = _conversational_result(
        SIPOC_ANSWER, limitations=["resposta baseada em conhecimento geral"]
    )
    envelope = serialize_result(result)
    presentation = envelope["presentation"]
    assert presentation["version"] == "2"
    assert presentation["blocks"][0]["kind"] == "text"
    assert presentation["blocks"][0]["format"] == "markdown_safe"
    # The v2 payload is exactly the admitted content — no reformatting,
    # no content synthesis at the presentation boundary.
    assert presentation["blocks"][0]["text"] == SIPOC_ANSWER
    # Legacy content field is preserved byte-for-byte.
    assert envelope["content"] == SIPOC_ANSWER
    assert result.presentation_markdown == SIPOC_ANSWER
    # Epistemic honesty is unchanged: conversational prose stays
    # NON_GROUNDED regardless of rich presentation.
    assert envelope["grounding_status"] == "NON_GROUNDED"
    assert envelope["limitations"] == [
        "resposta baseada em conhecimento geral"
    ]


def test_conversational_plain_answer_admitted_without_structure():
    """Prose with no markdown syntax is still admitted to v2 — the
    consumer renders it as the same paragraphs; no structure is
    invented."""
    answer = "Resposta curta e simples."
    envelope = serialize_result(_conversational_result(answer))
    assert envelope["presentation"]["version"] == "2"
    assert envelope["presentation"]["blocks"][0]["text"] == answer
    assert envelope["content"] == answer


def test_conversational_markdown_byte_parity_with_content():
    answer = "Linha um.\n\n- a\n- b\n\n**fim**"
    result = _conversational_result(answer)
    assert result.content == result.presentation_markdown == answer


def test_conversational_answer_serialized_as_single_ndjson_line():
    """Markdown newlines must survive JSON serialization — the NDJSON
    wire record remains a single parseable line."""
    result = _conversational_result(SIPOC_ANSWER)
    line = json.dumps(serialize_result(result), ensure_ascii=False)
    assert "\n" not in line
    decoded = json.loads(line)
    assert decoded["presentation"]["version"] == "2"
    assert decoded["presentation"]["blocks"][0]["text"] == SIPOC_ANSWER


# ---------------- bounds / fail-closed -----------------


def test_oversize_conversational_answer_fails_closed_to_v1():
    answer = "x" * (_MAX_BLOCK_TEXT_CHARS + 1)
    envelope = serialize_result(_conversational_result(answer))
    assert envelope["presentation"]["version"] == "1"
    assert "format" not in envelope["presentation"]["blocks"][0]
    assert envelope["content"] == answer


def test_v1_consumer_compat_content_field_unchanged():
    result = _conversational_result(SIPOC_ANSWER)
    assert result.content == SIPOC_ANSWER
    # compose_presentation emits v1 transparently when the field is
    # absent — legacy consumers never see a regression.
    plain = compose_presentation(
        dataclasses.replace(result, presentation_markdown=None)
    )
    assert plain["version"] == "1"


# ---------------- forbidden propagation -----------------


def test_owner_content_text_markdown_stays_plain():
    """Category-B owner prose with markdown-looking syntax must NOT be
    admitted — markdown_safe is reserved for governed Category-A typed
    projections and now the conversational RESULT boundary only."""
    markdown_laden = "# owner\n- not admitted\n<script>x</script>"
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="corr",
        content=markdown_laden,
    )
    handler = HandleInteractiveConversationTurn(
        InvokeModel(_AnswerAdapter("never used")),
        capability_orchestration=_Orch(attempt),
    )
    result = handler.execute(_request())
    assert result.presentation_markdown is None
    assert serialize_result(result)["presentation"]["version"] == "1"


def test_authorization_denial_not_markdown_admitted():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.AUTHZ_DENIED,
        correlation_id="corr",
        content="**denied**: you cannot access that",
    )
    handler = HandleInteractiveConversationTurn(
        InvokeModel(_AnswerAdapter("never used")),
        capability_orchestration=_Orch(attempt),
    )
    envelope = serialize_result(handler.execute(_request()))
    assert envelope["presentation"]["version"] == "1"
    assert "format" not in envelope["presentation"]["blocks"][0]


def test_confirmation_required_not_markdown_admitted():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.CONFIRMATION_REQUIRED,
        correlation_id="corr",
        content="Confirme a alteracao",
        confirmation_context={"digest": "d1"},
        owner_hint="supplier",
    )
    handler = HandleInteractiveConversationTurn(
        InvokeModel(_AnswerAdapter("never used")),
        capability_orchestration=_Orch(attempt),
    )
    envelope = serialize_result(handler.execute(_request()))
    assert envelope["presentation"]["version"] == "1"
    assert (
        envelope["presentation"]["message_kind"]
        == "CONFIRMATION_REQUIRED"
    )


# ---------------- hostile content ----------------------


def test_hostile_markdown_is_carried_inert_on_the_wire():
    """Script/link payload inside admitted conversational text reaches
    the wire as plain v2 text — inertness is enforced by the bounded
    consumer (authorizedLinks gate), not by mutating content."""
    hostile = (
        "<script>alert(1)</script>\n"
        "[clique](https://evil.example/x)\n"
        "visite https://malicious.example\n"
        "![img](https://tracker.example/i.png)"
    )
    envelope = serialize_result(_conversational_result(hostile))
    block = envelope["presentation"]["blocks"][0]
    assert block["format"] == "markdown_safe"
    assert block["text"] == hostile
    # No authorized_links are synthesized from model prose.
    assert not envelope["presentation"].get("authorized_links")


def test_conversational_admission_preserves_turn_metadata():
    result = _conversational_result(SIPOC_ANSWER)
    envelope = serialize_result(result)
    assert envelope["session_id"] == result.session_id
    assert envelope["model_invocation_id"]
    assert envelope["grounding_status"] == "NON_GROUNDED"
    assert envelope["epistemic_class"] == result.epistemic_class.value
