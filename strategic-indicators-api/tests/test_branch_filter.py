from si_app.shared.branch_filter import effective_query_branch


def test_effective_query_branch_treats_consolidated_tokens_as_none() -> None:
    assert effective_query_branch(None) is None
    assert effective_query_branch("") is None
    assert effective_query_branch("consolidated") is None
    assert effective_query_branch("consolidated-all") is None
    assert effective_query_branch("all") is None


def test_effective_query_branch_keeps_unit_codes() -> None:
    assert effective_query_branch("01") == "01"
    assert effective_query_branch("02") == "02"
