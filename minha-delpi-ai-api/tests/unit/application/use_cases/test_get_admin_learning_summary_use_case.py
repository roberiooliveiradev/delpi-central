from app.application.use_cases.get_admin_learning_summary_use_case import (
    GetAdminLearningSummaryUseCase,
)


class _FakeCandidateRepo:
    def __init__(self):
        self.since = "unset"

    def summary(self, *, since=None):
        self.since = since
        return {
            "total": 4,
            "byStatus": {"pending": 2, "promoted": 1, "rejected": 1},
            "byType": {"term_definition": 4},
            "pendingHighConfidence": 1,
            "recentCreated": 2,
            "avgPendingConfidence": 0.6,
        }


class _FakeVocabRepo:
    def summary(self):
        return {
            "total": 3,
            "approved": 3,
            "activeApproved": 2,
            "byType": {"typo": 3},
        }


class _FakeMemoryRepo:
    def summary(self):
        return {
            "total": 5,
            "active": 4,
            "forgotten": 1,
            "byStatus": {"active": 4, "forgotten": 1},
            "byType": {"preference": 3, "profile": 1},
        }


class _FakeEvalRepo:
    def summary(self):
        return {
            "total": 2,
            "active": 2,
            "disabled": 0,
            "failing": 1,
            "passing": 1,
            "neverRun": 0,
            "byCategory": {"routing": 2},
        }


def test_execute_assembles_summary_with_window():
    candidate_repo = _FakeCandidateRepo()

    use_case = GetAdminLearningSummaryUseCase(
        candidate_repository=candidate_repo,
        vocabulary_repository=_FakeVocabRepo(),
        memory_repository=_FakeMemoryRepo(),
        evaluation_repository=_FakeEvalRepo(),
    )

    result = use_case.execute(hours=24)

    assert result["windowHours"] == 24
    assert result["funnel"]["created"] == 4
    assert result["funnel"]["promoted"] == 1
    assert result["vocabulary"]["activeApproved"] == 2
    assert result["memory"]["active"] == 4
    assert result["highlights"]["memoryItemsActive"] == 4
    assert result["highlights"]["evaluationCasesFailing"] == 1
    assert result["evaluation"]["active"] == 2
    # janela aplicada ao repositório de candidatos
    assert candidate_repo.since is not None


def test_execute_normalizes_invalid_hours():
    use_case = GetAdminLearningSummaryUseCase(
        candidate_repository=_FakeCandidateRepo(),
        vocabulary_repository=_FakeVocabRepo(),
        memory_repository=_FakeMemoryRepo(),
        evaluation_repository=_FakeEvalRepo(),
    )

    result = use_case.execute(hours=0)

    assert result["windowHours"] == 1
