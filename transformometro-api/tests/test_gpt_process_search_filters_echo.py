"""process.search enumeration semantics + filters_applied echo — INT-1 P2.

Causal remediation for the P2 failure: the owner contract supports a
true unfiltered enumeration (``search`` with no params lists every record
the caller can see), and the result must echo the applied criteria so a
consumer can distinguish "filtered result with zero matches" from
"empty catalog". Positive/sibling/negative coverage only — no behavior
beyond the existing contract.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)

_PATCH_PREFIX = "tm_app.application.gpt_actions.dispatch_service"


def _search_process(rows, **kwargs):
    """Invoke process.search with canonical repo/access mocks."""
    request = MagicMock()
    with (
        patch(f"{_PATCH_PREFIX}.ProcessoRepository") as proc_cls,
        patch(
            f"{_PATCH_PREFIX}.filter_rows_for_access",
            side_effect=lambda _req, r, **_kw: r,
        ),
        patch(
            f"{_PATCH_PREFIX}.ProcessoSetupStatsService"
        ) as stats_cls,
        patch(
            f"{_PATCH_PREFIX}.require_transformometro_view_access",
            return_value=None,
        ),
    ):
        proc_cls.return_value.list.return_value = list(rows)
        stats_cls.return_value.enrich_processos.side_effect = (
            lambda r: r
        )
        out = GptActionsDispatchService().search_records(
            request, "process", **kwargs
        )
    return out, proc_cls


def test_search_process_unfiltered_enumerates_all_and_echoes_no_filters():
    """ENUMERATION_WITHOUT_FILTER — no params lists every visible record
    and advertises an empty filters_applied (true enumeration, not a
    filtered-empty result)."""
    rows = [
        {"processo_id": "p1", "nome_processo": "Expedição"},
        {"processo_id": "p2", "nome_processo": "Recebimento"},
    ]
    out, proc_cls = _search_process(rows)

    assert out["total"] == 2
    assert len(out["items"]) == 2
    assert out["filters_applied"] == {}
    # repository called without q — full list, not a filtered scan
    assert proc_cls.return_value.list.call_args.kwargs["q"] is None


def test_search_process_filtered_empty_result_echoes_applied_filters():
    """FILTERED_EMPTY_RESULT — a restrictive q returning zero matches must
    echo the caller's filter so the consumer can see the empty result is
    scoped, not an empty catalog."""
    out, _ = _search_process([], q="zzz-no-match")

    assert out["total"] == 0
    assert out["items"] == []
    assert out["filters_applied"] == {"q": "zzz-no-match"}


def test_filtered_empty_is_not_equivalent_to_empty_catalog():
    """FILTERED_RESULT_NOT_EQUIVALENT_TO_EMPTY_CATALOG — the same total=0
    payload distinguishes scoped-empty from empty-inventory via
    filters_applied."""
    filtered, _ = _search_process([], q="inexistente")
    unfiltered, _ = _search_process([])

    assert filtered["total"] == unfiltered["total"] == 0
    assert filtered["filters_applied"] == {"q": "inexistente"}
    assert unfiltered["filters_applied"] == {}


def test_search_process_pagination_and_total_echo_filters():
    """PAGINATION_AND_TOTAL — page/page_size slice the full result and
    ride the filters_applied echo."""
    rows = [{"processo_id": f"p{i}"} for i in range(3)]
    out, _ = _search_process(rows, page="1", page_size="2")

    assert out["total"] == 3
    assert len(out["items"]) == 2
    assert out["pagination"] == {"page": 1, "page_size": 2, "has_more": True}
    assert out["filters_applied"] == {"page": "1", "page_size": "2"}


def test_search_process_family_filter_is_exact_and_echoed():
    """Sibling — familia_processo is an exact-match filter (not the same
    as q) and rides the echo."""
    rows = [{"processo_id": "p1", "familia_processo": "melhoria"}]
    out, proc_cls = _search_process(rows, familia_processo="melhoria")

    assert out["total"] == 1
    assert out["filters_applied"] == {"familia_processo": "melhoria"}
    assert (
        proc_cls.return_value.list.call_args.kwargs["familia_processo"]
        == "melhoria"
    )


def test_search_process_disallowed_field_still_fails_closed():
    """Negative — the fail-closed filter contract is unchanged."""
    with pytest.raises(GptActionsError) as exc:
        GptActionsDispatchService().record_read(
            MagicMock(), "process", action="search", unit_code="kg"
        )
    assert exc.value.status_code == 400
    assert exc.value.data["error_code"] == "INVALID_FIELD"


def test_project_search_records_preserves_filters_applied():
    """Projection keeps the echo — the MCP/GPT response surface exposes
    it to callers."""
    from tm_app.application.gpt_actions.response_compact import (
        project_search_records,
    )

    out = project_search_records(
        {
            "total": 0,
            "items": [],
            "filters_applied": {"q": "zzz"},
            "pagination": {"page": 1, "page_size": 10, "has_more": False},
        }
    )
    assert out["filters_applied"] == {"q": "zzz"}
    assert out["pagination"]["has_more"] is False
