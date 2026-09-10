#!/usr/bin/env python3
"""Smoke — catálogos de display → OpenAPI + FieldLabelBundle (sem LLM indevido).

Uso:
  cd minha-delpi-ai-api
  PYTHONPATH=. .venv/bin/python -u scripts/smoke_catalog_display_openapi.py

Modos:
  SMOKE_CATALOG_DISPLAY_PHASE=inprocess|http|all  (default all)
  SMOKE_BASE_URL=http://localhost
  SMOKE_USER / SMOKE_PASSWORD
  SMOKE_AGENT_ID  (opcional; senão usa o primeiro agente do usuário)

Fases:
  1) inprocess — resolvers + preferredColumns keys-only + commentary FLB + allowlist
  2) http — capabilities / descrição / estoque via gateway (quando stack up)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PHASE = os.environ.get("SMOKE_CATALOG_DISPLAY_PHASE", "all").strip().lower()
_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost").strip().rstrip("/")
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_AGENT_ID = os.environ.get("SMOKE_AGENT_ID", "").strip()
_PRODUCT_CODE = os.environ.get("SMOKE_PRODUCT_CODE", "10080011").strip()
_STOCK_CODE = os.environ.get("SMOKE_STOCK_CODE", "10080001").strip()

_failed = 0


def _ok(label: str, detail: str = "") -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"PASS  {label}{suffix}")


def _fail(label: str, detail: str) -> None:
    global _failed
    _failed += 1
    print(f"FAIL  {label} — {detail}")


def _warn(label: str, detail: str) -> None:
    print(f"WARN  {label} — {detail}")


def _phase_inprocess() -> None:
    from app.composition.content_composer import configure_domain_infrastructure_ports

    configure_domain_infrastructure_ports()

    from app.domain.services.action_display_label_resolver import (
        SOURCE_OPENAPI_SUMMARY,
        ActionDisplayLabelResolver,
    )
    from app.domain.services.chat_data_insight_service import ChatDataInsightService
    from app.domain.services.chat_humanized_data_response_service import (
        ChatHumanizedDataResponseService,
    )
    from app.domain.services.recommendation_action_validator import (
        RecommendationActionValidator,
    )
    from app.domain.services.result_presentation_title_resolver import (
        SOURCE_PRESENTATION_TITLE,
        ResultPresentationTitleResolver,
    )

    # preferredColumns keys-only
    column_labels = json.loads(
        (_ROOT / "app/content/pt-BR/assistant/column_labels.json").read_text(encoding="utf-8")
    )
    profiles = column_labels.get("tableProfiles") or {}
    bad_pairs = []
    for name, profile in profiles.items():
        for item in profile.get("preferredColumns") or []:
            if not isinstance(item, str):
                bad_pairs.append((name, item))
    if bad_pairs:
        _fail("preferredColumns_keys_only", f"{len(bad_pairs)} pares residuais: {bad_pairs[:3]}")
    else:
        _ok("preferredColumns_keys_only", f"{len(profiles)} perfis")

    # Action display: PT summary vence pathLabel
    pt = ActionDisplayLabelResolver.resolve(
        path="/products/{code}/stock",
        method="GET",
        summary="Consultar estoque do produto por filial",
    )
    if pt.source != SOURCE_OPENAPI_SUMMARY or "estoque" not in pt.label.casefold():
        _fail("action_label_pt_summary", f"source={pt.source} label={pt.label!r}")
    else:
        _ok("action_label_pt_summary", pt.label)

    # First-party: locale pt-BR vence summary EN (sem pathLabels no default)
    en = ActionDisplayLabelResolver.resolve(
        path="/commercial/closing-rate",
        method="GET",
        summary="Get Sales Conversion Rate",
        delpi_metadata={
            "locale": {"pt-BR": {"summary": "Taxa de conversão de vendas"}},
        },
    )
    if en.label != "Taxa de conversão de vendas" or en.source != "OPENAPI_LOCALIZED":
        _fail("action_label_en_locale", f"{en.source}:{en.label!r}")
    else:
        _ok("action_label_en_locale", en.label)

    # LLM-off / sem locale: humanize determinístico (nunca pathLabels)
    en_bridge = ActionDisplayLabelResolver.resolve(
        path="/products/{code}/customers",
        method="GET",
        summary="Customers",
    )
    if en_bridge.source in {"LEGACY_PATH_LABEL", "ENGLISH_SUMMARY_MAP"}:
        _fail("action_label_no_legacy_catalogs", f"{en_bridge.source}:{en_bridge.label}")
    elif "cliente" not in en_bridge.label.casefold():
        _fail("action_label_en_humanize", f"{en_bridge.source}:{en_bridge.label!r}")
    else:
        _ok("action_label_en_humanize", f"{en_bridge.source}:{en_bridge.label}")
    # Unknown API sem api_paths
    unknown = ActionDisplayLabelResolver.resolve(
        path="/acme/widgets/{id}/inventory",
        method="GET",
        summary="Consultar inventário de widgets",
        action_id="acme.widgets.inventory",
        provider_key="acme-erp",
    )
    if "inventário" not in unknown.label.casefold() and "widget" not in unknown.label.casefold():
        _fail("unknown_external_api_label", unknown.label)
    else:
        _ok("unknown_external_api_label", f"{unknown.source}:{unknown.label}")

    # Metamórfico: rename path, mesmo summary
    summary = "Consultar disponibilidade de item"
    a = ActionDisplayLabelResolver.resolve(
        path="/v1/widgets/{id}/availability",
        method="GET",
        summary=summary,
        provider_key="acme",
    )
    b = ActionDisplayLabelResolver.resolve(
        path="/catalog/sku/{sku}/availability",
        method="GET",
        summary=summary,
        provider_key="acme",
    )
    if a.label != b.label:
        _fail("metamorphic_rename", f"{a.label!r} != {b.label!r}")
    else:
        _ok("metamorphic_rename", a.label)

    # Commentary via FieldLabelBundle
    lines = ChatDataInsightService._highlights_from_operational_summary(
        {"summary": {"oee_pct": 87.5, "late_ops": 3}},
        metadata={
            "resolvedFieldLabels": {
                "labels": {"oee_pct": "OEE %", "late_ops": "OPs em atraso"},
                "sourceByKey": {"oee_pct": "OPENAPI", "late_ops": "OPENAPI"},
            }
        },
    )
    joined = " ".join(lines)
    if "OEE %" not in joined or "OPs em atraso" not in joined:
        _fail("commentary_field_label_parity", joined)
    else:
        _ok("commentary_field_label_parity", joined[:80])

    # Presentation title materializado
    title = ResultPresentationTitleResolver.resolve(
        path="/products/X/stock",
        metadata={"presentation": {"title": "Posição de estoque"}},
        legacy_title="Estoque",
    )
    if title.source != SOURCE_PRESENTATION_TITLE or title.title != "Posição de estoque":
        _fail("presentation_title_metadata", f"{title.source}:{title.title}")
    else:
        _ok("presentation_title_metadata", title.title)

    # Recommendations allowlist
    filtered = RecommendationActionValidator.filter_items(
        [
            {"label": "Estoque", "query": "estoque", "actionId": "a1"},
            {"label": "Proibido", "query": "x", "actionId": "a2"},
            {"label": "Só texto", "query": "texto"},
        ],
        ["a1"],
    )
    ids = {item.get("actionId") for item in filtered if item.get("actionId")}
    if ids != {"a1"} or not any(item.get("label") == "Só texto" for item in filtered):
        _fail("recommendation_allowlist", str(filtered))
    else:
        _ok("recommendation_allowlist", f"kept={len(filtered)}")

    commentary = ChatHumanizedDataResponseService.normalize(
        {
            "highlights": ["ok"],
            "structuredRecommendations": [
                {"label": "Estoque", "query": "estoque", "actionId": "a1"},
                {"label": "Proibido", "query": "x", "actionId": "a2"},
            ],
        },
        profile_key="generic_list",
        allowed_action_ids=["a1"],
    )
    recs = (commentary or {}).get("recommendations") or []
    if len(recs) != 1 or recs[0].get("actionId") != "a1":
        _fail("normalize_structured_recommendations", str(recs))
    else:
        _ok("normalize_structured_recommendations")

    # LLM off: sem localizer configurado, EN externo cai no humanize
    ActionDisplayLabelResolver.configure(llm_localizer=None, cache_get=None, cache_put=None)
    llm_off = ActionDisplayLabelResolver.resolve(
        path="/acme/things",
        method="GET",
        summary="List Things",
        provider_key="acme-erp",
        action_id="acme.things.list",
    )
    if not llm_off.label:
        _fail("llm_off_fallback", "label vazio")
    else:
        _ok("llm_off_fallback", f"{llm_off.source}:{llm_off.label}")


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: float = 180,
) -> dict:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _fetch_token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USERNAME,
            "password": _PASSWORD,
        }
    ).encode("utf-8")
    url = f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token"
    request = urllib.request.Request(
        url,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    token = str(payload.get("access_token") or "").strip()
    if not token:
        raise RuntimeError("token vazio")
    return token


def _resolve_agent_id(token: str) -> str:
    if _AGENT_ID:
        return _AGENT_ID
    payload = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents", token=token)
    if isinstance(payload, list):
        agents = payload
    elif isinstance(payload, dict):
        agents = payload.get("agents") or payload.get("items") or []
        if isinstance(agents, dict):
            agents = agents.get("agents") or agents.get("items") or []
    else:
        agents = []
    if not isinstance(agents, list) or not agents:
        raise RuntimeError(f"nenhum agente: {payload!r}")
    agent_id = str(agents[0].get("id") or agents[0].get("agentId") or "").strip()
    if not agent_id:
        raise RuntimeError(f"agente sem id: {agents[0]!r}")
    return agent_id


def _create_session(token: str, agent_id: str) -> str:
    payload = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"agentId": agent_id, "title": "smoke-catalog-display-openapi"},
    )
    session_id = str(payload.get("id") or payload.get("sessionId") or "").strip()
    if not session_id:
        raise RuntimeError(f"session sem id: {payload!r}")
    return session_id


def _send_message(token: str, session_id: str, message: str) -> dict:
    return _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={"message": message, "responseMode": "normal"},
        timeout=360,
    )


def _collect_action_summaries(payload: dict) -> list[str]:
    texts: list[str] = []
    answer = str(payload.get("answer") or payload.get("content") or "")
    if answer:
        texts.append(answer)
    for tool in payload.get("toolCalls") or []:
        if not isinstance(tool, dict):
            continue
        meta = tool.get("metadata") if isinstance(tool.get("metadata"), dict) else {}
        for key in ("summary", "actionSummary", "routeTitle", "title"):
            value = meta.get(key)
            if isinstance(value, str) and value.strip():
                texts.append(value.strip())
        plan = meta.get("stackPresentationPlan")
        if isinstance(plan, dict):
            for key in ("resolvedRouteTitle",):
                value = plan.get(key)
                if isinstance(value, str) and value.strip():
                    texts.append(value.strip())
            route_titles = plan.get("routeTitles")
            if isinstance(route_titles, dict):
                texts.extend(str(v) for v in route_titles.values() if str(v).strip())
    return texts


def _looks_technical_leak(text: str) -> bool:
    lowered = text.casefold()
    leaks = (
        "get sales conversion rate",
        "get hr snapshot",
        "customers —",
        "suppliers —",
        "operationid",
    )
    return any(token in lowered for token in leaks)


def _phase_http() -> None:
    try:
        token = _fetch_token()
    except Exception as exc:
        _warn("http_auth", f"gateway indisponível ({exc}); skip live")
        return

    try:
        agent_id = _resolve_agent_id(token)
        session_id = _create_session(token, agent_id)
    except Exception as exc:
        _fail("http_session", str(exc))
        return

    _ok("http_session", f"agent={agent_id} session={session_id}")

    cases = [
        ("capabilities_list", "o que você pode fazer? liste as consultas autorizadas"),
        ("product_description", f"descrição do produto {_PRODUCT_CODE}"),
        ("product_stock", f"estoque do produto {_STOCK_CODE}"),
    ]

    for case_id, message in cases:
        try:
            payload = _send_message(token, session_id, message)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            _fail(case_id, f"HTTP {exc.code}: {body[:240]}")
            continue
        except Exception as exc:
            _fail(case_id, str(exc))
            continue

        texts = _collect_action_summaries(payload)
        blob = "\n".join(texts)
        if not blob.strip():
            _fail(case_id, "resposta vazia")
            continue
        if _looks_technical_leak(blob):
            _fail(case_id, f"vazamento técnico EN: {blob[:200]}")
            continue
        _ok(case_id, f"chars={len(blob)}")


def main() -> int:
    print(
        f"smoke_catalog_display_openapi phase={_PHASE} base={_BASE_URL}",
        flush=True,
    )

    run_inprocess = _PHASE in {"all", "inprocess", "offline", "unit"}
    run_http = _PHASE in {"all", "http", "live"}

    if run_inprocess:
        print("--- inprocess ---", flush=True)
        _phase_inprocess()

    if run_http:
        print("--- http ---", flush=True)
        _phase_http()

    if _failed:
        print(f"RESULT FAIL ({_failed})", flush=True)
        return 1

    print("RESULT PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
