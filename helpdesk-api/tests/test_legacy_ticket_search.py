"""Unit tests for legacy Ticket Search path (assignee filter/sort exception)."""

from helpdesk_app.infrastructure.glpi.legacy_ticket_search import (
    build_legacy_ticket_search_path_from_parts,
    parse_legacy_ticket_search,
    ticket_list_needs_legacy_actor_search,
)
from helpdesk_app.infrastructure.glpi.mapping import build_ticket_list_query


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
    path = build_legacy_ticket_search_path_from_parts(assignee_id=22, page=1, page_size=20)
    assert path.startswith("/apirest.php/search/Ticket?")
    assert "criteria[0][field]=5" in path or "criteria%5B0%5D%5Bfield%5D=5" in path
    assert "criteria[0][searchtype]=equals" in path or "criteria%5B0%5D%5Bsearchtype%5D=equals" in path
    assert "22" in path
    assert "forcedisplay" in path


def test_build_legacy_search_uses_canonical_status_field():
    # GLPI canonical search option: 12 = glpi_tickets.status
    # (CommonITILObject::getSearchOptionsMain).
    path = build_legacy_ticket_search_path_from_parts(assignee_id=22, status="open")
    encoded = path.replace("%5B", "[").replace("%5D", "]")
    assert "criteria[0][field]=5" in encoded  # assignee
    assert "criteria[1][field]=12" in encoded  # status group first criterion
    assert "criteria[1][searchtype]=equals" in encoded


def test_build_legacy_search_sort_assigned():
    path = build_legacy_ticket_search_path_from_parts(sort="assigned:asc")
    assert "sort=5" in path or "sort=5" in path.replace("%3D", "=")
    assert "ASC" in path


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
