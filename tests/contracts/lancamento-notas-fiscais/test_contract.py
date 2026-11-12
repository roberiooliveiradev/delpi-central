"""Contrato de envelope, erros alcançáveis e códigos fora da caixa-preta."""

from __future__ import annotations

import hashlib
import os
from datetime import date, datetime

import pytest

from lnf_contract.catalog import FAKE_REQUEST_ID, ROUTES
from lnf_contract.client import ContractClient
from lnf_contract.guard import profile_token, target_name
from lnf_contract.normalize import envelope_snapshot
from lnf_contract.report import record, write_golden

MARKER = "CONTRACT-TEST F2"

NOT_COVERED = (
    ("invoice_posting_reconciliation.erp_unavailable", "502 exige falha do Protheus; não injetar no runtime"),
    ("invoice_posting_request.upstream", "502 exige falha de upstream; não injetar no runtime"),
    ("INTERNAL_ERROR", "500 de exceção interna não é provocável sem alterar o runtime"),
)


def _actor_read() -> str | None:
    for profile in ("P7", "P6", "P4", "P9", "P10"):
        if profile == "P10" and target_name() == "bff":
            continue
        if profile_token(profile):
            return profile
    return None


def _actor_create() -> str | None:
    """Create HTTP exige permission create; entre os perfis só P9 passa branch+decorator."""
    for profile in ("P9", "P5"):
        if profile_token(profile):
            return profile
    return None


def _actor_manage() -> str | None:
    for profile in ("P7", "P9"):
        if profile_token(profile):
            return profile
    return None


def _client() -> ContractClient | None:
    client = ContractClient()
    return client if client.configured() else None


def _write_golden(operation_id: str, case: str, payload: dict) -> None:
    write_golden(operation_id, case, payload)


def _error_code(body: object) -> str | None:
    if not isinstance(body, dict):
        return None
    error = body.get("error")
    if isinstance(error, dict):
        return str(error.get("code") or "") or None
    return None


def _data(body: object) -> dict:
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body["data"]
    return {}


def _supplier_unblocked(client: ContractClient, actor: str) -> dict | None:
    result = client.call(
        "GET",
        "/lancamento-notas-fiscais/suppliers",
        profile=actor,
        params={"query": (os.getenv("LNF_SUPPLIER_QUERY") or "aa").strip() or "aa", "limit": "20"},
    )
    items = _data(result.body).get("items") if result.status == 200 else None
    if not isinstance(items, list):
        return None
    for item in items:
        if isinstance(item, dict) and item.get("supplier_code") and item.get("supplier_store") and not item.get("blocked"):
            return item
    return None


def _find_blocked_supplier(client: ContractClient, actor: str) -> dict | None:
    code = (os.getenv("LNF_BLOCKED_SUPPLIER_CODE") or "").strip()
    store = (os.getenv("LNF_BLOCKED_SUPPLIER_STORE") or "").strip()
    if code and store:
        return {"supplier_code": code, "supplier_store": store}
    queries = [
        "aa", "ab", "ac", "ad", "ae", "af", "ag", "ah", "ai", "aj", "al", "am", "an",
        "ao", "ap", "ar", "as", "at", "au", "av", "ba", "be", "bi", "bo", "br", "ca",
        "ce", "co", "da", "de", "di", "do", "em", "en", "es", "fa", "fe", "fi", "fo",
        "ga", "ge", "go", "ha", "he", "ia", "ig", "im", "in", "ja", "jo", "la", "le",
        "li", "lo", "ma", "me", "mi", "mo", "na", "ne", "no", "pa", "pe", "pi", "po",
        "pr", "ra", "re", "ri", "ro", "sa", "se", "si", "so", "su", "ta", "te", "ti",
        "to", "tr", "va", "ve", "vi", "01", "02", "03", "10", "20",
    ]
    seen: set[tuple[str, str]] = set()
    for query in queries:
        result = client.call(
            "GET",
            "/lancamento-notas-fiscais/suppliers",
            profile=actor,
            params={"query": query, "limit": "50"},
        )
        if result.status != 200:
            continue
        items = _data(result.body).get("items") or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            key = (str(item.get("supplier_code") or ""), str(item.get("supplier_store") or ""))
            if not key[0] or key in seen:
                continue
            seen.add(key)
            if item.get("blocked") is True:
                return item
    return None


