#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("audit_openapi_contracts.py")
spec = importlib.util.spec_from_file_location("audit_openapi_contracts", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def spec_with_operation(operation: dict, version: str = "1.0.0") -> dict:
    return {
        "openapi": "3.0.3",
        "info": {"title": "X", "version": version},
        "paths": {"/items": {"get": {"operationId": "list_items", **operation}}},
    }


class OpenApiContractGuardrailsTest(unittest.TestCase):
    def test_openapi_operation_id_is_required(self):
        document = {
            "openapi": "3.0.3",
            "info": {"title": "X", "version": "1.0.0"},
            "paths": {"/items": {"get": {"responses": {"200": {"description": "ok"}}}}},
        }
        findings = mod.validate_openapi_document("x/openapi.json", document)
        self.assertEqual([item.rule for item in findings], ["OPENAPI_OPERATION_ID_REQUIRED"])

    def test_openapi_duplicate_operation_id_is_blocked(self):
        document = {
            "openapi": "3.0.3",
            "info": {"title": "X", "version": "1.0.0"},
            "paths": {
                "/a": {"get": {"operationId": "get_item"}},
                "/b": {"get": {"operationId": "get_item"}},
            },
        }
        findings = mod.validate_openapi_document("x/openapi.json", document)
        self.assertEqual([item.rule for item in findings], ["OPENAPI_OPERATION_ID_DUPLICATE"])

    def test_breaking_operation_removal_requires_classification(self):
        base = {
            "openapi": "3.0.3",
            "info": {"title": "X", "version": "1.0.0"},
            "paths": {"/items": {"get": {"operationId": "list_items"}}},
        }
        current = {
            "openapi": "3.0.3",
            "info": {"title": "X", "version": "1.1.0"},
            "paths": {},
        }
        findings = mod.validate_openapi_document("x/openapi.json", current, base)
        self.assertEqual([item.rule for item in findings], ["OPENAPI_BREAKING_UNCLASSIFIED"])

    def test_breaking_change_with_version_bound_metadata_is_allowed(self):
        base = {
            "openapi": "3.0.3",
            "info": {"title": "X", "version": "1.0.0"},
            "paths": {"/items": {"get": {"operationId": "list_items"}}},
        }
        current = {
            "openapi": "3.0.3",
            "info": {
                "title": "X",
                "version": "2.0.0",
                "x-delpi-contract-change": "BREAKING",
                "x-delpi-contract-change-from": "1.0.0",
                "x-delpi-contract-change-reason": "Contrato substituído por uma nova versão pública.",
            },
            "paths": {},
        }
        findings = mod.validate_openapi_document("x/openapi.json", current, base)
        self.assertEqual(findings, [])

    def test_stale_breaking_metadata_does_not_authorize_future_break(self):
        base = {
            "openapi": "3.0.3",
            "info": {"title": "X", "version": "2.0.0"},
            "paths": {"/items": {"get": {"operationId": "list_items"}}},
        }
        current = {
            "openapi": "3.0.3",
            "info": {
                "title": "X",
                "version": "3.0.0",
                "x-delpi-contract-change": "BREAKING",
                "x-delpi-contract-change-from": "1.0.0",
                "x-delpi-contract-change-reason": "Razão antiga.",
            },
            "paths": {},
        }
        findings = mod.validate_openapi_document("x/openapi.json", current, base)
        self.assertEqual([item.rule for item in findings], ["OPENAPI_BREAKING_UNCLASSIFIED"])

    def test_required_query_parameter_added_is_breaking(self):
        base = spec_with_operation({"parameters": []})
        current = spec_with_operation(
            {
                "parameters": [
                    {"name": "branch", "in": "query", "required": True, "schema": {"type": "string"}}
                ]
            },
            version="1.1.0",
        )
        findings = mod.validate_openapi_document("x/openapi.json", current, base)
        self.assertEqual([item.rule for item in findings], ["OPENAPI_BREAKING_UNCLASSIFIED"])
        self.assertIn("parâmetro obrigatório adicionado", findings[0].message)

    def test_optional_query_parameter_added_is_additive(self):
        base = spec_with_operation({"parameters": []})
        current = spec_with_operation(
            {
                "parameters": [
                    {"name": "search", "in": "query", "required": False, "schema": {"type": "string"}}
                ]
            },
            version="1.1.0",
        )
        findings = mod.validate_openapi_document("x/openapi.json", current, base)
        self.assertEqual(findings, [])

    def test_required_parameter_local_ref_is_resolved(self):
        base = spec_with_operation({"parameters": []})
        current = spec_with_operation(
            {"parameters": [{"$ref": "#/components/parameters/Branch"}]},
            version="1.1.0",
        )
        current["components"] = {
            "parameters": {
                "Branch": {
                    "name": "branch",
                    "in": "query",
                    "required": True,
                    "schema": {"type": "string"},
                }
            }
        }
        findings = mod.validate_openapi_document("x/openapi.json", current, base)
        self.assertEqual([item.rule for item in findings], ["OPENAPI_BREAKING_UNCLASSIFIED"])

    def test_request_body_becoming_required_is_breaking(self):
        base = spec_with_operation(
            {"requestBody": {"required": False, "content": {"application/json": {"schema": {"type": "object"}}}}}
        )
        current = spec_with_operation(
            {"requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object"}}}}},
            version="1.1.0",
        )
        findings = mod.validate_openapi_document("x/openapi.json", current, base)
        self.assertEqual([item.rule for item in findings], ["OPENAPI_BREAKING_UNCLASSIFIED"])
        self.assertIn("requestBody passou a obrigatório", findings[0].message)

    def test_documented_success_response_removal_is_breaking(self):
        base = spec_with_operation({"responses": {"200": {"description": "ok"}, "404": {"description": "not found"}}})
        current = spec_with_operation(
            {"responses": {"204": {"description": "no content"}, "404": {"description": "not found"}}},
            version="1.1.0",
        )
        findings = mod.validate_openapi_document("x/openapi.json", current, base)
        self.assertEqual([item.rule for item in findings], ["OPENAPI_BREAKING_UNCLASSIFIED"])
        self.assertIn("resposta 2xx removida", findings[0].message)

    def test_fastapi_changed_route_requires_literal_operation_id(self):
        source = '''\nfrom fastapi import APIRouter\nrouter = APIRouter()\n\n@router.get("/items")\nasync def list_items():\n    return []\n'''
        findings = mod.scan_changed_fastapi_file("orders-api/app/routes.py", source, {5})
        self.assertEqual([item.rule for item in findings], ["FASTAPI_OPERATION_ID_REQUIRED"])

    def test_fastapi_empty_local_path_requires_operation_id(self):
        source = '''\nfrom fastapi import APIRouter\nrouter = APIRouter(prefix="/items")\n\n@router.post("")\nasync def create_item():\n    return {}\n'''
        findings = mod.scan_changed_fastapi_file("orders-api/app/routes.py", source, {5})
        self.assertEqual([item.rule for item in findings], ["FASTAPI_OPERATION_ID_REQUIRED"])

    def test_fastapi_explicit_operation_id_is_allowed(self):
        source = '''\nfrom fastapi import APIRouter\nrouter = APIRouter()\n\n@router.get(\n    "/items",\n    operation_id="list_items",\n)\nasync def list_items():\n    return []\n'''
        findings = mod.scan_changed_fastapi_file("orders-api/app/routes.py", source, {7})
        self.assertEqual(findings, [])

    def test_fastapi_starred_local_agent_route_constant_is_allowed(self):
        source = '''\nfrom fastapi import APIRouter\nrouter = APIRouter()\n\nMETA = agent_route(\n    summary="List items",\n    operation_id="list_items",\n)\n\n@router.get("/items", **META)\nasync def list_items():\n    return []\n'''
        findings = mod.scan_changed_fastapi_file("orders-api/app/routes.py", source, {10})
        self.assertEqual(findings, [])

    def test_fastapi_starred_local_dict_constant_is_allowed(self):
        source = '''\nfrom fastapi import APIRouter\nrouter = APIRouter()\n\nMETA = {"summary": "List items", "operation_id": "list_items"}\n\n@router.get("/items", **META)\nasync def list_items():\n    return []\n'''
        findings = mod.scan_changed_fastapi_file("orders-api/app/routes.py", source, {7})
        self.assertEqual(findings, [])

    def test_fastapi_starred_imported_constant_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            meta_dir = root / "orders-api" / "app" / "interface" / "http"
            meta_dir.mkdir(parents=True)
            (meta_dir / "openapi_agent_metadata.py").write_text(
                'SI_ITEMS = agent_route(\n'
                '    summary="List items",\n'
                '    operation_id="list_items",\n'
                ')\n',
                encoding="utf-8",
            )
            source = '''\nfrom fastapi import APIRouter\nfrom app.interface.http.openapi_agent_metadata import SI_ITEMS\nrouter = APIRouter()\n\n@router.get("/items", **SI_ITEMS)\nasync def list_items():\n    return []\n'''
            with patch.object(mod, "ROOT", root):
                findings = mod.scan_changed_fastapi_file(
                    "orders-api/app/routes.py", source, {6}
                )
        self.assertEqual(findings, [])

    def test_fastapi_starred_unresolvable_name_still_requires_operation_id(self):
        source = '''\nfrom fastapi import APIRouter\nrouter = APIRouter()\n\n@router.get("/items", **DYNAMIC_META)\nasync def list_items():\n    return []\n'''
        findings = mod.scan_changed_fastapi_file("orders-api/app/routes.py", source, {5})
        self.assertEqual(
            [item.rule for item in findings], ["FASTAPI_OPERATION_ID_REQUIRED"]
        )

    def test_fastapi_starred_dynamic_call_metadata_still_requires_operation_id(self):
        source = '''\nfrom fastapi import APIRouter\nrouter = APIRouter()\n\nMETA = build_metadata()\n\n@router.get("/items", **META)\nasync def list_items():\n    return []\n'''
        findings = mod.scan_changed_fastapi_file("orders-api/app/routes.py", source, {7})
        self.assertEqual(
            [item.rule for item in findings], ["FASTAPI_OPERATION_ID_REQUIRED"]
        )

    def test_fastapi_duplicate_operation_id_in_same_api_is_blocked_when_new_route_touched(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            api_dir = root / "orders-api" / "app"
            api_dir.mkdir(parents=True)
            (api_dir / "a.py").write_text(
                '@router.get("/a", operation_id="get_item")\ndef a():\n    pass\n',
                encoding="utf-8",
            )
            (api_dir / "b.py").write_text(
                '@router.get("/b", operation_id="get_item")\ndef b():\n    pass\n',
                encoding="utf-8",
            )
            with patch.object(mod, "ROOT", root):
                findings = mod.scan_fastapi_duplicates({"orders-api/app/b.py": {1}})
        self.assertEqual([item.rule for item in findings], ["FASTAPI_OPERATION_ID_DUPLICATE"])

    def test_flask_blueprint_route_is_not_checked_as_fastapi(self):
        source = '''\nfrom flask import Blueprint\nsupplier_bp = Blueprint("supplier", __name__)\n\n@supplier_bp.get("/analytics/supplier-performance")\ndef supplier_performance():\n    return {}\n'''
        findings = mod.scan_changed_fastapi_file(
            "supplies-api/app/interfaces/http/routes/supplier_performance_routes.py",
            source,
            {5},
        )
        self.assertEqual(findings, [])

    def test_flask_aliased_blueprint_and_flask_module_are_skipped(self):
        source = '''\nimport flask as web\nfrom flask import Blueprint as BP\napp = web.Flask(__name__)\nbp = BP("id", __name__)\n\n@app.get("/app")\ndef app_get():\n    return {}\n\n@bp.post("/submit")\ndef bp_post():\n    return {}\n'''
        self.assertEqual(mod.fastapi_routes_from_source(source), [])

    def test_mixed_flask_and_fastapi_requires_literal_operation_id(self):
        source = '''\nfrom flask import Blueprint\nfrom fastapi import APIRouter\nbp = Blueprint("id", __name__)\nrouter = APIRouter()\n\n@bp.get("/flask")\ndef flask_route():\n    return {}\n\n@router.get("/fastapi")\ndef fastapi_route():\n    return {}\n'''
        findings = mod.scan_changed_fastapi_file(
            "supplies-api/app/routes.py", source, {11}
        )
        self.assertEqual(
            [finding.rule for finding in findings],
            ["FASTAPI_OPERATION_ID_REQUIRED"],
        )
        self.assertIn("/fastapi", findings[0].message)

    def test_unidentified_router_is_not_implicitly_exempt(self):
        source = '''\n@unknown.get("/items")\ndef list_items():\n    return []\n'''
        findings = mod.scan_changed_fastapi_file(
            "orders-api/app/routes.py", source, {2}
        )
        self.assertEqual(
            [finding.rule for finding in findings],
            ["FASTAPI_OPERATION_ID_REQUIRED"],
        )

    def test_non_api_python_is_ignored(self):
        source = '@router.get("/items")\ndef x():\n    pass\n'
        findings = mod.scan_changed_fastapi_file("scripts/example.py", source, {1})
        self.assertEqual(findings, [])

    def test_json_openapi_detection(self):
        payload = json.dumps({"openapi": "3.0.3", "paths": {}})
        document = mod.load_document("spec.json", payload)
        self.assertTrue(mod.is_openapi_document(document))


if __name__ == "__main__":
    unittest.main()
