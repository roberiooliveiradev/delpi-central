"""CLI one-shot — dry-run / publish de observação MyWEG NF (sem timer)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from production_control_app.jobs.myweg_invoice_observations_publisher.collection_reader import (
    InvoiceCollectionIncompleteError,
    InvoiceCollectionReadError,
    load_invoice_collection,
    resolve_collection_dir,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.config import (
    InvoicePublisherConfig,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.http_client import (
    MyWegInvoiceObservationsPublisherClient,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.payload_builder import (
    build_ingest_payload,
)
from production_control_app.jobs.myweg_needs_publisher.http_client import redact_secrets

logger = logging.getLogger("myweg_invoice_observations_publisher")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="myweg-invoice-observations-publisher",
        description=(
            "Publica observações históricas de NF MyWEG (filial 02) no Production Control. "
            "Somente one-shot manual — não instala timer."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lê/valida e emite resumo sem POST e sem escrita no banco.",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Envia POST S2S (obrigatório para publicação real).",
    )
    parser.add_argument(
        "--collection-id",
        help="Seleciona pasta pelo collection_id sob MYWEG_INVOICE_ROOT.",
    )
    parser.add_argument(
        "--directory",
        help="Caminho absoluto/relativo da pasta da coleta (manifesto.json).",
    )
    parser.add_argument(
        "--invoice-root",
        help="Override de MYWEG_INVOICE_ROOT.",
    )
    parser.add_argument(
        "--api-url",
        help="Override de MYWEG_PC_API_URL / PRODUCTION_CONTROL_API_URL.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emite resultado em JSON (sem secrets).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.dry_run == args.publish:
        parser.error("Informe exatamente um modo: --dry-run ou --publish.")
    if not args.collection_id and not args.directory:
        parser.error("Informe --collection-id ou --directory.")

    try:
        config = InvoicePublisherConfig.from_env()
    except ValueError as exc:
        if args.dry_run:
            # dry-run pode operar sem token S2S
            config = InvoicePublisherConfig(
                invoice_root=Path(
                    args.invoice_root
                    or __import__("os").getenv(
                        "MYWEG_INVOICE_ROOT",
                        "/home/michael/.local/share/MyWEG-Automacao/notas-fiscais/"
                        "filial-02/empresa-1009/centro-1106/fornecedor-50471",
                    )
                ).expanduser(),
                api_base_url="http://localhost",
                service_token="",
                caller_app="myweg-invoice-observations-publisher",
                timeout_seconds=60.0,
                max_attempts=1,
                stability_wait_seconds=0.0 if args.dry_run else 0.75,
            )
            logger.warning("dry-run sem token S2S: %s", exc)
        else:
            _emit({"ok": False, "error": str(exc)}, as_json=args.json)
            return 2

    if args.invoice_root:
        config = InvoicePublisherConfig(
            invoice_root=Path(args.invoice_root).expanduser(),
            api_base_url=args.api_url or config.api_base_url,
            service_token=config.service_token,
            caller_app=config.caller_app,
            timeout_seconds=config.timeout_seconds,
            max_attempts=config.max_attempts,
            stability_wait_seconds=0.0 if args.dry_run else config.stability_wait_seconds,
        )
    elif args.api_url:
        config = InvoicePublisherConfig(
            invoice_root=config.invoice_root,
            api_base_url=args.api_url.rstrip("/"),
            service_token=config.service_token,
            caller_app=config.caller_app,
            timeout_seconds=config.timeout_seconds,
            max_attempts=config.max_attempts,
            stability_wait_seconds=0.0 if args.dry_run else config.stability_wait_seconds,
        )
    elif args.dry_run:
        config = InvoicePublisherConfig(
            invoice_root=config.invoice_root,
            api_base_url=config.api_base_url,
            service_token=config.service_token,
            caller_app=config.caller_app,
            timeout_seconds=config.timeout_seconds,
            max_attempts=config.max_attempts,
            stability_wait_seconds=0.0,
        )

    try:
        directory = resolve_collection_dir(
            config.invoice_root,
            collection_id=args.collection_id,
            directory=Path(args.directory) if args.directory else None,
        )
        artifacts = load_invoice_collection(
            directory,
            stability_wait_seconds=config.stability_wait_seconds,
            expected_collection_id=args.collection_id,
        )
        built = build_ingest_payload(artifacts)
    except (InvoiceCollectionIncompleteError, InvoiceCollectionReadError, ValueError) as exc:
        result = {
            "ok": False,
            "mode": "dry-run" if args.dry_run else "publish",
            "error": str(exc),
            "error_class": exc.__class__.__name__,
        }
        _emit(result, as_json=args.json)
        return 1

    summary = {
        "ok": True,
        "mode": "dry-run" if args.dry_run else "publish",
        "collectionId": built["collection_id"],
        "documentDate": built["document_date"],
        "observationStatus": built["observation_status"],
        "recordCount": built["record_count"],
        "totalQuantityUn": built["total_quantity_un"],
        "sourceSha256": built["source_sha256"],
        "payloadSha256": built["payload_sha256"],
        "semanticSha256": built["semantic_sha256"],
        "idempotencyKey": built["idempotency_key"],
    }

    if args.dry_run:
        _emit(summary, as_json=args.json)
        return 0

    client = MyWegInvoiceObservationsPublisherClient(
        base_url=config.api_base_url,
        service_token=config.service_token,
        caller_app=config.caller_app,
        timeout_seconds=config.timeout_seconds,
        max_attempts=config.max_attempts,
    )
    http_result = client.publish(
        built["payload"],
        idempotency_key=built["idempotency_key"],
    )
    data = (http_result.body or {}).get("data") or {}
    summary.update(
        {
            "ok": http_result.ok,
            "httpStatus": http_result.status_code,
            "created": http_result.created,
            "observationId": data.get("id"),
            "attempts": http_result.attempts,
            "error": http_result.error,
        }
    )
    if config.service_token and summary.get("error"):
        summary["error"] = redact_secrets(str(summary["error"]), config.service_token)
    _emit(summary, as_json=args.json)
    return 0 if http_result.ok else 1


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        return
    if payload.get("ok"):
        logger.info(
            "result mode=%s collection=%s status=%s records=%s observation=%s",
            payload.get("mode"),
            payload.get("collectionId"),
            payload.get("observationStatus") or payload.get("httpStatus"),
            payload.get("recordCount"),
            payload.get("observationId"),
        )
    else:
        logger.error("result error=%s", payload.get("error"))


if __name__ == "__main__":
    raise SystemExit(main())