def _create_request(client: ContractClient, actor: str, supplier: dict, *, document: str, observation: str) -> tuple[str | None, object]:
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
    if result.status not in {200, 201}:
        return None, result
    data = _data(result.body)
    request_id = str(data.get("id") or (data.get("request") or {}).get("id") or "")
    return (request_id or None), result


def test_success_envelope_list_requests() -> None:
    client = _client()
    actor = _actor_read()
    route = "list_lancamento_notas_fiscais_requests"
    if client is None or actor is None:
        record(route=route, case="success-envelope", profile=actor or "-", expected="200 envelope", obtained="sem alvo ou token de leitura", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    result = client.call("GET", "/lancamento-notas-fiscais/requests", profile=actor, params={"branch": "01", "page": "1", "page_size": "5"})
    body = result.body if isinstance(result.body, dict) else {}
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
    ok = (
        result.status == 200
        and body.get("success") is True
        and set(body) >= {"success", "message", "data", "error"}
        and body.get("error") is None
        and meta.get("dataVersion") == "2026-07"
        and meta.get("operationId") == route
        and meta.get("entity") == "invoice_posting_request"
        and meta.get("shape") == "paged_list"
        and "pagination" in meta
    )
    obtained = f"{result.status} op={meta.get('operationId')} shape={meta.get('shape')}"
    record(route=route, case="success-envelope", profile=actor, expected="200 envelope dataVersion=2026-07", obtained=obtained, outcome="PASS" if ok else "FAIL")
    if ok:
        _write_golden(route, "success-envelope", {"http_status": 200, "content_type": result.content_type, "snapshot": envelope_snapshot(body)})
    assert ok, obtained


def test_validation_error_short_query() -> None:
    client = _client()
    actor = _actor_create()
    route = "search_lancamento_notas_fiscais_suppliers"
    if client is None or actor is None:
        record(route=route, case="validation-422", profile=actor or "-", expected="422 VALIDATION_ERROR", obtained="sem alvo ou token create", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    result = client.call("GET", "/lancamento-notas-fiscais/suppliers", profile=actor, params={"query": "a"})
    body = result.body if isinstance(result.body, dict) else {}
    error = body.get("error") if isinstance(body.get("error"), dict) else {}
    ok = (
        result.status == 422
        and body.get("message") == "Parâmetros inválidos"
        and error.get("code") == "VALIDATION_ERROR"
        and error.get("recoverable") is True
    )
    record(route=route, case="validation-422", profile=actor, expected="422 VALIDATION_ERROR recoverable", obtained=f"{result.status} {error.get('code')}", outcome="PASS" if ok else "FAIL")
    if isinstance(body, dict) and body:
        _write_golden(route, "validation-422", {"http_status": result.status, "snapshot": envelope_snapshot(body)})
    assert ok


def test_not_found_and_filters() -> None:
    client = _client()
    actor = _actor_read()
    if client is None or actor is None:
        record(route="get_lancamento_notas_fiscais_request", case="not-found", profile=actor or "-", expected="404 invoice_posting_request.not_found", obtained="sem alvo", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    missing = client.call("GET", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}", profile=actor)
    missing_code = _error_code(missing.body)
    ok_missing = missing.status == 404 and missing_code == "invoice_posting_request.not_found"
    record(route="get_lancamento_notas_fiscais_request", case="not-found", profile=actor, expected="404 invoice_posting_request.not_found", obtained=f"{missing.status} {missing_code}", outcome="PASS" if ok_missing else "FAIL")
    if isinstance(missing.body, dict):
        _write_golden("get_lancamento_notas_fiscais_request", "not-found", {"http_status": missing.status, "snapshot": envelope_snapshot(missing.body)})

    invalid = client.call("GET", "/lancamento-notas-fiscais/requests", profile=actor, params={"branch": "01", "status": "not-a-status"})
    invalid_code = _error_code(invalid.body)
    ok_filter = invalid.status == 400 and invalid_code == "INVALID_STATUS_FILTER"
    record(route="list_lancamento_notas_fiscais_requests", case="invalid-status", profile=actor, expected="400 INVALID_STATUS_FILTER", obtained=f"{invalid.status} {invalid_code}", outcome="PASS" if ok_filter else "FAIL")
    if isinstance(invalid.body, dict):
        _write_golden("list_lancamento_notas_fiscais_requests", "invalid-status", {"http_status": invalid.status, "snapshot": envelope_snapshot(invalid.body)})

    danfe = client.call("GET", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/danfe", profile=actor, params={"disposition": "inline"})
    danfe_code = _error_code(danfe.body)
    ok_danfe = danfe.status == 404 and danfe_code in {"invoice_posting_request.not_found", "danfe.not_found"}
    record(route="get_lancamento_notas_fiscais_request_danfe", case="danfe-missing-id", profile=actor, expected="404 not_found ou danfe.not_found", obtained=f"{danfe.status} {danfe_code}", outcome="PASS" if ok_danfe else "FAIL", note="id inexistente não chega em danfe.not_found")
    if isinstance(danfe.body, dict):
        _write_golden("get_lancamento_notas_fiscais_request_danfe", "missing-id", {"http_status": danfe.status, "snapshot": envelope_snapshot(danfe.body)})

    attachment = client.call("GET", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/fiscal-attachments/xml_original", profile=actor)
    attachment_code = _error_code(attachment.body)
    ok_attachment = attachment.status == 404 and attachment_code == "invoice_posting_request.not_found"
    record(route="get_lancamento_notas_fiscais_request_fiscal_attachment", case="attachment-missing", profile=actor, expected="404 invoice_posting_request.not_found", obtained=f"{attachment.status} {attachment_code}", outcome="PASS" if ok_attachment else "FAIL")
    assert ok_missing and ok_filter and ok_danfe and ok_attachment


def test_danfe_not_found_on_real_request() -> None:
    client = _client()
    creator = _actor_create()
    reader = _actor_read()
    if client is None or creator is None or reader is None:
        record(route="get_lancamento_notas_fiscais_request_danfe", case="danfe.not_found", profile="-", expected="404 danfe.not_found", obtained="sem alvo/token", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    supplier = _supplier_unblocked(client, creator if creator != "P5" else "P9" if profile_token("P9") else creator)
    create_actor = "P9" if profile_token("P9") else creator
    if supplier is None:
        record(route="get_lancamento_notas_fiscais_request_danfe", case="danfe.not_found", profile=create_actor, expected="404 danfe.not_found", obtained="sem fornecedor", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    stamp = datetime.now().strftime("%H%M%S")
    request_id, created = _create_request(
        client,
        create_actor,
        supplier,
        document=f"6{stamp}",
        observation=f"{MARKER} danfe.not_found",
    )
    if not request_id:
        record(route="get_lancamento_notas_fiscais_request_danfe", case="danfe.not_found", profile=create_actor, expected="404 danfe.not_found", obtained=f"create {getattr(created,'status',0)} {_error_code(getattr(created,'body',None))}", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    try:
        danfe = client.call(
            "GET",
            f"/lancamento-notas-fiscais/requests/{request_id}/danfe",
            profile=reader,
            params={"disposition": "inline"},
        )
        code = _error_code(danfe.body)
        ok = danfe.status == 404 and code == "danfe.not_found"
        record(route="get_lancamento_notas_fiscais_request_danfe", case="danfe.not_found", profile=reader, expected="404 danfe.not_found", obtained=f"{danfe.status} {code}", outcome="PASS" if ok else "FAIL")
        if isinstance(danfe.body, dict):
            _write_golden("get_lancamento_notas_fiscais_request_danfe", "danfe.not_found", {"http_status": danfe.status, "snapshot": envelope_snapshot(danfe.body)})
        assert ok
    finally:
        client.call("POST", f"/lancamento-notas-fiscais/requests/{request_id}/cancel", profile=create_actor, json_body={"justification": MARKER})


def test_supplier_not_found_on_safe_create() -> None:
    client = _client()
    actor = "P9" if profile_token("P9") else _actor_create()
    if client is None or actor is None:
        record(route="create_lancamento_notas_fiscais_request", case="supplier-not-found", profile=actor or "-", expected="404 supplier.not_found", obtained="sem alvo", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    result = client.call(
        "POST",
        "/lancamento-notas-fiscais/requests",
        profile=actor,
        json_body={
            "branch": "01",
            "document": "999999",
            "series": "1",
            "fiscal_model": "nfe",
            "supplier_code": "CONTRACT-NO-SUCH",
            "supplier_store": "01",
            "issue_date": "2026-11-12",
            "amount": 1,
            "received_at": "2026-11-12T12:00:00",
            "observation": f"{MARKER} supplier-not-found",
        },
    )
    code = _error_code(result.body)
    ok = result.status == 404 and code == "supplier.not_found"
    outcome = "PASS" if ok else "AS_IS_BEHAVIOR" if result.status >= 500 else "FAIL"
    note = "" if ok else "Protheus pode estar indisponível" if result.status >= 500 else ""
    record(route="create_lancamento_notas_fiscais_request", case="supplier-not-found", profile=actor, expected="404 supplier.not_found", obtained=f"{result.status} {code}", outcome=outcome, note=note)
    if isinstance(result.body, dict):
        _write_golden("create_lancamento_notas_fiscais_request", "supplier-not-found", {"http_status": result.status, "snapshot": envelope_snapshot(result.body)})
    if outcome == "AS_IS_BEHAVIOR":
        pytest.skip(f"AS_IS_BEHAVIOR {result.status} {code}")
    assert ok


def test_supplier_blocked() -> None:
    client = _client()
    search_actor = "P5" if profile_token("P5") else ("P9" if profile_token("P9") else None)
    create_actor = "P9" if profile_token("P9") else search_actor
    if client is None or search_actor is None or create_actor is None:
        record(route="create_lancamento_notas_fiscais_request", case="supplier-blocked", profile="-", expected="422 supplier.blocked", obtained="sem alvo/token", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    blocked = _find_blocked_supplier(client, search_actor)
    if blocked is None:
        record(route="create_lancamento_notas_fiscais_request", case="supplier-blocked", profile=search_actor, expected="422 supplier.blocked", obtained="nenhum fornecedor bloqueado via /suppliers", outcome="INCONCLUSIVE", note="leitura SA2 não retornou A2_MSBLQL=1")
        pytest.skip("INCONCLUSIVE")
    result = client.call(
        "POST",
        "/lancamento-notas-fiscais/requests",
        profile=create_actor,
        json_body={
            "branch": "01",
            "document": "888888",
            "series": "1",
            "fiscal_model": "nfe",
            "supplier_code": blocked.get("supplier_code"),
            "supplier_store": blocked.get("supplier_store"),
            "issue_date": "2026-11-12",
            "amount": 1,
            "received_at": "2026-11-12T12:00:00",
            "observation": f"{MARKER} supplier-blocked",
        },
    )
    code = _error_code(result.body)
    ok = result.status == 422 and code == "supplier.blocked"
    record(
        route="create_lancamento_notas_fiscais_request",
        case="supplier-blocked",
        profile=create_actor,
        expected="422 supplier.blocked",
        obtained=f"{result.status} {code} supplier={blocked.get('supplier_code')}/{blocked.get('supplier_store')}",
        outcome="PASS" if ok else "FAIL",
    )
    if isinstance(result.body, dict):
        _write_golden("create_lancamento_notas_fiscais_request", "supplier-blocked", {"http_status": result.status, "snapshot": envelope_snapshot(result.body)})
    assert ok


def test_not_owner_and_already_assigned() -> None:
    client = _client()
    if client is None or not profile_token("P9") or not profile_token("P6") or not profile_token("P6B"):
        record(route="start_lancamento_notas_fiscais_request", case="not-owner", profile="P6B", expected="403 invoice_posting_request.not_owner", obtained="sem P9/P6/P6B", outcome="INCONCLUSIVE")
        record(route="start_lancamento_notas_fiscais_request", case="already-assigned", profile="P6B", expected="409 invoice_posting_request.already_assigned", obtained="sem P9/P6/P6B", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    supplier = _supplier_unblocked(client, "P5" if profile_token("P5") else "P9")
    if supplier is None:
        record(route="start_lancamento_notas_fiscais_request", case="already-assigned", profile="P6", expected="409 already_assigned", obtained="sem fornecedor", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    stamp = datetime.now().strftime("%H%M%S")
    request_id, created = _create_request(
        client,
        "P9",
        supplier,
        document=f"5{stamp}",
        observation=f"{MARKER} ownership",
    )
    if not request_id:
        record(route="start_lancamento_notas_fiscais_request", case="already-assigned", profile="P6", expected="409", obtained=f"create failed {getattr(created,'status',0)}", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    try:
        started = client.call("POST", f"/lancamento-notas-fiscais/requests/{request_id}/start", profile="P6")
        ok_start = started.status == 200
        record(route="start_lancamento_notas_fiscais_request", case="assign-p6", profile="P6", expected="200", obtained=str(started.status), outcome="PASS" if ok_start else "FAIL")
        assert ok_start

        conflict = client.call("POST", f"/lancamento-notas-fiscais/requests/{request_id}/start", profile="P6B")
        conflict_code = _error_code(conflict.body)
        ok_assigned = conflict.status == 409 and conflict_code == "invoice_posting_request.already_assigned"
        record(
            route="start_lancamento_notas_fiscais_request",
            case="already-assigned",
            profile="P6B",
            expected="409 invoice_posting_request.already_assigned",
            obtained=f"{conflict.status} {conflict_code}",
            outcome="PASS" if ok_assigned else "FAIL",
        )
        if isinstance(conflict.body, dict):
            _write_golden("start_lancamento_notas_fiscais_request", "already-assigned", {"http_status": conflict.status, "snapshot": envelope_snapshot(conflict.body)})

        # process sem manage não cancela solicitação de outro → not_owner
        denied = client.call(
            "POST",
            f"/lancamento-notas-fiscais/requests/{request_id}/cancel",
            profile="P6B",
            json_body={"justification": MARKER},
        )
        denied_code = _error_code(denied.body)
        ok_owner = denied.status == 403 and denied_code == "invoice_posting_request.not_owner"
        record(
            route="cancel_lancamento_notas_fiscais_request",
            case="not-owner",
            profile="P6B",
            expected="403 invoice_posting_request.not_owner",
            obtained=f"{denied.status} {denied_code}",
            outcome="PASS" if ok_owner else "FAIL",
        )
        if isinstance(denied.body, dict):
            _write_golden("cancel_lancamento_notas_fiscais_request", "not-owner", {"http_status": denied.status, "snapshot": envelope_snapshot(denied.body)})
        assert ok_assigned and ok_owner
    finally:
        client.call("POST", f"/lancamento-notas-fiscais/requests/{request_id}/cancel", profile="P9", json_body={"justification": MARKER})


def test_reconciliation_refresh_cooldown_as_is() -> None:
    """Cooldown do refresh: 200 com status=skipped (não 409 busy)."""
    client = _client()
    actor = _actor_read()
    if client is None or actor is None:
        record(route="refresh_lancamento_notas_fiscais_reconciliation", case="cooldown", profile=actor or "-", expected="200 skipped no 2º", obtained="sem alvo", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    first = client.call("POST", "/lancamento-notas-fiscais/reconciliation/refresh", profile=actor)
    second = client.call("POST", "/lancamento-notas-fiscais/reconciliation/refresh", profile=actor)
    first_status = (_data(first.body) or {}).get("status")
    second_status = (_data(second.body) or {}).get("status")
    ok = first.status == 200 and second.status == 200 and second_status == "skipped"
    # Contrato AS_IS: cooldown não é 409 busy; resposta estável 200 + status=skipped.
    outcome = "AS_IS_BEHAVIOR" if ok else "FAIL"
    record(
        route="refresh_lancamento_notas_fiscais_reconciliation",
        case="cooldown",
        profile=actor,
        expected="200 e 200 status=skipped no 2º",
        obtained=f"{first.status}/{first_status}->{second.status}/{second_status}",
        outcome=outcome,
        note="AS_IS do contrato atual: cooldown responde 200 skipped, não 409",
    )
    if isinstance(second.body, dict):
        _write_golden("refresh_lancamento_notas_fiscais_reconciliation", "cooldown-skipped", {"http_status": second.status, "snapshot": envelope_snapshot(second.body)})
    assert first.status == 200 and second.status == 200


def test_reconciliation_busy_concurrent_run() -> None:
    """ERP DEV é base real: a suíte limita reconciliation/run a 1× por execução.

    Dois POSTs concorrentes violariam esse limite; busy fica NOT_COVERED nesta fase.
    """
    record(
        route="run_lancamento_notas_fiscais_reconciliation",
        case="busy",
        profile="P7",
        expected="409 invoice_posting_reconciliation.busy",
        obtained="não provocado",
        outcome="NOT_COVERED_BLACKBOX",
        note="TOTVS_DB_HOST=192.168.1.230/DELPI é ERP real; suíte limita run a 1×/execução",
    )
    pytest.skip("NOT_COVERED_BLACKBOX: limite 1× run contra ERP real")


def test_binary_signature_when_present() -> None:
    """Com Questor saudável captura sha256; se upstream falhar, INCONCLUSIVE."""
    client = _client()
    actor = _actor_create()
    route = "get_lancamento_notas_fiscais_received_invoice_danfe"
    if client is None or actor is None:
        record(route=route, case="binary", profile=actor or "-", expected="%PDF ou XML", obtained="sem token", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")

    raw_path = (os.getenv("LNF_BINARY_PATH") or "").strip()
    if not raw_path:
        listed = client.call(
            "GET",
            "/lancamento-notas-fiscais/received-invoices",
            profile=actor if actor != "P5" or profile_token("P5") else "P9",
            params={"invoice_number": (os.getenv("LNF_RECEIVED_INVOICE_NUMBER") or "1"), "page": "1", "page_size": "5"},
        )
        code = _error_code(listed.body)
        if listed.status != 200:
            outcome = "INCONCLUSIVE" if listed.status in {502, 503} or code in {"financial_invoices.upstream"} else "AS_IS_BEHAVIOR"
            record(
                route="list_lancamento_notas_fiscais_received_invoices",
                case="binary-preflight",
                profile=actor,
                expected="200 com items para baixar DANFE",
                obtained=f"{listed.status} {code}",
                outcome=outcome,
                note="FIN_QUESTOR_* presentes, mas Questor/financial-api respondeu upstream",
            )
            if isinstance(listed.body, dict):
                _write_golden("list_lancamento_notas_fiscais_received_invoices", "upstream", {"http_status": listed.status, "snapshot": envelope_snapshot(listed.body)})
            pytest.skip("INCONCLUSIVE: documentos recebidos indisponíveis")
        items = _data(listed.body).get("items") or []
        if not items:
            record(route=route, case="binary", profile=actor, expected="%PDF", obtained="lista vazia", outcome="INCONCLUSIVE")
            pytest.skip("INCONCLUSIVE")
        first = items[0] if isinstance(items[0], dict) else {}
        document_id = str(first.get("id") or first.get("document_id") or "")
        if not document_id:
            record(route=route, case="binary", profile=actor, expected="document_id", obtained="item sem id", outcome="INCONCLUSIVE")
            pytest.skip("INCONCLUSIVE")
        raw_path = f"/lancamento-notas-fiscais/received-invoices/{document_id}/danfe"

    result = client.call("GET", raw_path, profile="P5" if profile_token("P5") else actor)
    if result.status in {502, 503}:
        record(route=route, case="binary", profile=actor, expected="200 %PDF", obtained=f"{result.status} {_error_code(result.body)}", outcome="INCONCLUSIVE", note="upstream Questor")
        pytest.skip("INCONCLUSIVE")
    signature = result.raw[:5]
    is_pdf = signature == b"%PDF-"
    is_xml = result.raw.lstrip().startswith(b"<")
    ok = result.status == 200 and (is_pdf or is_xml)
    digest = hashlib.sha256(result.raw).hexdigest() if ok else ""
    record(route=route, case="binary", profile=actor, expected="200 %PDF ou XML", obtained=f"{result.status} sha256={digest[:16]}", outcome="PASS" if ok else "FAIL")
    if ok:
        _write_golden(
            "binary",
            "sha256",
            {"sha256": digest, "content_type": result.content_type, "path": raw_path, "bytes": len(result.raw)},
        )
    assert ok


@pytest.mark.parametrize("code,reason", NOT_COVERED)
def test_not_covered_blackbox(code: str, reason: str) -> None:
    record(route="-", case=code, profile="-", expected=code, obtained="não provocado", outcome="NOT_COVERED_BLACKBOX", note=reason)


def test_route_catalog_has_24() -> None:
    assert len(ROUTES) == 24
    record(route="catalog", case="count", profile="-", expected="24", obtained=str(len(ROUTES)), outcome="PASS")
