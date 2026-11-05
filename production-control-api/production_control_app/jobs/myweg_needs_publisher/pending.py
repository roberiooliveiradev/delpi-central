"""Descoberta e publicação sequencial de coletas pendentes (sem backfill em massa)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from production_control_app.jobs.myweg_needs_publisher.collection_reader import (
    CollectionIncompleteError,
    list_collection_dirs,
    load_collection,
)
from production_control_app.jobs.myweg_needs_publisher.config import PublisherConfig
from production_control_app.jobs.myweg_needs_publisher.http_client import (
    MyWegNeedsPublisherClient,
)
from production_control_app.jobs.myweg_needs_publisher.payload_builder import (
    build_ingest_payload,
)
from production_control_app.jobs.myweg_needs_publisher.state_store import PublisherStateStore

logger = logging.getLogger("myweg_needs_publisher")
_SAO_PAULO = ZoneInfo("America/Sao_Paulo")


@dataclass(frozen=True)
class PendingCandidate:
    collection_id: str
    collected_at: datetime
    directory: Path
    status: str  # eligible | blocked | conflict | already_published | before_watermark
    reason: str | None = None
    payload_sha256: str | None = None


def discover_pending_candidates(
    *,
    root: Path,
    state: PublisherStateStore,
    stability_wait_seconds: float,
    activation_collected_at: datetime | None,
    include_historical: bool,
) -> list[PendingCandidate]:
    """Lista pastas sob a raiz, ordenadas por collected_at ascendente."""
    candidates: list[PendingCandidate] = []
    for directory in list_collection_dirs(root):
        collection_id = directory.name
        try:
            artifacts = load_collection(
                directory, stability_wait_seconds=stability_wait_seconds
            )
            built = build_ingest_payload(artifacts)
            sha = str(built["batch"]["payload_sha256"])
            collected_at = artifacts.collected_at
        except CollectionIncompleteError as exc:
            candidates.append(
                PendingCandidate(
                    collection_id=collection_id,
                    collected_at=_fallback_sort_key(directory),
                    directory=directory,
                    status="blocked",
                    reason=str(exc),
                )
            )
            continue
        except (ValueError, OSError) as exc:
            candidates.append(
                PendingCandidate(
                    collection_id=collection_id,
                    collected_at=_fallback_sort_key(directory),
                    directory=directory,
                    status="blocked",
                    reason=str(exc),
                )
            )
            continue

        prior = state.get_success_for_collection(collection_id)
        if prior is not None:
            prior_sha = str(prior.get("payload_sha256") or "").lower()
            if prior_sha and prior_sha != sha.lower():
                candidates.append(
                    PendingCandidate(
                        collection_id=collection_id,
                        collected_at=collected_at,
                        directory=directory,
                        status="conflict",
                        reason=(
                            "collection_id já publicado com payload_sha256 diferente "
                            f"(estado={prior_sha[:12]}… atual={sha[:12]}…). "
                            "Não sobrescrever — investigar."
                        ),
                        payload_sha256=sha,
                    )
                )
                continue
            candidates.append(
                PendingCandidate(
                    collection_id=collection_id,
                    collected_at=collected_at,
                    directory=directory,
                    status="already_published",
                    reason="Sucesso local prévio com o mesmo hash.",
                    payload_sha256=sha,
                )
            )
            continue

        if (
            activation_collected_at is not None
            and not include_historical
            and collected_at < activation_collected_at
        ):
            candidates.append(
                PendingCandidate(
                    collection_id=collection_id,
                    collected_at=collected_at,
                    directory=directory,
                    status="before_watermark",
                    reason=(
                        "collected_at anterior ao marco de ativação "
                        f"({activation_collected_at.isoformat()})."
                    ),
                    payload_sha256=sha,
                )
            )
            continue

        candidates.append(
            PendingCandidate(
                collection_id=collection_id,
                collected_at=collected_at,
                directory=directory,
                status="eligible",
                payload_sha256=sha,
            )
        )

    candidates.sort(key=lambda item: (item.collected_at, item.collection_id))
    return candidates


def run_pending_publish(
    *,
    config: PublisherConfig,
    dry_run: bool,
    max_batches: int,
    include_historical: bool,
    client: MyWegNeedsPublisherClient | None = None,
) -> dict[str, Any]:
    state = PublisherStateStore(config.state_dir)
    activation = config.activation_collected_at or state.get_activation_watermark()

    with state.acquire_run_lock() as acquired:
        if not acquired:
            return {
                "ok": True,
                "mode": "dry-run-pending" if dry_run else "publish-pending",
                "status": "busy",
                "message": "Outra execução do publicador ainda está ativa (run lock).",
                "pending": 0,
                "published": 0,
                "rejected": 0,
                "blocked": 0,
                "skipped": 0,
                "items": [],
            }

        if activation is None and not include_historical:
            return {
                "ok": False,
                "mode": "dry-run-pending" if dry_run else "publish-pending",
                "status": "activation_watermark_required",
                "error": (
                    "Marco de ativação ausente. Defina "
                    "MYWEG_PUBLISHER_ACTIVATION_COLLECTED_AT (ISO) ou grave via "
                    "estado/instalação para evitar backfill histórico em massa."
                ),
                "pending": 0,
                "published": 0,
                "rejected": 0,
                "blocked": 0,
                "skipped": 0,
                "items": [],
            }

        discovered = discover_pending_candidates(
            root=config.normalized_root,
            state=state,
            stability_wait_seconds=config.stability_wait_seconds,
            activation_collected_at=activation,
            include_historical=include_historical,
        )

        eligible = [item for item in discovered if item.status == "eligible"]
        blocked = [item for item in discovered if item.status == "blocked"]
        conflicts = [item for item in discovered if item.status == "conflict"]
        skipped = [
            item
            for item in discovered
            if item.status in {"already_published", "before_watermark"}
        ]

        to_process = eligible[: max(0, max_batches)]
        items: list[dict[str, Any]] = []
        published = 0
        rejected = 0

        for candidate in blocked + conflicts + skipped:
            items.append(_candidate_summary(candidate))

        http_client = client
        if not dry_run and to_process and http_client is None:
            http_client = MyWegNeedsPublisherClient(
                base_url=config.api_base_url,
                service_token=config.service_token,
                caller_app=config.caller_app,
                timeout_seconds=config.timeout_seconds,
                max_attempts=config.max_attempts,
            )

        for candidate in to_process:
            detail = _process_one(
                candidate=candidate,
                dry_run=dry_run,
                state=state,
                client=http_client,
                stability_wait_seconds=config.stability_wait_seconds,
            )
            items.append(detail)
            if detail.get("status") in {"published", "idempotent", "dry_run_ok"}:
                published += 1
            elif detail.get("status") in {"failed", "conflict"}:
                rejected += 1

        deferred = eligible[max(0, max_batches) :]
        for candidate in deferred:
            items.append(
                {
                    **_candidate_summary(candidate),
                    "status": "deferred_max_batches",
                    "reason": f"Limite max_batches={max_batches} nesta execução.",
                }
            )

        return {
            "ok": rejected == 0,
            "mode": "dry-run-pending" if dry_run else "publish-pending",
            "status": "completed",
            "activation_collected_at": activation.isoformat() if activation else None,
            "max_batches": max_batches,
            "include_historical": include_historical,
            "pending": len(eligible),
            "published": published,
            "rejected": rejected,
            "blocked": len(blocked) + len(conflicts),
            "skipped": len(skipped) + len(deferred),
            "sb1_note": (
                "Coletas novas entram com SB1 pending; dry_run=false de matching "
                "NÃO é automatizado por este publicador."
            ),
            "items": items,
        }


def _process_one(
    *,
    candidate: PendingCandidate,
    dry_run: bool,
    state: PublisherStateStore,
    client: MyWegNeedsPublisherClient | None,
    stability_wait_seconds: float,
) -> dict[str, Any]:
    base = _candidate_summary(candidate)
    try:
        artifacts = load_collection(
            candidate.directory, stability_wait_seconds=stability_wait_seconds
        )
        built = build_ingest_payload(artifacts)
    except (CollectionIncompleteError, ValueError, OSError) as exc:
        state.record_attempt(
            collection_id=candidate.collection_id,
            payload_sha256=candidate.payload_sha256 or "unknown",
            status="blocked",
            result=str(exc),
            dry_run=dry_run,
        )
        return {**base, "status": "blocked", "reason": str(exc), "ok": False}

    sha = str(built["batch"]["payload_sha256"])
    base["payload_sha256"] = sha
    base["collected_at"] = artifacts.collected_at.isoformat()
    base["record_count"] = built["record_count"]
    base["idempotency_key"] = built["idempotency_key"]

    if dry_run:
        return {**base, "status": "dry_run_ok", "ok": True, "http": {"sent": False}}

    assert client is not None
    result = client.publish(built["payload"], idempotency_key=built["idempotency_key"])
    if result.ok:
        label = "published" if result.created else "idempotent"
        state.record_attempt(
            collection_id=artifacts.collection_id,
            payload_sha256=sha,
            status=label,
            http_status=result.status_code,
            result=f"created={result.created}",
            dry_run=False,
        )
        return {
            **base,
            "status": label,
            "ok": True,
            "http": {
                "sent": True,
                "ok": True,
                "status_code": result.status_code,
                "created": result.created,
                "attempts": result.attempts,
            },
        }

    status = "conflict" if result.status_code == 409 else "failed"
    state.record_attempt(
        collection_id=artifacts.collection_id,
        payload_sha256=sha,
        status=status,
        http_status=result.status_code,
        result=result.error,
        dry_run=False,
    )
    return {
        **base,
        "status": status,
        "ok": False,
        "reason": result.error,
        "http": {
            "sent": True,
            "ok": False,
            "status_code": result.status_code,
            "created": result.created,
            "attempts": result.attempts,
            "error": result.error,
        },
    }


def _candidate_summary(candidate: PendingCandidate) -> dict[str, Any]:
    return {
        "collection_id": candidate.collection_id,
        "collected_at": candidate.collected_at.isoformat(),
        "status": candidate.status,
        "reason": candidate.reason,
        "payload_sha256": candidate.payload_sha256,
    }


def _fallback_sort_key(directory: Path) -> datetime:
    # Pastas bloqueadas ainda entram na lista ordenada pelo mtime (não some silenciosamente).
    try:
        return datetime.fromtimestamp(directory.stat().st_mtime, tz=_SAO_PAULO)
    except OSError:
        return datetime(1970, 1, 1, tzinfo=_SAO_PAULO)
