"""DELIA-C3-SELF-AWARENESS — S3 PT-BR presentation (RQ-SA05, D8).

The governed ``field_labels`` section of the versioned
``cri_presentation`` resource covers generic business fields in
PT-BR; ``conversational_response`` is the single resolver for CRI,
detail, list and comparison paths. Unknown or business-specific
identifiers render VERBATIM — a raw key is the field's real name; a
pseudo-English label like "B2 cm1" corrupts an identifier the user
may need verbatim. Owner guidance sections never expose technical
structure keys (schema/registry versions, capability pointers) as
content.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.application.capability_provision.conversational_response import (
    field_clause_label,
    field_display_label,
    presented_record,
)
from app.application.capability_provision.orchestration import (
    OperationalCapabilityOrchestrator,
    _render_guidance_value,
)
from app.application.capability_provision.conversational_response import (
    _detail_lines,
    _proven_field_differences,
)

from app.application.capability_provision.outcome_assessment import (
    _canonical_key,
)

from app.infrastructure.config.cri_instruction_resource import (
    CriInstructionResourceError,
    load_cri_presentation_vocabulary,
)

_VOCAB_PATH = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "cri_presentation.delpi.json"
)
_VOCAB = load_cri_presentation_vocabulary(_VOCAB_PATH)
_LABELS = _VOCAB.field_labels


def _label(name: str) -> str:
    return field_display_label(_canonical_key(name), name, _LABELS)


def test_sa18_known_fields_get_ptbr_labels_detail_lines():
    """D8 golden: generic business fields render approved PT-BR
    labels in the baseline detail path."""
    lines = _detail_lines(
        [
            ("updated_at", "2026-10-20"),
            ("created_at", "2026-01-05"),
            ("email", "loja@exemplo.com"),
            ("telefone", "11 4002-8922"),
            ("cnpj", "12.345.678/0001-90"),
            ("quantidade", "3"),
            ("preco", "19,90"),
        ],
        field_labels=_LABELS,
    )
    joined = "\n".join(lines)
    assert "Data de atualização: 2026-10-20" in joined
    assert "Data de criação: 2026-01-05" in joined
    assert "E-mail: loja@exemplo.com" in joined
    assert "Telefone: 11 4002-8922" in joined
    assert "CNPJ: 12.345.678/0001-90" in joined
    assert "Quantidade: 3" in joined
    assert "Preço: 19,90" in joined
    # No English pseudo-labels.
    assert "Updated at" not in joined
    assert "Created at" not in joined


def test_sa19_unknown_keys_humanize_or_stay_verbatim():
    """Unmapped keys: word keys humanize (owner words preserved,
    underscores become spaces); digit-bearing code-shaped keys are
    identifiers and stay byte-exact — never mangled."""
    lines = _detail_lines(
        [("b2_cm1", "7.5"), ("custom_flag", "x")], field_labels=_LABELS
    )
    assert lines == ["- b2_cm1: 7.5", "- Custom flag: x"]


def test_sa20_clause_label_ptbr_and_verbatim_fallback():
    """The focused-answer clause uses the PT-BR form for known fields
    and the verbatim key for unknown ones — same governed resolver
    as the detail path."""
    assert (
        field_clause_label(
            _canonical_key("updated_at"), "updated_at", _LABELS
        )
        == "a data de atualização informada"
    )
    assert (
        field_clause_label(_canonical_key("preco"), "preco", _LABELS)
        == "o preço cadastrado"
    )
    assert (
        field_clause_label(_canonical_key("b2_cm1"), "b2_cm1", _LABELS)
        == 'o campo "b2_cm1"'
    )


def test_sa21_cri_presented_record_labels_ptbr():
    """Same canonical labels in the CRI presentation path — one
    governed source, not two maps."""
    orch = OperationalCapabilityOrchestrator.__new__(
        OperationalCapabilityOrchestrator
    )
    orch._field_labels = dict(_LABELS)
    record = {
        "updated_at": "2026-10-20",
        "email": "loja@exemplo.com",
        "b2_cm1": "7.5",
    }
    presented = presented_record(record, orch._field_labels)
    labels = {label for label, _value in presented.fields}
    assert "Data de atualização" in labels
    assert "E-mail" in labels
    assert "b2_cm1" in labels
    assert "Updated at" not in labels
    assert "B2 cm1" not in labels


def test_sa21b_baseline_without_vocabulary_stays_neutral():
    """An orchestrator without the governed labels renders the
    neutral fallback — never an invented translation, never a raw
    dump of English pseudo-labels either."""
    lines = _detail_lines([("descricao", "X"), ("b2_cm1", "7.5")])
    assert lines == ["- Descricao: X", "- b2_cm1: 7.5"]


def test_sa22_proven_differences_verbatim_unknown():
    """Field diffs keep the raw key for unknown fields — the
    identifier is user-facing evidence, not prose to translate."""
    left = (("b2_cm1", "7.5"),)
    right = (("b2_cm1", "8.0"),)
    lines = _proven_field_differences(left, right, field_labels=_LABELS)
    assert lines == ["- b2_cm1: 7.5 → 8.0"]


def test_sa22b_proven_differences_known_label():
    """Known fields in the comparison path resolve through the same
    governed label — one projection for every presentation path."""
    left = (("quantidade", "3"),)
    right = (("quantidade", "5"),)
    lines = _proven_field_differences(left, right, field_labels=_LABELS)
    assert lines == ["- Quantidade: 3 → 5"]


def test_sa23_guidance_section_drops_technical_structure():
    """Owner technical structure keys inside a guidance section map —
    schema/registry versions, capability pointers — are provenance
    metadata, not user content."""
    rendered = _render_guidance_value(
        {
            "schema": "product_guide_index_v1",
            "registryVersion": "product-guide-registry-v1",
            "authority": "GUIDANCE_NOT_DOMAIN_TRUTH",
            "topics": [
                {"id": "display_formats", "title": "Formatos"},
            ],
        }
    )
    assert "topics" in rendered
    assert "schema" not in rendered
    assert "registryVersion" not in rendered
    assert "authority" not in rendered


def test_sa24_guidance_content_business_fields_preserved():
    """Sibling: business content inside a guidance section survives —
    only declared meta/structure keys are skipped."""
    rendered = _render_guidance_value(
        {
            "summary": "Como formatar valores",
            "currency": "BRL",
        }
    )
    assert "summary" in rendered
    assert "currency" in rendered


# ---- governed resource contract ------------------------------------


def test_sa25_vocabulary_v5_loads_field_labels():
    """The versioned resource loads the field_labels map — canonical
    keys, declared parts, bounded size."""
    assert _VOCAB.version == "5"
    assert _LABELS["updatedat"] == (
        "a",
        "data de atualização",
        "informada",
    )
    assert _LABELS["cnpj"] == ("o", "CNPJ", "informado")
    assert len(_LABELS) > 50


def test_sa26_vocabulary_unknown_version_fails_closed(tmp_path):
    """An unlisted version is rejected — the contract never loads a
    schema it does not know."""
    path = tmp_path / "v.json"
    path.write_text(
        _VOCAB_PATH.read_text(encoding="utf-8").replace(
            '"version": "5"', '"version": "99"'
        ),
        encoding="utf-8",
    )
    with pytest.raises(CriInstructionResourceError):
        load_cri_presentation_vocabulary(path)


def test_sa27_field_labels_section_shapes_fail_closed(tmp_path):
    """Malformed field_labels sections reject: non-object section,
    non-canonical key, missing parts, bad article, placeholders."""
    import json

    base = json.loads(_VOCAB_PATH.read_text(encoding="utf-8"))

    def write_and_expect_error(mutate):
        data = json.loads(json.dumps(base))
        mutate(data)
        path = tmp_path / "mut.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(CriInstructionResourceError):
            load_cri_presentation_vocabulary(path)

    write_and_expect_error(lambda d: d.update(field_labels=["x"]))
    write_and_expect_error(
        lambda d: d["field_labels"].update(
            {"Bad Key": {"article": "o", "label": "x", "suffix": "y"}}
        )
    )
    write_and_expect_error(
        lambda d: d["field_labels"].update({"novo": {"label": "x"}})
    )
    write_and_expect_error(
        lambda d: d["field_labels"].update(
            {"novo": {"article": "um", "label": "x", "suffix": "y"}}
        )
    )
    write_and_expect_error(
        lambda d: d["field_labels"].update(
            {
                "novo": {
                    "article": "o",
                    "label": "x {count}",
                    "suffix": "y",
                }
            }
        )
    )
    write_and_expect_error(
        lambda d: d.update(
            field_labels={
                f"campo{i}": {
                    "article": "o",
                    "label": "x",
                    "suffix": "y",
                }
                for i in range(300)
            }
        )
    )


def test_sa28_field_labels_absent_loads_empty(tmp_path):
    """An older-shape resource without field_labels is still valid —
    the section is optional and resolves to an empty map."""
    import json

    data = json.loads(_VOCAB_PATH.read_text(encoding="utf-8"))
    data.pop("field_labels")
    data["version"] = "3"
    path = tmp_path / "v3.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    vocab = load_cri_presentation_vocabulary(path)
    assert vocab.field_labels == {}
