"""Descoberta, publicação e resolução SB1 de coletas pendentes (sem backfill em massa)."""

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
                "sb1_resolved": 0,
                "sb1_skipped": 0,
                "sb1_failed": 0,
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
                "sb1_resolved": 0,
                "sb1_skipped": 0,
                "sb1_failed": 0,
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
        already_published = [
            item for item in discovered if item.status == "already_published"
        ]
        before_watermark = [
            item for item in discovered if item.status == "before_watermark"
        ]

        to_process = eligible[: max(0, max_batches)]
        items: list[dict[str, Any]] = []
        published = 0
        rejected = 0
        sb1_resolved = 0
        sb1_skipped = 0
        sb1_failed = 0

        for candidate in blocked + conflicts + before_watermark:
            items.append(_candidate_summary(candidate))

        http_client = client
        needs_http = (not dry_run) and (
            bool(to_process)
            or (config.auto_sb1_resolve and bool(already_published))
        )
        if needs_http and http_client is None:
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
                auto_sb1_resolve=config.auto_sb1_resolve,
            )
            items.append(detail)
            if detail.get("status") in {"published", "idempotent", "dry_run_ok"}:
                published += 1
            elif detail.get("status") in {"failed", "conflict"}:
                rejected += 1
            sb1 = detail.get("sb1") or {}
            if sb1.get("status") in {"resolved", "dry_run_ok"}:
                sb1_resolved += 1
            elif sb1.get("status") == "already_resolved":
                sb1_skipped += 1
            elif sb1.get("status") in {"failed", "auth_failed", "semantics_blocked"}:
                sb1_failed += 1

        # Recuperação E4: lotes already_published no watermark sem SB1 completa.
        recovery_pool = [
            item
            for item in already_published
            if activation is None
            or include_historical
            or item.collected_at >= activation
        ]
        recovery_limit = max(0, int(config.max_sb1_batches_per_run))
        recovery_to_run = recovery_pool[:recovery_limit] if config.auto_sb1_resolve else []
        recovery_deferred = recovery_pool[recovery_limit:] if config.auto_sb1_resolve else recovery_pool

        for candidate in recovery_to_run:
            detail = _candidate_summary(candidate)
            if dry_run:
                detail["sb1"] = {
                    "status": "dry_run_ok",
                    "ok": True,
                    "mode": "recover-already-published",
                    "note": "Would call sb1-resolve with skip_if_complete=true",
                }
                sb1_resolved += 1
            else:
                assert http_client is not None
                sb1 = _resolve_sb1(
                    client=http_client,
                    collection_id=candidate.collection_id,
                    state=state,
                    payload_sha256=candidate.payload_sha256 or "unknown",
                )
                detail["sb1"] = sb1
                if sb1.get("status") in {"resolved"}:
                    sb1_resolved += 1
                elif sb1.get("status") == "already_resolved":
                    sb1_skipped += 1
                elif sb1.get("status") in {"failed", "auth_failed", "semantics_blocked"}:
                    sb1_failed += 1
            items.append(detail)

        for candidate in recovery_deferred:
            items.append(
                {
                    **_candidate_summary(candidate),
                    "sb1": {
                        "status": "deferred_max_sb1_batches",
                        "reason": (
                            f"Limite max_sb1_batches_per_run="
                            f"{config.max_sb1_batches_per_run}."
                            if config.auto_sb1_resolve
                            else "MYWEG_PUBLISHER_AUTO_SB1_RESOLVE desligado."
                        ),
                    },
                }
            )

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
            "ok": rejected == 0 and sb1_failed == 0,
            "mode": "dry-run-pending" if dry_run else "publish-pending",
            "status": "completed",
            "activation_collected_at": activation.isoformat() if activation else None,
            "max_batches": max_batches,
            "include_historical": include_historical,
            "auto_sb1_resolve": config.auto_sb1_resolve,
            "pending": len(eligible),
            "published": published,
            "rejected": rejected,
            "blocked": len(blocked) + len(conflicts),
            "skipped": len(before_watermark) + len(deferred),
            "sb1_resolved": sb1_resolved,
            "sb1_skipped": sb1_skipped,
            "sb1_failed": sb1_failed,
            "items": items,
        }


