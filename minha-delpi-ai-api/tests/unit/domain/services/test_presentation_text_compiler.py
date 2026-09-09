"""Unit tests — PresentationTextCompilerService."""

from __future__ import annotations

from app.domain.entities.presentation_spec import PresentationSpec, PresentationTextSpec
from app.domain.services.presentation_compilers.presentation_text_compiler_service import (
    PresentationTextCompilerService,
)


def test_text_compiler_applies_section_plan_to_framing_metadata_only():
    markdown = "### Status\n\n**Destaques**\n\n- OP aberta com 12 itens.\n"
    spec = PresentationSpec(
        view="text",
        text=PresentationTextSpec(
            section_plan=("summary", "highlights", "next_steps"),
            prose_density="compact",
        ),
    )
    metadata = {
        "textPresentation": {
            "type": "markdown",
            "markdown": markdown,
        },
        "presentationDecision": {},
    }
    PresentationTextCompilerService.apply(metadata, spec=spec)

    assert metadata["textPresentation"]["markdown"] == markdown
    assert metadata["textPresentation"]["config"]["sectionPlan"] == [
        "summary",
        "highlights",
        "next_steps",
    ]
    assert metadata["textPresentation"]["config"]["proseDensity"] == "compact"
    assert metadata["stackPresentationPlan"]["narrativeOrder"] == [
        "lead",
        "highlights",
        "attention",
    ]
    assert metadata["presentationDecision"]["textFraming"]["bindingProvenance"] == "COMPILED"


def test_text_compiler_ignores_invented_markers_not_in_spec():
    spec = PresentationSpec(
        view="text",
        text=PresentationTextSpec(section_plan=("summary", "highlights")),
    )
    metadata = {
        "textPresentation": {"markdown": "Fato operacional intacto."},
        "stackPresentationPlan": {"narrativeOrder": ["lead"]},
    }
    PresentationTextCompilerService.apply(metadata, spec=spec)
    assert metadata["textPresentation"]["markdown"] == "Fato operacional intacto."
    assert "inject_css" not in metadata["stackPresentationPlan"].get("sectionPlan", [])
