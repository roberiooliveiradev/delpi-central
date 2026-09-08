#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_fastapi_authz.py")
spec = importlib.util.spec_from_file_location("audit_fastapi_authz", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class FastApiAuthzGuardrailsTest(unittest.TestCase):
    def test_empty_local_path_is_composed_with_router_prefix(self):
        source = '''
from fastapi import APIRouter
router = APIRouter(prefix="/items")

@router.post("", operation_id="create_item")
def create_item(body):
    return service.create(body)
'''
        routes = mod.route_contracts(source)
        self.assertEqual([(route.method, route.path) for route in routes], [("post", "/items")])

    def test_write_with_permission_decorator_is_allowed(self):
        source = '''
from fastapi import APIRouter
router = APIRouter(prefix="/items")

@router.post("", operation_id="create_item")
@require_permission("items.create")
def create_item(body):
    return service.create(body)
'''
        findings = mod.scan_fastapi_authz_source("orders-api/app/routes.py", source, {5})
        self.assertEqual(findings, [])

    def test_write_with_require_auth_is_explicitly_authenticated(self):
        source = '''
from fastapi import APIRouter
router = APIRouter(prefix="/me")

@router.patch("/preferences", operation_id="update_preferences")
@require_auth()
def update_preferences(body):
    return service.update(body)
'''
        findings = mod.scan_fastapi_authz_source("orders-api/app/routes.py", source, {5})
        self.assertEqual(findings, [])

    def test_write_without_access_evidence_is_blocked(self):
        source = '''
from fastapi import APIRouter
router = APIRouter(prefix="/items")

@router.delete("/{item_id}", operation_id="delete_item")
def delete_item(item_id: str):
    return service.delete(item_id)
'''
        findings = mod.scan_fastapi_authz_source("orders-api/app/routes.py", source, {5})
        self.assertEqual([item.rule for item in findings], ["FASTAPI_WRITE_AUTHZ_EVIDENCE_REQUIRED"])

    def test_get_without_route_authz_is_out_of_scope_for_now(self):
        source = '''
from fastapi import APIRouter
router = APIRouter(prefix="/items")

@router.get("", operation_id="list_items")
def list_items():
    return service.list()
'''
        findings = mod.scan_fastapi_authz_source("orders-api/app/routes.py", source, {5})
        self.assertEqual(findings, [])

    def test_application_user_handoff_is_accepted(self):
        source = '''
from fastapi import APIRouter, Request
router = APIRouter(prefix="/members")

@router.post("", operation_id="create_member")
def create_member(request: Request, body):
    return service.create_member(request.state.user, body)
'''
        findings = mod.scan_fastapi_authz_source("comite-etica-conduta-api/cec_app/routes.py", source, {5})
        self.assertEqual(findings, [])

    def test_user_alias_handoff_is_accepted(self):
        source = '''
from fastapi import APIRouter, Request
router = APIRouter(prefix="/members")

@router.patch("/{member_id}", operation_id="update_member")
def update_member(request: Request, member_id: str, body):
    actor = request.state.user
    return service.update_member(actor, member_id, body)
'''
        findings = mod.scan_fastapi_authz_source("comite-etica-conduta-api/cec_app/routes.py", source, {5, 7})
        self.assertEqual(findings, [])

    def test_resolved_user_handoff_is_accepted(self):
        source = '''
from fastapi import APIRouter, Request
router = APIRouter(prefix="/forms")

@router.post("", operation_id="create_form")
def create_form(request: Request, body):
    user = resolve_user(request)
    return service.create(user, body)
'''
        findings = mod.scan_fastapi_authz_source("customer-experience-api/cx_app/routes.py", source, {5})
        self.assertEqual(findings, [])

    def test_manual_permission_guard_call_is_accepted(self):
        source = '''
from fastapi import APIRouter
router = APIRouter(prefix="/reports")

@router.post("/run", operation_id="run_report")
def run_report(body):
    denied = _permission_denied_if_missing(REPORTS_WRITE_PERMISSIONS)
    if denied:
        return denied
    return service.run(body)
'''
        findings = mod.scan_fastapi_authz_source("api-delpi/app/routes.py", source, {5})
        self.assertEqual(findings, [])

    def test_public_write_allowed_only_when_middleware_contract_matches(self):
        source = '''
from fastapi import APIRouter
router = APIRouter(prefix="/public/forms")

@router.post("/{token}", operation_id="submit_public_form")
def submit(token: str, body):
    return service.submit(token, body)
'''
        findings = mod.scan_fastapi_authz_source(
            "customer-experience-api/cx_app/routes.py",
            source,
            {5},
            public_prefixes={"/public/"},
            public_exacts={"/health"},
            generic_public=True,
        )
        self.assertEqual(findings, [])

    def test_public_looking_write_not_released_by_middleware_is_blocked_as_drift(self):
        source = '''
from fastapi import APIRouter
router = APIRouter(prefix="/public/admin")

@router.post("", operation_id="public_admin_write")
def write(body):
    return service.write(body)
'''
        findings = mod.scan_fastapi_authz_source(
            "orders-api/app/routes.py",
            source,
            {5},
            public_prefixes={"/public/forms/"},
            public_exacts={"/health"},
            generic_public=False,
        )
        self.assertEqual([item.rule for item in findings], ["FASTAPI_PUBLIC_ROUTE_AUTH_DRIFT"])

    def test_public_contract_extracts_constants_and_generic_startswith(self):
        source = '''
PUBLIC_EXACT = frozenset({"/health", "/public/status"})
PUBLIC_PREFIXES = ("/public/forms/",)

def _is_public(path: str) -> bool:
    return path.startswith("/public/")
'''
        prefixes, exacts, generic = mod.extract_public_contract(source)
        self.assertIn("/public/forms/", prefixes)
        self.assertIn("/public/status", exacts)
        self.assertTrue(generic)

    def test_health_is_public_by_default(self):
        self.assertTrue(mod.public_contract_allows("/health", set(), {"/health"}, False))

    def test_non_api_source_is_ignored(self):
        source = '@router.post("/x")\ndef x():\n    pass\n'
        findings = mod.scan_fastapi_authz_source("scripts/example.py", source, {1})
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
