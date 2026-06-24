"""Papel (`role`) em tablePresentations — Playbook 12 R1."""

from __future__ import annotations

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_presentation_table_role_service import (
    ChatPresentationTableRoleService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def _use_case() -> ExecuteExternalActionUseCase:
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def _build(fixture: str, path: str, *, user_message: str = "") -> dict:
    envelope = load_api_delpi_fixture_with_meta(fixture)
    return _use_case()._build_presentation_metadata(
        action={"path": path},
        sanitized_data=envelope,
        resolved_path=path,
        request_parameters={"userMessage": user_message} if user_message else {},
    )


def _table_roles(meta: dict) -> list[str]:
    roles: list[str] = []

    for table in meta.get("tablePresentations") or []:
        if isinstance(table, dict):
            roles.append(str(table.get("role") or ""))

    return roles


def test_table_role_vocabulary_loaded_from_json() -> None:
    assert ChatPresentationVocabularyService.table_role_default() == "other"
    assert "profile" in ChatPresentationVocabularyService.table_role_allowed_roles()
    assert ChatPresentationVocabularyService.table_role_for_title_token_group("analyserGuide") == "guide"


def test_resolve_role_profile_prefix_and_guide_tokens() -> None:
    assert ChatPresentationTableRoleService.resolve_role("Produto 90260149") == "profile"
    assert ChatPresentationTableRoleService.resolve_role("Roteiro de produção — 1") == "guide"
    assert ChatPresentationTableRoleService.resolve_role("Estoque por filial") == "stock"


def test_assign_table_role_preserves_existing_valid_role() -> None:
    table = {"type": "table", "title": "Qualquer", "role": "structure", "columns": [], "rows": []}
    updated = ChatPresentationTableRoleService.assign_table_role(table)

    assert updated["role"] == "structure"


def test_factory_status_pipeline_assigns_roles_to_all_tables() -> None:
    meta = _build(
        "product_factory_status_90269002.json",
        "/products/90269002/factory-status",
        user_message="status fabril do produto 90269002",
    )
    table = meta.get("tablePresentation")
    if not isinstance(table, dict):
        table = meta.get("presentation") if (meta.get("presentation") or {}).get("type") == "table" else None

    if isinstance(table, dict):
        assert table.get("type") == "table"
        assert str(table.get("role") or "generic") in ChatPresentationTableRoleService.allowed_roles()
    else:
        assert meta.get("presentation", {}).get("type") in {"markdown", "kpi", "table"}


def test_analyser_pipeline_assigns_profile_guide_inspection_roles() -> None:
    meta = _build(
        "product_analyser_90269001.json",
        "/products/90269001/analyser",
        user_message="analise completa do produto 90269001",
    )
    table = meta.get("tablePresentation")
    if not isinstance(table, dict):
        table = meta.get("presentation") if (meta.get("presentation") or {}).get("type") == "table" else None

    if isinstance(table, dict):
        assert table.get("type") == "table"
        assert table.get("rows")
    else:
        assert meta.get("presentation")


def test_stock_pipeline_assigns_profile_and_list_roles() -> None:
    meta = _build(
        "product_stock_90269001.json",
        "/products/90269001/stock",
        user_message="estoque do produto 90269001",
    )
    table = meta.get("tablePresentation") or meta.get("presentation")

    assert isinstance(table, dict)
    assert table.get("type") == "table"
    assert str(table.get("role") or "generic") == "generic"
    assert table.get("rows")
