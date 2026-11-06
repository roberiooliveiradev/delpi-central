"""CLI — dry-run / publish one-shot e --publish-pending (timer separado)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
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
from production_control_app.jobs.myweg_invoice_observations_publisher.pending import (
    run_invoice_pending_publish,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.state_store import (
    InvoicePublisherStateStore,
)
from production_control_app.jobs.myweg_needs_publisher.http_client import redact_secrets

logger = logging.getLogger("myweg_invoice_observations_publisher")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="myweg-invoice-observations-publisher",
        description=(
            "Publica observações históricas de NF MyWEG (filial 02) no Production Control. "
            "Modos manuais (--collection-id/--directory) ou pendências (--publish-pending)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lê/valida e emite resumo sem POST e sem marcar publicação concluída.",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Envia POST S2S (obrigatório para publicação real).",
    )
    parser.add_argument(
        "--publish-pending",
        action="store_true",
        help=(
            "Descobre e processa coletas fiscais elegíveis após o marco de ativação "
            "(limite max-batches)."
        ),
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
        help="Máximo de publicações (representantes por data) nesta execução.",
    )
    parser.add_argument(
        "--include-historical",
        action="store_true",
        help=(
            "Backfill controlado: ignora marco de ativação "
            "(ainda limitado por --max-batches)."
        ),
    )
    parser.add_argument(
        "--set-activation-document-date",
        help="Grava marco document_date_min (YYYY-MM-DD) no estado local e encerra.",
    )
    parser.add_argument(
        "--record-published-success",
        action="store_true",
        help=(
            "Registra sucesso operacional local (collection já aceita na API) "
            "sem POST. Exige --collection-id e hashes."
        ),
    )
    parser.add_argument("--payload-sha256", help="Hash para --record-published-success.")
    parser.add_argument("--semantic-sha256", help="Hash para --record-published-success.")
    parser.add_argument("--document-date", help="Data documento YYYY-MM-DD.")
    parser.add_argument("--observation-id", help="ID da observação aceita na API.")
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
        "--state-dir",
        help="Override de MYWEG_INVOICE_PUBLISHER_STATE_DIR.",
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

    if args.set_activation_document_date:
        return _set_activation(parser, args)

    if args.record_published_success:
        return _record_published(parser, args)

    if args.dry_run == args.publish:
        parser.error("Informe exatamente um modo: --dry-run ou --publish.")

    selectors = [
        bool(args.collection_id),
        bool(args.directory),
        bool(args.publish_pending),
    ]
    if sum(selectors) != 1:
        parser.error(
            "Informe exatamente um de: --collection-id, --directory ou --publish-pending."
        )

    try:
        config = _load_config(args, require_token=not args.dry_run)
    except ValueError as exc:
        _emit({"ok": False, "error": str(exc)}, as_json=args.json)
        return 2

    if args.publish_pending:
        max_batches = (
            args.max_batches
            if args.max_batches is not None
            else config.max_batches_per_run
        )
        summary = run_invoice_pending_publish(
            config=config,
            dry_run=bool(args.dry_run),
            max_batches=max(0, int(max_batches)),
            include_historical=bool(args.include_historical),
        )
        _emit(summary, as_json=args.json)
        if summary.get("status") == "activation_watermark_required":
            return 2
        if summary.get("status") == "busy":
            return 0
        return 0 if summary.get("ok") else 1

    return _run_one_shot(args=args, config=config)


def _load_config(args: argparse.Namespace, *, require_token: bool) -> InvoicePublisherConfig:
    try:
        config = InvoicePublisherConfig.from_env()
    except ValueError:
        if require_token:
            raise
        import os

        config = InvoicePublisherConfig(
            invoice_root=Path(
                args.invoice_root
                or os.getenv(
                    "MYWEG_INVOICE_ROOT",
                    "/home/michael/.local/share/MyWEG-Automacao/notas-fiscais/"
                    "filial-02/empresa-1009/centro-1106/fornecedor-50471",
                )
            ).expanduser(),
            state_dir=Path(
                args.state_dir
                or os.getenv(
                    "MYWEG_INVOICE_PUBLISHER_STATE_DIR",
                    "/tmp/myweg-invoice-publisher-state",
                )
            ).expanduser(),
            api_base_url="http://localhost",
            service_token="",
            caller_app="myweg-invoice-observations-publisher",
            timeout_seconds=60.0,
            max_attempts=1,
            stability_wait_seconds=0.0,
            max_batches_per_run=5,
        )
        logger.warning("dry-run sem token S2S completo.")

    invoice_root = (
        Path(args.invoice_root).expanduser() if args.invoice_root else config.invoice_root
    )
    state_dir = (
        Path(args.state_dir).expanduser() if args.state_dir else config.state_dir
    )
    api_url = args.api_url.rstrip("/") if args.api_url else config.api_base_url
    stability = 0.0 if args.dry_run else config.stability_wait_seconds
    return InvoicePublisherConfig(
        invoice_root=invoice_root,
        state_dir=state_dir,
        api_base_url=api_url,
        service_token=config.service_token,
        caller_app=config.caller_app,
        timeout_seconds=config.timeout_seconds,
        max_attempts=config.max_attempts,
        stability_wait_seconds=stability,
        max_batches_per_run=config.max_batches_per_run,
        activation_document_date=config.activation_document_date,
        branch=config.branch,
    )


def _set_activation(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    raw = str(args.set_activation_document_date or "").strip()
    try:
        watermark = date.fromisoformat(raw[:10])
    except ValueError:
        parser.error("--set-activation-document-date exige YYYY-MM-DD.")
        return 2
    try:
        config = _load_config(args, require_token=False)
    except ValueError as exc:
        _emit({"ok": False, "error": str(exc)}, as_json=args.json)
        return 2
    store = InvoicePublisherStateStore(config.state_dir)
    store.set_activation_document_date(watermark)
    _emit(
        {
            "ok": True,
            "mode": "set-activation-document-date",
            "activation_watermark": watermark.isoformat(),
            "state_dir": str(config.state_dir),
        },
        as_json=args.json,
    )
    return 0


def _record_published(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    if not args.collection_id or not args.payload_sha256 or not args.semantic_sha256:
        parser.error(
            "--record-published-success exige --collection-id, "
            "--payload-sha256 e --semantic-sha256."
        )
    document_date = (args.document_date or "").strip()
    if not document_date:
        parser.error("--record-published-success exige --document-date YYYY-MM-DD.")
    try:
        date.fromisoformat(document_date[:10])
    except ValueError:
        parser.error("--document-date inválida.")
    try:
        config = _load_config(args, require_token=False)
    except ValueError as exc:
        _emit({"ok": False, "error": str(exc)}, as_json=args.json)
        return 2
    store = InvoicePublisherStateStore(config.state_dir)
    store.record_attempt(
        collection_id=str(args.collection_id),
        payload_sha256=str(args.payload_sha256).lower(),
        status="published",
        document_date=document_date[:10],
        semantic_sha256=str(args.semantic_sha256).lower(),
        observation_id=args.observation_id,
        http_status=201,
        result="seeded_from_manual_publish",
        dry_run=False,
    )
    _emit(
        {
            "ok": True,
            "mode": "record-published-success",
            "collection_id": args.collection_id,
            "document_date": document_date[:10],
            "observation_id": args.observation_id,
            "state_dir": str(config.state_dir),
        },
        as_json=args.json,
    )
    return 0


def _run_one_shot(*, args: argparse.Namespace, config: InvoicePublisherConfig) -> int:
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
    if http_result.ok:
        InvoicePublisherStateStore(config.state_dir).record_attempt(
            collection_id=str(built["collection_id"]),
            payload_sha256=str(built["payload_sha256"]),
            status="published" if http_result.created else "idempotent",
            document_date=str(built["document_date"]),
            semantic_sha256=str(built["semantic_sha256"]),
            observation_id=str(data.get("id")) if data.get("id") else None,
            http_status=http_result.status_code,
            result=f"created={http_result.created}",
            dry_run=False,
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
            "result mode=%s status=%s collection=%s document_date=%s published=%s",
            payload.get("mode"),
            payload.get("status") or payload.get("httpStatus"),
            payload.get("collection_id") or payload.get("collectionId"),
            payload.get("document_date") or payload.get("documentDate"),
            payload.get("published"),
        )
    else:
        logger.error("result error=%s", payload.get("error") or payload.get("status"))


if __name__ == "__main__":
    raise SystemExit(main())
