"""Fidelity characterization of ``render_specialist_outcome``.

DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R3 / doc 84 §4 / doc 86 §E.2.

These tests pin the EXISTING governed projection behaviour the
`presentation.v2` producer extension (RW-G1-01, EXTEND — not a new
formatter) must preserve: verbatim IDs/quantities/units/order,
inert markdown literals, credential redaction, truthful empty
results, generic-status suppression and declared truncation.

R3-01 closed the bare ``token`` key residual previously tracked as
``xfail(strict=True)`` — the canonical name is now in
``_SENSITIVE_KEY_NAMES``. Exact-key matching is preserved so business
fields such as ``token_count`` / ``token_value`` remain intact.
"""

from __future__ import annotations

from app.application.capability_provision.orchestration import (
    render_specialist_outcome,
)
from app.application.capability_provision.conversational_response import (
    MAX_RENDER_CONTENT_CHARS,
)

from app.application.capability_provision.outcome_assessment import (
    REDACTION_MARKER,
    _sanitize_renderable,
)

from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)

_PROV = SpecialistResultProvenance(
    specialist_id="spec-ops",
    remote_name="ops.read",
    protocol=InteropProtocol.MCP,
    correlation_id="corr-probe-1",
    observed_at="2026-02-14T12:00:00Z",
)

_TRUNC_SUFFIX = "\n…(resultado parcial — truncado)"


def _outcome(**kw) -> SpecialistOutcome:
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED, provenance=_PROV, **kw
    )


def test_structured_records_preserve_ids_quantities_units_and_order() -> None:
    text, _ = render_specialist_outcome(
        _outcome(
            content_text="",
            structured={
                "data": {
                    "items": [
                        {"op": "OP-10293", "produto": "PA-771", "qtd": 150.5, "un": "KG"},
                        {"op": "OP-10294", "produto": "PA-772", "qtd": 3, "un": "UN"},
                    ]
                }
            },
        )
    )
    assert "OP-10293" in text and "OP-10294" in text
    assert "150.5" in text and "KG" in text and "UN" in text
    assert text.index("OP-10293") < text.index("OP-10294")


def test_owner_text_preserved_verbatim_with_linebreaks() -> None:
    owner_text = "Lote L-88 conferido\nItem 1: 10 CX\nItem 2: 5 CX"
    text, _ = render_specialist_outcome(_outcome(content_text=owner_text))
    assert text == owner_text


def test_markdown_literals_are_inert() -> None:
    text, _ = render_specialist_outcome(
        _outcome(content_text="Valor **não** é negrito: 2*3=6 e [x](y)")
    )
    assert "**não**" in text and "[x](y)" in text


def test_sensitive_structured_keys_are_redacted_business_kept() -> None:
    text, _ = render_specialist_outcome(
        _outcome(
            content_text="",
            structured={
                "data": {
                    "access_token": "tok-xyz-SECRET",
                    "refresh_token": "rt-SECRET",
                    "client_secret": "cs-SECRET",
                    "password": "pw-SECRET",
                    "op": "OP-1",
                }
            },
        )
    )
    assert "tok-xyz-SECRET" not in text
    assert "rt-SECRET" not in text
    assert "cs-SECRET" not in text
    assert "pw-SECRET" not in text
    assert "OP-1" in text


def test_bare_token_key_is_redacted() -> None:
    """R3-01: literal canonical key ``token`` must redact (was RED/xfail)."""
    text, _ = render_specialist_outcome(
        _outcome(
            content_text="",
            structured={"data": {"token": "tk-raw-SECRET", "op": "OP-2"}},
        )
    )
    assert "tk-raw-SECRET" not in text
    assert "OP-2" in text


def test_token_key_case_and_separator_variants_are_redacted() -> None:
    """Exact canonical match covers Token/TOKEN; compound names stay exact."""
    for key in ("token", "Token", "TOKEN"):
        out = _sanitize_renderable({key: "tk-CASE-SECRET", "op": "OP-3"})
        assert out[key] == REDACTION_MARKER, key
        assert out["op"] == "OP-3"

    # token_value / token-value canonicalize to tokenvalue — NOT the
    # exact credential concept ``token``. Exact matching preserves them
    # (same family as token_count); substring matching is forbidden.
    for key in ("token_value", "token-value"):
        out = _sanitize_renderable({key: "biz-TOKEN-VALUE", "op": "OP-4"})
        assert out[key] == "biz-TOKEN-VALUE", key
        assert out["op"] == "OP-4"


def test_nested_list_token_redaction_preserves_business_siblings() -> None:
    out = _sanitize_renderable(
        {
            "data": {
                "items": [
                    {"token": "NESTED-SECRET", "op": "OP-10", "qtd": 12, "un": "KG"},
                    {"Token": "NESTED-SECRET-2", "op": "OP-11"},
                ]
            }
        }
    )
    rendered = str(out)
    assert "NESTED-SECRET" not in rendered
    assert "NESTED-SECRET-2" not in rendered
    assert out["data"]["items"][0]["op"] == "OP-10"
    assert out["data"]["items"][0]["qtd"] == 12
    assert out["data"]["items"][0]["un"] == "KG"
    assert out["data"]["items"][1]["op"] == "OP-11"
    assert out["data"]["items"][0]["token"] == REDACTION_MARKER


def test_empty_authoritative_result_is_truthful() -> None:
    text, _ = render_specialist_outcome(
        _outcome(content_text="", structured={"data": {"items": []}})
    )
    assert "Nenhum resultado encontrado." in text


def test_generic_status_suppressed_when_business_payload_exists() -> None:
    text, _ = render_specialist_outcome(
        _outcome(
            content_text="execution completed.",
            structured={"data": {"items": [{"op": "OP-55"}]}},
        )
    )
    assert "OP-55" in text


def test_truncation_is_bounded_and_declared() -> None:
    text, limitations = render_specialist_outcome(
        _outcome(content_text="x" * 5000)
    )
    assert len(text) <= MAX_RENDER_CONTENT_CHARS + len(_TRUNC_SUFFIX)
    assert "truncado" in text[-40:]
    assert "result_truncated" in limitations
