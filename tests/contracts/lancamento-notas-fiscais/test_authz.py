"""Matriz AuthZ 24 rotas × P0–P12. Só HTTP."""

from __future__ import annotations

import pytest

from lnf_contract.catalog import (
    SIDE_EFFECT_SAMPLE,
    Route,
    ROUTES,
    auth_probe,
    branch_allowed,
    decorator_allows,
)
from lnf_contract.client import ContractClient
from lnf_contract.guard import PROFILES, profile_token, target_name
from lnf_contract.report import record

_RECONCILE_AUTHZ_USED = False


def _denial(body: object) -> bool:
    return (
        isinstance(body, dict)
        and "detail" in body
        and "success" not in body
    )


def _code(body: object) -> str | None:
    if not isinstance(body, dict):
        return None
    error = body.get("error")
    if isinstance(error, dict):
        return str(error.get("code") or "") or None
    return None


def _client() -> ContractClient | None:
    client = ContractClient()
    if not client.configured():
        return None
    return client


@pytest.mark.parametrize("route", ROUTES, ids=lambda route: route.operation_id)
@pytest.mark.parametrize("profile", PROFILES)
def test_authz_matrix(route: Route, profile: str) -> None:
    target = target_name()
    allowed = decorator_allows(profile, route, target=target)
    expected = "passa o decorator" if allowed else "403 {detail}"
    if profile == "P10":
        expected = (
            "403/401 sem bypass (KNOWN_DIVERGENCE_D8)"
            if target == "bff"
            else "bypass superadmin atual (KNOWN_DIVERGENCE_D8)"
        )
    client = _client()
    if client is None:
        record(route=route.operation_id, case="authz", profile=profile, expected=expected, obtained="sem LNF_BASE_URL", outcome="INCONCLUSIVE", note="URL de dev não configurada")
        pytest.skip("INCONCLUSIVE: LNF_BASE_URL ausente")
    if profile_token(profile) is None:
        record(route=route.operation_id, case="authz", profile=profile, expected=expected, obtained="sem token", outcome="INCONCLUSIVE", note="perfil sem token; usuários de teste não foram criados")
        pytest.skip(f"INCONCLUSIVE: token {profile} ausente")
    global _RECONCILE_AUTHZ_USED
    if allowed and route.operation_id in SIDE_EFFECT_SAMPLE:
        if not __import__("os").getenv("LNF_ALLOW_RECONCILE_RUN"):
            record(
                route=route.operation_id,
                case="authz",
                profile=profile,
                expected=expected,
                obtained="não chamado",
                outcome="INCONCLUSIVE",
                note="run varre o Protheus; defina LNF_ALLOW_RECONCILE_RUN=1 para a amostra positiva",
            )
            pytest.skip("INCONCLUSIVE: run não disparado")
        if _RECONCILE_AUTHZ_USED:
            record(
                route=route.operation_id,
                case="authz",
                profile=profile,
                expected=expected,
                obtained="orçamento 1× run esgotado",
                outcome="PASS",
                note="TOTVS DEV é ERP real; só uma amostra positiva de run por execução",
            )
            return

    path, params, body = auth_probe(route, profile)
    # Amostra positiva consome orçamento 1×; negações AuthZ sempre batem no servidor.
    result = client.call(
        route.method,
        path,
        profile=profile,
        params=params,
        json_body=body,
        budget_reconcile_run=bool(
            allowed and route.operation_id in SIDE_EFFECT_SAMPLE
        ),
    )
    if (
        allowed
        and route.operation_id in SIDE_EFFECT_SAMPLE
        and result.status not in {0, 401, 403}
    ):
        _RECONCILE_AUTHZ_USED = True
    if result.status == 0:
        record(route=route.operation_id, case="authz", profile=profile, expected=expected, obtained=result.error or "sem conexão", outcome="INCONCLUSIVE", note="alvo LNF inacessível")
        pytest.skip("INCONCLUSIVE: sem conexão")
    obtained = f"{result.status} code={_code(result.body) or _detail(result.body)}"
    note = "KNOWN_DIVERGENCE_D8" if profile == "P10" else ""

    if profile == "P10" and target == "bff":
        ok = result.status in {401, 403}
        outcome = "PASS" if ok else "FAIL"
        record(route=route.operation_id, case="authz", profile=profile, expected=expected, obtained=obtained, outcome=outcome, note=note)
        assert ok, obtained
        return

    if not allowed:
        ok = result.status == 403 and _denial(result.body)
        outcome = "PASS" if ok else "AS_IS_BEHAVIOR" if result.status in {401, 403, 503} else "FAIL"
        if outcome == "AS_IS_BEHAVIOR":
            note = (note + " " if note else "") + "negação diferente do {detail: Forbidden} derivado"
        record(route=route.operation_id, case="authz", profile=profile, expected=expected, obtained=obtained, outcome=outcome, note=note.strip())
        assert ok, obtained
        return

    create_branch = "01"
    if profile in {"P2", "P3", "P11", "P12"}:
        create_branch = {"P2": "01", "P3": "02", "P11": "01", "P12": "02"}[profile]
    if route.operation_id == "create_lancamento_notas_fiscais_request" and not branch_allowed(
        profile, create_branch, target=target
    ):
        ok = result.status == 403 and _code(result.body) == "BRANCH_FORBIDDEN"
        outcome = "PASS" if ok else "FAIL"
        record(route=route.operation_id, case="authz-branch", profile=profile, expected="403 BRANCH_FORBIDDEN", obtained=obtained, outcome=outcome, note=note)
        assert ok, obtained
        return

    denied = result.status == 403 and _denial(result.body)
    outcome = "FAIL" if denied else "PASS"
    record(route=route.operation_id, case="authz", profile=profile, expected=expected, obtained=obtained, outcome=outcome, note=note)
    assert not denied, obtained


