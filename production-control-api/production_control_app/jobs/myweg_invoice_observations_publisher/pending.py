"""Descoberta e publicação pendente de observações fiscais MyWEG (independente de necessidades)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from production_control_app.domain.myweg_invoice_observations_contract import (
    OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP,
    OBSERVATION_STATUS_WITH_RECORDS,
)
from production_control_app.jobs.myweg_invoice_observations_publisher.collection_reader import (
    InvoiceCollectionIncompleteError,
    InvoiceCollectionReadError,
    list_invoice_collection_dirs,
    load_invoice_collection,
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
from production_control_app.jobs.myweg_invoice_observations_publisher.state_store import (
    InvoicePublisherStateStore,
)

logger = logging.getLogger("myweg_invoice_observations_publisher")
_SAO_PAULO = ZoneInfo("America/Sao_Paulo")


@dataclass(frozen=True)
class InvoicePendingCandidate:
    collection_id: str
    document_date: date
    directory: Path
    status: str
    reason: str | None = None
    payload_sha256: str | None = None
    semantic_sha256: str | None = None
    observation_status: str | None = None
    source_prepared_at: datetime | None = None


def discover_invoice_pending_candidates(
    *,
    root: Path,
    state: InvoicePublisherStateStore,
    stability_wait_seconds: float,
    activation_document_date: date | None,
    include_historical: bool,
) -> list[InvoicePendingCandidate]:
    raw: list[InvoicePendingCandidate] = []
    for directory in list_invoice_collection_dirs(root):
        collection_id = directory.name
        try:
            artifacts = load_invoice_collection(
                directory, stability_wait_seconds=stability_wait_seconds
            )
            built = build_ingest_payload(artifacts)
            payload_sha = str(built["payload_sha256"])
            semantic_sha = str(built["semantic_sha256"])
            document_date = artifacts.document_date
            observation_status = str(built["observation_status"])
            prepared_at = artifacts.source_prepared_at
        except InvoiceCollectionIncompleteError as exc:
            raw.append(
                InvoicePendingCandidate(
                    collection_id=collection_id,
                    document_date=_fallback_document_date(directory),
                    directory=directory,
                    status="blocked",
                    reason=str(exc),
                )
            )
            continue
        except (InvoiceCollectionReadError, ValueError, OSError) as exc:
            raw.append(
                InvoicePendingCandidate(
                    collection_id=collection_id,
                    document_date=_fallback_document_date(directory),
                    directory=directory,
                    status="blocked",
                    reason=str(exc),
                )
            )
            continue

        prior = state.get_success_for_collection(collection_id)
        if prior is not None:
            prior_sha = str(prior.get("payload_sha256") or "").lower()
            if prior_sha and prior_sha != payload_sha.lower():
                raw.append(
                    InvoicePendingCandidate(
                        collection_id=collection_id,
                        document_date=document_date,
                        directory=directory,
                        status="conflict",
                        reason=(
                            "collection_id já publicado com payload_sha256 diferente "
                            f"(estado={prior_sha[:12]}… atual={payload_sha[:12]}…)."
                        ),
                        payload_sha256=payload_sha,
                        semantic_sha256=semantic_sha,
                        observation_status=observation_status,
                        source_prepared_at=prepared_at,
                    )
                )
                continue
            raw.append(
                InvoicePendingCandidate(
                    collection_id=collection_id,
                    document_date=document_date,
                    directory=directory,
                    status="already_published",
                    reason="Sucesso local prévio com o mesmo hash.",
                    payload_sha256=payload_sha,
                    semantic_sha256=semantic_sha,
                    observation_status=observation_status,
                    source_prepared_at=prepared_at,
                )
            )
            continue

        if (
            activation_document_date is not None
            and not include_historical
            and document_date < activation_document_date
        ):
            raw.append(
                InvoicePendingCandidate(
                    collection_id=collection_id,
                    document_date=document_date,
                    directory=directory,
                    status="before_watermark",
                    reason=(
                        "document_date anterior ao marco de ativação "
                        f"({activation_document_date.isoformat()})."
                    ),
                    payload_sha256=payload_sha,
                    semantic_sha256=semantic_sha,
                    observation_status=observation_status,
                    source_prepared_at=prepared_at,
                )
            )
            continue

        raw.append(
            InvoicePendingCandidate(
                collection_id=collection_id,
                document_date=document_date,
                directory=directory,
                status="eligible",
                payload_sha256=payload_sha,
                semantic_sha256=semantic_sha,
                observation_status=observation_status,
                source_prepared_at=prepared_at,
            )
        )

    return _apply_document_date_selection(raw, state=state)


def _apply_document_date_selection(
    candidates: list[InvoicePendingCandidate],
    *,
    state: InvoicePublisherStateStore,
) -> list[InvoicePendingCandidate]:
    """Por data: uma representante semântica; equivalentes ignorados; divergência → conflict."""
    result: list[InvoicePendingCandidate] = []
    by_date: dict[date, list[InvoicePendingCandidate]] = {}
    for item in candidates:
        if item.status != "eligible":
            result.append(item)
            continue
        by_date.setdefault(item.document_date, []).append(item)

    for document_date in sorted(by_date.keys()):
        group = by_date[document_date]
        day_key = document_date.isoformat()
        prior_day = state.get_success_for_document_date(day_key)
        prior_semantic = (
            str(prior_day.get("semantic_sha256") or "").lower() if prior_day else ""
        )

        statuses = {
            str(item.observation_status or "")
            for item in group
            if item.observation_status
        }
        if (
            OBSERVATION_STATUS_EMPTY_SIGNALED_BY_SAP in statuses
            and OBSERVATION_STATUS_WITH_RECORDS in statuses
        ):
            for item in group:
                result.append(
                    InvoicePendingCandidate(
                        collection_id=item.collection_id,
                        document_date=item.document_date,
                        directory=item.directory,
                        status="conflict",
                        reason=(
                            "Mesma data com empty_signaled_by_sap e with_records — "
                            "publicação automática bloqueada."
                        ),
                        payload_sha256=item.payload_sha256,
                        semantic_sha256=item.semantic_sha256,
                        observation_status=item.observation_status,
                        source_prepared_at=item.source_prepared_at,
                    )
                )
            continue

        semantics = sorted(
            {
                str(item.semantic_sha256 or "").lower()
                for item in group
                if item.semantic_sha256
            }
        )
        if prior_semantic and any(s and s != prior_semantic for s in semantics):
            for item in group:
                result.append(
                    InvoicePendingCandidate(
                        collection_id=item.collection_id,
                        document_date=item.document_date,
                        directory=item.directory,
                        status="conflict",
                        reason=(
                            "Conteúdo semântico diverge da observação já publicada "
                            f"para {day_key} — sem supersedência automática."
                        ),
                        payload_sha256=item.payload_sha256,
                        semantic_sha256=item.semantic_sha256,
                        observation_status=item.observation_status,
                        source_prepared_at=item.source_prepared_at,
                    )
                )
            continue

        if len(semantics) > 1:
            for item in group:
                result.append(
                    InvoicePendingCandidate(
                        collection_id=item.collection_id,
                        document_date=item.document_date,
                        directory=item.directory,
                        status="conflict",
                        reason=(
                            f"Versões semanticamente divergentes em {day_key} "
                            f"({len(semantics)} hashes) — intervenção necessária."
                        ),
                        payload_sha256=item.payload_sha256,
                        semantic_sha256=item.semantic_sha256,
                        observation_status=item.observation_status,
                        source_prepared_at=item.source_prepared_at,
                    )
                )
            continue

        if prior_semantic and semantics and semantics[0] == prior_semantic:
            for item in group:
                result.append(
                    InvoicePendingCandidate(
                        collection_id=item.collection_id,
                        document_date=item.document_date,
                        directory=item.directory,
                        status="equivalent_skipped",
                        reason=(
                            f"Conteúdo equivalente à observação já publicada em {day_key}."
                        ),
                        payload_sha256=item.payload_sha256,
                        semantic_sha256=item.semantic_sha256,
                        observation_status=item.observation_status,
                        source_prepared_at=item.source_prepared_at,
                    )
                )
            continue

        # Uma representante determinística: prepared_at mais recente, depois collection_id.
        ordered = sorted(
            group,
            key=lambda item: (
                item.source_prepared_at or datetime.min.replace(tzinfo=_SAO_PAULO),
                item.collection_id,
            ),
            reverse=True,
        )
        # Empate de prepared_at: menor collection_id entre os do mesmo instante.
        best_prepared = ordered[0].source_prepared_at
        same_wave = [
            item
            for item in group
            if item.source_prepared_at == best_prepared
        ]
        representative = sorted(same_wave, key=lambda item: item.collection_id)[0]
        for item in group:
            if item.collection_id == representative.collection_id:
                result.append(item)
            else:
                result.append(
                    InvoicePendingCandidate(
                        collection_id=item.collection_id,
                        document_date=item.document_date,
                        directory=item.directory,
                        status="equivalent_skipped",
                        reason=(
                            "Exportação semanticamente equivalente; "
                            f"representante={representative.collection_id}."
                        ),
                        payload_sha256=item.payload_sha256,
                        semantic_sha256=item.semantic_sha256,
                        observation_status=item.observation_status,
                        source_prepared_at=item.source_prepared_at,
                    )
                )

    result.sort(key=lambda item: (item.document_date, item.collection_id))
    return result


def run_invoice_pending_publish(
    *,
    config: InvoicePublisherConfig,
    dry_run: bool,
    max_batches: int,
    include_historical: bool,
    client: MyWegInvoiceObservationsPublisherClient | None = None,
) -> dict[str, Any]:
    state = InvoicePublisherStateStore(config.state_dir)
    activation = config.activation_document_date or state.get_activation_document_date()

    with state.acquire_run_lock() as acquired:
        if not acquired:
            return {
                "ok": True,
                "mode": "dry-run-pending" if dry_run else "publish-pending",
                "status": "busy",
                "message": "Outra execução do publicador fiscal ainda está ativa (run lock).",
                "activation_watermark": None,
                "discovered": 0,
                "eligible": 0,
                "published": 0,
                "idempotent": 0,
                "already_published": 0,
                "equivalent_skipped": 0,
                "conflict": 0,
                "blocked": 0,
                "failed": 0,
                "deferred": 0,
                "items": [],
            }

        if activation is None and not include_historical:
            return {
                "ok": False,
                "mode": "dry-run-pending" if dry_run else "publish-pending",
                "status": "activation_watermark_required",
                "error": (
                    "Marco de ativação ausente. Defina "
                    "MYWEG_INVOICE_PUBLISHER_ACTIVATION_DOCUMENT_DATE (YYYY-MM-DD) "
                    "ou --set-activation-document-date para evitar backfill histórico."
                ),
                "activation_watermark": None,
                "discovered": 0,
                "eligible": 0,
                "published": 0,
                "idempotent": 0,
                "already_published": 0,
                "equivalent_skipped": 0,
                "conflict": 0,
                "blocked": 0,
                "failed": 0,
                "deferred": 0,
                "items": [],
            }

        discovered = discover_invoice_pending_candidates(
            root=config.invoice_root,
            state=state,
            stability_wait_seconds=config.stability_wait_seconds,
            activation_document_date=activation,
            include_historical=include_historical,
        )

        eligible = [item for item in discovered if item.status == "eligible"]
        blocked = [item for item in discovered if item.status == "blocked"]
        conflicts = [item for item in discovered if item.status == "conflict"]
        already_published = [
            item for item in discovered if item.status == "already_published"
        ]
        equivalent_skipped = [
            item for item in discovered if item.status == "equivalent_skipped"
        ]
        before_watermark = [
            item for item in discovered if item.status == "before_watermark"
        ]

        to_process = eligible[: max(0, max_batches)]
        deferred = eligible[max(0, max_batches) :]
        items: list[dict[str, Any]] = []
        published = 0
        idempotent = 0
        failed = 0

        for candidate in (
            blocked
            + conflicts
            + already_published
            + equivalent_skipped
            + before_watermark
        ):
            items.append(_candidate_summary(candidate))

        http_client = client
        if (not dry_run) and to_process and http_client is None:
            http_client = MyWegInvoiceObservationsPublisherClient(
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
            status = str(detail.get("status") or "")
            if status == "published":
                published += 1
            elif status in {"idempotent", "dry_run_ok"}:
                if status == "idempotent":
                    idempotent += 1
                else:
                    published += 1
            elif status in {"failed", "conflict", "blocked"}:
                failed += 1

        for candidate in deferred:
            items.append(
                {
                    **_candidate_summary(candidate),
                    "status": "deferred_max_batches",
                    "reason": f"Limite max_batches={max_batches} nesta execução.",
                }
            )

        return {
            "ok": failed == 0,
            "mode": "dry-run-pending" if dry_run else "publish-pending",
            "status": "completed",
            "activation_watermark": activation.isoformat() if activation else None,
            "max_batches": max_batches,
            "include_historical": include_historical,
            "discovered": len(discovered),
            "eligible": len(eligible),
            "published": published,
            "idempotent": idempotent,
            "already_published": len(already_published),
            "equivalent_skipped": len(equivalent_skipped),
            "conflict": len(conflicts),
            "blocked": len(blocked),
            "failed": failed,
            "deferred": len(deferred) + len(before_watermark),
            "items": items,
        }


def _process_one(
    *,
    candidate: InvoicePendingCandidate,
    dry_run: bool,
    state: InvoicePublisherStateStore,
    client: MyWegInvoiceObservationsPublisherClient | None,
    stability_wait_seconds: float,
) -> dict[str, Any]:
    base = _candidate_summary(candidate)
    try:
        artifacts = load_invoice_collection(
            candidate.directory, stability_wait_seconds=stability_wait_seconds
        )
        built = build_ingest_payload(artifacts)
    except (InvoiceCollectionIncompleteError, InvoiceCollectionReadError, ValueError, OSError) as exc:
        state.record_attempt(
            collection_id=candidate.collection_id,
            payload_sha256=candidate.payload_sha256 or "unknown",
            status="blocked",
            document_date=candidate.document_date.isoformat(),
            semantic_sha256=candidate.semantic_sha256,
            result=str(exc),
            dry_run=dry_run,
        )
        return {**base, "status": "blocked", "reason": str(exc), "ok": False}

    payload_sha = str(built["payload_sha256"])
    semantic_sha = str(built["semantic_sha256"])
    document_date = str(built["document_date"])
    base.update(
        {
            "payload_sha256": payload_sha,
            "semantic_sha256": semantic_sha,
            "document_date": document_date,
            "observation_status": built["observation_status"],
            "record_count": built["record_count"],
            "total_quantity_un": built["total_quantity_un"],
            "idempotency_key": built["idempotency_key"],
        }
    )

    if dry_run:
        return {
            **base,
            "status": "dry_run_ok",
            "ok": True,
            "http_status": None,
            "observation_id": None,
        }

    assert client is not None
    result = client.publish(built["payload"], idempotency_key=built["idempotency_key"])
    data = (result.body or {}).get("data") or {}
    observation_id = data.get("id")

    if result.ok:
        label = "published" if result.created else "idempotent"
        state.record_attempt(
            collection_id=artifacts.collection_id,
            payload_sha256=payload_sha,
            status=label,
            document_date=document_date,
            semantic_sha256=semantic_sha,
            observation_id=str(observation_id) if observation_id else None,
            http_status=result.status_code,
            result=f"created={result.created}",
            dry_run=False,
        )
        return {
            **base,
            "status": label,
            "ok": True,
            "http_status": result.status_code,
            "observation_id": observation_id,
            "attempts": result.attempts,
        }

    status = "conflict" if result.status_code == 409 else "failed"
    state.record_attempt(
        collection_id=artifacts.collection_id,
        payload_sha256=payload_sha,
        status=status,
        document_date=document_date,
        semantic_sha256=semantic_sha,
        http_status=result.status_code,
        result=result.error,
        dry_run=False,
    )
    return {
        **base,
        "status": status,
        "ok": False,
        "reason": result.error,
        "http_status": result.status_code,
        "observation_id": observation_id,
        "attempts": result.attempts,
    }


def _candidate_summary(candidate: InvoicePendingCandidate) -> dict[str, Any]:
    return {
        "collection_id": candidate.collection_id,
        "document_date": candidate.document_date.isoformat(),
        "status": candidate.status,
        "reason": candidate.reason,
        "payload_sha256": candidate.payload_sha256,
        "semantic_sha256": candidate.semantic_sha256,
        "observation_status": candidate.observation_status,
    }


def _fallback_document_date(directory: Path) -> date:
    parent = directory.parent.name
    if parent.startswith("data-documento="):
        try:
            return date.fromisoformat(parent.split("=", 1)[1].strip()[:10])
        except ValueError:
            pass
    try:
        return datetime.fromtimestamp(directory.stat().st_mtime, tz=_SAO_PAULO).date()
    except OSError:
        return date(1970, 1, 1)
