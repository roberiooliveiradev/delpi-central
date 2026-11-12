"""Perfis combinados P11/P12 e ciclo realista create→process sem superadmin."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from lnf_contract.client import ContractClient
from lnf_contract.guard import profile_token
from lnf_contract.normalize import envelope_snapshot
from lnf_contract.report import record, write_golden

MARKER = "CONTRACT-TEST F2"


def _code(body: object) -> str | None:
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        return str(body["error"].get("code") or "") or None
    return None


def _data(body: object) -> dict:
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body["data"]
    return {}


def _supplier(client: ContractClient, actor: str) -> dict | None:
    result = client.call(
        "GET",
        "/lancamento-notas-fiscais/suppliers",
        profile=actor,
        params={"query": "aa", "limit": "10"},
    )
    items = _data(result.body).get("items") if result.status == 200 else []
    for item in items or []:
        if isinstance(item, dict) and item.get("supplier_code") and not item.get("blocked"):
            return item
    return None


def _create(client: ContractClient, actor: str, *, branch: str, supplier: dict, document: str) -> tuple[str | None, object]:
    result = client.call(
        "POST",
        "/lancamento-notas-fiscais/requests",
        profile=actor,
        json_body={
            "branch": branch,
            "document": document,
            "series": "1",
            "fiscal_model": "nfe",
            "supplier_code": supplier.get("supplier_code"),
            "supplier_store": supplier.get("supplier_store"),
            "issue_date": date.today().isoformat(),
            "amount": 1,
            "received_at": datetime.now().replace(microsecond=0).isoformat(),
            "observation": f"{MARKER} combined {actor}",
        },
    )
    if result.status not in {200, 201}:
        return None, result
    data = _data(result.body)
    return str(data.get("id") or "") or None, result


def test_p11_p12_branch_gates() -> None:
    client = ContractClient()
    if not client.configured() or not profile_token("P11") or not profile_token("P12"):
        record(route="create_lancamento_notas_fiscais_request", case="p11-p12-branch", profile="-", expected="P11/P12", obtained="sem tokens", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    supplier = _supplier(client, "P11")
    if supplier is None:
        record(route="create_lancamento_notas_fiscais_request", case="p11-p12-branch", profile="P11", expected="fornecedor", obtained="vazio", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    stamp = datetime.now().strftime("%H%M%S")

    ok_id, ok_res = _create(client, "P11", branch="01", supplier=supplier, document=f"4{stamp}")
    ok = bool(ok_id) and ok_res.status in {200, 201}
    record(route="create_lancamento_notas_fiscais_request", case="p11-filial-01", profile="P11", expected="200", obtained=f"{ok_res.status} {_code(ok_res.body)}", outcome="PASS" if ok else "FAIL")
    if ok_id:
        client.call("POST", f"/lancamento-notas-fiscais/requests/{ok_id}/cancel", profile="P11", json_body={"justification": MARKER})

    denied = client.call(
        "POST",
        "/lancamento-notas-fiscais/requests",
        profile="P11",
        json_body={
            "branch": "02",
            "document": f"3{stamp}",
            "series": "1",
            "fiscal_model": "nfe",
            "supplier_code": supplier.get("supplier_code"),
            "supplier_store": supplier.get("supplier_store"),
            "issue_date": date.today().isoformat(),
            "amount": 1,
            "received_at": datetime.now().replace(microsecond=0).isoformat(),
            "observation": f"{MARKER} p11-forbidden",
        },
    )
    ok_deny = denied.status == 403 and _code(denied.body) == "BRANCH_FORBIDDEN"
    record(route="create_lancamento_notas_fiscais_request", case="p11-filial-02", profile="P11", expected="403 BRANCH_FORBIDDEN", obtained=f"{denied.status} {_code(denied.body)}", outcome="PASS" if ok_deny else "FAIL")

    ok12_id, ok12 = _create(client, "P12", branch="02", supplier=supplier, document=f"2{stamp}")
    ok_p12 = bool(ok12_id) and ok12.status in {200, 201}
    record(route="create_lancamento_notas_fiscais_request", case="p12-filial-02", profile="P12", expected="200", obtained=f"{ok12.status} {_code(ok12.body)}", outcome="PASS" if ok_p12 else "FAIL")
    if ok12_id:
        # P12 create-only can cancel own pending
        client.call("POST", f"/lancamento-notas-fiscais/requests/{ok12_id}/cancel", profile="P12", json_body={"justification": MARKER})

    denied12 = client.call(
        "POST",
        "/lancamento-notas-fiscais/requests",
        profile="P12",
        json_body={
            "branch": "01",
            "document": f"1{stamp}",
            "series": "1",
            "fiscal_model": "nfe",
            "supplier_code": supplier.get("supplier_code"),
            "supplier_store": supplier.get("supplier_store"),
            "issue_date": date.today().isoformat(),
            "amount": 1,
            "received_at": datetime.now().replace(microsecond=0).isoformat(),
            "observation": f"{MARKER} p12-forbidden",
        },
    )
    ok_deny12 = denied12.status == 403 and _code(denied12.body) == "BRANCH_FORBIDDEN"
    record(route="create_lancamento_notas_fiscais_request", case="p12-filial-01", profile="P12", expected="403 BRANCH_FORBIDDEN", obtained=f"{denied12.status} {_code(denied12.body)}", outcome="PASS" if ok_deny12 else "FAIL")
    assert ok and ok_deny and ok_p12 and ok_deny12


def test_realistic_cycle_p11_create_p6_process() -> None:
    client = ContractClient()
    if not client.configured() or not profile_token("P11") or not profile_token("P6"):
        record(route="create_lancamento_notas_fiscais_request", case="realistic-cycle", profile="-", expected="P11 create + P6 process", obtained="sem tokens", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    supplier = _supplier(client, "P11")
    if supplier is None:
        record(route="create_lancamento_notas_fiscais_request", case="realistic-cycle", profile="P11", expected="fornecedor", obtained="vazio", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    stamp = datetime.now().strftime("%H%M%S")
    request_id, created = _create(client, "P11", branch="01", supplier=supplier, document=f"0{stamp}")
    if not request_id:
        record(route="create_lancamento_notas_fiscais_request", case="realistic-create", profile="P11", expected="200", obtained=f"{created.status} {_code(created.body)}", outcome="FAIL")
        pytest.fail("create P11 falhou")
    record(route="create_lancamento_notas_fiscais_request", case="realistic-create", profile="P11", expected="200", obtained=request_id, outcome="PASS")
    if isinstance(created.body, dict):
        write_golden("create_lancamento_notas_fiscais_request", "realistic-p11", {"http_status": created.status, "snapshot": envelope_snapshot(created.body)})

    started = client.call("POST", f"/lancamento-notas-fiscais/requests/{request_id}/start", profile="P6")
    record(route="start_lancamento_notas_fiscais_request", case="realistic-start", profile="P6", expected="200", obtained=str(started.status), outcome="PASS" if started.status == 200 else "FAIL")
    me = _me(client, "P6") or {"id": "00000000-0000-4000-8000-0000000000aa", "name": "Contract Probe"}
    blocked = client.call(
        "POST",
        f"/lancamento-notas-fiscais/requests/{request_id}/block",
        profile="P6",
        json_body={
            "block_reason": "other",
            "block_description": MARKER,
            "assignee_user_id": me["id"],
            "assignee_name": me.get("name") or "Contract Probe",
        },
    )
    record(route="block_lancamento_notas_fiscais_request", case="realistic-block", profile="P6", expected="200", obtained=str(blocked.status), outcome="PASS" if blocked.status == 200 else "FAIL")
    resumed = client.call("POST", f"/lancamento-notas-fiscais/requests/{request_id}/resume", profile="P6")
    record(route="resume_lancamento_notas_fiscais_request", case="realistic-resume", profile="P6", expected="200", obtained=str(resumed.status), outcome="PASS" if resumed.status == 200 else "FAIL")
    posted = client.call(
        "POST",
        f"/lancamento-notas-fiscais/requests/{request_id}/post-manual",
        profile="P6",
        json_body={"justification": MARKER},
    )
    record(route="post_manual_lancamento_notas_fiscais_request", case="realistic-post-manual", profile="P6", expected="200", obtained=str(posted.status), outcome="PASS" if posted.status == 200 else "FAIL")
    if isinstance(posted.body, dict) and posted.status == 200:
        write_golden("post_manual_lancamento_notas_fiscais_request", "realistic-p6", {"http_status": posted.status, "snapshot": envelope_snapshot(posted.body)})
    assert started.status == 200 and blocked.status == 200 and resumed.status == 200 and posted.status == 200


def _me(client: ContractClient, actor: str) -> dict | None:
    from lnf_contract.guard import assert_not_production, core_base_url
    import httpx

    core = core_base_url()
    if not core:
        return None
    assert_not_production(core)
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
    return data if isinstance(data, dict) else None