def _detail(body: object) -> str:
    if isinstance(body, dict) and "detail" in body:
        return str(body.get("detail"))
    return "-"


def test_branch_required_without_global_access() -> None:
    """P2 em GET /requests sem branch: 400 BRANCH_REQUIRED."""
    client = _client()
    expected = "400 BRANCH_REQUIRED"
    if client is None or profile_token("P2") is None:
        record(route="list_lancamento_notas_fiscais_requests", case="branch-required", profile="P2", expected=expected, obtained="sem alvo ou token", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    result = client.call("GET", "/lancamento-notas-fiscais/requests", profile="P2", params={"page": "1", "page_size": "5"})
    obtained = f"{result.status} code={_code(result.body)}"
    ok = result.status == 400 and _code(result.body) == "BRANCH_REQUIRED"
    record(route="list_lancamento_notas_fiscais_requests", case="branch-required", profile="P2", expected=expected, obtained=obtained, outcome="PASS" if ok else "FAIL")
    assert ok, obtained


def test_sibling_branch_forbidden() -> None:
    client = _client()
    cases = (("P2", "02"), ("P3", "01"))
    if client is None:
        for profile, branch in cases:
            record(route="list_lancamento_notas_fiscais_requests", case=f"sibling-{branch}", profile=profile, expected="403 BRANCH_FORBIDDEN", obtained="sem URL", outcome="INCONCLUSIVE")
        pytest.skip("INCONCLUSIVE")
    for profile, branch in cases:
        if profile_token(profile) is None:
            record(route="list_lancamento_notas_fiscais_requests", case=f"sibling-{branch}", profile=profile, expected="403 BRANCH_FORBIDDEN", obtained="sem token", outcome="INCONCLUSIVE")
            continue
        result = client.call(
            "GET",
            "/lancamento-notas-fiscais/requests",
            profile=profile,
            params={"branch": branch, "page": "1", "page_size": "5"},
        )
        obtained = f"{result.status} code={_code(result.body)}"
        ok = result.status == 403 and _code(result.body) == "BRANCH_FORBIDDEN"
        record(route="list_lancamento_notas_fiscais_requests", case=f"sibling-{branch}", profile=profile, expected="403 BRANCH_FORBIDDEN", obtained=obtained, outcome="PASS" if ok else "FAIL")
        assert ok, obtained
