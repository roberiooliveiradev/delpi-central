"""CLARA — catálogo LNF (F7) no clara-semantic-v1."""

from __future__ import annotations

from controllership_finance_app.interface.mcp import semantic_bridge as sb
from controllership_finance_app.application.clara.invoice_posting_capabilities import (
    build_lnf_capability_table,
)
from controllership_finance_app.application.clara.governed_writes import _require


def test_tools_list_still_six():
    from controllership_finance_app.interface.mcp.constants import MCP_TOOL_NAMES

    assert len(MCP_TOOL_NAMES) == 6


def test_lnf_read_actions_registered():
    expected = {
        ("invoice_posting", "list"),
        ("invoice_posting", "get"),
        ("invoice_posting", "purchase_orders"),
        ("purchase_order", "open"),
        ("received_invoice", "list"),
        ("received_invoice", "detail"),
        ("unmapped_product", "list"),
        ("supplier", "search"),
    }
    assert expected.issubset(set(sb.READ_ACTIONS))


def test_lnf_analyze_registered():
    assert "invoice_posting.backlog" in sb.ANALYZE_ACTIONS
    spec = sb.ANALYZE_ACTIONS["invoice_posting.backlog"]
    assert spec["entity"] == "invoice_posting"
    assert spec["gate"] == "lnf_read"


def test_lnf_governed_capabilities():
    table = build_lnf_capability_table(require=_require)
    assert "invoice_posting.comment" in table
    assert table["invoice_posting.comment"]["direct"] is True
    assert "reconciliation.refresh" in table
    assert table["reconciliation.refresh"]["direct"] is True
    assert table["invoice_posting.create"]["direct"] is False
    assert table["invoice_posting.cancel"]["destructive"] is True
    assert "justification" in table["invoice_posting.post_manual"]["required_params"]
    assert "justification" in table["invoice_posting.cancel"]["required_params"]


def test_catalog_hides_lnf_without_flags():
    catalog = sb._semantic_catalog(
        {
            "is_manage": False,
            "is_dre": False,
            "lnf_read": False,
            "lnf_create": False,
            "lnf_write": False,
            "lnf_process": False,
            "lnf_manage": False,
            "lnf_review_unmapped": False,
        }
    )
    read_keys = {(e["entity"], e["action"]) for e in catalog["actions"]["read"]}
    assert ("invoice_posting", "list") not in read_keys
    analyze = {e["action"] for e in catalog["actions"]["analyze"]}
    assert "backlog" not in analyze
    gov = {e["capability"] for e in catalog["actions"]["governed"]}
    assert "invoice_posting.comment" not in gov


def test_catalog_shows_lnf_reads_with_lnf_read():
    catalog = sb._semantic_catalog(
        {
            "is_manage": False,
            "is_dre": False,
            "lnf_read": True,
            "lnf_create": False,
            "lnf_write": False,
            "lnf_process": False,
            "lnf_manage": False,
            "lnf_review_unmapped": False,
        }
    )
    read_keys = {(e["entity"], e["action"]) for e in catalog["actions"]["read"]}
    assert ("invoice_posting", "list") in read_keys
    assert ("invoice_posting", "get") in read_keys
    assert ("purchase_order", "open") not in read_keys  # create gate
    analyze = {(e["entity"], e["action"]) for e in catalog["actions"]["analyze"]}
    assert ("invoice_posting", "backlog") in analyze
    gov = {e["capability"] for e in catalog["actions"]["governed"]}
    assert "reconciliation.refresh" in gov
    assert "invoice_posting.create" not in gov


def test_catalog_create_and_process_gates():
    catalog = sb._semantic_catalog(
        {
            "lnf_read": True,
            "lnf_create": True,
            "lnf_write": True,
            "lnf_process": True,
            "lnf_manage": False,
            "lnf_review_unmapped": True,
        }
    )
    read_keys = {(e["entity"], e["action"]) for e in catalog["actions"]["read"]}
    assert ("purchase_order", "open") in read_keys
    assert ("unmapped_product", "list") in read_keys
    gov = {e["capability"] for e in catalog["actions"]["governed"]}
    assert "invoice_posting.create" in gov
    assert "invoice_posting.start" in gov
    assert "invoice_posting.cancel" in gov
    assert "reconciliation.run" not in gov  # manage only
