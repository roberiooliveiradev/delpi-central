"""Gate CI — role em tabelas tier A (Playbook 12 R9)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


@dataclass(frozen=True)
class TableRoleCoverageGap:
    case_id: str
    profile_key: str
    path: str
    detail: str


def collect_metadata_tables(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []

    bundled = metadata.get("tablePresentations")

    if isinstance(bundled, list):
        for item in bundled:
            if isinstance(item, dict) and item.get("type") == "table":
                tables.append(item)

    for key in (
        "tablePresentation",
        "profileTablePresentation",
        "inspectionTablePresentation",
        "presentation",
    ):
        presentation = metadata.get(key)

        if isinstance(presentation, dict) and presentation.get("type") == "table":
            tables.append(presentation)

    return tables


def find_table_role_gaps() -> list[TableRoleCoverageGap]:
    from app.application.use_cases.execute_external_action_use_case import (
        ExecuteExternalActionUseCase,
    )
    from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

    use_case = ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )
    gaps: list[TableRoleCoverageGap] = []

    for case in ChatPresentationVocabularyService.playbook12_tier_a_pipeline_cases():
        if not isinstance(case, dict):
            continue

        case_id = str(case.get("id") or "").strip() or "unknown"
        profile_key = str(case.get("profile_key") or "").strip()
        path = str(case.get("path") or "").strip()
        fixture = str(case.get("fixture") or "").strip()
        user_message = str(case.get("user_message") or "").strip()

        if not path or not fixture:
            gaps.append(
                TableRoleCoverageGap(
                    case_id=case_id,
                    profile_key=profile_key,
                    path=path,
                    detail="fixture ou path ausente em tierAPipelineCases",
                )
            )
            continue

        try:
            envelope = load_api_delpi_fixture_with_meta(fixture)
        except (FileNotFoundError, ValueError, KeyError) as exc:
            gaps.append(
                TableRoleCoverageGap(
                    case_id=case_id,
                    profile_key=profile_key,
                    path=path,
                    detail=f"fixture indisponível: {exc}",
                )
            )
            continue

        metadata = use_case._build_presentation_metadata(
            action={"path": path},
            sanitized_data=envelope,
            resolved_path=path,
            request_parameters={"userMessage": user_message} if user_message else {},
        )
        tables = collect_metadata_tables(metadata)

        for index, table in enumerate(tables):
            role = str(table.get("role") or "").strip()

            if role:
                continue

            title = str(table.get("title") or f"table[{index}]").strip()
            gaps.append(
                TableRoleCoverageGap(
                    case_id=case_id,
                    profile_key=profile_key,
                    path=path,
                    detail=f"tabela «{title}» sem role após pipeline tier A",
                )
            )

    return gaps


def validate_table_roles_for_ci() -> dict[str, Any]:
    gaps = find_table_role_gaps()

    return {
        "tableRoleGaps": [asdict(gap) for gap in gaps],
        "ok": not gaps,
    }
