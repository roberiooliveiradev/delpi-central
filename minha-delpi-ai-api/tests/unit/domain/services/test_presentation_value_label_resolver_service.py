from app.domain.services.presentation_value_label_resolver_service import (
    PresentationValueLabelResolverService,
)


def test_value_label_keeps_canonical_when_unknown():
    assert (
        PresentationValueLabelResolverService.resolve("work_in_progress")
        == "work_in_progress"
    )


def test_value_label_uses_vocabulary_when_present():
    assert (
        PresentationValueLabelResolverService.resolve(
            "work_in_progress",
            vocabulary={"work_in_progress": "Em andamento"},
        )
        == "Em andamento"
    )
