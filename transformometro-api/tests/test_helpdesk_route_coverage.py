"""R4.1 — Helpdesk BFF route coverage ledger (drift detector).

Every HTTP route exposed by the Helpdesk BFF must appear exactly once in
``ROUTE_LEDGER`` with an explicit classification and a TÉO mapping (or a
documented reason it is not agent-facing). A new BFF route silently added
without a coverage decision fails this test — UNCLASSIFIED must stay 0.

Route coverage != route proxy: EXPOSED_* rows map to bounded semantic
surfaces (``helpdesk_read`` / ``prepare_helpdesk_change`` →
``commit_proposal``), never to method+path tools.

The ledger is read from the sibling ``helpdesk-api`` app source — the BFF
owns the Helpdesk contract; this test only asserts the consumer-side
coverage decision stays complete.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BFF_APP_DIR = _REPO_ROOT / "helpdesk-api" / "helpdesk_app"

_BFF_SOURCES = (
    *_BFF_APP_DIR.glob("interface/http/*.py"),
    _BFF_APP_DIR / "main.py",  # app-level routes (e.g. GET /health)
)

# The ledger only drifts when the BFF source is co-located (dev monorepo
# checkout / CI). Inside the transformometro-api container the sibling app
# is not mounted — skip there rather than fake coverage.
pytestmark = pytest.mark.skipif(
    not _BFF_APP_DIR.is_dir(),
    reason="helpdesk-api source not co-located (container run)",
)

_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

_CLASSIFICATIONS = {
    "EXPOSED_READ",
    "EXPOSED_WRITE",
    "COVERED_BY_EXISTING_PROJECTION",
    "UI_ONLY",
    "BROWSER_FLOW",
    "INFRA_ONLY",
    "PLATFORM_BLOCKED_BINARY",
    "NOT_AGENT_CAPABILITY",
    "TO_IMPLEMENT",
    "TO_INVENTORY",
}

# (METHOD, path) → (classification, TÉO semantic mapping)
ROUTE_LEDGER: dict[tuple[str, str], tuple[str, str]] = {
    # --- OAuth / session ----------------------------------------------------
    ("GET", "/auth/glpi/start"): (
        "BROWSER_FLOW",
        "interactive OAuth — TÉO may surface authorize_url only",
    ),
    ("GET", "/auth/glpi/callback"): (
        "BROWSER_FLOW",
        "OAuth callback — browser only, never an agent ACT",
    ),
    ("GET", "/auth/glpi/session"): (
        "EXPOSED_READ",
        "helpdesk_read(action=session)",
    ),
    ("DELETE", "/auth/glpi/session"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=unlink_glpi_session)",
    ),
    # --- Catalogs / session-scoped reads ------------------------------------
    ("GET", "/ticket-categories"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=categories)",
    ),
    ("GET", "/request-types"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=request_types)",
    ),
    ("GET", "/followup-templates"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=followup_templates)",
    ),
    ("GET", "/solution-types"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=solution_types)",
    ),
    ("GET", "/solution-templates"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=solution_templates)",
    ),
    ("GET", "/task-categories"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=task_categories)",
    ),
    ("GET", "/task-templates"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=task_templates)",
    ),
    ("GET", "/task-statuses"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=task_statuses)",
    ),
    ("GET", "/groups"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=groups)",
    ),
    ("GET", "/validation-templates"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=validation_templates)",
    ),
    ("GET", "/approval-steps"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=approval_steps)",
    ),
    ("GET", "/urgencies"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=urgencies)",
    ),
    ("GET", "/users"): (
        "EXPOSED_READ",
        "helpdesk_read(action=catalog, catalog_kind=users)",
    ),
    ("GET", "/session/capabilities"): (
        "EXPOSED_READ",
        "helpdesk_read(action=capabilities)",
    ),
    # --- Tickets -------------------------------------------------------------
    ("GET", "/tickets"): (
        "EXPOSED_READ",
        "helpdesk_read(action=tickets)",
    ),
    ("GET", "/tickets/{ticket_id}"): (
        "EXPOSED_READ",
        "helpdesk_read(action=ticket)",
    ),
    # --- Attachments (binary transport) --------------------------------------
    ("GET", "/tickets/{ticket_id}/attachments/{document_id}"): (
        "PLATFORM_BLOCKED_BINARY",
        "no canonical binary/file transport on MCP/GPT — metadata only "
        "via helpdesk_read(action=ticket).attachments",
    ),
    ("POST", "/tickets/{ticket_id}/attachments"): (
        "PLATFORM_BLOCKED_BINARY",
        "multipart upload — no governed binary transport; never base64",
    ),
    # --- Governed writes ------------------------------------------------------
    ("POST", "/tickets"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=create_ticket)",
    ),
    ("PUT", "/tickets/{ticket_id}/assignee"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=set_assignee)",
    ),
    ("POST", "/tickets/{ticket_id}/followups"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=add_followup)",
    ),
    ("POST", "/tickets/{ticket_id}/solutions"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=add_solution)",
    ),
    ("POST", "/tickets/{ticket_id}/tasks"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=create_task)",
    ),
    ("POST", "/tickets/{ticket_id}/validations"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=request_validation)",
    ),
    ("POST", "/tickets/{ticket_id}/solution/accept"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=accept_solution)",
    ),
    ("POST", "/tickets/{ticket_id}/solution/reject"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=reject_solution)",
    ),
    ("GET", "/tickets/{ticket_id}/satisfaction"): (
        "COVERED_BY_EXISTING_PROJECTION",
        "satisfaction + satisfaction_comment + can_submit_satisfaction "
        "already projected by helpdesk_read(action=ticket)",
    ),
    ("PUT", "/tickets/{ticket_id}/satisfaction"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=submit_satisfaction)",
    ),
    ("POST", "/tickets/{ticket_id}/validations/{validation_id}/accept"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=accept_validation)",
    ),
    ("POST", "/tickets/{ticket_id}/validations/{validation_id}/reject"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=reject_validation)",
    ),
    ("DELETE", "/tickets/{ticket_id}"): (
        "EXPOSED_WRITE",
        "prepare_helpdesk_change(action=delete_ticket) — GLPI trash",
    ),
    # --- Person profile / infra ------------------------------------------------
    ("GET", "/person-profiles/{user_id}/photo"): (
        "UI_ONLY",
        "avatar image for Portal UI — binary, not an agent capability",
    ),
    ("GET", "/health"): (
        "INFRA_ONLY",
        "container health probe — observability, not a business capability",
    ),
}


def _bff_routes() -> set[tuple[str, str]]:
    """Extract (METHOD, path) from every @router.<method> decorator in the
    BFF http interface — source-level, no app import required."""
    routes: set[tuple[str, str]] = set()
    for source in _BFF_SOURCES:
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not (
                    isinstance(dec, ast.Call)
                    and isinstance(dec.func, ast.Attribute)
                ):
                    continue
                method = dec.func.attr.upper()
                if method not in _METHODS:
                    continue
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    routes.add((method, str(dec.args[0].value)))
    return routes


def test_bff_route_source_inventory_matches_runtime():
    """Sanity: the source scan finds the expected route surface."""
    routes = _bff_routes()
    assert len(routes) == 37  # 36 baseline + DELETE /tickets/{id}
    assert ("DELETE", "/tickets/{ticket_id}") in routes


def test_every_bff_route_is_classified():
    """UNCLASSIFIED ROUTES = 0 — the non-negotiable R4.1 invariant."""
    unclassified = _bff_routes() - set(ROUTE_LEDGER)
    assert not unclassified, f"unclassified BFF routes: {sorted(unclassified)}"


def test_no_stale_ledger_entries():
    """A ledger entry for a route that no longer exists is also drift."""
    stale = set(ROUTE_LEDGER) - _bff_routes()
    assert not stale, f"stale ledger entries: {sorted(stale)}"


def test_ledger_uses_only_allowed_classifications():
    for route, (classification, _mapping) in ROUTE_LEDGER.items():
        assert classification in _CLASSIFICATIONS, (
            f"{route}: invalid classification {classification!r}"
        )


def test_no_orphan_business_write_route():
    """Every non-binary, non-browser, non-infra write route maps to the
    governed semantic surface — no orphaned business route."""
    exempt = {
        "BROWSER_FLOW",
        "UI_ONLY",
        "INFRA_ONLY",
        "PLATFORM_BLOCKED_BINARY",
        "NOT_AGENT_CAPABILITY",
    }
    writes = {
        route
        for route in _bff_routes()
        if route[0] in {"POST", "PUT", "PATCH", "DELETE"}
    }
    orphans = {
        route
        for route in writes
        if ROUTE_LEDGER.get(route, ("", ""))[0] not in {"EXPOSED_WRITE", *exempt}
    }
    assert not orphans, f"orphan business write routes: {sorted(orphans)}"


def test_no_orphan_business_read_route():
    exempt = {
        "BROWSER_FLOW",
        "UI_ONLY",
        "INFRA_ONLY",
        "PLATFORM_BLOCKED_BINARY",
        "NOT_AGENT_CAPABILITY",
    }
    reads = {route for route in _bff_routes() if route[0] == "GET"}
    orphans = {
        route
        for route in reads
        if ROUTE_LEDGER.get(route, ("", ""))[0]
        not in {"EXPOSED_READ", "COVERED_BY_EXISTING_PROJECTION", *exempt}
    }
    assert not orphans, f"orphan business read routes: {sorted(orphans)}"
