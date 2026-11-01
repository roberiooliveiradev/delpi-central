"""DI-5 — governed autonomous authoring chain.

Composed proposal ops flow into the canonical execute.apply_mutation
pipeline (prepare -> consent -> commit -> VERIFIED read-back) — the
same governed contract certified in B1–B5. Human-channel E2E remains
PENDING_EXTERNAL_VERIFICATION (doc 25 handoff).
"""
from __future__ import annotations

from unittest.mock import patch

import test_vista_execute as tx

PLANNER = (
    "tv_app.application.gpt_actions.dispatch_service."
    "PresentationCommandPlannerService"
)


def test_composed_ops_execute_via_governed_pipeline():
    d, writes, _ = tx._dispatch()
    ops = [{"op": "add_blank_slide", "title": "T"}]
    with patch(
        f"{PLANNER}.plan", return_value={"operations": ops}
    ), patch(
        f"{PLANNER}.to_suggest_payload",
        return_value={"operations": ops},
    ):
        suggestion = d.suggest_change(
            user=tx._user(),
            message="crie um painel de produção",
            host_context={},
            authorization=None,
        )
    assert suggestion["operations"] == ops

    prepared = tx._prepare(d, suggestion["operations"])
    result = tx._commit(d, prepared, idempotency_key="k-di5")
    assert result["status"] == "VERIFIED"


def test_authoring_chain_preserves_catalog():
    from tv_app.application.gpt_actions.capability_surface import (
        EXECUTE_ENTITIES,
    )

    assert "apply_mutation" in EXECUTE_ENTITIES["presentation"]
