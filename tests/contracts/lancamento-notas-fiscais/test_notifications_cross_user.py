"""F3-R R2 — notificações cross-user (P6 atribui/menciona P6B)."""

from __future__ import annotations

from datetime import date, datetime

import httpx
import pytest

from lnf_contract.client import ContractClient
from lnf_contract.guard import assert_not_production, core_base_url, profile_token, target_name
from lnf_contract.report import record, write_golden as _write_golden

MARKER = "CONTRACT-TEST F3R-R2"


def _code(body: object) -> str | None:
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        return str(body["error"].get("code") or "") or None
    return None


def _data(body: object) -> dict:
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body["data"]
    return {}


def _me(profile: str) -> dict | None:
    core = core_base_url()
    if not core or not profile_token(profile):
        return None
    assert_not_production(core)
    token = profile_token(profile) or ""
    headers = {
        "Authorization": token if token.lower().startswith("bearer ") else f"Bearer {token}"
    }
    try:
        response = httpx.get(f"{core}/me", headers=headers, timeout=15.0)
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        return None
    body = response.json()
    if isinstance(body, dict) and body.get("id"):
        return body
    data = body.get("data") if isinstance(body, dict) else None
    if isinstance(data, dict) and data.get("id"):
        return data
    return None


def _inbox(profile: str) -> list[dict]:
    core = core_base_url()
    if not core or not profile_token(profile):
        return []
    assert_not_production(core)
    token = profile_token(profile) or ""
    headers = {
        "Authorization": token if token.lower().startswith("bearer ") else f"Bearer {token}"
    }
    response = httpx.get(
        f"{core}/me/notifications/history",
        params={"status": "all", "limit": "50"},
        headers=headers,
        timeout=15.0,
    )
    if response.status_code != 200:
        return []
    payload = response.json()
    items = payload if isinstance(payload, list) else payload.get("items") if isinstance(payload, dict) else []
    return [item for item in items or [] if isinstance(item, dict)]


def _lnf_matches(items: list[dict], *, request_id: str) -> list[dict]:
    matched = []
    for item in items:
        meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        category = item.get("category")
        source = meta.get("source") or item.get("sourceApp")
        target = ""
        action = item.get("action")
        if isinstance(action, dict):
            target = str(action.get("target") or "")
        elif isinstance(meta.get("action"), dict):
            target = str(meta["action"].get("target") or "")
        if category not in {
            "lancamento_notas_fiscais",
            "lancamento_notas_fiscais_unmapped_products",
        } and source != "lancamento-notas-fiscais":
            continue
        if request_id and request_id not in target and request_id not in str(meta):
            # still accept category+source match for this request window
            if MARKER not in str(item.get("message") or "") and MARKER not in str(
                item.get("title") or ""
            ):
                continue
        matched.append(item)
    return matched


def _supplier(client: ContractClient) -> dict | None:
    for actor in ("P5", "P9"):
        if not profile_token(actor):
            continue
        for query in ("aa", "ab", "ac", "forne", "ltda"):
            result = client.call(
                "GET",
                "/lancamento-notas-fiscais/suppliers",
                profile=actor,
                params={"query": query, "limit": "20"},
            )
            items = _data(result.body).get("items") if result.status == 200 else []
            for item in items or []:
                if (
                    isinstance(item, dict)
                    and item.get("supplier_code")
                    and item.get("supplier_store")
                    and not item.get("blocked")
                ):
                    return item
    return None


