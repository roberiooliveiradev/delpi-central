"""Gate R12 — suíte consolidada Playbook 12 (entity contract + audit coverage)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_coverage_service import (
    ChatPresentationCoverageService,
)
from app.domain.services.chat_presentation_refactor_baseline_service import (
    ChatPresentationRefactorBaselineService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)
from tests.fixtures.presentation_interactivity_gate import (
    validate_tier_a_interactivity_cases,
)
from tests.fixtures.presentation_legacy_table_columns_gate import (
    validate_no_legacy_table_columns_in_presenters,
)
from tests.fixtures.presentation_kv_label_context_gate import (
    validate_kv_label_context_in_presenters,
)
from tests.fixtures.presentation_table_column_label_gate import (
    validate_table_column_labels_for_ci,
)
from tests.fixtures.presentation_table_role_gate import validate_table_roles_for_ci


def validate_playbook12_ci_gates(
    *,
    openapi_baseline_path=None,
    stored_baseline_path=None,
) -> dict[str, Any]:
    profile_validation = ChatPresentationCoverageService.validate_for_ci(
        openapi_baseline_path=openapi_baseline_path,
        stored_baseline_path=stored_baseline_path,
    )
    table_role_validation = validate_table_roles_for_ci()
    table_column_label_validation = validate_table_column_labels_for_ci()
    builder_validation = ChatPresentationCoverageService.validate_visual_builders_for_ci()
    interactivity_gaps = validate_tier_a_interactivity_cases()
    path_baseline = ChatPresentationRefactorBaselineService.compare_to_stored()
    legacy_columns = validate_no_legacy_table_columns_in_presenters()
    kv_label_context = validate_kv_label_context_in_presenters()

    profile_gaps = list(profile_validation.get("profileGaps") or [])
    new_operation_gaps = list(profile_validation.get("newOperationGaps") or [])
    table_role_gaps = list(table_role_validation.get("tableRoleGaps") or [])
    table_column_label_gaps = list(
        table_column_label_validation.get("tableColumnLabelGaps") or []
    )
    visual_builder_warnings = list(builder_validation.get("visualBuilderWarnings") or [])
    path_drift = list(path_baseline.get("drift") or [])

    blocking_issues: list[str] = []

    for gap in profile_gaps:
        blocking_issues.append(
            f"profile:{gap.get('kind')} {gap.get('operation_id')} {gap.get('path')}"
        )

    for gap in new_operation_gaps:
        blocking_issues.append(
            f"new_operation:{gap.get('operation_id')} {gap.get('path')}"
        )

    for gap in table_role_gaps:
        blocking_issues.append(
            f"table_role:{gap.get('case_id')} {gap.get('path')} ({gap.get('detail')})"
        )

    for gap in table_column_label_gaps:
        blocking_issues.append(
            f"table_column_label:{gap.get('case_id')} {gap.get('path')} ({gap.get('detail')})"
        )

    blocking_issues.extend(f"interactivity:{gap}" for gap in interactivity_gaps)

    for item in path_drift:
        blocking_issues.append(f"path_baseline:{item}")

    for violation in legacy_columns.get("violations") or []:
        blocking_issues.append(f"legacy_table_columns:{violation}")

    for violation in kv_label_context.get("violations") or []:
        blocking_issues.append(f"kv_label_context:{violation}")

    return {
        "ok": not blocking_issues,
        "blockingIssues": blocking_issues,
        "profileGaps": profile_gaps,
        "newOperationGaps": new_operation_gaps,
        "tableRoleGaps": table_role_gaps,
        "tableColumnLabelGaps": table_column_label_gaps,
        "interactivityGaps": interactivity_gaps,
        "visualBuilderWarnings": visual_builder_warnings,
        "pathBaselineDrift": path_drift,
        "legacyTableColumnViolations": list(legacy_columns.get("violations") or []),
        "kvLabelContextViolations": list(kv_label_context.get("violations") or []),
        "entityContractCaseCount": len(
            ChatPresentationCoverageService.build_entity_contract_cases()
        ),
        "tierAPipelineCaseCount": len(
            ChatPresentationVocabularyService.playbook12_tier_a_pipeline_cases()
        ),
    }
