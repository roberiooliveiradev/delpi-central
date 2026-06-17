from app.domain.services.operational_api_parameter_builder_service import (
    OperationalApiParameterBuilderService,
)


def test_build_date_branch_extracts_branch_and_dates():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "branch", "in": "query"},
                {"name": "start_date", "in": "query"},
                {"name": "end_date", "in": "query"},
            ],
        },
        "rol da filial 01 em marco de 2026",
    )

    assert parameters["branch"] == "01"
    assert parameters["start_date"] == "01-03-2026"
    assert parameters["end_date"] == "31-03-2026"


def test_build_date_branch_infers_granularity_for_series():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "granularity", "in": "query", "required": True},
                {"name": "start_date", "in": "query"},
            ],
        },
        "rol do mes de marco",
    )

    assert parameters["granularity"] == "month"
    assert parameters["start_date"]


def test_build_date_branch_empty_default_limit():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {"parametersSchema": []},
        "qual o cpv",
    )

    assert parameters["limit"] == 10


def test_build_supplies_stock_uses_json_literal_binding():
    parameters = OperationalApiParameterBuilderService.build_supplies_stock(
        {
            "parametersSchema": [
                {"name": "top_limit", "in": "query"},
                {"name": "limit", "in": "query"},
            ],
        }
    )

    assert parameters["top_limit"] == 10
    assert parameters["limit"] == 10


def test_build_sale_orders_pagination_and_dates():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_sale_orders(
        {
            "parametersSchema": [
                {"name": "page", "in": "query"},
                {"name": "page_size", "in": "query"},
                {"name": "start_date", "in": "query"},
                {"name": "end_date", "in": "query"},
            ],
        },
        "ovs de marco de 2026",
    )

    assert parameters["page"] == 1
    assert parameters["page_size"] == 50
    assert parameters["start_date"] == "01-03-2026"
    assert parameters["end_date"] == "31-03-2026"


def test_merge_date_range_adds_missing_dates():
    builder = OperationalApiParameterBuilderService()

    merged = builder.merge_date_range(
        {
            "parametersSchema": [
                {"name": "start_date", "in": "query"},
                {"name": "end_date", "in": "query"},
            ],
        },
        "marco de 2026",
        {"page": 1},
    )

    assert merged["page"] == 1
    assert merged["start_date"] == "01-03-2026"
    assert merged["end_date"] == "31-03-2026"
