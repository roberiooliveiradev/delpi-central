"""Fidelity characterization of ``render_specialist_outcome``.

DELIA-UX-CONVERSATION-MARKDOWN-B2-G1-G2-R2 / doc 84 §4 / doc 86 §E.2.

These tests pin the EXISTING governed projection behaviour the
`presentation.v2` producer extension (RW-G1-01, EXTEND — not a new
formatter) must preserve: verbatim IDs/quantities/units/order,
inert markdown literals, credential redaction, truthful empty
results, generic-status suppression and declared truncation.

``test_bare_token_key_is_redacted`` is ``xfail(strict=True)``: it is
the RED probe for R2-03 — the literal key ``token`` is not covered by
``_SENSITIVE_KEY_NAMES`` today. It fails green only after the bounded
fix lands (separate authorized slice); XPASS will fail the suite so
the marker cannot go stale.
"""

from __future__ import annotations

import pytest

from app.application.capability_provision.orchestration import (
    MAX_RENDER_CONTENT_CHARS,
    render_specialist_outcome,
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
                    "client_secret": "cs-SECRET",
                    "op": "OP-1",
                }
            },
        )
    )
    assert "tok-xyz-SECRET" not in text
    assert "cs-SECRET" not in text
    assert "OP-1" in text


@pytest.mark.xfail(
    strict=True,
    reason=(
        "R2-03 residual: canonical key 'token' is not in "
        "_SENSITIVE_KEY_NAMES — value renders unredacted today. "
        "Fix = add 'token' to the owner set (bounded brief, doc 86/R2)."
    ),
)
def test_bare_token_key_is_redacted() -> None:
    text, _ = render_specialist_outcome(
        _outcome(
            content_text="",
            structured={"data": {"token": "tk-raw-SECRET", "op": "OP-2"}},
        )
    )
    assert "tk-raw-SECRET" not in text
    assert "OP-2" in text


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
