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


def test_build_date_branch_maps_todas_as_filiais_to_todas():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "branch", "in": "query"},
            ],
        },
        "rol de todas as filiais",
    )

    assert "branch" not in parameters


def test_build_date_branch_extracts_bare_branch_code_after_rol():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "branch", "in": "query"},
                {"name": "start_date", "in": "query"},
                {"name": "end_date", "in": "query"},
            ],
        },
        "rol 01 ago/26",
    )

    assert parameters["branch"] == "01"
    assert parameters["start_date"] == "01-08-2026"
    assert parameters["end_date"] == "31-08-2026"


def test_build_date_branch_omits_branch_for_consolidado():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "branch", "in": "query"},
                {"name": "start_date", "in": "query"},
                {"name": "end_date", "in": "query"},
            ],
        },
        "qual o rol consolidado em agosto 2026",
    )

    assert "branch" not in parameters
    assert parameters["start_date"] == "01-08-2026"
    assert parameters["end_date"] == "31-08-2026"


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


def test_build_date_branch_does_not_bind_limit_from_pagination_page_size() -> None:
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "reference_date", "in": "query"},
                {"name": "limit", "in": "query"},
            ],
        },
        "produtos programados para produzir hoje",
    )

    assert "reference_date" in parameters
    assert "limit" not in parameters


def test_build_date_branch_empty_default_does_not_invent_limit_without_schema():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {"parametersSchema": []},
        "qual o cpv",
    )

    assert "limit" not in parameters


def test_build_department_idd_extracts_department_and_branch():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_department_idd(
        {
            "parametersSchema": [
                {"name": "department_id", "in": "query"},
                {"name": "branch", "in": "query"},
            ],
        },
        "idd do comercial com metas e realizado filial 02",
    )

    assert parameters["department_id"] == "commercial"
    assert parameters["branch"] == "02"


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


def test_build_date_branch_binds_status_late_from_atraso_terms():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "status", "in": "query"},
                {"name": "page", "in": "query"},
                {"name": "page_size", "in": "query"},
            ],
        },
        "ops em atraso",
    )

    assert parameters["status"] == "late"
    assert parameters["page"] == 1
    assert parameters["page_size"] == 50


def test_build_date_branch_binds_status_on_time_from_no_prazo():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "status", "in": "query"},
            ],
        },
        "ops no prazo na producao",
    )

    assert parameters["status"] == "on_time"


def test_build_date_branch_merge_inherits_period_and_overrides_branch():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "branch", "in": "query"},
                {"name": "start_date", "in": "query"},
                {"name": "end_date", "in": "query"},
            ],
        },
        "somente da filial 01",
        base_params={
            "start_date": "01-08-2026",
            "end_date": "28-08-2026",
            "branch": "all",
        },
    )

    assert parameters["branch"] == "01"
    assert parameters["start_date"] == "01-08-2026"
    assert parameters["end_date"] == "28-08-2026"


def test_build_date_branch_accepts_filail_typo():
    builder = OperationalApiParameterBuilderService()

    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "branch", "in": "query"},
            ],
        },
        "rol filail 01 deste mês",
    )

    assert parameters["branch"] == "01"


def test_merge_last_action_params_immutable():
    base = {"branch": "all", "start_date": "01-08-2026"}
    incoming = {"branch": "01"}
    merged = OperationalApiParameterBuilderService.merge_last_action_params(incoming, base)
    assert merged == {"branch": "01", "start_date": "01-08-2026"}
    assert base["branch"] == "all"


def test_pagination_page_size_uses_canonical_standard():
    from app.domain.services.chat_operational_pagination_defaults_service import (
        ChatOperationalPaginationDefaultsService,
    )

    builder = OperationalApiParameterBuilderService()
    parameters = builder.build_date_branch(
        {
            "parametersSchema": [
                {"name": "page", "in": "query"},
                {"name": "page_size", "in": "query"},
            ],
        },
        "otd da filial 01",
    )

    assert parameters["page"] == 1
    assert parameters["page_size"] == ChatOperationalPaginationDefaultsService.standard()
