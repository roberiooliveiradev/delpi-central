"""DAVI live action-index bootstrap — real-startup regression.

Reproduces the productive lifecycle defect where the live OpenAPI refresh ran
inside ``create_mcp_server()`` at import time, when ``app.main.app`` did not
yet exist: the refresh silently failed and the action index degraded to the
static baseline (70 executable, both governed SEMANTIC_READ_POST operations
closed). The authoritative seed now runs in ``_app_lifespan`` at FastAPI
startup, when the route table is complete (72 executable).

The bootstrap assertions run in a subprocess with a fresh action index so no
module state from other tests can mask the startup-order regression. The test
never calls ``seed_actions_from_openapi``/``set_actions_for_tests`` itself —
the PASS condition comes only from entering the real application lifespan.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from app.application.external_capabilities.dynamic_information.action_index import (
    get_technical_actions,
    reset_action_index_for_tests,
)
from app.application.external_capabilities.dynamic_information.constants import (
    STATUS_DAVI_ELIGIBLE_READ,
    STATUS_NEEDS_BOUNDED_EXECUTION,
)

_API_ROOT = Path(__file__).resolve().parents[1]
_ACTOR = "11111111-1111-4111-8111-111111111111"

_CHILD_SCRIPT = r"""
import asyncio
import json
import os
import sys
from unittest.mock import MagicMock

sys.modules.setdefault("pyodbc", MagicMock())
os.environ.setdefault("OPENAPI_CONSUMER_NOTIFY_ON_STARTUP", "false")
os.environ.setdefault("RUN_PLUGINS_MIGRATIONS_ON_STARTUP", "false")
os.environ.setdefault("DAVI_CANDIDATE_HMAC_SECRET", "bootstrap-child-hmac")

from app.application.external_capabilities.dynamic_information.action_index import (
    get_technical_actions,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.main import app


def _snapshot():
    actions = get_technical_actions()
    by_id = {a.operation_id: a for a in actions}
    physical = by_id["list_product_physical_locations"]
    blocks = by_id["list_product_inventory_blocks"]
    return {
        "executable": sum(1 for a in actions if a.executable),
        "physical_locations": {
            "davi_status": physical.davi_status,
            "executable": bool(physical.executable),
        },
        "inventory_blocks": {
            "davi_status": blocks.davi_status,
            "executable": bool(blocks.executable),
        },
    }


async def _main():
    out = {"pre_startup": _snapshot()}
    async with app.router.lifespan_context(app):
        out["post_startup"] = _snapshot()
        for key, query, expected in (
            (
                "physical_query",
                "local físico do produto 10090043 na filial 01",
                "list_product_physical_locations",
            ),
            (
                "blocks_query",
                "bloqueio de inventário do produto 10090043",
                "list_product_inventory_blocks",
            ),
        ):
            result = discover_delpi_information(
                query=query,
                actor_id="11111111-1111-4111-8111-111111111111",
            )
            ids = [c["action_id"] for c in result["candidates"]]
            out[key] = {
                "eligible_action_count": result["eligible_action_count"],
                "expected_in_candidates": expected in ids,
            }
    print("RESULT::" + json.dumps(out))


asyncio.run(_main())
"""


def _run_child() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_API_ROOT)
    proc = subprocess.run(
        [sys.executable, "-c", _CHILD_SCRIPT],
        cwd=str(_API_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stderr[-3000:]
    line = next(
        ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT::")
    )
    return json.loads(line.removeprefix("RESULT::"))


def test_real_startup_seeds_live_action_index() -> None:
    """Fresh process → real lifespan → 72 executable + POSTs eligible.

    Fails on the pre-fix source with the actual defect: the import-time
    refresh cannot resolve ``app.main.app``, so the index stays on the
    baseline fallback (70) and both POSTs remain non-executable.
    """
    out = _run_child()
    before = out["pre_startup"]
    after = out["post_startup"]

    # Fail-closed fallback before any live seed exists.
    assert before["executable"] == 75
    assert before["physical_locations"] == {
        "davi_status": STATUS_NEEDS_BOUNDED_EXECUTION,
        "executable": False,
    }
    assert before["inventory_blocks"] == {
        "davi_status": STATUS_NEEDS_BOUNDED_EXECUTION,
        "executable": False,
    }

    # Real startup seeds the live OpenAPI contract.
    assert after["executable"] == 77
    assert after["physical_locations"] == {
        "davi_status": STATUS_DAVI_ELIGIBLE_READ,
        "executable": True,
    }
    assert after["inventory_blocks"] == {
        "davi_status": STATUS_DAVI_ELIGIBLE_READ,
        "executable": True,
    }


def test_real_startup_discovery_reaches_semantic_posts() -> None:
    """Post-startup discovery resolves both governed intents with 72 eligible."""
    out = _run_child()
    for key in ("physical_query", "blocks_query"):
        assert out[key]["eligible_action_count"] == 77, out[key]
        assert out[key]["expected_in_candidates"], out[key]


def test_reset_index_falls_back_to_baseline() -> None:
    """Without a live seed the index stays fail-closed on the baseline."""
    reset_action_index_for_tests()
    try:
        actions = get_technical_actions()
        by_id = {a.operation_id: a for a in actions}
        assert sum(1 for a in actions if a.executable) == 75
        for oid in (
            "list_product_physical_locations",
            "list_product_inventory_blocks",
        ):
            assert by_id[oid].davi_status == STATUS_NEEDS_BOUNDED_EXECUTION
            assert not by_id[oid].executable
    finally:
        reset_action_index_for_tests()
