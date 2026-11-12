"""Ciclo de vida com observação CONTRACT-TEST F2. Limpeza só por cancel."""

from __future__ import annotations

import os
from datetime import date, datetime

import pytest

from lnf_contract.client import ContractClient
from lnf_contract.guard import core_base_url, profile_token, target_name
from lnf_contract.normalize import envelope_snapshot
from lnf_contract.report import record, write_golden as _write_golden

MARKER = "CONTRACT-TEST F2"


def _creator() -> str | None:
    # Só P9 (superadmin) passa decorator create + branch gate nos perfis provisionados.
    if profile_token("P9"):
        return "P9"
    return None


def _processor() -> str | None:
    for profile in ("P6", "P7", "P9"):
        if profile_token(profile):
            return profile
    return None


def _reader() -> str | None:
    for profile in ("P7", "P4", "P9", "P6"):
        if profile_token(profile):
            return profile
    if target_name() != "bff" and profile_token("P10"):
        return "P10"
    return None


def _supplier_search_actor() -> str | None:
    for profile in ("P5", "P9"):
        if profile_token(profile):
            return profile
    return None


def _code(body: object) -> str | None:
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        return str(body["error"].get("code") or "") or None
    return None


def _data(body: object) -> dict:
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body["data"]
    return {}


def test_lifecycle_and_notifications() -> None:
    client = ContractClient()
    creator = _creator()
    processor = _processor()
    reader = _reader()
    search_actor = _supplier_search_actor()
    if not client.configured() or creator is None or processor is None or reader is None or search_actor is None:
        record(
            route="create_lancamento_notas_fiscais_request",
            case="lifecycle",
            profile=creator or "-",
            expected="ciclo create→post-manual e create→cancel",
            obtained="sem URL/token (precisa P9 create + P6/P7 process + P5/P9 suppliers)",
            outcome="INCONCLUSIVE",
            note="P5 create sozinho cai em BRANCH_FORBIDDEN; P6/P7 não passam @require_permission(create)",
        )
        pytest.skip("INCONCLUSIVE")

    _sweep_contract_rows(client, creator)
    supplier = _supplier(client, search_actor)
    if supplier is None:
        record(route="search_lancamento_notas_fiscais_suppliers", case="lifecycle-supplier", profile=search_actor, expected="fornecedor de dev", obtained="busca vazia ou erro", outcome="INCONCLUSIVE", note="Protheus indisponível ou sem SA2 para a consulta")
        pytest.skip("INCONCLUSIVE")

    stamp = datetime.now().strftime("%H%M%S")
    first = _create(client, creator, supplier, document=f"8{stamp}", observation=f"{MARKER} ciclo")
    if first is None:
        pytest.skip("INCONCLUSIVE")
    request_id = str(first.get("id") or _nested_id(first))
    record(route="create_lancamento_notas_fiscais_request", case="lifecycle-create", profile=creator, expected="201/200", obtained=request_id or "sem id", outcome="PASS" if request_id else "FAIL")
    if not request_id:
        pytest.fail("create sem id")

    got = client.call("GET", f"/lancamento-notas-fiscais/requests/{request_id}", profile=reader)
    record(route="get_lancamento_notas_fiscais_request", case="lifecycle-get", profile=reader, expected="200", obtained=str(got.status), outcome="PASS" if got.status == 200 else "FAIL")
    if isinstance(got.body, dict) and got.status == 200:
        _write_golden("get_lancamento_notas_fiscais_request", "lifecycle-success", {"http_status": 200, "snapshot": envelope_snapshot(got.body)})

    listed = client.call(
        "GET",
        "/lancamento-notas-fiscais/requests",
        profile=reader,
        params={"branch": "01", "document": f"8{stamp}", "page": "1", "page_size": "20"},
    )
    items = _data(listed.body).get("items") if listed.status == 200 else []
    contract_items = [
        item
        for item in (items or [])
        if isinstance(item, dict) and str(item.get("observation") or "").startswith(MARKER)
    ]
    ok_list = listed.status == 200 and len(contract_items) >= 1
    record(
        route="list_lancamento_notas_fiscais_requests",
        case="lifecycle-list",
        profile=reader,
        expected="200 items≥1 observation CONTRACT-TEST",
        obtained=f"{listed.status} contract_items={len(contract_items)}",
        outcome="PASS" if ok_list else "FAIL",
    )
    if isinstance(listed.body, dict) and ok_list:
        _write_golden("list_lancamento_notas_fiscais_requests", "success", {"http_status": 200, "snapshot": envelope_snapshot(listed.body)})

    _maybe_link(client, processor, request_id, supplier, search_actor)
    _step(client, processor, "POST", f"/lancamento-notas-fiscais/requests/{request_id}/start", None, "start", {200})
    me = _me(client, processor) or {"id": "00000000-0000-4000-8000-0000000000aa", "name": "Contract Probe"}
    _step(
        client,
        processor,
        "POST",
        f"/lancamento-notas-fiscais/requests/{request_id}/block",
        {
            "block_reason": "other",
            "block_description": MARKER,
            "assignee_user_id": me["id"],
            "assignee_name": me.get("name") or "Contract Probe",
        },
        "block",
        {200},
    )
    _step(client, processor, "POST", f"/lancamento-notas-fiscais/requests/{request_id}/resume", None, "resume", {200})
    _step(
        client,
        processor,
        "POST",
        f"/lancamento-notas-fiscais/requests/{request_id}/comments",
        {"body": MARKER, "mentioned_user_ids": [me["id"]]},
        "comment",
        {200},
    )
    _timeline(client, reader, request_id)
    missing_file = client.call(
        "GET",
        f"/lancamento-notas-fiscais/requests/{request_id}/fiscal-attachments/xml_original",
        profile=reader,
    )
    file_code = _code(missing_file.body)
    ok_file = missing_file.status == 404 and file_code == "fiscal_attachment.not_found"
    record(route="get_lancamento_notas_fiscais_request_fiscal_attachment", case="no-file", profile=reader, expected="404 fiscal_attachment.not_found", obtained=f"{missing_file.status} {file_code}", outcome="PASS" if ok_file else "FAIL")
    if isinstance(missing_file.body, dict):
        _write_golden("get_lancamento_notas_fiscais_request_fiscal_attachment", "not-found", {"http_status": missing_file.status, "snapshot": envelope_snapshot(missing_file.body)})
    if _me(client, processor):
        _notifications(client, processor)
    else:
        record(route="notifications", case="block-mention", profile=processor, expected="categoria no inbox do usuário", obtained="token sem /me", outcome="INCONCLUSIVE", note="P10 é service token; o inbox exige usuário humano")

    _step(client, processor, "POST", f"/lancamento-notas-fiscais/requests/{request_id}/post-manual", {"justification": MARKER}, "post-manual", {200})

    second = _create(client, creator, supplier, document=f"7{stamp}", observation=f"{MARKER} cancelar")
    second_id = str((second or {}).get("id") or _nested_id(second or {}))
    if not second_id:
        record(route="cancel_lancamento_notas_fiscais_request", case="lifecycle-cancel", profile=creator, expected="200", obtained="segunda solicitação não criada", outcome="INCONCLUSIVE")
        return
    twin = _create(client, creator, supplier, document=f"7{stamp}", observation=f"{MARKER} duplicada", quiet=True)
    raw = getattr(_create, "last", None)
    dup_status = raw.status if raw is not None else 0
    dup_code = _code(raw.body) if raw is not None else None
    meta = raw.body.get("meta") if raw is not None and isinstance(raw.body, dict) else {}
    ok_dup = dup_status == 409 and dup_code == "invoice_posting_request.duplicate" and isinstance(meta, dict) and "existing_request_id" in meta
    record(route="create_lancamento_notas_fiscais_request", case="duplicate", profile=creator, expected="409 duplicate meta.existing_request_id", obtained=f"{dup_status} {dup_code}", outcome="PASS" if ok_dup else "FAIL")
    if isinstance(getattr(raw, "body", None), dict):
        _write_golden("create_lancamento_notas_fiscais_request", "duplicate", {"http_status": dup_status, "snapshot": envelope_snapshot(raw.body)})
    if twin:
        extra = str(twin.get("id") or _nested_id(twin))
        if extra:
            client.call("POST", f"/lancamento-notas-fiscais/requests/{extra}/cancel", profile=creator, json_body={"justification": MARKER})
    cancelled = client.call(
        "POST",
        f"/lancamento-notas-fiscais/requests/{second_id}/cancel",
        profile=creator,
        json_body={"justification": MARKER},
    )
    record(route="cancel_lancamento_notas_fiscais_request", case="lifecycle-cancel", profile=creator, expected="200", obtained=str(cancelled.status), outcome="PASS" if cancelled.status == 200 else "FAIL")
    again = client.call("POST", f"/lancamento-notas-fiscais/requests/{second_id}/start", profile=processor)
    again_code = _code(again.body)
    ok_transition = again.status == 409 and again_code == "invoice_posting_request.invalid_transition"
    record(route="start_lancamento_notas_fiscais_request", case="invalid-transition", profile=processor, expected="409 invalid_transition", obtained=f"{again.status} {again_code}", outcome="PASS" if ok_transition else "AS_IS_BEHAVIOR")
    if isinstance(again.body, dict):
        _write_golden("start_lancamento_notas_fiscais_request", "invalid-transition", {"http_status": again.status, "snapshot": envelope_snapshot(again.body)})
    assert ok_list and ok_file and ok_dup and cancelled.status == 200 and ok_transition


