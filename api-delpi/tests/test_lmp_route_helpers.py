from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.interface.http.routes.engineering.lmp_route_helpers import (
    build_get_lmp_request,
    build_list_lmp_request,
)


def test_build_list_lmp_request_maps_query_fields() -> None:
    request = build_list_lmp_request(
        date_start="20260501",
        date_end="20260531",
        branch="01",
        listing_type="LMP",
        page=2,
        page_size=50,
        include_qtd_pi=False,
    )

    assert isinstance(request, ListLMPRequest)
    assert request.date_start == "20260501"
    assert request.branch == "01"
    assert request.listing_type == "LMP"
    assert request.page == 2
    assert request.page_size == 50
    assert request.include_qtd_pi is False


def test_build_get_lmp_request_maps_sale_number_and_scope() -> None:
    request = build_get_lmp_request(
        "003578",
        date_start="20260501",
        date_end="20260531",
        branch="01",
    )

    assert isinstance(request, GetLMPRequest)
    assert request.sale_number == "003578"
    assert request.date_start == "20260501"
    assert request.date_end == "20260531"
    assert request.branch == "01"
