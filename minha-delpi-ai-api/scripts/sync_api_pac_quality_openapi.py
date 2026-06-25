#!/usr/bin/env python3
"""Reimporta OpenAPI da API PAC Qualidade e gera catálogo MD.

Uso (container minha-delpi-ai-api):

  PYTHONPATH=/app python scripts/sync_api_pac_quality_openapi.py
  PYTHONPATH=/app python scripts/sync_api_pac_quality_openapi.py \\
      --from-url https://pac-api.minhadelpi.com.br/openapi.json

Pré-requisito: provider `api-pac-quality` cadastrado no agente.
Schema canônico: GET /openapi.json (gerado pelo FastAPI, como api-delpi).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import urlopen

from app.domain.services.api_delpi_openapi_catalog_service import (
    build_openapi_catalog_markdown,
    collect_openapi_operations,
)

DEFAULT_PROVIDER_KEY = "api-pac-quality"
DEFAULT_OPENAPI_URL = "https://pac-api.minhadelpi.com.br/openapi.json"
DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "knowledge"
    / "_generated"
    / "api-pac-quality-openapi-catalog.md"
)

ONDA1_REQUIRED_OPENAPI_PATHS = (
    "/quality/action-plans",
    "/quality/action-plans/intelligence/similar-cases",
    "/quality/action-plans/{plan_id}",
    "/quality/action-plans/{plan_id}/rnc-8d",
    "/quality/action-plans/{plan_id}/export/rnc-8d",
    "/quality/action-plans/{plan_id}/evidences",
    "/quality/action-plans/{plan_id}/ishikawa",
    "/quality/action-plans/{plan_id}/five-whys",
    "/quality/action-plans/{plan_id}/actions",
)


def _validate_onda1_openapi_paths(schema: dict) -> list[str]:
    paths = schema.get("paths") if isinstance(schema.get("paths"), dict) else {}
    return [path for path in ONDA1_REQUIRED_OPENAPI_PATHS if path not in paths]


def _load_schema_from_file(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError("OpenAPI file must contain a JSON object")

    return payload


def _load_schema_from_url(url: str) -> dict:
    with urlopen(url, timeout=30) as response:
        payload = json.load(response)

    if not isinstance(payload, dict):
        raise ValueError("OpenAPI URL must return a JSON object")

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
        "--from-url",
        default=DEFAULT_OPENAPI_URL,
        help=f"URL do OpenAPI público (default: {DEFAULT_OPENAPI_URL}).",
    )
    parser.add_argument(
        "--from-file",
        type=Path,
        help="Schema OpenAPI local (opcional; ignora --from-url).",
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
    parser.add_argument(
        "--check-onda1",
        action="store_true",
        help="Falha se o OpenAPI não tiver rotas Onda 1 (8D, evidências, inteligência).",
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
            if args.from_file:
                schema = _load_schema_from_file(args.from_file)
                report["schemaSource"] = str(args.from_file)
            else:
                schema = _load_schema_from_url(args.from_url)
                report["schemaSource"] = args.from_url

            missing_paths = _validate_onda1_openapi_paths(schema)
            report["onda1MissingPaths"] = missing_paths
            if args.check_onda1 and missing_paths:
                print(
                    json.dumps(
                        {
                            "error": "OpenAPI sem rotas Onda 1 — faça deploy api-pac no srv-api antes do sync.",
                            "missingPaths": missing_paths,
                            "schemaSource": report["schemaSource"],
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    file=sys.stderr,
                )
                return 1

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
                catalog_title="API PAC Qualidade — OpenAPI",
            )
            args.catalog_path.parent.mkdir(parents=True, exist_ok=True)
            args.catalog_path.write_text(catalog, encoding="utf-8")
            report["catalogPath"] = str(args.catalog_path)
            report["catalogOperations"] = len(collect_openapi_operations(schema))

            from app.domain.services.openapi_delpi_extension_service import (
                OpenApiDelpiExtensionService,
            )

            report["delpiMetadataCoverage"] = OpenApiDelpiExtensionService.summarize_schema_coverage(
                schema,
            )
            report["delpiMetadataInDatabase"] = sum(
                1
                for action in actions
                if isinstance(action.get("delpiMetadata"), dict) and action.get("delpiMetadata")
            )

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not _report_is_successful(report, skip_import=args.skip_import):
        return 1

    return 0


def _report_is_successful(report: dict, *, skip_import: bool) -> bool:
    if int(report.get("actionsInDatabase") or 0) <= 0 and not skip_import:
        return False

    if skip_import:
        return True

    import_result = report.get("import")

    if isinstance(import_result, dict) and import_result.get("found") is False:
        return False

    coverage = report.get("delpiMetadataCoverage")

    if isinstance(coverage, dict):
        operations = int(coverage.get("operations") or 0)
        with_delpi = int(coverage.get("withDelpiMetadata") or 0)

        if operations > 0 and with_delpi < operations:
            return False

    return True


if __name__ == "__main__":
    sys.exit(main())