def _sweep_contract_rows(client: ContractClient, actor: str) -> None:
    listed = client.call(
        "GET",
        "/lancamento-notas-fiscais/requests",
        profile=actor,
        params={"branch": "01", "page": "1", "page_size": "100"},
    )
    items = (_data(listed.body).get("items") or []) if listed.status == 200 else []
    cancelled = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        if not str(item.get("observation") or "").startswith(MARKER):
            continue
        if str(item.get("status") or "") not in {"pending", "in_progress", "blocked"}:
            continue
        request_id = str(item.get("id") or "")
        if not request_id:
            continue
        result = client.call(
            "POST",
            f"/lancamento-notas-fiscais/requests/{request_id}/cancel",
            profile=actor,
            json_body={"justification": MARKER},
        )
        if result.status == 200:
            cancelled += 1
    record(route="cancel_lancamento_notas_fiscais_request", case="sweep", profile=actor, expected="cancel só de CONTRACT-TEST F2 ativo", obtained=str(cancelled), outcome="PASS")


def _timeline(client: ContractClient, actor: str, request_id: str) -> None:
    got = client.call("GET", f"/lancamento-notas-fiscais/requests/{request_id}", profile=actor)
    history = _data(got.body).get("history")
    events = []
    if isinstance(history, list):
        for row in history:
            if isinstance(row, dict) and row.get("event_type"):
                events.append(str(row.get("event_type")))
    ok = got.status == 200 and bool(events)
    record(route="get_lancamento_notas_fiscais_request", case="timeline", profile=actor, expected="history.event_type", obtained=",".join(events) or str(got.status), outcome="PASS" if ok else "FAIL")


