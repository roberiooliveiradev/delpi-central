"""Aviso user-facing quando unmetIntent impede materializar a visualização pedida."""

from __future__ import annotations

from app.domain.services.presentation_unmet_intent_notice_service import (
    PresentationUnmetIntentNoticeService,
)


def test_heatmap_unmet_intent_applies_user_facing_notice():
    metadata = {
        "presentationDecision": {
            "selected": "chart",
            "insight": "Comparação por depósito.",
        },
        "chartPresentation": {"type": "chart", "chartType": "horizontal_bar"},
        "textPresentation": {"type": "text", "markdown": "Saldo disponível."},
    }

    notice = PresentationUnmetIntentNoticeService.apply(
        metadata,
        unmet_intent="heatmap_not_materializable",
    )

    assert notice
    assert "mapa de calor" in notice.lower()
    decision = metadata["presentationDecision"]
    assert decision["unmetIntent"] == "heatmap_not_materializable"
    assert decision["unmetIntentNotice"] == notice
    assert decision["policyNotice"] == notice
    assert notice in decision["insight"]
    assert notice in metadata["textPresentation"]["markdown"]
    assert notice in metadata["dataCommentary"]["attention"]


def test_tree_unmet_intent_sibling_notice():
    metadata = {"presentationDecision": {}}

    notice = PresentationUnmetIntentNoticeService.apply(
        metadata,
        unmet_intent="tree_not_materializable",
    )

    assert notice
    assert "árvore" in notice.lower() or "arvore" in notice.lower()
    assert metadata["presentationDecision"]["unmetIntentNotice"] == notice


def test_no_unmet_intent_does_not_inject_notice():
    metadata = {
        "presentationDecision": {
            "selected": "heatmap",
            "insight": "Mapa de calor aplicado.",
        },
        "textPresentation": {"type": "text", "markdown": "OK"},
    }

    notice = PresentationUnmetIntentNoticeService.apply(metadata, unmet_intent=None)

    assert notice is None
    assert "unmetIntentNotice" not in metadata["presentationDecision"]
    assert metadata["textPresentation"]["markdown"] == "OK"


def test_prepend_to_answer_is_idempotent():
    notice = "Não consegui montar o mapa de calor."
    once = PresentationUnmetIntentNoticeService.prepend_to_answer("Prosa.", notice)
    twice = PresentationUnmetIntentNoticeService.prepend_to_answer(once, notice)

    assert once == f"{notice}\n\nProsa."
    assert twice == once


def test_mark_unavailable_family_resolves_notice():
    notice = PresentationUnmetIntentNoticeService.notice_for_token(
        "mark_unavailable:heatmap",
    )

    assert notice
    assert "formato visual" in notice.lower() or "disponível" in notice.lower()
