"""CLI manual do publicador MyWEG Necessidades."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

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
from production_control_app.jobs.myweg_needs_publisher.state_store import PublisherStateStore

logger = logging.getLogger("myweg_needs_publisher")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="myweg-needs-publisher",
        description=(
            "Publica coletas MyWEG (filial 02) no Production Control. "
            "Execução exclusivamente manual — sem cron."
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

    if args.publish and args.dry_run:
        parser.error("Use --dry-run OU --publish, não ambos.")
    if not args.publish and not args.dry_run:
        parser.error("Informe --dry-run (simulação) ou --publish (envio real).")
    if bool(args.collection_id) == bool(args.latest):
        parser.error("Informe exatamente um de: --collection-id ou --latest.")

    try:
        config = PublisherConfig.from_env()
    except ValueError as exc:
        if args.dry_run:
            # Dry-run pode validar artefatos sem token se API não for chamada,
            # mas a config exige token. Permitir token dummy só em dry-run via env.
            import os

            os.environ.setdefault("API_DELPI_INTERNAL_SERVICE_TOKEN", "dry-run-unused-token")
            config = PublisherConfig.from_env()
        else:
            _emit({"ok": False, "error": str(exc)}, as_json=args.json)
            return 2

    if args.normalized_root:
        config = _replace(config, normalized_root=Path(args.normalized_root))
    if args.state_dir:
        config = _replace(config, state_dir=Path(args.state_dir))
    if args.api_url:
        config = _replace(config, api_base_url=args.api_url.rstrip("/"))

    if config.branch != "02":
        _emit({"ok": False, "error": "Escopo restrito à filial 02."}, as_json=args.json)
        return 2

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
    status_label = "published" if result.ok else "failed"
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
        "branch": config.branch,
    }
    data.update(changes)
    return PublisherConfig(**data)


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    # Defesa: nunca imprimir token mesmo se vazou em error strings.
    print(text if as_json else text)


if __name__ == "__main__":
    sys.exit(main())
