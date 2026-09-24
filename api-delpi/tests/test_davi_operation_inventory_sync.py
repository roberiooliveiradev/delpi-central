"""Guard: committed DAVI operation inventory must track allowlist eligible count."""

from __future__ import annotations

import json
from pathlib import Path

from app.application.external_capabilities.dynamic_information.catalog_builder import (
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.eligibility import (
    is_dynamically_executable,
    load_allowlist_operation_ids,
)

_API_ROOT = Path(__file__).resolve().parents[1]
_INVENTORY = (
    _API_ROOT / "docs/integrations/evidence/davi-api-delpi-operation-inventory.json"
)


def test_committed_inventory_eligible_matches_allowlist():
    allow = load_external_read_allowlist()
    allow_ids = load_allowlist_operation_ids(allow)
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    actions = build_technical_actions_from_baseline(baseline, allowlist=allow)
    runtime_eligible = {
        a.operation_id for a in actions if is_dynamically_executable(a.davi_status)
    }
    assert runtime_eligible == allow_ids
    assert len(runtime_eligible) == len(allow.get("operations") or [])

    inventory = json.loads(_INVENTORY.read_text(encoding="utf-8"))
    inv_count = int(inventory["DAVI_ELIGIBLE_READ"])
    inv_ids = set(inventory.get("ELIGIBLE_OPERATION_IDS") or [])
    assert inv_count == len(allow_ids)
    assert inv_ids == allow_ids
    # Stale historical failure mode: inventory stuck at 17 after allowlist grew.
    assert inv_count != 17 or len(allow_ids) == 17
    assert inv_count >= 35
