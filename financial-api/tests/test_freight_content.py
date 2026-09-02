from __future__ import annotations

from decimal import Decimal

from financial_app.application.services.content_loader import load_content


def _content() -> dict:
    return load_content("freight.json")


def test_branch_limits_parse_as_decimal() -> None:
    limits = _content()["branchLimits"]

    assert Decimal(limits["01"]) == Decimal("3.25")
    assert Decimal(limits["02"]) == Decimal("4.25")


def test_branch_limits_are_strings_to_survive_json_round_trip() -> None:
    """Limite como float perderia precisão na comparação com o percentual."""
    for value in _content()["branchLimits"].values():
        assert isinstance(value, str)


def test_minimum_issue_date_guards_legacy_protheus_data() -> None:
    assert _content()["minimumIssueDate"] == "2023-01-01"


def test_pagination_and_fetch_limits_exist() -> None:
    content = _content()

    assert content["pagination"]["defaultPageSize"] == 25
    assert content["pagination"]["maxPageSize"] == 200
    assert content["linkFetchLimit"] == 20000
    assert content["cacheTtlSeconds"]["dashboard"] > 0


def test_every_inconsistency_code_has_a_reason_text() -> None:
    expected = {
        "nf_not_found",
        "cte_not_found",
        "nf_goods_value_not_positive",
        "cte_gross_value_not_positive",
        "duplicated_link",
        "cte_without_valid_base",
        "special_or_unknown_cte",
        "branch_without_limit",
    }

    assert set(_content()["inconsistencyReasons"]) == expected


def test_situations_and_labels_are_aligned() -> None:
    content = _content()

    assert content["situations"] == ["all", "normal", "above_limit", "inconsistent"]
    assert set(content["situationLabels"]) == {"normal", "above_limit", "inconsistent"}


def test_messages_expose_the_cutoff_placeholder() -> None:
    messages = _content()["messages"]

    assert "{minimum}" in messages["periodBeforeCutoff"]
    assert "{allowed}" in messages["invalidSortBy"]
    assert messages["periodRequired"]


def test_special_freight_kinds_are_declared() -> None:
    content = _content()

    assert content["normalFreightType"] == "N"
    assert content["normalFreightKind"] == "CTE"
    assert "CTEOS" in content["specialFreightKinds"]
