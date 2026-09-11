"""J-R8 — parallel technical registry/content duplication removed."""

from __future__ import annotations

import json
from pathlib import Path

from app.domain.services.chat_operational_refinement.chat_operational_refinement_metric_service import (
    ChatOperationalRefinementMetricService,
)
from app.domain.services.chat_route_context_service import RecentMetricRoute


_ROOT = Path(__file__).resolve().parents[4]
_REGISTRY = _ROOT / "app/content/pt-BR/assistant/operational_route_registry.json"
_DOMAINS = _ROOT / "app/content/pt-BR/assistant/api_route_domains.json"


def test_j_r8_registry_operation_ids_all_empty():
    payload = json.loads(_REGISTRY.read_text(encoding="utf-8"))
    routes = payload.get("routes") or []
    assert routes
    for route in routes:
        spec = route.get("route") if isinstance(route.get("route"), dict) else {}
        assert (spec.get("operationIds") or []) == [], route.get("id")
    assert payload.get("cleanupMeta", {}).get("operationIdsEmptiedAt") == "J-R8"
    assert payload.get("cleanupMeta", {}).get("operationIdsObserverCount") == 0


def test_j_r8_domains_have_no_http_method_duplication():
    payload = json.loads(_DOMAINS.read_text(encoding="utf-8"))
    for domain, cfg in (payload.get("domains") or {}).items():
        if isinstance(cfg, dict):
            assert "method" not in cfg, domain


def test_j_r8_no_path_prefix_to_department_map():
    payload = json.loads(_DOMAINS.read_text(encoding="utf-8"))
    dept = (payload.get("parameterStrategies") or {}).get("department_idd") or {}
    assert "pathPrefixToDepartmentId" not in dept


def test_j_r8_department_from_semantic_domain_token():
    recent = RecentMetricRoute(
        kind="kpi",
        domain_prefix="/commercial/",
        path_token="rol",
        path="/ignored/http/path",
    )
    assert (
        ChatOperationalRefinementMetricService._department_id_for_recent_route(recent)
        == "commercial"
    )


def test_j_r8_autotierc_ci_is_justified_non_semantic():
    path = _ROOT / "app/content/pt-BR/assistant/operational_route_registry_autotierc.ci.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    justification = payload.get("justification") or {}
    assert justification.get("classification") == "JUSTIFIED_NON_SEMANTIC"
    assert justification.get("runtimeAuthority") is False
    assert "Not loaded for chat action selection" in str(payload.get("note") or "")

