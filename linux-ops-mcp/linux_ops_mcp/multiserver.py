"""Multiserver inventory and consolidated health orchestration (read-only)."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from .diagnosis import analyze_observation, classify_os_family
from .reader import MAX_UPSTREAM_BYTES, ItPortalReader, ReadError, Settings, require_uuid

# IT Portal counts description length in Unicode code points (max 4000), while
# MAX_UPSTREAM_BYTES counts UTF-8 bytes. Worst case: 4 bytes/code point.
_SERVER_DESCRIPTION_MAX_CHARS = 4000
_UTF8_MAX_BYTES_PER_CHAR = 4
_SERVER_ROW_OVERHEAD_BYTES = 4_096  # other ServerOut fields + JSON punctuation
_LIST_ENVELOPE_OVERHEAD_BYTES = 1_024
_SAFE_INVENTORY_UPSTREAM_PAGE_SIZE = max(
    1,
    min(
        25,
        (MAX_UPSTREAM_BYTES - _LIST_ENVELOPE_OVERHEAD_BYTES)
        // (
            _SERVER_DESCRIPTION_MAX_CHARS * _UTF8_MAX_BYTES_PER_CHAR
            + _SERVER_ROW_OVERHEAD_BYTES
        ),
    ),
)
# Backwards-compatible alias used by older tests/docs.
_FILTERED_INVENTORY_UPSTREAM_PAGE_SIZE = _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE


def _normalize_hostname(value: str) -> str:
    return value.strip().rstrip(".").lower()


def _matches_os_family(server: dict[str, Any], os_family: str | None) -> bool:
    if not os_family:
        return True
    wanted = os_family.strip().lower()
    if wanted not in {"linux", "windows"}:
        raise ReadError("invalid_os_family")
    family = classify_os_family(server.get("operating_system"))
    return family == wanted


def _matches_admin_status(server: dict[str, Any], administrative_status: str | None) -> bool:
    if not administrative_status:
        return True
    current = (server.get("administrative_status") or "").strip().lower()
    return current == administrative_status.strip().lower()


def _annotate_os_family(item: dict[str, Any]) -> dict[str, Any]:
    item["os_family"] = classify_os_family(item.get("operating_system"))
    return item


async def _fetch_upstream_inventory_page(
    reader: ItPortalReader,
    authorization: str,
    *,
    q: str | None,
    unit_code: str | None,
    environment: str | None,
    criticality: str | None,
    archived: str,
    page: int,
) -> dict[str, Any]:
    """Always request a UTF-8-safe upstream page size for /servers."""
    return await reader.list_servers_page(
        authorization,
        q=q,
        unit_code=unit_code,
        environment=environment,
        criticality=criticality,
        archived=archived,
        page=page,
        page_size=_SAFE_INVENTORY_UPSTREAM_PAGE_SIZE,
    )


async def _collect_matching_servers(
    reader: ItPortalReader,
    authorization: str,
    *,
    q: str | None = None,
    unit_code: str | None = None,
    environment: str | None = None,
    criticality: str | None = None,
    os_family: str | None = None,
    administrative_status: str | None = None,
    include_archived: bool = False,
) -> tuple[list[dict[str, Any]], int | None]:
    """Walk the full upstream inventory once with safe pages; apply client filters."""
    archived = "all" if include_archived else "active"
    collected: list[dict[str, Any]] = []
    upstream_page = 1
    upstream_total: int | None = None
    page_size = _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE
    while True:
        batch = await _fetch_upstream_inventory_page(
            reader,
            authorization,
            q=q,
            unit_code=unit_code,
            environment=environment,
            criticality=criticality,
            archived=archived,
            page=upstream_page,
        )
        upstream_total = batch["total"]
        for item in batch["items"]:
            if not _matches_os_family(item, os_family):
                continue
            if not _matches_admin_status(item, administrative_status):
                continue
            collected.append(_annotate_os_family(item))
        fetched = upstream_page * page_size
        if fetched >= (upstream_total or 0) or not batch["items"]:
            break
        upstream_page += 1
        if upstream_page > 10_000:
            break
    return collected, upstream_total


async def _assemble_unfiltered_page(
    reader: ItPortalReader,
    authorization: str,
    *,
    q: str | None,
    unit_code: str | None,
    environment: str | None,
    criticality: str | None,
    archived: str,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    """Build one client page from one or more UTF-8-safe upstream pages."""
    safe = _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE
    start = (page - 1) * page_size
    end = start + page_size
    first_upstream = start // safe + 1
    last_upstream = max(first_upstream, (end - 1) // safe + 1)
    items: list[dict[str, Any]] = []
    total: int | None = None
    for upstream_page in range(first_upstream, last_upstream + 1):
        batch = await _fetch_upstream_inventory_page(
            reader,
            authorization,
            q=q,
            unit_code=unit_code,
            environment=environment,
            criticality=criticality,
            archived=archived,
            page=upstream_page,
        )
        total = batch["total"]
        batch_start = (upstream_page - 1) * safe
        for offset, item in enumerate(batch["items"]):
            index = batch_start + offset
            if start <= index < end:
                items.append(_annotate_os_family(item))
        if not batch["items"]:
            break
        if total is not None and batch_start + len(batch["items"]) >= total:
            break
    return {
        "items": items,
        "total": total if type(total) is int and total >= 0 else len(items),
        "page": page,
        "page_size": page_size,
    }


async def list_servers(
    reader: ItPortalReader,
    authorization: str,
    *,
    q: str | None = None,
    unit_code: str | None = None,
    environment: str | None = None,
    criticality: str | None = None,
    os_family: str | None = None,
    administrative_status: str | None = None,
    include_archived: bool = False,
    page: int = 1,
    page_size: int = 25,
) -> dict[str, Any]:
    page = max(1, min(int(page), 10_000))
    page_size = max(1, min(int(page_size), 100))
    archived = "all" if include_archived else "active"
    client_filters = bool(os_family or administrative_status)

    if not client_filters:
        result = await _assemble_unfiltered_page(
            reader,
            authorization,
            q=q,
            unit_code=unit_code,
            environment=environment,
            criticality=criticality,
            archived=archived,
            page=page,
            page_size=page_size,
        )
        result["include_archived"] = include_archived
        result["source"] = "it-portal-api"
        return result

    # Client-side filters: one full walk, then local pagination.
    # Do NOT apply infra_max_servers here — that bound belongs to consolidation.
    collected, upstream_total = await _collect_matching_servers(
        reader,
        authorization,
        q=q,
        unit_code=unit_code,
        environment=environment,
        criticality=criticality,
        os_family=os_family,
        administrative_status=administrative_status,
        include_archived=include_archived,
    )
    total = len(collected)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": collected[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "include_archived": include_archived,
        "source": "it-portal-api",
        "filtered_client_side": True,
        "inventory_scanned": upstream_total,
    }


async def resolve_server(
    reader: ItPortalReader,
    authorization: str,
    *,
    server_id: str | None = None,
    hostname: str | None = None,
    include_archived: bool = False,
) -> dict[str, Any]:
    if server_id and hostname:
        raise ReadError("ambiguous_server_selector")
    if server_id:
        server = await reader.get_server(authorization, require_uuid(server_id))
        if server["archived"] and not include_archived:
            raise ReadError("server_archived")
        server["os_family"] = classify_os_family(server.get("operating_system"))
        return server
    if not hostname or not isinstance(hostname, str) or not hostname.strip():
        raise ReadError("server_selector_required")
    needle = _normalize_hostname(hostname)
    if len(needle) > 253:
        raise ReadError("invalid_hostname")
    archived = "all" if include_archived else "active"
    matches: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = await reader.list_servers_page(
            authorization,
            q=hostname.strip()[:120],
            archived=archived,
            page=page,
            page_size=100,
        )
        for item in batch["items"]:
            if _normalize_hostname(item["hostname"]) == needle:
                item["os_family"] = classify_os_family(item.get("operating_system"))
                matches.append(item)
        fetched = page * 100
        if fetched >= batch["total"] or not batch["items"]:
            break
        page += 1
        if page > 50:
            break
    if not matches:
        raise ReadError("server_not_found")
    if len(matches) > 1:
        raise ReadError("ambiguous_hostname")
    return matches[0]


def ambiguous_hostname_payload(matches: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ok": False,
        "error": "ambiguous_hostname",
        "candidates": [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "hostname": item.get("hostname"),
                "operating_system": item.get("operating_system"),
                "environment": item.get("environment"),
                "unit_code": item.get("unit_code"),
            }
            for item in matches[:20]
        ],
    }


async def resolve_server_or_candidates(
    reader: ItPortalReader,
    authorization: str,
    *,
    server_id: str | None = None,
    hostname: str | None = None,
    include_archived: bool = False,
) -> dict[str, Any]:
    """Resolve one server; on ambiguous hostname return candidates instead of raising."""
    if server_id and hostname:
        raise ReadError("ambiguous_server_selector")
    if server_id:
        return await resolve_server(
            reader, authorization, server_id=server_id, include_archived=include_archived,
        )
    if not hostname or not isinstance(hostname, str) or not hostname.strip():
        raise ReadError("server_selector_required")
    needle = _normalize_hostname(hostname)
    archived = "all" if include_archived else "active"
    matches: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = await reader.list_servers_page(
            authorization,
            q=hostname.strip()[:120],
            archived=archived,
            page=page,
            page_size=100,
        )
        for item in batch["items"]:
            if _normalize_hostname(item["hostname"]) == needle:
                item["os_family"] = classify_os_family(item.get("operating_system"))
                matches.append(item)
        fetched = page * 100
        if fetched >= batch["total"] or not batch["items"]:
            break
        page += 1
        if page > 50:
            break
    if not matches:
        raise ReadError("server_not_found")
    if len(matches) > 1:
        return {"__ambiguous__": matches}
    return matches[0]


async def get_server_health(
    reader: ItPortalReader,
    authorization: str,
    *,
    server_id: str | None = None,
    hostname: str | None = None,
    include_archived: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    resolved = await resolve_server_or_candidates(
        reader,
        authorization,
        server_id=server_id,
        hostname=hostname,
        include_archived=include_archived,
    )
    if "__ambiguous__" in resolved:
        return ambiguous_hostname_payload(resolved["__ambiguous__"])
    try:
        observation = await reader.latest_for(authorization, resolved["id"], linux_only=False)
    except ReadError as exc:
        if exc.code == "server_not_found":
            # Inventory exists but observation endpoint denied/missing: still report inventory.
            observation = None
        else:
            raise
    settings = reader.settings
    analysis = analyze_observation(
        observation,
        server=resolved,
        now=now,
        stale_after_hours=settings.stale_after_hours,
        memory_attention_pct=settings.memory_attention_pct,
        memory_critical_pct=settings.memory_critical_pct,
        disk_attention_pct=settings.disk_attention_pct,
        disk_critical_pct=settings.disk_critical_pct,
        cpu_attention_pct=settings.cpu_attention_pct,
        cpu_critical_pct=settings.cpu_critical_pct,
    )
    analysis["os_family"] = classify_os_family(
        resolved.get("operating_system"), analysis.get("observation_source"),
    )
    return analysis


async def get_infrastructure_health(
    reader: ItPortalReader,
    authorization: str,
    *,
    unit_code: str | None = None,
    environment: str | None = None,
    criticality: str | None = None,
    os_family: str | None = None,
    include_archived: bool = False,
    page: int = 1,
    page_size: int = 25,
    now: datetime | None = None,
) -> dict[str, Any]:
    clock = now or datetime.now(timezone.utc)
    max_servers = reader.settings.infra_max_servers
    # Client-side OS filter requires a full inventory walk — do it once per call.
    # Without it, walk safe upstream pages until the consolidation bound is filled.
    if os_family:
        matching, _upstream_total = await _collect_matching_servers(
            reader,
            authorization,
            unit_code=unit_code,
            environment=environment,
            criticality=criticality,
            os_family=os_family,
            include_archived=include_archived,
        )
        total = len(matching)
        servers = matching[:max_servers]
    else:
        archived = "all" if include_archived else "active"
        servers = []
        total = 0
        upstream_page = 1
        safe = _SAFE_INVENTORY_UPSTREAM_PAGE_SIZE
        while len(servers) < max_servers:
            batch = await _fetch_upstream_inventory_page(
                reader,
                authorization,
                q=None,
                unit_code=unit_code,
                environment=environment,
                criticality=criticality,
                archived=archived,
                page=upstream_page,
            )
            total = batch["total"]
            for item in batch["items"]:
                servers.append(_annotate_os_family(item))
                if len(servers) >= max_servers:
                    break
            if upstream_page * safe >= (total or 0) or not batch["items"]:
                break
            upstream_page += 1
            if upstream_page > 10_000:
                break
        servers = servers[:max_servers]

    semaphore = asyncio.Semaphore(reader.settings.infra_concurrency)
    settings = reader.settings

    async def _one(server: dict[str, Any]) -> dict[str, Any]:
        async with semaphore:
            try:
                observation = await reader.latest_for(
                    authorization, server["id"], linux_only=False,
                )
                analysis = analyze_observation(
                    observation,
                    server=server,
                    now=clock,
                    stale_after_hours=settings.stale_after_hours,
                    memory_attention_pct=settings.memory_attention_pct,
                    memory_critical_pct=settings.memory_critical_pct,
                    disk_attention_pct=settings.disk_attention_pct,
                    disk_critical_pct=settings.disk_critical_pct,
                    cpu_attention_pct=settings.cpu_attention_pct,
                    cpu_critical_pct=settings.cpu_critical_pct,
                )
                analysis["os_family"] = classify_os_family(
                    server.get("operating_system"), analysis.get("observation_source"),
                )
                analysis["read_ok"] = True
                return analysis
            except Exception:
                return {
                    "server_id": server.get("id"),
                    "name": server.get("name"),
                    "hostname": server.get("hostname"),
                    "operating_system": server.get("operating_system"),
                    "unit_code": server.get("unit_code"),
                    "environment": server.get("environment"),
                    "criticality": server.get("criticality"),
                    "collection_status": "failed_read",
                    "health_status": "unknown",
                    "overall_status": "unknown",
                    "issues": [{
                        "severity": "attention",
                        "code": "server_read_failed",
                        "message": "Falha ao obter a observacao deste servidor.",
                    }],
                    "read_ok": False,
                    "source": "it-portal-api",
                    "analyzed_at": clock.isoformat().replace("+00:00", "Z"),
                }

    analyses = await asyncio.gather(*[_one(server) for server in servers])

    with_observation = 0
    without_observation = 0
    stale = 0
    with_problems = 0
    attention_servers: list[dict[str, Any]] = []
    for row in analyses:
        collection = row.get("collection_status")
        if collection in {"available", "partial", "stale"}:
            with_observation += 1
        if collection in {"unavailable", "failed_read"}:
            without_observation += 1
        if collection == "stale":
            stale += 1
        overall = row.get("overall_status")
        if overall in {"attention", "critical", "stale", "no_data", "partial", "unknown"} and (
            row.get("health_status") in {"attention", "critical"}
            or collection in {"stale", "unavailable", "failed_read", "partial"}
        ):
            with_problems += 1
            attention_servers.append({
                "server_id": row.get("server_id"),
                "name": row.get("name"),
                "hostname": row.get("hostname"),
                "overall_status": overall,
                "health_status": row.get("health_status"),
                "collection_status": collection,
                "criticality": row.get("criticality"),
                "issue_codes": [issue.get("code") for issue in (row.get("issues") or [])][:10],
            })

    criticality_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "normal": 4}
    attention_servers.sort(
        key=lambda item: (
            0 if item.get("overall_status") == "critical" else
            1 if item.get("overall_status") == "attention" else
            2 if item.get("collection_status") == "stale" else
            3,
            criticality_rank.get((item.get("criticality") or "").lower(), 9),
            item.get("hostname") or "",
        )
    )

    page = max(1, min(int(page), 10_000))
    page_size = max(1, min(int(page_size), 100))
    start = (page - 1) * page_size
    end = start + page_size
    summaries = [
        {
            "server_id": row.get("server_id"),
            "name": row.get("name"),
            "hostname": row.get("hostname"),
            "os_family": row.get("os_family"),
            "operating_system": row.get("operating_system"),
            "unit_code": row.get("unit_code"),
            "environment": row.get("environment"),
            "criticality": row.get("criticality"),
            "collection_status": row.get("collection_status"),
            "health_status": row.get("health_status"),
            "overall_status": row.get("overall_status"),
            "observed_at": row.get("observed_at"),
            "issue_count": len(row.get("issues") or []),
            "read_ok": row.get("read_ok", True),
        }
        for row in analyses
    ]

    return {
        "analyzed_at": clock.isoformat().replace("+00:00", "Z"),
        "source": "it-portal-api",
        "scope": {
            "unit_code": unit_code,
            "environment": environment,
            "criticality": criticality,
            "os_family": os_family,
            "include_archived": include_archived,
            "servers_considered": len(servers),
            "inventory_total": total,
            "bounded_by_max_servers": len(servers) < total,
        },
        "totals": {
            "servers": len(servers),
            "with_observation": with_observation,
            "without_observation": without_observation,
            "stale_observation": stale,
            "with_possible_problems": with_problems,
        },
        "priority_attention": attention_servers[:50],
        "servers": summaries[start:end],
        "page": page,
        "page_size": page_size,
        "servers_total": len(summaries),
    }


# Bound how many Windows inventory rows we walk when client-side filters need
# the full set (e.g. critical_only). Upstream page_size max is 100.
_MAX_WINDOWS_SERVICE_SCAN = 2_000
_WINDOWS_CRITICALITY = frozenset(("high", "critical"))


def _is_windows_critical(item: dict[str, Any]) -> bool:
    return item.get("criticality") in _WINDOWS_CRITICALITY


async def _collect_windows_host_services(
    reader: ItPortalReader,
    authorization: str,
    server_id: str,
    *,
    q: str | None = None,
    state: str | None = None,
    favorites_only: bool = False,
    critical_only: bool = False,
    page: int = 1,
    page_size: int = 25,
) -> dict[str, Any]:
    """List Windows host services with correct totals for client-side filters.

    Upstream pagination is authoritative when no client-side filter is needed.
    For ``critical_only``, scan the inventory (bounded), filter, then paginate.
    """
    page = max(1, min(int(page), 10_000))
    page_size = max(1, min(int(page_size), 100))

    if not critical_only:
        listing = await reader.list_host_services(
            authorization,
            server_id,
            q=q,
            state=state,
            favorites_only=favorites_only,
            page=page,
            page_size=page_size,
        )
        items = listing["items"]
        attention = [
            item for item in items
            if item.get("state") != "running" and (
                _is_windows_critical(item) or item.get("is_favorite")
            )
        ]
        return {
            "items": items,
            "total": listing["total"],
            "page": listing["page"],
            "page_size": listing["page_size"],
            "favorites_count": listing.get("favorites_count"),
            "attention_items": attention[:50],
            "filtered_client_side": False,
            "inventory_scanned": None,
            "bounded_by_max_scan": False,
        }

    collected: list[dict[str, Any]] = []
    scanned = 0
    upstream_page = 1
    upstream_total: int | None = None
    favorites_count = None
    max_scan = min(_MAX_WINDOWS_SERVICE_SCAN, max(100, reader.settings.infra_max_servers * 4))

    while scanned < max_scan:
        batch = await reader.list_host_services(
            authorization,
            server_id,
            q=q,
            state=state,
            favorites_only=favorites_only,
            page=upstream_page,
            page_size=100,
        )
        if favorites_count is None:
            favorites_count = batch.get("favorites_count")
        upstream_total = batch["total"]
        batch_items = batch["items"]
        if not batch_items:
            break
        for item in batch_items:
            scanned += 1
            if _is_windows_critical(item):
                collected.append(item)
            if scanned >= max_scan:
                break
        fetched = upstream_page * 100
        if fetched >= (upstream_total or 0):
            break
        upstream_page += 1
        if upstream_page > 100:
            break

    total = len(collected)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = collected[start:end]
    attention = [
        item for item in collected
        if item.get("state") != "running" and (
            _is_windows_critical(item) or item.get("is_favorite")
        )
    ]
    return {
        "items": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "favorites_count": favorites_count,
        "attention_items": attention[:50],
        "filtered_client_side": True,
        "inventory_scanned": scanned if upstream_total is None else min(scanned, upstream_total),
        "bounded_by_max_scan": scanned >= max_scan and (upstream_total or 0) > scanned,
    }


async def get_server_services(
    reader: ItPortalReader,
    authorization: str,
    *,
    server_id: str | None = None,
    hostname: str | None = None,
    include_archived: bool = False,
    state: str | None = None,
    q: str | None = None,
    favorites_only: bool = False,
    critical_only: bool = False,
    page: int = 1,
    page_size: int = 25,
    include_windows_dashboard: bool = False,
) -> dict[str, Any]:
    resolved = await resolve_server_or_candidates(
        reader,
        authorization,
        server_id=server_id,
        hostname=hostname,
        include_archived=include_archived,
    )
    if "__ambiguous__" in resolved:
        return ambiguous_hostname_payload(resolved["__ambiguous__"])

    os_family = classify_os_family(resolved.get("operating_system"))
    observation: dict[str, Any] | None = None
    # Inventory OS may be absent/unrecognized; use latest observation source
    # (windows_host_collector / linux_host_collector) before choosing the
    # service backend. Never use include_windows_dashboard as OS identity.
    if os_family is None:
        observation = await reader.latest_for(
            authorization, resolved["id"], linux_only=False,
        )
        obs_source = observation.get("source") if isinstance(observation, dict) else None
        os_family = classify_os_family(resolved.get("operating_system"), obs_source)

    result: dict[str, Any] = {
        "server_id": resolved["id"],
        "name": resolved.get("name"),
        "hostname": resolved.get("hostname"),
        "os_family": os_family,
        "operating_system": resolved.get("operating_system"),
        "source": "it-portal-api",
    }

    if os_family == "windows":
        listing = await _collect_windows_host_services(
            reader,
            authorization,
            resolved["id"],
            q=q,
            state=state,
            favorites_only=favorites_only,
            critical_only=critical_only,
            page=page,
            page_size=page_size,
        )
        result.update({
            "service_source": "it-portal-host-services",
            "items": listing["items"],
            "total": listing["total"],
            "page": listing["page"],
            "page_size": listing["page_size"],
            "favorites_count": listing.get("favorites_count"),
            "attention_items": listing["attention_items"],
        })
        if listing.get("filtered_client_side"):
            result["filtered_client_side"] = True
            result["inventory_scanned"] = listing.get("inventory_scanned")
            if listing.get("bounded_by_max_scan"):
                result["bounded_by_max_scan"] = True
        if include_windows_dashboard:
            result["windows_dashboard"] = await reader.windows_services_health(authorization)
        return result

    # Linux / unknown path: observation systemd allowlist only; no host commands.
    if observation is None:
        observation = await reader.latest_for(
            authorization, resolved["id"], linux_only=False,
        )
    analysis = analyze_observation(
        observation,
        server=resolved,
        stale_after_hours=reader.settings.stale_after_hours,
    )
    services = (analysis.get("services_summary") or {}).get("items") or []
    if state:
        wanted = state.strip().lower()
        services = [item for item in services if item.get("active_state") == wanted]
    if q:
        needle = q.strip().lower()
        services = [item for item in services if needle in (item.get("name") or "").lower()]
    page = max(1, min(int(page), 10_000))
    page_size = max(1, min(int(page_size), 100))
    start = (page - 1) * page_size
    end = start + page_size
    result.update({
        "service_source": "observation_systemd_allowlist",
        "collection_status": analysis.get("collection_status"),
        "observed_at": analysis.get("observed_at"),
        "items": services[start:end],
        "total": len(services),
        "page": page,
        "page_size": page_size,
        "attention_items": (analysis.get("services_summary") or {}).get("attention_items") or [],
        "note": "linux_services_limited_to_observed_allowlist_no_host_commands",
    })
    return result


def settings_for_legacy() -> Settings:
    return Settings.from_environment(require_legacy_server_id=True)
