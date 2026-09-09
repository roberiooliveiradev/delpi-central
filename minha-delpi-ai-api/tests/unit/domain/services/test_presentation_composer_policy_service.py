"""Unit: PresentationComposerPolicyService skip/invoke rules."""

from app.domain.services.presentation_composer_policy_service import (
    PresentationComposerPolicyService,
)


def test_skip_when_spec_applied_with_high_bind_confidence():
    """Positive: intent/bind altos → skip composer."""
    assert (
        PresentationComposerPolicyService.should_invoke(
            summary={"specApplied": True, "bindConfidence": 0.9, "needsComposer": True},
            intent={"mark": "bar"},
        )
        is False
    )


def test_invoke_when_needs_composer_and_low_confidence():
    """Sibling: needsComposer com bind baixo → invoke."""
    assert (
        PresentationComposerPolicyService.should_invoke(
            summary={"specApplied": False, "bindConfidence": 0.4, "needsComposer": True},
            intent={"view": "auto"},
        )
        is True
    )


def test_invoke_when_ambiguous_profile_even_without_flag():
    """Sibling: multi-slot ambíguo sem needsComposer → invoke."""
    assert (
        PresentationComposerPolicyService.should_invoke(
            summary={"specApplied": False, "bindConfidence": 0.5, "needsComposer": False},
            intent={"view": "auto"},
            profile={
                "dimensionCandidates": ["product_code", "branch"],
                "measureCandidates": ["balance", "planned_qty"],
            },
        )
        is True
    )


def test_negative_empty_summary_does_not_invoke():
    """Negative: summary inválido não dispara composer."""
    assert PresentationComposerPolicyService.should_invoke(summary=None) is False
    assert PresentationComposerPolicyService.should_invoke(summary={}) is False
