"""CLI do publicador MyWEG Necessidades (manual + pendências)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from production_control_app.jobs.myweg_needs_publisher.collection_reader import (
    CollectionIncompleteError,
    load_collection,
    select_latest_eligible_dir,
)
from production_control_app.jobs.myweg_needs_publisher.config import PublisherConfig
from production_control_app.jobs.myweg_needs_publisher.http_client import (
    MyWegNeedsPublisherClient,
    redact_secrets,
)
from production_control_app.jobs.myweg_needs_publisher.payload_builder import (
    build_ingest_payload,
)
from production_control_app.jobs.myweg_needs_publisher.pending import run_pending_publish
from production_control_app.jobs.myweg_needs_publisher.state_store import PublisherStateStore

logger = logging.getLogger("myweg_needs_publisher")
_SAO_PAULO = ZoneInfo("America/Sao_Paulo")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="myweg-needs-publisher",
        description=(
            "Publica coletas MyWEG (filial 02) no Production Control. "
            "Modos manuais (--collection-id/--latest) ou pendências (--publish-pending)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula validação/payload sem HTTP e sem alterar estado de publicação.",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Envia POST S2S (obrigatório para publicação real).",
    )
    parser.add_argument(
        "--collection-id",
        help="Seleciona pasta explícita sob MYWEG_NORMALIZED_ROOT.",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Seleciona a coleta elegível mais recente (nome de pasta).",
    )
    parser.add_argument(
        "--publish-pending",
        action="store_true",
        help=(
            "Processa coletas pendentes em ordem de collected_at "
            "(limite max-batches; exige marco de ativação)."
        ),
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
        help="Máximo de coletas elegíveis por execução pending (default env/5).",
    )
    parser.add_argument(
        "--include-historical",
        action="store_true",
        help=(
            "Permite recuperação explícita de coletas anteriores ao marco "
            "(ainda limitada por --max-batches)."
        ),
    )
    parser.add_argument(
        "--set-activation-watermark",
        metavar="ISO_DATETIME",
        help=(
            "Grava marco de ativação no estado (America/Sao_Paulo se naive) e encerra. "
            "Não publica."
        ),
    )
    parser.add_argument(
        "--normalized-root",
        help="Override de MYWEG_NORMALIZED_ROOT.",
    )
    parser.add_argument(
        "--state-dir",
        help="Override de MYWEG_PUBLISHER_STATE_DIR.",
    )
    parser.add_argument(
        "--api-url",
        help="Override de MYWEG_PC_API_URL.",
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

    if args.set_activation_watermark:
        return _set_watermark(parser, args)

    if args.publish and args.dry_run:
        parser.error("Use --dry-run OU --publish, não ambos.")
    if not args.publish and not args.dry_run:
        parser.error("Informe --dry-run (simulação) ou --publish (envio real).")

    selectors = sum(
        bool(x) for x in (args.collection_id, args.latest, args.publish_pending)
    )
    if selectors != 1:
        parser.error(
            "Informe exatamente um de: --collection-id, --latest ou --publish-pending."
        )

    try:
        config = PublisherConfig.from_env()
    except ValueError as exc:
        if args.dry_run:
            import os

            os.environ.setdefault("API_DELPI_INTERNAL_SERVICE_TOKEN", "dry-run-unused-token")
            config = PublisherConfig.from_env()
        else:
            _emit({"ok": False, "error": str(exc)}, as_json=args.json)
            return 2

    config = _apply_overrides(config, args)

    if config.branch != "02":
        _emit({"ok": False, "error": "Escopo restrito à filial 02."}, as_json=args.json)
        return 2

    if args.publish_pending:
        max_batches = (
            args.max_batches
            if args.max_batches is not None
            else config.max_batches_per_run
        )
        summary = run_pending_publish(
            config=config,
            dry_run=bool(args.dry_run),
            max_batches=max(0, int(max_batches)),
            include_historical=bool(args.include_historical),
        )
        _emit(summary, as_json=args.json)
        if summary.get("status") == "busy":
            return 0
        if summary.get("status") == "activation_watermark_required":
            return 2
        return 0 if summary.get("ok") else 1

    return _run_single(config=config, args=args)


def _set_watermark(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    raw = str(args.set_activation_watermark or "").strip()
    try:
        watermark = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        parser.error("--set-activation-watermark exige datetime ISO.")
    if watermark.tzinfo is None:
        watermark = watermark.replace(tzinfo=_SAO_PAULO)

    # Token não é necessário para gravar watermark; use dry-run token stub se ausente.
    import os

    os.environ.setdefault("API_DELPI_INTERNAL_SERVICE_TOKEN", "watermark-unused-token")
    try:
        config = PublisherConfig.from_env()
    except ValueError as exc:
        _emit({"ok": False, "error": str(exc)}, as_json=args.json)
        return 2
    config = _apply_overrides(config, args)
    store = PublisherStateStore(config.state_dir)
    store.set_activation_watermark(watermark)
    _emit(
        {
            "ok": True,
            "mode": "set-activation-watermark",
            "activation_collected_at": watermark.isoformat(),
            "state_dir": str(config.state_dir),
        },
        as_json=args.json,
    )
    return 0


def _run_single(*, config: PublisherConfig, args: argparse.Namespace) -> int:
    try:
        directory = _resolve_directory(config.normalized_root, args)
        artifacts = load_collection(
            directory,
            stability_wait_seconds=config.stability_wait_seconds,
        )
        built = build_ingest_payload(artifacts)
    except (CollectionIncompleteError, ValueError, OSError) as exc:
        message = redact_secrets(str(exc), config.service_token)
        logger.error("coleta_rejeitada: %s", message)
        _emit({"ok": False, "error": message}, as_json=args.json)
        return 1

    summary = {
        "ok": True,
        "mode": "dry-run" if args.dry_run else "publish",
        "collection_id": artifacts.collection_id,
        "branch": "02",
        "record_count": built["record_count"],
        "empty_referencia_count": built["empty_referencia_count"],
        "payload_sha256": built["batch"]["payload_sha256"],
        "idempotency_key": built["idempotency_key"],
        "totals": built["batch"]["totals"],
        "collected_at": built["payload"]["collected_at"],
        "source_files": {
            key: value[:12] + "…" for key, value in artifacts.file_hashes.items()
        },
        "sb1_note": (
            "Coleta entra com SB1 pending; matching persistido NÃO é disparado aqui."
        ),
    }

    if args.dry_run:
        summary["http"] = {"sent": False}
        _emit(summary, as_json=args.json)
        return 0

    state = PublisherStateStore(config.state_dir)
    client = MyWegNeedsPublisherClient(
        base_url=config.api_base_url,
        service_token=config.service_token,
        caller_app=config.caller_app,
        timeout_seconds=config.timeout_seconds,
        max_attempts=config.max_attempts,
    )
    result = client.publish(
        built["payload"],
        idempotency_key=built["idempotency_key"],
    )
    status_label = "published" if result.ok and result.created else (
        "idempotent" if result.ok else "failed"
    )
    if result.status_code == 409:
        status_label = "conflict"
    state.record_attempt(
        collection_id=artifacts.collection_id,
        payload_sha256=built["batch"]["payload_sha256"],
        status=status_label,
        http_status=result.status_code,
        result=(
            "created=true"
            if result.created is True
            else "created=false"
            if result.created is False
            else result.error
        ),
        dry_run=False,
    )
    summary["http"] = {
        "sent": True,
        "ok": result.ok,
        "status_code": result.status_code,
        "created": result.created,
        "attempts": result.attempts,
        "error": result.error,
    }
    if result.body and isinstance(result.body.get("data"), dict):
        data = result.body["data"]
        summary["http"]["id"] = data.get("id")
        summary["http"]["recordCount"] = data.get("recordCount")

    _emit(summary, as_json=args.json)
    return 0 if result.ok else 1


def _resolve_directory(root: Path, args: argparse.Namespace) -> Path:
    if args.collection_id:
        return root / str(args.collection_id).strip()
    return select_latest_eligible_dir(root)


def _apply_overrides(config: PublisherConfig, args: argparse.Namespace) -> PublisherConfig:
    changes: dict[str, Any] = {}
    if args.normalized_root:
        changes["normalized_root"] = Path(args.normalized_root)
    if args.state_dir:
        changes["state_dir"] = Path(args.state_dir)
    if args.api_url:
        changes["api_base_url"] = args.api_url.rstrip("/")
    if not changes:
        return config
    return _replace(config, **changes)


def _replace(config: PublisherConfig, **changes: Any) -> PublisherConfig:
    data = {
        "normalized_root": config.normalized_root,
        "state_dir": config.state_dir,
        "api_base_url": config.api_base_url,
        "service_token": config.service_token,
        "caller_app": config.caller_app,
        "timeout_seconds": config.timeout_seconds,
        "max_attempts": config.max_attempts,
        "stability_wait_seconds": config.stability_wait_seconds,
        "max_batches_per_run": config.max_batches_per_run,
        "activation_collected_at": config.activation_collected_at,
        "branch": config.branch,
    }
    data.update(changes)
    return PublisherConfig(**data)


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    print(text if as_json else text)


if __name__ == "__main__":
    sys.exit(main())
