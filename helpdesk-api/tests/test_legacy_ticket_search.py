"""Unit tests for legacy Ticket Search path (assignee filter/sort exception)."""

import pytest

from helpdesk_app.domain.errors import GlpiValidation
from helpdesk_app.infrastructure.glpi.legacy_ticket_search import (
    build_legacy_ticket_search_paths_from_parts,
    merge_legacy_ticket_search,
    parse_legacy_ticket_search,
    ticket_list_needs_legacy_actor_search,
)
from helpdesk_app.infrastructure.glpi.mapping import build_ticket_list_query


def _encoded(path: str) -> str:
    return path.replace("%5B", "[").replace("%5D", "]")


def test_needs_legacy_when_assignee_or_assigned_sort():
    base = build_ticket_list_query()
    assert ticket_list_needs_legacy_actor_search(base) is False
    assert ticket_list_needs_legacy_actor_search(
        build_ticket_list_query(assignee_id=15)
    ) is True
    assert ticket_list_needs_legacy_actor_search(
        build_ticket_list_query(sort="assigned:asc")
    ) is True
    assert ticket_list_needs_legacy_actor_search(
        build_ticket_list_query(sort="updated_at:desc,title:asc")
    ) is False


def test_build_legacy_search_path_includes_assign_field():
    # GLPI canonical search option: 5 = Technician (assigned),
    # glpi_tickets_users join type=ASSIGN (CommonITILObject::getSearchOptionsActors).
    (path,) = build_legacy_ticket_search_paths_from_parts(
        assignee_id=22, page=1, page_size=20
    )
    assert path.startswith("/apirest.php/search/Ticket?")
    encoded = _encoded(path)
    assert "criteria[0][field]=5" in encoded
    assert "criteria[0][searchtype]=equals" in encoded
    assert "22" in encoded
    assert "forcedisplay" in encoded


def test_build_legacy_search_uses_canonical_status_field():
    # GLPI canonical search option: 12 = glpi_tickets.status
    # (CommonITILObject::getSearchOptionsMain).
    (path,) = build_legacy_ticket_search_paths_from_parts(
        assignee_id=22, status="open"
    )
    encoded = _encoded(path)
    assert "criteria[0][field]=5" in encoded  # assignee
    assert "criteria[1][field]=12" in encoded  # status group first criterion
    assert "criteria[1][searchtype]=equals" in encoded


def test_build_legacy_search_sort_assigned():
    (path,) = build_legacy_ticket_search_paths_from_parts(sort="assigned:asc")
    encoded = _encoded(path)
    assert "sort=5" in encoded
    assert "ASC" in encoded
    # The sort column is also requested via forcedisplay for merged ordering.
    assert "forcedisplay[1]=5" in encoded


def test_numeric_term_fanout_covers_id_name_and_content():
    """q=1465 must match the ticket id as well as title/content hits."""
    paths = build_legacy_ticket_search_paths_from_parts(q="1465", assignee_id=22)
    assert len(paths) == 3
    fields = []
    for path in paths:
        encoded = _encoded(path)
        assert "criteria[0][field]=5" not in encoded  # term criterion comes first
        assert "field]=5" in encoded  # assignee ANDed in every sub-search
        assert "forcedisplay[0]=2" in encoded
        fields.append(encoded.split("criteria[0][field]=")[1].split("&")[0])
    assert fields == ["2", "1", "21"]  # id equals, name contains, content contains
    assert "criteria[0][searchtype]=equals" in _encoded(paths[0])


def test_text_term_fanout_covers_name_and_content_not_id():
    paths = build_legacy_ticket_search_paths_from_parts(q="Portal Comercial")
    assert len(paths) == 2
    fields = [
        _encoded(path).split("criteria[0][field]=")[1].split("&")[0]
        for path in paths
    ]
    assert fields == ["1", "21"]


def test_no_term_single_search():
    paths = build_legacy_ticket_search_paths_from_parts(assignee_id=15)
    assert len(paths) == 1


