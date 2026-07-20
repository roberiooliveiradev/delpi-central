"""Endpoint interno: reimport OpenAPI api-delpi (disparado pela própria api-delpi)."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from flask import current_app, jsonify, request

from app.extensions.db import db
from app.interfaces.http.routes.chat.shared import chat_bp

logger = logging.getLogger(__name__)

_CATALOG_PATH = (
    Path(__file__).resolve().parents[5]
    / "docs"
    / "knowledge"
    / "_generated"
    / "api-delpi-openapi-catalog.md"
)


def _require_internal_service_token():
    from delpi_auth.service_token import headers_have_valid_internal_service_token

    if headers_have_valid_internal_service_token(dict(request.headers)):
        return None
    return jsonify({"success": False, "message": "Unauthorized service"}), 401


@chat_bp.post("/internal/openapi/sync-api-delpi")
def sync_api_delpi_openapi_internal():
    """S2S: api-delpi notifica o chat para reimportar o provider api-delpi."""
    denied = _require_internal_service_token()
    if denied is not None:
        return denied

    from app.application.services.external_action_import_job_service import (
        ExternalActionImportJobService,
    )
    from app.domain.services.api_delpi_openapi_catalog_service import (
        build_openapi_catalog_markdown,
        collect_openapi_operations,
    )
    from app.domain.services.openapi_delpi_extension_service import (
        OpenApiDelpiExtensionService,
    )
    from app.infrastructure.persistence.postgres_external_action_repository import (
        PostgresExternalActionRepository,
    )

    provider_key = (request.args.get("providerKey") or "api-delpi").strip() or "api-delpi"
    # Por padrão atualiza schemas OpenAPI (reimport). Embeddings só pulam se
    # skipEmbeddings=1/true (ou updateEmbeddings=0).
    skip_raw = (request.args.get("skipEmbeddings") or "").strip().lower()
    update_emb_raw = (request.args.get("updateEmbeddings") or "").strip().lower()
    if update_emb_raw in {"0", "false", "no", "off"}:
        skip_embeddings = True
    elif update_emb_raw in {"1", "true", "yes", "on"}:
        skip_embeddings = False
    elif skip_raw in {"1", "true", "yes", "on"}:
        skip_embeddings = True
    elif skip_raw in {"0", "false", "no", "off"}:
        skip_embeddings = False
    else:
        # Default S2S: atualizar schemas + embeddings.
        skip_embeddings = False

    update_schema_raw = (request.args.get("updateSchema") or "1").strip().lower()
    if update_schema_raw in {"0", "false", "no", "off"}:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "updateSchema=0 não é suportado — o endpoint sempre reimporta o schema.",
                }
            ),
            400,
        )

    report: dict = {
        "providerKey": provider_key,
        "source": "internal_s2s",
        "updateSchema": True,
        "skipEmbeddings": skip_embeddings,
    }

    try:
        started = time.perf_counter()
        job = ExternalActionImportJobService.run_to_completion(
            current_app._get_current_object(),
            provider_key=provider_key,
            skip_embeddings=skip_embeddings,
        )
        repository = PostgresExternalActionRepository()
        provider = repository.get_provider_by_key(provider_key)
        schema = None
        if provider:
            provider_dict = repository._provider_to_dict(provider)
            latest = provider_dict.get("latestSchema")
            schema = latest if isinstance(latest, dict) else None

        result = job.get("result") if isinstance(job.get("result"), dict) else {}
        import_report = {
            "jobId": job.get("jobId"),
            "status": job.get("status"),
            "found": job.get("status") != "failed",
            "actionsImported": result.get("actionsImported"),
            "embeddingsUpdated": result.get("embeddingsUpdated"),
            "error": job.get("error"),
        }
        report["import"] = import_report
        report["importDurationSeconds"] = round(time.perf_counter() - started, 2)

        if job.get("status") == "failed":
            db.session.rollback()
            report["ok"] = False
            return jsonify(report), 502

        db.session.commit()
        actions = repository.list_actions(provider_key=provider_key)
        report["actionsInDatabase"] = len(actions)

        if schema:
            catalog = build_openapi_catalog_markdown(schema, provider_key=provider_key)
            _CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            _CATALOG_PATH.write_text(catalog, encoding="utf-8")
            report["catalogPath"] = str(_CATALOG_PATH)
            report["catalogOperations"] = len(collect_openapi_operations(schema))
            report["delpiMetadataCoverage"] = (
                OpenApiDelpiExtensionService.summarize_schema_coverage(schema)
            )

        report["ok"] = True
        logger.info(
            "sync-api-delpi interno ok: actions=%s",
            report.get("actionsInDatabase"),
        )
        return jsonify(report), 200
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        logger.exception("sync-api-delpi interno falhou")
        return (
            jsonify({"ok": False, "providerKey": provider_key, "error": str(exc)}),
            502,
        )
