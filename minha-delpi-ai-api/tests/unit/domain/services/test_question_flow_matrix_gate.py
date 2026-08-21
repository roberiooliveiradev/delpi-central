"""Gate CI: 100% dos ids da QUESTION_FLOW_MATRIX têm caso no runner parametrizado."""

from tests.fixtures.question_flow_matrix import (
    QUESTION_FLOW_MATRIX,
    QUESTION_FLOW_REQUIRED_IDS,
)


def test_question_flow_matrix_coverage_100_percent():
    required = set(QUESTION_FLOW_REQUIRED_IDS)
    present = {str(item["id"]) for item in QUESTION_FLOW_MATRIX}

    assert present == required
    assert len(QUESTION_FLOW_MATRIX) == len(required)

    kinds = {str(item.get("kind") or "") for item in QUESTION_FLOW_MATRIX}
    assert "" not in kinds

    # Todos os kinds usados no inventário devem ter handler no runner.
    from tests.unit.domain.services import test_question_flow_matrix as runner

    source = open(runner.__file__, encoding="utf-8").read()
    for kind in sorted(kinds):
        assert f'kind == "{kind}"' in source or f"kind == '{kind}'" in source, kind
