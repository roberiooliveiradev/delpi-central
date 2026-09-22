"""F3 residual: write confirmation uniform + TV handoff intact."""

from __future__ import annotations

import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_APP = _ROOT / "app"
_INVENTORY = (
    _ROOT
    / "tests/fixtures/intelligence_baseline/f3_write_confirmation_authority_inventory.json"
)
_CONFIRM = _APP / "domain/services/chat_write_confirmation_service.py"
_PROVIDER_ROUTES = _APP / "interfaces/http/routes/chat/agent_provider_routes.py"
_COMPOSER = _APP / "composition/tool_composer.py"


def test_f3_inventory_core_items_closed():
    payload = json.loads(_INVENTORY.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in payload["items"]}
    assert by_id["selection_execution_confirm_divergence"]["postStatus"] == "RETIRED"
    assert by_id["allow_write_create_default"]["postStatus"] == "RETIRED"
    assert by_id["tv_vista_handoff"]["postStatus"] == "CANONICAL"


def test_f3_should_block_matches_bridge_rule():
    source = _CONFIRM.read_text(encoding="utf-8")
    match = re.search(
        r"def should_block_execution\(.*?\n(?:.*?\n)*?        return True\n",
        source,
    )
    assert match, "should_block_execution not found"
    body = match.group(0)
    assert "action_requires_confirmation" in body
    assert "user_confirmed" in body
    # Legacy split (write markers OR sensitivity subset) must stay retired.
    assert "message_requests_write" not in body


def test_f3_sql_post_does_not_require_write_confirmation():
    from app.domain.services.chat_write_confirmation_service import (
        ChatWriteConfirmationService,
    )

    sql_action = {
        "method": "POST",
        "path": "/data/sql",
        "sensitivity": "sql",
        "summary": "Executar SQL",
    }
    assert not ChatWriteConfirmationService.action_requires_confirmation(sql_action)
    assert not ChatWriteConfirmationService.should_block_execution(
        message="rode select top 10",
        action=sql_action,
    )


def test_f3_write_without_confirm_blocks_uniformly():
    from app.domain.services.chat_write_confirmation_service import (
        ChatWriteConfirmationService,
    )

    action = {
        "method": "POST",
        "path": "/quality/action-plans",
        "sensitivity": "write",
        "summary": "Criar plano",
    }
    # Positive — block without confirm (even without write-intent markers).
    assert ChatWriteConfirmationService.should_block_execution(
        message="olá",
        action=action,
    )
    # Sibling — confirm unlocks.
    assert not ChatWriteConfirmationService.should_block_execution(
        message="confirmo",
        action=action,
    )
    # Negative — read stays free.
    assert not ChatWriteConfirmationService.should_block_execution(
        message="olá",
        action={"method": "GET", "path": "/products/1/stock", "sensitivity": "read"},
    )


def test_f3_explicit_requires_confirmation_flag():
    from app.domain.services.chat_write_confirmation_service import (
        ChatWriteConfirmationService,
    )

    action = {
        "method": "GET",
        "path": "/special",
        "sensitivity": "read",
        "requiresConfirmation": True,
    }
    assert ChatWriteConfirmationService.action_requires_confirmation(action)
    assert ChatWriteConfirmationService.should_block_execution(
        message="abre especial",
        action=action,
    )


def test_f3_allow_write_create_default_false():
    source = _PROVIDER_ROUTES.read_text(encoding="utf-8")
    # First create-path default (not the upsert/update False already present).
    assert 'payload.get("allowWrite", False)' in source
    assert 'payload.get("allowWrite", True)' not in source


def test_f3_negative_no_tv_copilot_mutation_tool_in_composer():
    source = _COMPOSER.read_text(encoding="utf-8")
    assert "tv-dashboard-copilot" not in source
    assert "TvDashboardCopilot" not in source
