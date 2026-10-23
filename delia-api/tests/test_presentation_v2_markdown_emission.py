"""G3 — presentation.v2 markdown_safe emitter contract tests.

DELIA-C3-MARKDOWN-B2-G3-IMPLEMENTATION-01 / doc 97 §10 (G3 bounded
approval 2026-10-23) / docs 83–84 / CP-333.

RED-first coverage of the bounded backend producer:

- MUST-FIX reconciliation: ``PROCESSING_TIMEOUT`` exists in the v1
  canonical message vocabulary and in the frontend reader allowlist
  but was absent from the proposal v2 JSON Schema enum — the schema
  must be additively reconciled, never extended with a novel status;
- emission selectivity: ``version="2"`` + ``format="markdown_safe"``
  only when a legitimately admitted structured projection exists
  (Category A); B/C stay v1 plain verbatim;
- legacy parity: v1 envelope shape unchanged — no silent ``format``
  member, same block structure;
- same-facts rule: the markdown source preserves identifiers,
  quantities, units, values and order of the same sanitized payload
  the plain body renders;
- bounds, redaction, NDJSON compatibility and fail-closed transport;
- attempt→result typed propagation;
- zero link fabrication: no admitted public-URL source exists at the
  producer boundary, so the emitter must never synthesize links.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    GovernedCapabilityProvenance,
    InteractiveTurnRequest,
    InteractiveTurnResult,
)
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
    serialize_result,
)
from app.application.interaction.presentation import (
    _KNOWN_MESSAGE_KINDS,
    compose_presentation,
)
from app.application.capability_provision.orchestration import (
    render_specialist_outcome,
)

try:
    from app.application.capability_provision.orchestration import (
        render_specialist_outcome_rich,
    )
except ImportError:  # RED — I1 projection not implemented yet
    def render_specialist_outcome_rich(*args, **kwargs):  # type: ignore[misc]
        pytest.fail("render_specialist_outcome_rich not implemented")
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.domain.evidence.model import EpistemicClass, SourceRef
from app.domain.interaction.model import GroundingStatus
from app.domain.model_invocation.model import ProviderExposureClass
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT
    / "docs/12-roadmap-e-evolucao/delia/contracts/"
    "presentation-v2.proposal.schema.json"
)
schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

_PROV = SpecialistResultProvenance(
    specialist_id="spec-ops",
    remote_name="ops.read",
    protocol=InteropProtocol.MCP,
    correlation_id="corr-g3-1",
    observed_at="2026-02-14T12:00:00Z",
)


def _outcome(**kw) -> SpecialistOutcome:
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=_PROV,
        **kw,
    )


def _result(**overrides) -> InteractiveTurnResult:
    base = dict(
        session_id="s1",
        user_turn_id="u1",
        result_turn_id="r1",
        content="conteúdo governado",
        epistemic_class=EpistemicClass.OBSERVATION,
        limitations=(),
        generated_at="2026-01-01T00:00:00+00:00",
        model_invocation_id=None,
        grounding_status=GroundingStatus.GROUNDED,
    )
    base.update(overrides)
    return InteractiveTurnResult(**base)


def _context() -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="u1",
        name="User",
        email="u@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


class _StubModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self):
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        return ProviderInvocationPayload(
            structured_output={"answer": "prose"},
            generated_at="2026-01-01T00:00:00+00:00",
        )


class _StubOrchestration:
    def __init__(self, attempt: GovernedCapabilityAttempt):
        self._attempt = attempt

    def attempt(self, *args, **kwargs):
        return self._attempt


def _provenance() -> GovernedCapabilityProvenance:
    return GovernedCapabilityProvenance(
        source_refs=(
            SourceRef(
                source_id="DELPI",
                source_system="totvs",
                provider_name="spec-ops",
                observed_at="2026-02-14T12:00:00Z",
            ),
        ),
        specialist_id="spec-ops",
        remote_capability="ops.read",
        action_id="ops.read",
        protocol="MCP",
        observed_at="2026-02-14T12:00:00Z",
        correlation_id="corr-g3-1",
        is_complete=True,
    )


def _execute(attempt: GovernedCapabilityAttempt) -> InteractiveTurnResult:
    return HandleInteractiveConversationTurn(
        InvokeModel(_StubModel()),
        capability_orchestration=_StubOrchestration(attempt),
    ).execute(
        InteractiveTurnRequest(
            access_context=_context(), input_text="consulta"
        )
    )


# ---------------------------------------------------------------------------
# MUST-FIX contract reconciliation — PROCESSING_TIMEOUT
# ---------------------------------------------------------------------------


def test_v2_schema_message_kind_enum_covers_v1_vocabulary() -> None:
    """G3 MUST-FIX: every canonical v1 message kind must validate in
    the v2 schema — the consumer reader already admits
    PROCESSING_TIMEOUT, so the producer contract must not reject it."""
    schema_kinds = set(schema["properties"]["message_kind"]["enum"])
    missing = _KNOWN_MESSAGE_KINDS - schema_kinds
    assert missing == set(), (
        f"v2 schema rejects canonical v1 kinds: {sorted(missing)}"
    )


def test_v2_schema_accepts_processing_timeout_envelope() -> None:
    kind_enum = schema["properties"]["message_kind"]["enum"]
    assert "PROCESSING_TIMEOUT" in kind_enum


# ---------------------------------------------------------------------------
# Emission selectivity — v2 only for admitted projection
# ---------------------------------------------------------------------------


def test_result_without_markdown_stays_v1_and_has_no_format() -> None:
    presentation = compose_presentation(_result())
    assert presentation["version"] == "1"
    text_block = presentation["blocks"][0]
    assert "format" not in text_block


def test_result_with_markdown_emits_v2_markdown_safe() -> None:
    markdown = "**Produto:** PA-771\n\n- **Quantidade:** 150.5 KG"
    presentation = compose_presentation(
        _result(presentation_markdown=markdown)
    )
    assert presentation["version"] == "2"
    assert presentation["blocks"][0] == {
        "kind": "text",
        "format": "markdown_safe",
        "text": markdown,
    }
    assert presentation["allowed_interactions"] == ["reply"]


def test_empty_markdown_is_not_emitted() -> None:
    for empty in (None, "", "   "):
        presentation = compose_presentation(
            _result(presentation_markdown=empty)
        )
        assert presentation["version"] == "1", repr(empty)


def test_markdown_block_is_bounded() -> None:
    presentation = compose_presentation(
        _result(presentation_markdown="x" * 20_000)
    )
    # bounded or fail-closed — never an unbounded wire block
    text = presentation["blocks"][0]["text"]
    assert len(text) <= 16_384


def test_notice_block_coexists_with_markdown_text() -> None:
    hint = "Helpdesk BFF error: glpi_link_required."
    presentation = compose_presentation(
        _result(
            owner_hint=hint,
            presentation_markdown="**Resumo:** ok",
        )
    )
    assert presentation["version"] == "2"
    kinds = [b["kind"] for b in presentation["blocks"]]
    assert kinds == ["text", "notice"]
    assert presentation["blocks"][1]["text"] == hint


def test_kind_vocabulary_preserved_with_markdown() -> None:
    """Markdown never elevates or fabricates message kinds."""
    presentation = compose_presentation(
        _result(
            confirmation_request={
                "proposal_digest": "d1",
                "preview_fingerprint": "f1",
            },
            presentation_markdown="**Prévia**",
        )
    )
    assert presentation["message_kind"] == "CONFIRMATION_REQUIRED"
    assert presentation["allowed_interactions"] == [
        "reply",
        "confirm",
        "reject",
    ]


def test_grounding_epistemic_preserved_in_v2() -> None:
    presentation = compose_presentation(
        _result(presentation_markdown="**ok**")
    )
    assert presentation["grounding_status"] == "GROUNDED"
    assert presentation["semantic_status"] == "OBSERVATION"


def test_serialized_result_carries_presentation_v2_json_safe() -> None:
    body = serialize_result(
        _result(presentation_markdown="**A:** 1\n\n```sql\nSELECT 1\n```")
    )
    assert body["presentation"]["version"] == "2"
    # NDJSON/JSON transport: the event must serialize losslessly.
    assert json.loads(json.dumps(body)) == body


def test_legacy_top_level_content_unchanged_by_markdown() -> None:
    """Legacy consumers read plain content — never raw markdown."""
    body = serialize_result(
        _result(
            content="Produto: PA-771\nQuantidade: 150.5 KG",
            presentation_markdown="**Produto:** PA-771",
        )
    )
    assert body["content"] == "Produto: PA-771\nQuantidade: 150.5 KG"


def test_markdown_never_contains_fabricated_links() -> None:
    """No admitted public-URL source exists at the boundary: the
    projection must emit zero markdown links even when owner data
    carries url/href-named fields."""
    outcome = _outcome(
        content_text="",
        structured={
            "data": {
                "items": [
                    {
                        "produto": "PA-771",
                        "url": "https://evil.example/x?token=abc",
                        "href": "javascript:alert(1)",
                    }
                ]
            }
        },
    )
    rendered = render_specialist_outcome_rich(outcome)
    assert rendered.markdown is None or "](" not in rendered.markdown


# ---------------------------------------------------------------------------
# Category admission — A structured / B owner text / C prose
# ---------------------------------------------------------------------------


def test_category_a_structured_records_yield_markdown() -> None:
    rendered = render_specialist_outcome_rich(
        _outcome(
            content_text="",
            structured={
                "data": {
                    "items": [
                        {
                            "op": "OP-10293",
                            "produto": "PA-771",
                            "qtd": 150.5,
                            "un": "KG",
                        },
                        {
                            "op": "OP-10294",
                            "produto": "PA-772",
                            "qtd": 3,
                            "un": "UN",
                        },
                    ]
                }
            },
        )
    )
    assert rendered.markdown is not None
    # Every ASCII punctuation mark is escaped so leaves stay literal —
    # strip backslashes to verify the business data itself is verbatim.
    literal = rendered.markdown.replace("\\", "")
    for token in ("OP-10293", "OP-10294", "PA-771", "150.5", "KG"):
        assert token in literal
    assert literal.index("OP-10293") < literal.index("OP-10294")
    # Same facts as the plain body — nothing added.
    for token in ("OP-10293", "OP-10294", "PA-771", "PA-772"):
        assert token in rendered.content


def test_category_b_owner_text_yields_no_markdown() -> None:
    owner_text = "Lote L-88 conferido\nItem 1: 10 CX\nItem 2: 5 CX"
    rendered = render_specialist_outcome_rich(
        _outcome(content_text=owner_text)
    )
    assert rendered.markdown is None
    assert rendered.content == owner_text


def test_category_b_markdown_looking_text_stays_plain() -> None:
    owner_text = "Valor **não** é negrito: 2*3=6 e [x](y)"
    rendered = render_specialist_outcome_rich(
        _outcome(content_text=owner_text)
    )
    assert rendered.markdown is None
    assert "**não**" in rendered.content


def test_category_c_empty_outcome_has_no_markdown() -> None:
    rendered = render_specialist_outcome_rich(
        _outcome(content_text="", structured=None)
    )
    assert rendered.markdown is None


def test_plain_wrapper_unchanged_for_legacy_callers() -> None:
    """Existing tuple signature preserved — 5 callers + suite rely on
    it; the rich projection is additive."""
    outcome = _outcome(
        content_text="",
        structured={"data": {"items": [{"op": "OP-1", "qtd": 1}]}},
    )
    content, limitations = render_specialist_outcome(outcome)
    assert isinstance(content, str)
    assert "OP-1" in content


def test_markdown_escapes_metachars_in_owner_values() -> None:
    """Owner values are data, not formatting instructions: markdown
    metacharacters inside leaf values stay literal."""
    rendered = render_specialist_outcome_rich(
        _outcome(
            content_text="",
            structured={
                "data": {
                    "items": [
                        {"produto": "PA-**URGENTE**-771", "qtd": 5}
                    ]
                }
            },
        )
    )
    assert rendered.markdown is not None
    assert "PA\\-\\*\\*URGENTE\\*\\*\\-771" in rendered.markdown


def test_sensitive_keys_redacted_in_markdown_projection() -> None:
    rendered = render_specialist_outcome_rich(
        _outcome(
            content_text="",
            structured={
                "data": {
                    "items": [
                        {"produto": "PA-771", "access_token": "tok-SECRET"}
                    ]
                }
            },
        )
    )
    if rendered.markdown is not None:
        assert "tok-SECRET" not in rendered.markdown


def test_generic_status_text_suppressed_in_markdown_too() -> None:
    rendered = render_specialist_outcome_rich(
        _outcome(
            content_text="Execution completed.",
            structured={"data": {"items": [{"op": "OP-9", "qtd": 2}]}},
        )
    )
    assert rendered.markdown is not None
    assert "Execution completed" not in rendered.markdown


# ---------------------------------------------------------------------------
# Typed propagation — attempt → InteractiveTurnResult → wire
# ---------------------------------------------------------------------------


def test_attempt_markdown_propagates_to_grounded_result() -> None:
    markdown = "**Produto:** PA-771\n\n- **Quantidade:** 150.5 KG"
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="corr-g3-1",
        outcome=_outcome(
            content_text="",
            structured={"data": {"items": [{"op": "OP-1"}]}},
        ),
        provenance=_provenance(),
        content="Produto: PA-771\nQuantidade: 150.5 KG",
        markdown_content=markdown,
    )
    result = _execute(attempt)
    assert result.presentation_markdown == markdown
    assert result.grounding_status is GroundingStatus.GROUNDED
    assert result.epistemic_class is EpistemicClass.OBSERVATION
    presentation = serialize_result(result)["presentation"]
    assert presentation["version"] == "2"
    assert presentation["blocks"][0]["format"] == "markdown_safe"


def test_attempt_without_markdown_keeps_v1() -> None:
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="corr-g3-1",
        outcome=_outcome(content_text="resposta do especialista"),
        provenance=_provenance(),
        content="resposta do especialista",
    )
    result = _execute(attempt)
    assert result.presentation_markdown is None
    assert serialize_result(result)["presentation"]["version"] == "1"


def test_terminal_statuses_never_carry_markdown() -> None:
    for status in (
        GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        GovernedCapabilityStatus.AUTHZ_DENIED,
        GovernedCapabilityStatus.PROCESSING_TIMEOUT,
    ):
        result = _execute(
            GovernedCapabilityAttempt(
                status=status,
                correlation_id="corr-g3-1",
                error_code="mcp_unavailable",
            )
        )
        assert result.presentation_markdown is None
        assert serialize_result(result)["presentation"]["version"] == "1"


# ---------------------------------------------------------------------------
# G3-RW-01 — multiline leaf literal safety (review df4008b44f)
# Owner keys/values are data: embedded CR/LF/CRLF/Unicode separators must
# never open block structures (headings, lists, quotes, fences, rules) or
# links the deterministic projector did not authorize.
# ---------------------------------------------------------------------------


def test_multiline_leaf_value_cannot_open_blocks() -> None:
    rendered = render_specialist_outcome_rich(
        _outcome(
            content_text="",
            structured={
                "data": {
                    "items": [
                        {
                            "produto": "PA-771",
                            "descricao": (
                                "normal\n# Attacker Heading\n- injected bullet"
                            ),
                        }
                    ]
                }
            },
        )
    )
    md = rendered.markdown
    assert md is not None
    assert "\n# Attacker" not in md
    assert "\n- injected" not in md
    # literal content preserved verbatim (minus normalized breaks)
    assert "Attacker Heading" in md
    assert "injected bullet" in md


@pytest.mark.parametrize(
    "sep", ["\n", "\r", "\r\n", "\u2028", "\u2029", "\n\n", "\r\n\r\n"]
)
def test_line_separators_in_leaf_are_normalized(sep) -> None:
    rendered = render_specialist_outcome_rich(
        _outcome(
            content_text="",
            structured={
                "data": {
                    "items": [
                        {"produto": f"PA-771{sep}# Injected{sep}- injected"}
                    ]
                }
            },
        )
    )
    md = rendered.markdown
    assert md is not None
    assert "\n# Injected" not in md
    assert "\n- injected" not in md
    assert not any(
        line.lstrip().startswith("# ") for line in md.splitlines()
    )


def test_leaf_key_with_newline_cannot_inject_structure() -> None:
    rendered = render_specialist_outcome_rich(
        _outcome(
            content_text="",
            structured={
                "data": {
                    "items": [
                        {"campo\n# Forged Heading\n- fake": "valor", "produto": "PA-771"}
                    ]
                }
            },
        )
    )
    md = rendered.markdown
    assert md is not None
    assert "\n# Forged" not in md
    assert "\n- fake" not in md
    assert "Forged Heading" in md


def test_block_constructs_in_leaf_stay_inline_literal() -> None:
    """Quote, thematic break, fenced code and link syntax inside a leaf
    remain inert text — never parsed structures."""
    hostile = "x\n> forged quote\n---\n```py\nexec(1)\n```\n[y](https://evil)"
    rendered = render_specialist_outcome_rich(
        _outcome(
            content_text="",
            structured={"data": {"items": [{"desc": hostile}]}},
        )
    )
    md = rendered.markdown
    assert md is not None
    assert "\n> " not in md
    assert "\n```" not in md
    assert "\n---" not in md
    assert "[y](https://evil)" not in md  # brackets already escaped
    assert "forged quote" in md
    assert "exec(1)" in md.replace("\\", "")


def test_guidance_excerpt_newlines_cannot_open_blocks() -> None:
    """Guidance sections legitimately become headings — but owner
    excerpt text inside them can never open new structures."""
    rendered = render_specialist_outcome_rich(
        _outcome(
            content_text="",
            structured={
                "objective": "Responder a pergunta do usuário",
                "steps": "passo um\n# Injected Heading\n- injected item\n> forged",
            },
        ),
        input_text="como proceder",
    )
    md = rendered.markdown
    assert md is not None
    assert "\n# Injected" not in md
    assert "\n- injected" not in md
    assert "\n> forged" not in md
    assert "Injected Heading" in md


def test_literal_fidelity_non_newline_chars_preserved() -> None:
    """Normalization only affects line separators — all other
    characters, identifiers, units and order stay verbatim."""
    rendered = render_specialist_outcome_rich(
        _outcome(
            content_text="",
            structured={
                "data": {
                    "items": [
                        {"op": "OP-10293", "qtd": "150,5 KG", "obs": "a  b\tc"}
                    ]
                }
            },
        )
    )
    md = rendered.markdown
    assert md is not None
    literal = md.replace("\\", "")
    assert "OP-10293" in literal
    assert "150,5 KG" in literal
    assert literal.index("OP-10293") < literal.index("150,5")


def test_v1_plain_parity_unaffected_by_leaf_fix() -> None:
    """Plain body keeps original newlines verbatim — only the markdown
    projection normalizes them (v1 byte parity)."""
    rendered = render_specialist_outcome_rich(
        _outcome(
            content_text="",
            structured={
                "data": {"items": [{"produto": "PA-1", "desc": "a\nb\nc"}]}
            },
        )
    )
    assert "a\nb\nc" in rendered.content