def test_legacy_search_window_covers_requested_page_for_merge():
    paths = build_legacy_ticket_search_paths_from_parts(
        q="Portal", page=3, page_size=10
    )
    for path in paths:
        assert "range=0-30" in path  # window 0..page*size for re-slicing


def test_merge_unions_dedupes_and_orders_by_sort_field():
    payloads = [
        {"totalcount": 1, "data": [{"2": 1465, "19": "2026-01-05 10:00:00"}]},
        {
            "totalcount": 2,
            "data": [
                {"2": 900, "19": "2026-01-07 09:00:00"},
                {"2": 1465, "19": "2026-01-05 10:00:00"},
            ],
        },
    ]
    result = merge_legacy_ticket_search(
        payloads, page=1, page_size=10, sort="updated_at:desc"
    )
    assert result.ticket_ids == (900, 1465)  # merged, deduped, date_mod desc


def test_merge_respects_requested_page_slice():
    payload = {
        "totalcount": 25,
        "data": [{"2": ticket_id, "19": f"2026-01-{day:02d}"} for ticket_id, day in zip(range(100, 131), range(1, 32))],
    }
    result = merge_legacy_ticket_search(
        [payload], page=3, page_size=10, sort="updated_at:asc"
    )
    assert result.ticket_ids == (120, 121, 122, 123, 124, 125, 126, 127, 128, 129)
    assert result.has_more is True


def test_merge_no_duplicates_on_page_two():
    payload = {
        "totalcount": 15,
        "data": [{"2": ticket_id, "19": f"2026-01-{day:02d}"} for ticket_id, day in zip(range(1, 16), range(1, 16))],
    }
    page_one = merge_legacy_ticket_search(
        [payload], page=1, page_size=10, sort="updated_at:asc"
    )
    page_two = merge_legacy_ticket_search(
        [payload], page=2, page_size=10, sort="updated_at:asc"
    )
    assert set(page_one.ticket_ids).isdisjoint(page_two.ticket_ids)
    assert page_two.ticket_ids == (11, 12, 13, 14, 15)


def test_merge_empty_result():
    result = merge_legacy_ticket_search(
        [{"totalcount": 0, "data": []}], page=1, page_size=10
    )
    assert result.ticket_ids == ()
    assert result.has_more is False


def test_parse_legacy_search_page_and_has_more():
    payload = {
        "totalcount": 25,
        "data": [
            {"2": 101},
            {"2": 102},
            {"2": 103},
            {"id": 104},
            {"2": 105},
            {"2": 106},
            {"2": 107},
            {"2": 108},
            {"2": 109},
            {"2": 110},
            {"2": 111},  # size+1
        ],
    }
    result = parse_legacy_ticket_search(payload, page=1, page_size=10)
    assert result.ticket_ids == (101, 102, 103, 104, 105, 106, 107, 108, 109, 110)
    assert result.has_more is True
    assert result.totalcount == 25


def test_build_ticket_list_query_keeps_assigned_client_sort():
    query = build_ticket_list_query(assignee_id=15, sort="assigned:desc")
    assert query.assignee_id == 15
    assert query.client_sort == "assigned:desc"
    assert "assigned" not in query.sort


def test_numeric_query_parity_with_hlapi_group():
    """HLAPI and legacy must express the same search surface for q=1465."""
    query = build_ticket_list_query(q="1465")
    assert "id==1465" in query.filter
    assert "name=like=*1465*" in query.filter
    assert "content=like=*1465*" in query.filter
    paths = build_legacy_ticket_search_paths_from_parts(q="1465")
    encoded = [_encoded(path) for path in paths]
    assert any("field]=2" in p and "equals" in p for p in encoded)
    assert any("field]=1" in p for p in encoded)
    assert any("field]=21" in p for p in encoded)


def test_legacy_rejects_invalid_sort():
    with pytest.raises(GlpiValidation):
        build_legacy_ticket_search_paths_from_parts(sort="entity:desc")