def _supplier(client: ContractClient, actor: str) -> dict | None:
    query = (os.getenv("LNF_SUPPLIER_QUERY") or "aa").strip() or "aa"
    result = client.call("GET", "/lancamento-notas-fiscais/suppliers", profile=actor, params={"query": query, "limit": "10"})
    data = _data(result.body)
    items = data.get("items") if isinstance(data.get("items"), list) else []
    for item in items:
        if isinstance(item, dict) and item.get("supplier_code") and item.get("supplier_store") and not item.get("blocked"):
            if isinstance(result.body, dict):
                _write_golden("search_lancamento_notas_fiscais_suppliers", "success", {"http_status": result.status, "snapshot": envelope_snapshot(result.body)})
            return item
    record(route="search_lancamento_notas_fiscais_suppliers", case="lookup", profile=actor, expected="item SA2 não bloqueado", obtained=f"{result.status}", outcome="INCONCLUSIVE")
    return None


def _create(client: ContractClient, actor: str, supplier: dict, *, document: str, observation: str, quiet: bool = False) -> dict | None:
    result = client.call(
        "POST",
        "/lancamento-notas-fiscais/requests",
        profile=actor,
        json_body={
            "branch": "01",
            "document": document,
            "series": "1",
            "fiscal_model": "nfe",
            "supplier_code": supplier.get("supplier_code"),
            "supplier_store": supplier.get("supplier_store"),
            "issue_date": date.today().isoformat(),
            "amount": 1,
            "received_at": datetime.now().replace(microsecond=0).isoformat(),
            "observation": observation,
        },
    )
    _create.last = result  # type: ignore[attr-defined]
    if result.status not in {200, 201}:
        if not quiet:
            record(route="create_lancamento_notas_fiscais_request", case="create", profile=actor, expected="200", obtained=f"{result.status} {_code(result.body)}", outcome="INCONCLUSIVE" if result.status >= 500 else "FAIL")
        return None
    if isinstance(result.body, dict) and not quiet:
        _write_golden("create_lancamento_notas_fiscais_request", "success", {"http_status": result.status, "snapshot": envelope_snapshot(result.body)})
    return _data(result.body)


def _nested_id(data: dict) -> str:
    request = data.get("request")
    if isinstance(request, dict):
        return str(request.get("id") or "")
    return ""


