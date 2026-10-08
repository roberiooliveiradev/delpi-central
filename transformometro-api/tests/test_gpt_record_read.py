"""record_read merged surface — Tool Surface Rationalization V1.

Fail-closed action dispatch + canonical filter validation shared by
GPT Actions and MCP transports (validation moved into the dispatch
service — no per-transport divergence).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)


def _svc() -> GptActionsDispatchService:
    return GptActionsDispatchService()


def test_record_read_search_delegates():
    svc = _svc()
    with patch.object(
        svc, "search_records", return_value={"total": 1, "items": []}
    ) as search:
        out = svc.record_read(
            MagicMock(), "process", action="search", q="pcp"
        )
    assert out == {"total": 1, "items": []}
    search.assert_called_once()


def test_record_read_get_delegates():
    svc = _svc()
    with (
        patch.object(
            svc, "get_record", return_value={"id": "p1", "extra": "x"}
        ) as get,
        patch(
            "tm_app.application.gpt_actions.response_compact.project_get_record",
            side_effect=lambda d: {"id": d["id"]},
        ),
    ):
        out = svc.record_read(
            MagicMock(), "process", action="get", record_id="p1"
        )
    assert out == {"id": "p1"}
    get.assert_called_once()


def test_record_read_get_requires_id():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.record_read(MagicMock(), "process", action="get")
    assert exc.value.status_code == 400


def test_record_read_search_rejects_id():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.record_read(
            MagicMock(), "process", action="search", record_id="p1"
        )
    assert exc.value.status_code == 400


def test_record_read_invalid_action_fails_closed():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.record_read(MagicMock(), "process", action="mutate")
    assert exc.value.status_code == 400
    assert exc.value.data["error_code"] == "INVALID_ACTION"


def test_record_read_search_rejects_disallowed_filter():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.record_read(
            MagicMock(), "branch", action="search", q="nope"
        )
    assert exc.value.status_code == 400
    assert exc.value.data["error_code"] == "INVALID_FIELD"


def test_record_read_unknown_entity_fails_closed():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.record_read(MagicMock(), "not_an_entity", action="search")
    assert exc.value.status_code == 400
