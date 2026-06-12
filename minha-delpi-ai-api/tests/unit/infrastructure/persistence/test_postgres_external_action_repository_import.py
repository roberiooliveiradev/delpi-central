from unittest.mock import MagicMock, patch

from app.infrastructure.persistence.postgres_external_action_repository import (
    PostgresExternalActionRepository,
)


def _minimal_openapi() -> dict:
    return {
        "openapi": "3.0.0",
        "paths": {
            "/health": {
                "get": {
                    "operationId": "get_health",
                    "summary": "Health",
                }
            }
        },
    }


@patch(
    "app.infrastructure.persistence.postgres_external_action_repository.db.session"
)
@patch(
    "app.infrastructure.persistence.postgres_external_action_repository.ExternalActionModel"
)
@patch(
    "app.infrastructure.persistence.postgres_external_action_repository.ExternalActionSchemaModel"
)
@patch(
    "app.infrastructure.persistence.postgres_external_action_repository.OpenApiActionImporter"
)
def test_import_schema_from_json_skips_embedding_when_disabled(
    mock_importer_cls,
    _schema_model,
    mock_action_model,
    _db_session,
):
    provider = MagicMock()
    provider.id = "provider-uuid"
    provider.provider_key = "api-delpi"

    repository = PostgresExternalActionRepository(embedding_service=MagicMock())
    repository.get_provider_by_key = MagicMock(return_value=provider)
    repository._provider_to_dict = MagicMock(return_value={"providerKey": "api-delpi"})

    mock_importer_cls.return_value.import_actions.return_value = [
        {
            "action_id": "api-delpi:get:/health",
            "operation_id": "get_health",
            "method": "GET",
            "path": "/health",
            "summary": "Health",
        }
    ]

    mock_action_model.query.filter.return_value.delete.return_value = None

    result = repository.import_schema_from_json(
        provider_key="api-delpi",
        schema_json=_minimal_openapi(),
        source_type="inline",
        embed_on_import=False,
    )

    assert result["actionsImported"] == 1
    repository.embedding_service.embed_action.assert_not_called()


@patch(
    "app.infrastructure.persistence.postgres_external_action_repository.db.session"
)
@patch(
    "app.infrastructure.persistence.postgres_external_action_repository.ExternalActionModel"
)
@patch(
    "app.infrastructure.persistence.postgres_external_action_repository.ExternalActionSchemaModel"
)
@patch(
    "app.infrastructure.persistence.postgres_external_action_repository.OpenApiActionImporter"
)
def test_backfill_action_embeddings_reports_progress(
    mock_importer_cls,
    _schema_model,
    mock_action_model,
    _db_session,
):
    del mock_importer_cls

    action = MagicMock()
    action.enabled = True
    action.embedding = None

    embedding_service = MagicMock()
    embedding_service.embed_action.return_value = [0.1, 0.2]

    repository = PostgresExternalActionRepository(embedding_service=embedding_service)

    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [action, action]
    mock_action_model.query = mock_query

    progress: list[tuple[int, int]] = []

    result = repository.backfill_action_embeddings(
        provider_key="api-delpi",
        on_progress=lambda done, total: progress.append((done, total)),
        commit_batch_size=1,
    )

    assert result == {"updated": 2, "skipped": 0, "total": 2}
    assert progress == [(1, 2), (2, 2)]
