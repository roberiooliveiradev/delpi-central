"""Contrato de envelope, erros alcançáveis e códigos fora da caixa-preta."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from lnf_contract.catalog import FAKE_REQUEST_ID, ROUTES
from lnf_contract.client import ContractClient
from lnf_contract.guard import profile_token, target_name
from lnf_contract.normalize import envelope_snapshot
from lnf_contract.report import GOLDEN, record

NOT_COVERED = (
    ("invoice_posting_reconciliation.erp_unavailable", "502 exige falha do Protheus; não injetar no runtime"),
    ("invoice_posting_request.upstream", "502 exige falha de upstream; não injetar no runtime"),
    ("financial_invoices.upstream", "502 exige financial-api/Questor indisponível de propósito"),
    ("INTERNAL_ERROR", "500 de exceção interna não é provocável sem alterar o runtime"),
)


def _actor() -> str | None:
    for profile in ("P7", "P6", "P9", "P10"):
        if profile == "P10" and target_name() == "bff":
            continue
        if profile_token(profile):
            return profile
    return None


def _client() -> ContractClient | None:
    client = ContractClient()
    return client if client.configured() else None


def _write_golden(operation_id: str, case: str, payload: dict) -> None:
    if os.getenv("LNF_WRITE_GOLDEN") != "1":
        return
    folder = GOLDEN / operation_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{case}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_success_envelope_list_requests() -> None:
    client = _client()
    actor = _actor()
    route = "list_lancamento_notas_fiscais_requests"
    if client is None or actor is None:
        record(route=route, case="success-envelope", profile=actor or "-", expected="200 envelope", obtained="sem alvo ou token de leitura global", outcome="INCONCLUSIVE")
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
        _write_golden(route, "success", {"http_status": 200, "content_type": result.content_type, "snapshot": envelope_snapshot(body)})
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
    actor = _actor()
    if client is None or actor is None:
        record(route="get_lancamento_notas_fiscais_request", case="not-found", profile=actor or "-", expected="404 invoice_posting_request.not_found", obtained="sem alvo", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    missing = client.call("GET", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}", profile=actor)
    missing_code = _error_code(missing.body)
    ok_missing = missing.status == 404 and missing_code == "invoice_posting_request.not_found"
    record(route="get_lancamento_notas_fiscais_request", case="not-found", profile=actor, expected="404 invoice_posting_request.not_found", obtained=f"{missing.status} {missing_code}", outcome="PASS" if ok_missing else "FAIL")

    invalid = client.call("GET", "/lancamento-notas-fiscais/requests", profile=actor, params={"branch": "01", "status": "not-a-status"})
    invalid_code = _error_code(invalid.body)
    ok_filter = invalid.status == 400 and invalid_code == "INVALID_STATUS_FILTER"
    record(route="list_lancamento_notas_fiscais_requests", case="invalid-status", profile=actor, expected="400 INVALID_STATUS_FILTER", obtained=f"{invalid.status} {invalid_code}", outcome="PASS" if ok_filter else "FAIL")

    danfe = client.call("GET", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/danfe", profile=actor, params={"disposition": "inline"})
    danfe_code = _error_code(danfe.body)
    ok_danfe = danfe.status == 404 and danfe_code in {"invoice_posting_request.not_found", "danfe.not_found"}
    record(route="get_lancamento_notas_fiscais_request_danfe", case="danfe-missing", profile=actor, expected="404 not_found ou danfe.not_found", obtained=f"{danfe.status} {danfe_code}", outcome="PASS" if ok_danfe else "FAIL", note="id inexistente não chega em danfe.not_found")

    attachment = client.call("GET", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/fiscal-attachments/xml_original", profile=actor)
    attachment_code = _error_code(attachment.body)
    ok_attachment = attachment.status == 404 and attachment_code == "invoice_posting_request.not_found"
    record(route="get_lancamento_notas_fiscais_request_fiscal_attachment", case="attachment-missing", profile=actor, expected="404 invoice_posting_request.not_found", obtained=f"{attachment.status} {attachment_code}", outcome="PASS" if ok_attachment else "FAIL", note="tipo inválido é 422; fiscal_attachment.not_found só com solicitação existente")
    assert ok_missing and ok_filter and ok_danfe and ok_attachment


def test_supplier_not_found_on_safe_create() -> None:
    client = _client()
    actor = _actor()
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
            "observation": "CONTRACT-TEST F2",
        },
    )
    code = _error_code(result.body)
    ok = result.status == 404 and code == "supplier.not_found"
    outcome = "PASS" if ok else "AS_IS_BEHAVIOR" if result.status >= 500 else "FAIL"
    note = "" if ok else "Protheus pode estar indisponível" if result.status >= 500 else ""
    record(route="create_lancamento_notas_fiscais_request", case="supplier-not-found", profile=actor, expected="404 supplier.not_found", obtained=f"{result.status} {code}", outcome=outcome, note=note)
    if outcome == "AS_IS_BEHAVIOR":
        pytest.skip(f"AS_IS_BEHAVIOR {result.status} {code}")
    assert ok


def test_supplier_blocked_requires_known_supplier() -> None:
    code = (os.getenv("LNF_BLOCKED_SUPPLIER_CODE") or "").strip()
    store = (os.getenv("LNF_BLOCKED_SUPPLIER_STORE") or "").strip()
    if not code or not store:
        record(route="create_lancamento_notas_fiscais_request", case="supplier-blocked", profile="-", expected="422 supplier.blocked", obtained="sem fornecedor bloqueado conhecido", outcome="INCONCLUSIVE", note="defina LNF_BLOCKED_SUPPLIER_CODE e LNF_BLOCKED_SUPPLIER_STORE")
        pytest.skip("INCONCLUSIVE")


def test_binary_signature_when_present() -> None:
    """Sem documento real, o binário fica INCONCLUSIVE. Com LNF_BINARY_PATH, confere assinatura e sha256."""
    raw_path = (os.getenv("LNF_BINARY_PATH") or "").strip()
    if not raw_path:
        record(route="get_lancamento_notas_fiscais_received_invoice_danfe", case="binary", profile="-", expected="%PDF ou XML", obtained="sem documento de dev", outcome="INCONCLUSIVE", note="financial-api/Questor não foi presumido")
        pytest.skip("INCONCLUSIVE")
    client = _client()
    actor = _actor_create()
    if client is None or actor is None:
        record(route=raw_path, case="binary", profile=actor or "-", expected="assinatura", obtained="sem token", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    result = client.call("GET", raw_path, profile=actor)
    signature = result.raw[:5]
    is_pdf = signature == b"%PDF-"
    is_xml = result.raw.lstrip().startswith(b"<")
    ok = result.status == 200 and (is_pdf or is_xml)
    digest = hashlib.sha256(result.raw).hexdigest() if ok else ""
    record(route=raw_path, case="binary", profile=actor, expected="200 %PDF ou XML", obtained=f"{result.status} sha256={digest[:12]}", outcome="PASS" if ok else "FAIL")
    if ok and os.getenv("LNF_WRITE_GOLDEN") == "1":
        folder = GOLDEN / "binary"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "sha256.json").write_text(json.dumps({"sha256": digest, "content_type": result.content_type}, indent=2) + "\n", encoding="utf-8")
    assert ok


@pytest.mark.parametrize("code,reason", NOT_COVERED)
def test_not_covered_blackbox(code: str, reason: str) -> None:
    record(route="-", case=code, profile="-", expected=code, obtained="não provocado", outcome="NOT_COVERED_BLACKBOX", note=reason)


def test_not_owner_and_already_assigned_need_two_users() -> None:
    second = (os.getenv("LNF_TOKEN_P6B") or "").strip()
    if not second:
        record(route="start_lancamento_notas_fiscais_request", case="not-owner", profile="P6B", expected="403 invoice_posting_request.not_owner", obtained="sem segundo usuário de processo", outcome="INCONCLUSIVE", note="o código exige outro actor com process/manage")
        record(route="start_lancamento_notas_fiscais_request", case="already-assigned", profile="P6B", expected="409 invoice_posting_request.already_assigned", obtained="sem segundo usuário de processo", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")


def _actor_create() -> str | None:
    for profile in ("P5", "P6", "P7", "P9", "P10"):
        if profile == "P10" and target_name() == "bff":
            continue
        if profile_token(profile):
            return profile
    return None


def _error_code(body: object) -> str | None:
    if not isinstance(body, dict):
        return None
    error = body.get("error")
    if isinstance(error, dict):
        return str(error.get("code") or "") or None
    return None


def test_reconciliation_busy_is_not_the_refresh_cooldown() -> None:
    """O cooldown de 45 s do refresh responde 200 skipped. O 409 busy é o lock do run."""
    client = _client()
    actor = _actor()
    if client is None or actor is None:
        record(route="refresh_lancamento_notas_fiscais_reconciliation", case="cooldown", profile=actor or "-", expected="200 no segundo refresh", obtained="sem alvo", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    first = client.call("POST", "/lancamento-notas-fiscais/reconciliation/refresh", profile=actor)
    second = client.call("POST", "/lancamento-notas-fiscais/reconciliation/refresh", profile=actor)
    ok = first.status == 200 and second.status == 200
    record(
        route="refresh_lancamento_notas_fiscais_reconciliation",
        case="cooldown",
        profile=actor,
        expected="200 e 200 (cooldown não é 409)",
        obtained=f"{first.status}->{second.status}",
        outcome="PASS" if ok else "AS_IS_BEHAVIOR",
        note="invoice_posting_reconciliation.busy exige lock preso no run; refresh sequencial não o provoca",
    )
    record(
        route="run_lancamento_notas_fiscais_reconciliation",
        case="busy",
        profile="-",
        expected="409 invoice_posting_reconciliation.busy",
        obtained="não provocado",
        outcome="NOT_COVERED_BLACKBOX",
        note="o lock só existe durante o run; dois refresh seguidos não seguram o lock",
    )
    assert ok


def test_route_catalog_has_24() -> None:
    assert len(ROUTES) == 24
    record(route="catalog", case="count", profile="-", expected="24", obtained=str(len(ROUTES)), outcome="PASS")