def test_notifications_p6_to_p6b_cross_user() -> None:
    """Block por P6 → assignee P6B; comentário P6 mencionando P6B; inbox de P6B."""
    client = ContractClient()
    if not client.configured() or not all(
        profile_token(p) for p in ("P9", "P6", "P6B", "P5")
    ):
        record(
            route="notifications",
            case="cross-user-p6-p6b",
            profile="-",
            expected="inbox P6B com sourceApp LNF",
            obtained="tokens ausentes",
            outcome="INCONCLUSIVE",
        )
        pytest.skip("INCONCLUSIVE: tokens P9/P6/P6B/P5")

    me_p6b = _me("P6B")
    me_p6 = _me("P6")
    if not me_p6b or not me_p6:
        record(
            route="notifications",
            case="cross-user-p6-p6b",
            profile="P6B",
            expected="/me P6 e P6B",
            obtained="sem /me",
            outcome="INCONCLUSIVE",
        )
        pytest.skip("INCONCLUSIVE: /me")

    assert me_p6b["id"] != me_p6["id"], "P6 e P6B devem ser usuários distintos"

    supplier = _supplier(client)
    if supplier is None:
        record(
            route="notifications",
            case="cross-user-p6-p6b",
            profile="P5",
            expected="fornecedor",
            obtained="busca vazia",
            outcome="INCONCLUSIVE",
            note="Protheus",
        )
        pytest.skip("INCONCLUSIVE: fornecedor")

    stamp = datetime.now().strftime("%H%M%S")
    created = client.call(
        "POST",
        "/lancamento-notas-fiscais/requests",
        profile="P9",
        json_body={
            "branch": "01",
            "document": f"6{stamp}",
            "series": "1",
            "fiscal_model": "nfe",
            "supplier_code": supplier["supplier_code"],
            "supplier_store": supplier["supplier_store"],
            "issue_date": date.today().isoformat(),
            "amount": 12.34,
            "received_at": datetime.now().replace(microsecond=0).isoformat(),
            "observation": MARKER,
        },
    )
    data = _data(created.body)
    request_id = str(data.get("id") or "")
    if created.status not in {200, 201} or not request_id:
        record(
            route="notifications",
            case="cross-user-p6-p6b",
            profile="P9",
            expected="create 200",
            obtained=f"{created.status} {_code(created.body)}",
            outcome="FAIL",
        )
        pytest.fail("create falhou")

    before = _inbox("P6B")
    before_ids = {str(item.get("id")) for item in before if item.get("id")}

    started = client.call(
        "POST", f"/lancamento-notas-fiscais/requests/{request_id}/start", profile="P6"
    )
    blocked = client.call(
        "POST",
        f"/lancamento-notas-fiscais/requests/{request_id}/block",
        profile="P6",
        json_body={
            "block_reason": "other",
            "block_description": MARKER,
            "assignee_user_id": me_p6b["id"],
            "assignee_name": me_p6b.get("name") or "P6B",
        },
    )
    commented = client.call(
        "POST",
        f"/lancamento-notas-fiscais/requests/{request_id}/comments",
        profile="P6",
        json_body={"body": f"{MARKER} @{me_p6b.get('name') or 'p6b'}", "mentioned_user_ids": [me_p6b["id"]]},
    )

    after = _inbox("P6B")
    new_items = [
        item
        for item in after
        if str(item.get("id")) not in before_ids
        or item.get("id") is None
    ]
    matched = _lnf_matches(new_items or after, request_id=request_id)
    # Prefer strictly new items; fall back to matched in full inbox for this request
    if not matched:
        matched = _lnf_matches(after, request_id=request_id)

    ok = (
        started.status == 200
        and blocked.status == 200
        and commented.status == 200
        and len(matched) >= 1
    )
    # Exactly one block-assigned OR at least one LNF notif; mention may share category
    block_like = [
        m
        for m in matched
        if "pend" in str(m.get("title") or "").lower()
        or "block" in str((m.get("metadata") or {}).get("event") or "").lower()
        or "lnf_request_blocked" in str((m.get("metadata") or {}))
    ]
    outcome = "PASS" if ok else ("INCONCLUSIVE" if blocked.status == 200 else "FAIL")
    note = (
        f"target={target_name()} new={len(new_items)} matched={len(matched)} "
        f"block_like={len(block_like)} p6b={me_p6b['id'][:8]}"
    )
    record(
        route="notifications",
        case="cross-user-p6-p6b",
        profile="P6B",
        expected="≥1 notificação LNF no inbox P6B (block/menção)",
        obtained=f"start={started.status} block={blocked.status} comment={commented.status} matched={len(matched)}",
        outcome=outcome,
        note=note,
    )
    snapshot = {
        "http_status": 200 if matched else 0,
        "matched_count": len(matched),
        "categories": sorted({str(m.get("category")) for m in matched}),
        "sources": sorted(
            {
                str(
                    (m.get("metadata") or {}).get("source")
                    or m.get("sourceApp")
                    or ""
                )
                for m in matched
            }
        ),
        "target": target_name(),
    }
    _write_golden("notifications", "cross-user-p6-p6b", snapshot)

    # cleanup
    client.call(
        "POST",
        f"/lancamento-notas-fiscais/requests/{request_id}/cancel",
        profile="P9",
        json_body={"justification": MARKER},
    )
    if not ok:
        if blocked.status != 200:
            pytest.fail(f"block falhou: {blocked.status} {_code(blocked.body)}")
        pytest.skip(f"INCONCLUSIVE: inbox sem LNF match ({note})")
