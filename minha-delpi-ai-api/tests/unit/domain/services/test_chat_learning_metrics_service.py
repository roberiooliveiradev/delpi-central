from app.domain.services.chat_learning_metrics_service import (
    ChatLearningMetricsService,
)


def _candidates(**overrides):
    base = {
        "total": 10,
        "byStatus": {
            "pending": 3,
            "auto_approved": 1,
            "approved": 2,
            "promoted": 3,
            "rejected": 1,
        },
        "byType": {"term_definition": 6, "normalization_rule": 4},
        "pendingHighConfidence": 2,
        "recentCreated": 5,
        "avgPendingConfidence": 0.72,
    }
    base.update(overrides)
    return base


def _vocabulary(**overrides):
    base = {
        "total": 8,
        "approved": 7,
        "activeApproved": 6,
        "byType": {"typo": 5, "term_definition": 3},
    }
    base.update(overrides)
    return base


def test_assemble_builds_funnel_and_rates():
    result = ChatLearningMetricsService.assemble(
        candidates=_candidates(),
        vocabulary=_vocabulary(),
    )

    funnel = result["funnel"]
    assert funnel["created"] == 10
    assert funnel["recentCreated"] == 5
    # pending + auto_approved
    assert funnel["pending"] == 4
    # approved + promoted
    assert funnel["approved"] == 5
    assert funnel["rejected"] == 1
    assert funnel["promoted"] == 3
    # (approved+promoted)/(approved+promoted+rejected) = 5/6
    assert funnel["approvalRate"] == round(5 / 6, 4)
    # promoted/total = 3/10
    assert funnel["promotionRate"] == 0.3


def test_assemble_highlights():
    result = ChatLearningMetricsService.assemble(
        candidates=_candidates(),
        vocabulary=_vocabulary(),
    )

    highlights = result["highlights"]
    assert highlights["termDefinitions"] == 6
    assert highlights["normalizationRules"] == 4
    assert highlights["pendingHighConfidence"] == 2
    assert highlights["learnedTermsActive"] == 6


def test_assemble_handles_empty_state():
    result = ChatLearningMetricsService.assemble(
        candidates={"total": 0, "byStatus": {}, "byType": {}},
        vocabulary={"total": 0, "approved": 0, "activeApproved": 0, "byType": {}},
    )

    assert result["funnel"]["created"] == 0
    assert result["funnel"]["approvalRate"] is None
    assert result["funnel"]["promotionRate"] is None
    assert result["highlights"]["learnedTermsActive"] == 0
