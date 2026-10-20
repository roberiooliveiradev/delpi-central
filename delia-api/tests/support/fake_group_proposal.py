"""TEST_ONLY helpers for FakeProposalModel group-selection wiring.

Production ``_select_group`` fail-closes when the model proposal is
missing — including singleton catalogs (Q02-A one-rework RQ-03).
Fixtures that exercise capability/argument/index stages without a
scripted group proposal may use ``singleton_group_proposal_from_request``
so the harness still reaches those stages. Explicit missing-group
tests must return ``None`` and assert fail-closed operational outcomes.
"""

from __future__ import annotations

import json
import re
from typing import Any

GROUP_SELECTION_PURPOSE = (
    "delia.capability_orchestration.select_group"
)

_GROUP_BLOCK_RE = re.compile(
    r"<capability_groups>\s*(.*?)\s*</capability_groups>",
    re.DOTALL,
)


def singleton_group_proposal_from_request(
    request: Any,
) -> dict[str, Any] | None:
    """Return applicable=true for the sole catalog key, else None.

    Parses the untrusted ``<capability_groups>`` block already sent to
    the model. Never invents a group id. Multi-group catalogs return
    None so fixtures must script an explicit selection.
    """
    purpose = getattr(request, "task_purpose_id", None)
    if purpose != GROUP_SELECTION_PURPOSE:
        return None
    text = getattr(request, "input_text", None) or ""
    match = _GROUP_BLOCK_RE.search(text)
    if match is None:
        return None
    raw = match.group(1).strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, list) or len(payload) != 1:
        return None
    entry = payload[0]
    if not isinstance(entry, dict):
        return None
    group_key = entry.get("capability_group_id")
    if not isinstance(group_key, str) or not group_key.strip():
        return None
    return {
        "applicable": True,
        "capability_group_id": group_key.strip(),
    }
