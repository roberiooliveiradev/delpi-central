#!/usr/bin/env python3
"""Reimporta OpenAPI snapshot da API PAC Qualidade e gera catálogo MD.

Uso (container minha-delpi-ai-api):

  PYTHONPATH=/app python scripts/sync_api_pac_quality_openapi.py
  PYTHONPATH=/app python scripts/sync_api_pac_quality_openapi.py \\
      --from-file /repo/api-pac-quality/docs/openapi-snapshot-chat.json

Pré-requisito: provider `api-pac-quality` cadastrado no agente com `authMode=user_token`
e `baseUrl` apontando para `https://pac-api.minhadelpi.com.br`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.domain.services.api_delpi_openapi_catalog_service import (
    build_openapi_catalog_markdown,
    collect_openapi_operations,
)

DEFAULT_PROVIDER_KEY = "api-pac-quality"


def _resolve_default_schema_file() -> Path:
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parents[3] / "api-pac-quality" / "docs" / "openapi-snapshot-chat.json",
        script_dir.parents[2] / "api-pac-quality" / "docs" / "openapi-snapshot-chat.json",
        Path("/repo/api-pac-quality/docs/openapi-snapshot-chat.json"),
    ]
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]


DEFAULT_SCHEMA_FILE = _resolve_default_schema_file()
DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "knowledge"
    / "_generated"
    / "api-pac-quality-openapi-catalog.md"
)


def _load_schema_from_file(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError("OpenAPI file must contain a JSON object")

    return payload


def _latest_schema_from_provider(repository, provider_key: str) -> dict | None:
    provider = repository.get_provider_by_key(provider_key)

    if not provider:
        return None

    provider_dict = repository._provider_to_dict(provider)
    latest = provider_dict.get("latestSchema")

    return latest if isinstance(latest, dict) else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider-key",
        default=DEFAULT_PROVIDER_KEY,
        help="Provider OpenAPI cadastrado no chat (default: api-pac-quality).",
    )
    parser.add_argument(
        "--from-file",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help="Schema OpenAPI local (default: api-pac-quality/docs/openapi-snapshot-chat.json).",
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="Não reimporta o schema (só reindex / catálogo).",
    )
    parser.add_argument(
        "--skip-reindex",
        action="store_true",
        help="Não reindexa embeddings das actions.",
    )
    parser.add_argument(
        "--skip-catalog",
        action="store_true",
        help="Não gera docs/knowledge/_generated/api-pac-quality-openapi-catalog.md.",
    )
    parser.add_argument(
        "--catalog-path",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
        help="Destino do catálogo markdown gerado.",
    )
    args = parser.parse_args()

    from app.application.use_cases.admin_chat_intelligence_use_cases import (
        ReindexExternalActionEmbeddingsUseCase,
    )
    from app.application.use_cases.import_external_actions_schema_use_case import (
        ImportExternalActionsSchemaUseCase,
    )
    from app.composition.root_composer import create_application
    from app.extensions.db import db
    from app.infrastructure.persistence.postgres_external_action_repository import (
        PostgresExternalActionRepository,
    )

    app = create_application()
    report: dict = {"providerKey": args.provider_key}

    with app.app_context():
        repository = PostgresExternalActionRepository()
        import_use_case = ImportExternalActionsSchemaUseCase(repository)
        schema: dict | None = None

        if not args.skip_import:
            schema = _load_schema_from_file(args.from_file)
            report["import"] = import_use_case.execute_from_json(
                args.provider_key,
                schema,
            )
            db.session.commit()
        else:
            schema = _latest_schema_from_provider(repository, args.provider_key)

        if not args.skip_reindex:
            report["reindex"] = ReindexExternalActionEmbeddingsUseCase(
                repository
            ).execute(provider_key=args.provider_key)
            db.session.commit()

        actions = repository.list_actions(provider_key=args.provider_key)
        report["actionsInDatabase"] = len(actions)

        if not args.skip_catalog and schema:
            catalog = build_openapi_catalog_markdown(
                schema,
                provider_key=args.provider_key,
                catalog_title="API PAC Qualidade — Snapshot (Chat)",
            )
            args.catalog_path.parent.mkdir(parents=True, exist_ok=True)
            args.catalog_path.write_text(catalog, encoding="utf-8")
            report["catalogPath"] = str(args.catalog_path)
            report["catalogOperations"] = len(collect_openapi_operations(schema))

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
