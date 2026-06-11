"""Gate R20 — colunas tier A com label PT (H17/H18)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)
from tests.fixtures.presentation_table_role_gate import collect_metadata_tables


@dataclass(frozen=True)
class TableColumnLabelGap:
    case_id: str
    profile_key: str
    path: str
    detail: str


def _is_raw_snake_case_label(key: str, label: str) -> bool:
    token = str(key or "").strip()
    text = str(label or "").strip()

    if not token or not text:
        return False

    if "_" not in token:
        return False

    return text == token


def find_table_column_label_gaps() -> list[TableColumnLabelGap]:
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
    gaps: list[TableColumnLabelGap] = []

    for case in ChatPresentationVocabularyService.playbook12_tier_a_pipeline_cases():
        if not isinstance(case, dict):
            continue

        case_id = str(case.get("id") or "").strip() or "unknown"
        profile_key = str(case.get("profile_key") or "").strip()
        path = str(case.get("path") or "").strip()
        fixture = str(case.get("fixture") or "").strip()
        user_message = str(case.get("user_message") or "").strip()

        if not path or not fixture:
            continue

        try:
            envelope = load_api_delpi_fixture_with_meta(fixture)
        except (FileNotFoundError, ValueError, KeyError) as exc:
            gaps.append(
                TableColumnLabelGap(
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
            columns = table.get("columns")

            if not isinstance(columns, list) or not columns:
                continue

            title = str(table.get("title") or f"table[{index}]").strip()

            for column_index, column in enumerate(columns):
                if not isinstance(column, dict):
                    gaps.append(
                        TableColumnLabelGap(
                            case_id=case_id,
                            profile_key=profile_key,
                            path=path,
                            detail=f"tabela «{title}» coluna[{column_index}] inválida",
                        )
                    )
                    continue

                key = str(column.get("key") or "").strip()
                label = str(column.get("label") or "").strip()

                if not key:
                    continue

                if not label:
                    gaps.append(
                        TableColumnLabelGap(
                            case_id=case_id,
                            profile_key=profile_key,
                            path=path,
                            detail=f"tabela «{title}» coluna «{key}» sem label",
                        )
                    )
                    continue

                if _is_raw_snake_case_label(key, label):
                    gaps.append(
                        TableColumnLabelGap(
                            case_id=case_id,
                            profile_key=profile_key,
                            path=path,
                            detail=(
                                f"tabela «{title}» coluna «{key}» com label snake_case cru"
                            ),
                        )
                    )

    return gaps


def validate_table_column_labels_for_ci() -> dict[str, Any]:
    gaps = find_table_column_label_gaps()

    return {
        "tableColumnLabelGaps": [asdict(gap) for gap in gaps],
        "ok": not gaps,
    }