def _process_one(
    *,
    candidate: PendingCandidate,
    dry_run: bool,
    state: PublisherStateStore,
    client: MyWegNeedsPublisherClient | None,
    stability_wait_seconds: float,
    auto_sb1_resolve: bool,
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
        out = {**base, "status": "dry_run_ok", "ok": True, "http": {"sent": False}}
        if auto_sb1_resolve:
            out["sb1"] = {
                "status": "dry_run_ok",
                "ok": True,
                "note": "Would resolve SB1 after successful ingest",
            }
        return out

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
        out: dict[str, Any] = {
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
        if auto_sb1_resolve:
            out["sb1"] = _resolve_sb1(
                client=client,
                collection_id=artifacts.collection_id,
                state=state,
                payload_sha256=sha,
            )
            # Ingestão permanece válida mesmo se SB1 falhar (RQ-05).
            out["ok"] = True
        return out

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


def _resolve_sb1(
    *,
    client: MyWegNeedsPublisherClient,
    collection_id: str,
    state: PublisherStateStore,
    payload_sha256: str,
) -> dict[str, Any]:
    result = client.resolve_sb1(
        collection_id=collection_id,
        dry_run=False,
        skip_if_complete=True,
    )
    data = ((result.body or {}).get("data") or {}) if result.body else {}
    counts = data.get("counts") or {}
    base = {
        "collection_id": collection_id,
        "http_status": result.status_code,
        "attempts": result.attempts,
        "counts": counts,
        "persisted": result.persisted,
        "skipped": result.skipped,
        "resolution_run_id": data.get("resolutionRunId") or data.get("resolution_run_id"),
        "semantics_proven": (data.get("semantics") or {}).get("proven"),
    }

    if result.ok and result.skipped:
        state.record_attempt(
            collection_id=collection_id,
            payload_sha256=payload_sha256,
            status="sb1_already_resolved",
            http_status=result.status_code,
            result="skip_if_complete",
            dry_run=False,
        )
        return {**base, "status": "already_resolved", "ok": True}

    if result.ok and result.persisted:
        state.record_attempt(
            collection_id=collection_id,
            payload_sha256=payload_sha256,
            status="sb1_resolved",
            http_status=result.status_code,
            result=_summarize_counts(counts),
            dry_run=False,
        )
        return {**base, "status": "resolved", "ok": True}

    if result.ok and not result.persisted:
        # dry-run remoto inesperado ou lookup unavailable sem persist
        error = data.get("error") or "sb1_not_persisted"
        state.record_attempt(
            collection_id=collection_id,
            payload_sha256=payload_sha256,
            status="sb1_incomplete",
            http_status=result.status_code,
            result=str(error)[:300],
            dry_run=False,
        )
        return {
            **base,
            "status": "incomplete",
            "ok": False,
            "error": error,
            "reason": "Resolução SB1 não persistida — nova tentativa no próximo timer.",
        }

    status = "auth_failed" if result.status_code in {401, 403} else "failed"
    if result.status_code == 422:
        status = "semantics_blocked"
    state.record_attempt(
        collection_id=collection_id,
        payload_sha256=payload_sha256,
        status=f"sb1_{status}",
        http_status=result.status_code,
        result=(result.error or "")[:300],
        dry_run=False,
    )
    return {
        **base,
        "status": status,
        "ok": False,
        "error": result.error,
        "reason": (
            "Falha SB1 não invalida a ingestão; recuperação no próximo disparo."
        ),
    }


def _summarize_counts(counts: dict[str, Any]) -> str:
    parts = [
        f"{key}={counts.get(key, 0)}"
        for key in (
            "confirmed",
            "ambiguous",
            "divergent",
            "not_found",
            "blocked",
            "unavailable",
            "pending",
        )
        if counts.get(key)
    ]
    return ",".join(parts) if parts else "counts_empty"


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
