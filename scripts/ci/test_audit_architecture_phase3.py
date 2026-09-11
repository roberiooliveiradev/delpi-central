#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_architecture_phase3 as phase3  # noqa: E402


class ArchitecturePhase3GateTests(unittest.TestCase):
    def test_route_path_literal_is_blocked(self) -> None:
        path = "minha-delpi-ai-api/app/application/services/external_actions/example.py"
        findings = phase3.scan_chat_route_hardcode(path, {10: 'if "/products/" in path:'})
        self.assertEqual([item.rule for item in findings], ["CHAT_ROUTE_HARDCODE"])

    def test_provider_bias_is_blocked(self) -> None:
        path = "minha-delpi-ai-api/app/application/services/external_actions/example.py"
        findings = phase3.scan_chat_route_hardcode(path, {7: 'if action_id.startswith("api_delpi."):'})
        self.assertEqual([item.rule for item in findings], ["CHAT_ROUTE_HARDCODE"])

    def test_non_routing_path_is_not_flagged_by_route_gate(self) -> None:
        findings = phase3.scan_chat_route_hardcode(
            "api-delpi/app/routes/products.py", {2: 'router.get("/products/{code}")'}
        )
        self.assertEqual(findings, [])

    def test_registry_state_tracks_manual_technical_metadata_only(self) -> None:
        payload = {
            "routes": [
                {
                    "id": "legacy",
                    "routeSegment": "stock",
                    "route": {
                        "pathMarkers": ["/stock"],
                        "operationIdMarkers": ["get_stock"],
                        "method": "GET",
                    },
                    "parameters": {"strategy": "product_code"},
                }
            ],
            "autoTierCRoutes": [
                {"id": "auto", "route": {"pathMarkers": ["/should-not-count"]}}
            ],
        }
        state = phase3.registry_technical_state(payload)
        self.assertEqual(set(state), {"legacy"})
        self.assertEqual(state["legacy"]["pathMarkers"], {"/stock"})
        self.assertEqual(state["legacy"]["parameterStrategy"], {"product_code"})

    def test_http_timeout_helper_rejects_missing_and_none(self) -> None:
        missing = ast.parse("requests.get(url)").body[0].value
        none_timeout = ast.parse("requests.get(url, timeout=None)").body[0].value
        explicit = ast.parse("requests.get(url, timeout=5)").body[0].value
        self.assertFalse(phase3.timeout_is_explicit(missing))
        self.assertFalse(phase3.timeout_is_explicit(none_timeout))
        self.assertTrue(phase3.timeout_is_explicit(explicit))

    def test_retry_helper_finds_write_methods(self) -> None:
        node = ast.parse("Retry(allowed_methods={'GET', 'POST', 'PATCH'})").body[0].value
        keyword = next(kw for kw in node.keywords if kw.arg == "allowed_methods")
        methods = phase3.literal_methods(keyword.value)
        self.assertEqual(methods & phase3.WRITE_METHODS, {"POST", "PATCH"})

    def test_sensitive_identifier_avoids_safe_metadata(self) -> None:
        self.assertTrue(phase3.sensitive_identifier("access_token"))
        self.assertTrue(phase3.sensitive_identifier("client_secret"))
        self.assertFalse(phase3.sensitive_identifier("token_count"))
        self.assertFalse(phase3.sensitive_identifier("token_usage"))

    def test_secret_literal_scanner_allows_placeholder(self) -> None:
        bad = phase3.scan_secret_lines("service/config.py", {1: 'API_KEY = "sk-live-secret-value"'})
        good = phase3.scan_secret_lines("service/config.py", {1: 'API_KEY = "change-me-example"'})
        self.assertEqual([item.rule for item in bad], ["SECRET_LITERAL"])
        self.assertEqual(good, [])

    def test_violation_fingerprint_is_stable(self) -> None:
        a = phase3.Violation("RULE", "x.py", 10, "hello   world")
        b = phase3.Violation("RULE", "x.py", 99, "hello world")
        self.assertEqual(a.fingerprint, b.fingerprint)

    def test_semantic_domain_rules_detected(self) -> None:
        path = "minha-delpi-ai-api/app/domain/services/api_route_domain_inference_service.py"
        findings = phase3.scan_semantic_substitute_lines(
            path, {19: "    _DOMAIN_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = ("}
        )
        self.assertEqual([item.rule for item in findings], ["SEMANTIC_PATH_DOMAIN_MAP"])

    def test_semantic_sibling_path_markers_content_detected(self) -> None:
        path = "minha-delpi-ai-api/app/content/pt-BR/assistant/api_route_domains.json"
        findings = phase3.scan_semantic_substitute_lines(
            path, {12: '      "pathMarkers": ["/products/"],'}
        )
        self.assertEqual([item.rule for item in findings], ["SEMANTIC_CONTENT_LATERAL_PATH_KEY"])

    def test_semantic_negative_generic_action_path_not_flagged(self) -> None:
        path = "minha-delpi-ai-api/app/domain/services/external_action_http_execution_service.py"
        findings = phase3.scan_semantic_substitute_lines(
            path, {40: '        path = action.get("path") or ""'}
        )
        self.assertEqual(findings, [])

    def test_semantic_negative_fixture_path_outside_scope(self) -> None:
        path = "minha-delpi-ai-api/tests/fixtures/intelligence_baseline/routing_cases.json"
        findings = phase3.scan_semantic_substitute_lines(
            path, {3: '      "pathMarkers": ["/stock"],'}
        )
        self.assertEqual(findings, [])

    def test_semantic_smoke_credential_default_detected(self) -> None:
        path = "minha-delpi-ai-api/scripts/smoke_openapi_first_live.py"
        findings = phase3.scan_semantic_substitute_lines(
            path, {31: '_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()'}
        )
        self.assertEqual([item.rule for item in findings], ["SEMANTIC_SMOKE_CREDENTIAL_DEFAULT"])

    def test_semantic_parameter_strategy_class_detected(self) -> None:
        path = "minha-delpi-ai-api/app/domain/services/parameter_strategy_inference_service.py"
        findings = phase3.scan_semantic_substitute_lines(
            path,
            {
                11: "class ParameterStrategyInferenceService:",
                45: '        if "/products/" in lowered and "search" in lowered:',
            },
        )
        self.assertTrue(
            any(item.rule == "SEMANTIC_ENDPOINT_PARAMETER_STRATEGY" for item in findings)
        )

    def test_semantic_parameter_strategy_stub_without_path_branches_not_flagged(self) -> None:
        path = "minha-delpi-ai-api/app/domain/services/parameter_strategy_inference_service.py"
        findings = phase3.scan_semantic_substitute_lines(
            path,
            {
                11: "class ParameterStrategyInferenceService:",
                20: '        return "schema"',
            },
        )
        self.assertEqual(findings, [])

    def test_registry_operation_ids_catalog_detected(self) -> None:
        findings = phase3.scan_registry_operation_id_catalog()
        self.assertTrue(any(item.rule == "SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG" for item in findings))
        self.assertGreater(len(findings), 0)


if __name__ == "__main__":
    unittest.main()