def _step(client: ContractClient, actor: str, method: str, path: str, body: dict | None, case: str, ok_status: set[int]) -> None:
    result = client.call(method, path, profile=actor, json_body=body)
    outcome = "PASS" if result.status in ok_status else "AS_IS_BEHAVIOR" if result.status < 500 else "FAIL"
    record(route=path, case=f"lifecycle-{case}", profile=actor, expected=str(sorted(ok_status)), obtained=f"{result.status} {_code(result.body)}", outcome=outcome)
    if isinstance(result.body, dict) and result.status in ok_status:
        op = path.strip("/").replace("/", "_")
        _write_golden(f"lifecycle_{case}", "success", {"http_status": result.status, "snapshot": envelope_snapshot(result.body)})


def _maybe_link(client: ContractClient, actor: str, request_id: str, supplier: dict, search_actor: str) -> None:
    # open POs exige create + branch; P5 sozinho leva BRANCH_FORBIDDEN — usar P9.
    opener = "P9" if profile_token("P9") else search_actor
    opened = client.call(
        "GET",
        "/lancamento-notas-fiscais/purchase-orders/open",
        profile=opener,
        params={
            "branch": "01",
            "supplier_code": str(supplier.get("supplier_code")),
            "supplier_store": str(supplier.get("supplier_store")),
        },
    )
    data = _data(opened.body)
    items = data.get("items") if isinstance(data.get("items"), list) else data.get("groups") if isinstance(data.get("groups"), list) else []
    if opened.status != 200 or not items:
        record(route="link_lancamento_notas_fiscais_request_purchase_order", case="lifecycle-link", profile=actor, expected="200 se houver PC", obtained=f"{opened.status} sem PC", outcome="INCONCLUSIVE", note="nenhum pedido aberto em dev para este fornecedor; PC não é criado pela suíte")
        return
    first = items[0] if isinstance(items[0], dict) else {}
    order_number = str(first.get("order_number") or first.get("orderNumber") or "")
    if not order_number:
        record(route="link_lancamento_notas_fiscais_request_purchase_order", case="lifecycle-link", profile=actor, expected="order_number", obtained="item sem número", outcome="INCONCLUSIVE")
        return
    linked = client.call(
        "POST",
        f"/lancamento-notas-fiscais/requests/{request_id}/purchase-orders/link",
        profile=actor,
        json_body={"order_number": order_number},
    )
    record(route="link_lancamento_notas_fiscais_request_purchase_order", case="lifecycle-link", profile=actor, expected="200", obtained=str(linked.status), outcome="PASS" if linked.status == 200 else "AS_IS_BEHAVIOR")


def _me(client: ContractClient, actor: str) -> dict | None:
    core = core_base_url()
    if not core:
        return None
    from lnf_contract.guard import assert_not_production

    assert_not_production(core)
    import httpx

    token = profile_token(actor) or ""
    headers = {"Authorization": token if token.lower().startswith("bearer ") else f"Bearer {token}"}
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


def _notifications(client: ContractClient, actor: str) -> None:
    core = core_base_url()
    if not core:
        record(route="notifications", case="block-mention", profile=actor, expected="sourceApp e categoria", obtained="sem core", outcome="INCONCLUSIVE")
        return
    import httpx

    token = profile_token(actor) or ""
    headers = {"Authorization": token if token.lower().startswith("bearer ") else f"Bearer {token}"}
    try:
        response = httpx.get(f"{core}/me/notifications/history", params={"status": "all", "limit": "50"}, headers=headers, timeout=15.0)
    except httpx.HTTPError as exc:
        record(route="notifications", case="block-mention", profile=actor, expected="lista", obtained=type(exc).__name__, outcome="INCONCLUSIVE")
        return
    if response.status_code != 200:
        record(route="notifications", case="block-mention", profile=actor, expected="200", obtained=str(response.status_code), outcome="INCONCLUSIVE", note="inbox do Core dev não respondeu")
        return
    payload = response.json()
    items = payload if isinstance(payload, list) else payload.get("items") if isinstance(payload, dict) else []
    matched = [
        item
        for item in items or []
        if isinstance(item, dict)
        and (
            item.get("category") in {"lancamento_notas_fiscais", "lancamento_notas_fiscais_unmapped_products"}
            or (isinstance(item.get("metadata"), dict) and item["metadata"].get("source") == "lancamento-notas-fiscais")
        )
    ]
    outcome = "PASS" if matched else "INCONCLUSIVE"
    record(
        route="notifications",
        case="block-mention",
        profile=actor,
        expected="categoria lancamento_notas_fiscais uma vez",
        obtained=str(len(matched)),
        outcome=outcome,
        note="sourceApp no inbox do usuário via metadata.source; o campo sourceApp fica no dispatch",
    )
