from unittest.mock import MagicMock

from commercial_app.application.use_cases.manage_seller_portfolio import (
    CreatePortfolioRequest,
    ManageSellerPortfolioUseCase,
    add_customer_result_to_dict,
    coverage_audit_to_dict,
    customer_shared_coverage_to_dict,
    load_summary_to_dict,
    parse_customer_assignments,
    portfolio_to_dict,
)
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)


def _portfolio(**kwargs) -> SellerPortfolio:
    defaults = dict(
        id="p1",
        user_id="u1",
        display_name="Vendedor A",
        active=True,
        customers=(
            SellerCustomerAssignment("100", "01", "Cliente 100"),
            SellerCustomerAssignment("200", "01", "Cliente 200"),
        ),
        members=(SellerPortfolioMember(user_id="u1", role="owner"),),
    )
    defaults.update(kwargs)
    return SellerPortfolio(**defaults)


def test_create_portfolio_allows_same_user_in_another_portfolio() -> None:
    repository = MagicMock()
    created = _portfolio(id="p2", display_name="Novo")
    repository.create_portfolio.return_value = created
    use_case = ManageSellerPortfolioUseCase(repository)

    result = use_case.create_portfolio(
        CreatePortfolioRequest(user_id="u1", display_name="Novo")
    )

    assert result.id == "p2"
    repository.get_by_user_id.assert_not_called()
    repository.create_portfolio.assert_called_once_with(
        user_id="u1",
        display_name="Novo",
        created_by_user_id=None,
        member_user_ids=[],
    )


def test_create_portfolio_with_user_ids_and_owner() -> None:
    repository = MagicMock()
    created = _portfolio(id="p3", user_id="owner-1", display_name="Equipe")
    repository.create_portfolio.return_value = created
    use_case = ManageSellerPortfolioUseCase(repository)

    result = use_case.create_portfolio(
        CreatePortfolioRequest(
            display_name="Equipe",
            user_ids=("owner-1", "helper-1"),
            owner_user_id="owner-1",
        )
    )

    assert result.id == "p3"
    repository.create_portfolio.assert_called_once_with(
        user_id="owner-1",
        display_name="Equipe",
        created_by_user_id=None,
        member_user_ids=["helper-1"],
    )


def test_replace_members_requires_exactly_one_owner() -> None:
    repository = MagicMock()
    use_case = ManageSellerPortfolioUseCase(repository)

    try:
        use_case.replace_members(
            portfolio_id="p1",
            members=[
                SellerPortfolioMember(user_id="u1", role="member"),
                SellerPortfolioMember(user_id="u2", role="member"),
            ],
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "exatamente um owner" in str(exc)
    repository.replace_members.assert_not_called()


def test_replace_members_success() -> None:
    repository = MagicMock()
    repository.get_by_id.return_value = _portfolio()
    updated = _portfolio(
        members=(
            SellerPortfolioMember(user_id="u1", role="owner"),
            SellerPortfolioMember(user_id="u2", role="member"),
        )
    )
    repository.replace_members.return_value = updated
    use_case = ManageSellerPortfolioUseCase(repository)

    result = use_case.replace_members(
        portfolio_id="p1",
        members=[
            SellerPortfolioMember(user_id="u1", role="owner"),
            SellerPortfolioMember(user_id="u2", role="member"),
        ],
    )

    assert len(result.members) == 2
    repository.replace_members.assert_called_once()


def test_create_portfolio_rejects_without_portal_access() -> None:
    repository = MagicMock()
    portal = MagicMock()
    portal.has_commercial_portal_access_batch.return_value = {"u1": False}
    use_case = ManageSellerPortfolioUseCase(repository, portal_access=portal)

    try:
        use_case.create_portfolio(
            CreatePortfolioRequest(user_id="u1", display_name="Novo")
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Portal Comercial" in str(exc)
    repository.create_portfolio.assert_not_called()


def test_add_member_rejects_without_portal_access() -> None:
    repository = MagicMock()
    portal = MagicMock()
    portal.has_commercial_portal_access_batch.return_value = {"u2": False}
    use_case = ManageSellerPortfolioUseCase(repository, portal_access=portal)

    try:
        use_case.add_member(portfolio_id="p1", user_id="u2")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Portal Comercial" in str(exc)
    repository.add_member.assert_not_called()


def test_add_member_writes_audit_when_configured() -> None:
    repository = MagicMock()
    updated = _portfolio(
        members=(
            SellerPortfolioMember(user_id="u1", role="owner"),
            SellerPortfolioMember(user_id="u2", role="member"),
        )
    )
    repository.add_member.return_value = updated
    audit = MagicMock()
    use_case = ManageSellerPortfolioUseCase(repository, audit_repository=audit)

    result = use_case.add_member(
        portfolio_id="p1",
        user_id="u2",
        actor_user_id="admin-1",
    )

    assert result.id == "p1"
    audit.append.assert_called_once()
    kwargs = audit.append.call_args.kwargs
    assert kwargs["action"] == "seller_portfolio.add_member"
    assert kwargs["entity_id"] == "p1"
    assert kwargs["payload"]["user_id"] == "u2"


def test_add_and_remove_customer_write_audit() -> None:
    repository = MagicMock()
    portfolio = _portfolio()
    repository.list_portfolios.return_value = [portfolio]
    repository.get_by_id.return_value = portfolio
    repository.add_customer.return_value = portfolio
    repository.remove_customer.return_value = portfolio
    audit = MagicMock()
    use_case = ManageSellerPortfolioUseCase(repository, audit_repository=audit)

    use_case.add_customer(
        portfolio_id="p1",
        customer=SellerCustomerAssignment(
            customer_code="000240",
            customer_store="01",
            customer_name="BUHLER DO BRASIL LTDA.",
        ),
        actor_user_id="admin-1",
    )
    assert audit.append.call_args.kwargs["action"] == "seller_portfolio.add_customer"
    assert audit.append.call_args.kwargs["payload"]["customer_code"] == "000240"

    use_case.remove_customer(
        portfolio_id="p1",
        customer_code="000240",
        customer_store="01",
        actor_user_id="admin-1",
    )
    assert audit.append.call_args.kwargs["action"] == "seller_portfolio.remove_customer"
    assert audit.append.call_args.kwargs["entity_id"] == "p1"


def test_deactivate_portfolio_writes_audit() -> None:
    repository = MagicMock()
    repository.deactivate_portfolio.return_value = _portfolio(active=False)
    audit = MagicMock()
    use_case = ManageSellerPortfolioUseCase(repository, audit_repository=audit)

    result = use_case.deactivate_portfolio("p1", actor_user_id="admin-1")

    assert result.active is False
    audit.append.assert_called_once()
    kwargs = audit.append.call_args.kwargs
    assert kwargs["action"] == "seller_portfolio.deactivate"
    assert kwargs["entity_id"] == "p1"


def test_update_portfolio_audits_active_flip() -> None:
    repository = MagicMock()
    repository.get_by_id.return_value = _portfolio(active=True)
    repository.update_portfolio.return_value = _portfolio(active=False)
    audit = MagicMock()
    use_case = ManageSellerPortfolioUseCase(repository, audit_repository=audit)

    use_case.update_portfolio(
        portfolio_id="p1",
        active=False,
        actor_user_id="admin-1",
    )

    audit.append.assert_called_once()
    assert audit.append.call_args.kwargs["action"] == "seller_portfolio.deactivate"



def test_remove_member_rejects_last_owner() -> None:
    repository = MagicMock()
    repository.get_by_id.return_value = _portfolio()
    use_case = ManageSellerPortfolioUseCase(repository)

    try:
        use_case.remove_member(portfolio_id="p1", user_id="u1")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "último membro" in str(exc) or "único owner" in str(exc)
    repository.remove_member.assert_not_called()


def test_remove_member_rejects_sole_owner_when_others_exist() -> None:
    repository = MagicMock()
    repository.get_by_id.return_value = _portfolio(
        members=(
            SellerPortfolioMember(user_id="u1", role="owner"),
            SellerPortfolioMember(user_id="u2", role="member"),
        )
    )
    use_case = ManageSellerPortfolioUseCase(repository)

    try:
        use_case.remove_member(portfolio_id="p1", user_id="u1")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "único owner" in str(exc)
    repository.remove_member.assert_not_called()


def test_get_me_portfolios_lists_active() -> None:
    repository = MagicMock()
    items = [
        _portfolio(id="p1"),
        _portfolio(id="p2", display_name="Outra"),
    ]
    repository.list_by_user_id.return_value = items
    use_case = ManageSellerPortfolioUseCase(repository)

    portfolios = use_case.get_me_portfolios("u1")
    me = use_case.get_me("u1")

    assert len(portfolios) == 2
    assert me is not None and me.id == "p1"
    repository.list_by_user_id.assert_called_with("u1", active_only=True)


def test_portfolio_to_dict_includes_members_and_owner() -> None:
    payload = portfolio_to_dict(
        _portfolio(
            members=(
                SellerPortfolioMember(user_id="u1", role="owner"),
                SellerPortfolioMember(user_id="u2", role="member"),
            )
        )
    )
    assert payload["owner_user_id"] == "u1"
    assert payload["members"] == [
        {"user_id": "u1", "role": "owner", "has_portal_access": True},
        {"user_id": "u2", "role": "member", "has_portal_access": True},
    ]


def test_portfolio_to_dict_includes_portal_access_from_map() -> None:
    payload = portfolio_to_dict(
        _portfolio(
            members=(
                SellerPortfolioMember(user_id="u1", role="owner"),
                SellerPortfolioMember(user_id="u2", role="member"),
            )
        ),
        portal_access_by_user={"u1": True, "u2": False},
    )
    assert payload["members"][0]["has_portal_access"] is True
    assert payload["members"][1]["has_portal_access"] is False


def test_serialize_portfolio_batches_portal_lookup() -> None:
    repository = MagicMock()
    portal = MagicMock()
    portal.has_commercial_portal_access_batch.return_value = {
        "u1": True,
        "u2": False,
    }
    use_case = ManageSellerPortfolioUseCase(repository, portal_access=portal)
    payload = use_case.serialize_portfolio(
        _portfolio(
            members=(
                SellerPortfolioMember(user_id="u1", role="owner"),
                SellerPortfolioMember(user_id="u2", role="member"),
            )
        )
    )
    portal.has_commercial_portal_access_batch.assert_called_once()
    assert payload["members"][1]["has_portal_access"] is False


def test_ensure_portal_access_uses_batch_and_content_message() -> None:
    repository = MagicMock()
    portal = MagicMock()
    portal.has_commercial_portal_access_batch.return_value = {"u-blocked": False}
    use_case = ManageSellerPortfolioUseCase(repository, portal_access=portal)
    try:
        use_case._ensure_portal_access(["u-blocked"])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Portal Comercial" in str(exc)
    portal.has_commercial_portal_access_batch.assert_called_once_with(["u-blocked"])


def test_transfer_customers_requires_reason_note() -> None:
    repository = MagicMock()
    repository.get_by_id.side_effect = [
        _portfolio(id="p1"),
        _portfolio(id="p2", user_id="u2", display_name="Destino"),
    ]
    use_case = ManageSellerPortfolioUseCase(repository)

    try:
        use_case.transfer_customers(
            source_portfolio_id="p1",
            target_portfolio_id="p2",
            customers=[SellerCustomerAssignment("100", "01")],
            actor_user_id="admin",
            reason_note="",
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "reason_note" in str(exc)


def test_transfer_customers_writes_audit_when_configured() -> None:
    repository = MagicMock()
    source = _portfolio(id="p1")
    target = _portfolio(id="p2", user_id="u2", display_name="Destino")
    repository.get_by_id.side_effect = [source, target, source, target]
    repository.transfer_customers.return_value = (source, target)
    audit = MagicMock()

    use_case = ManageSellerPortfolioUseCase(repository, audit_repository=audit)
    result = use_case.transfer_customers(
        source_portfolio_id="p1",
        target_portfolio_id="p2",
        customers=[SellerCustomerAssignment("100", "01")],
        actor_user_id="admin-1",
        reason_note="Reorganização comercial",
    )

    assert result[0].id == "p1"
    audit.append.assert_called_once()
    payload = audit.append.call_args.kwargs["payload"]
    assert payload["reason_note"] == "Reorganização comercial"
    assert payload["transferred_count"] == 1


def test_transfer_customers_bulk_best_effort_and_audit() -> None:
    repository = MagicMock()
    source = _portfolio(id="p1")
    target = _portfolio(id="p2", user_id="u2", display_name="Destino")
    # get: validate source/target, then reload after loop, (+ optional)
    repository.get_by_id.side_effect = [
        source,
        target,
        source,
        target,
    ]
    repository.transfer_customers.side_effect = [
        (source, target),
        ValueError("falha simulada"),
    ]
    audit = MagicMock()
    use_case = ManageSellerPortfolioUseCase(repository, audit_repository=audit)

    result = use_case.transfer_customers_bulk(
        source_portfolio_id="p1",
        target_portfolio_id="p2",
        customers=[
            SellerCustomerAssignment("100", "01"),
            SellerCustomerAssignment("200", "01"),
            SellerCustomerAssignment("999", "01"),
        ],
        actor_user_id="admin-1",
        reason_note="Bulk reorg",
    )

    assert result.transferred_count == 1
    assert result.failed_count == 2
    assert len(result.results) == 3
    assert result.results[0].ok is True
    assert result.results[1].ok is False
    assert result.results[2].ok is False
    assert "999" in (result.results[2].error or "")
    audit.append.assert_called_once()
    kwargs = audit.append.call_args.kwargs
    assert kwargs["action"] == "seller_portfolio.transfer_customers_bulk"
    assert kwargs["payload"]["transferred_count"] == 1
    assert kwargs["payload"]["failed_count"] == 2
    assert kwargs["payload"]["reason_note"] == "Bulk reorg"


def test_purge_portfolio_writes_audit_and_returns_snapshot() -> None:
    repository = MagicMock()
    current = _portfolio(id="p1")
    repository.get_by_id.return_value = current
    repository.delete_portfolio.return_value = current
    audit = MagicMock()
    use_case = ManageSellerPortfolioUseCase(repository, audit_repository=audit)

    deleted = use_case.purge_portfolio("p1", actor_user_id="admin-1")

    assert deleted.id == "p1"
    repository.delete_portfolio.assert_called_once_with("p1")
    audit.append.assert_called_once()
    kwargs = audit.append.call_args.kwargs
    assert kwargs["action"] == "seller_portfolio.purge"
    assert kwargs["entity_id"] == "p1"
    assert kwargs["payload"]["customer_count"] == 2
    assert kwargs["payload"]["user_id"] == "u1"


def test_purge_portfolio_missing_raises() -> None:
    repository = MagicMock()
    repository.get_by_id.return_value = None
    use_case = ManageSellerPortfolioUseCase(repository)

    try:
        use_case.purge_portfolio("missing", actor_user_id="admin-1")
        assert False, "expected LookupError"
    except LookupError as exc:
        assert "não encontrado" in str(exc)
    repository.delete_portfolio.assert_not_called()


def test_parse_customer_assignments_deduplicates() -> None:
    parsed = parse_customer_assignments(
        [
            {"customer_code": "100", "customer_store": "01"},
            {"customer_code": "100", "customer_store": "01", "customer_name": "Dup"},
        ]
    )
    assert len(parsed) == 1
    assert parsed[0].customer_code == "100"


def test_add_customer_returns_soft_overlap_warning() -> None:
    repository = MagicMock()
    other = _portfolio(
        id="p2",
        display_name="Outra",
        customers=(SellerCustomerAssignment("100", "01", "Cliente 100"),),
    )
    updated = _portfolio(
        customers=(
            SellerCustomerAssignment("100", "01", "Cliente 100"),
            SellerCustomerAssignment("200", "01", "Cliente 200"),
        )
    )
    repository.list_portfolios.return_value = [other]
    repository.add_customer.return_value = updated
    use_case = ManageSellerPortfolioUseCase(repository)

    result = use_case.add_customer(
        portfolio_id="p1",
        customer=SellerCustomerAssignment("100", "01", "Cliente 100"),
    )

    assert result.portfolio.id == "p1"
    assert result.warning is not None
    assert result.warning.code == "customer_in_other_portfolios"
    assert result.warning.other_portfolios[0].id == "p2"
    repository.add_customer.assert_called_once()
    payload = add_customer_result_to_dict(result)
    assert payload["coverage_warning"]["code"] == "customer_in_other_portfolios"
    assert payload["warnings"][0]["other_portfolios"][0]["display_name"] == "Outra"


def test_add_customer_without_overlap_has_no_warning() -> None:
    repository = MagicMock()
    repository.list_portfolios.return_value = [_portfolio(id="p2", display_name="Outra")]
    repository.add_customer.return_value = _portfolio()
    use_case = ManageSellerPortfolioUseCase(repository)

    result = use_case.add_customer(
        portfolio_id="p1",
        customer=SellerCustomerAssignment("999", "01", "Novo"),
    )

    assert result.warning is None
    assert add_customer_result_to_dict(result)["coverage_warning"] is None


def test_audit_customer_coverage_uses_active_portfolios() -> None:
    repository = MagicMock()
    repository.list_portfolios.return_value = [
        _portfolio(
            id="p1",
            customers=(SellerCustomerAssignment("100", "01", "Cliente"),),
        ),
        _portfolio(
            id="p2",
            display_name="B",
            customers=(SellerCustomerAssignment("100", "01", "Cliente"),),
        ),
    ]
    use_case = ManageSellerPortfolioUseCase(repository)

    audit = use_case.audit_customer_coverage()
    payload = coverage_audit_to_dict(audit)

    repository.list_portfolios.assert_called_once_with(active_only=True)
    assert payload["overlapping_count"] == 1
    assert payload["gap"]["available"] is False
    assert payload["portfolios_with_overlap"][0]["overlapping_customer_count"] == 1


def test_lookup_customer_shared_coverage_team_scope_filters_portfolio_ids() -> None:
    repository = MagicMock()
    repository.list_portfolios.return_value = [
        _portfolio(
            id="p1",
            display_name="Sul",
            customers=(SellerCustomerAssignment("100", "01", "Cliente"),),
        ),
        _portfolio(
            id="p2",
            display_name="Ana",
            customers=(SellerCustomerAssignment("100", "01", "Cliente"),),
        ),
        _portfolio(
            id="p3",
            display_name="Fora",
            customers=(SellerCustomerAssignment("100", "01", "Cliente"),),
        ),
    ]
    use_case = ManageSellerPortfolioUseCase(repository)

    items = use_case.lookup_customer_shared_coverage(
        customers=[("100", "01")],
        portfolio_ids=["p1", "p2"],
        team_scope=True,
    )
    payload = customer_shared_coverage_to_dict(items)

    repository.list_portfolios.assert_called_once_with(active_only=True)
    repository.list_by_user_id.assert_not_called()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["shared"] is True
    assert [ref["display_name"] for ref in payload["items"][0]["also_in_portfolios"]] == [
        "Sul",
        "Ana",
    ]


def test_lookup_customer_shared_coverage_seller_uses_own_portfolios() -> None:
    repository = MagicMock()
    repository.list_by_user_id.return_value = [
        _portfolio(
            id="p1",
            display_name="Minha A",
            customers=(SellerCustomerAssignment("100", "01", "Cliente"),),
        ),
        _portfolio(
            id="p2",
            display_name="Minha B",
            customers=(SellerCustomerAssignment("100", "01", "Cliente"),),
        ),
    ]
    use_case = ManageSellerPortfolioUseCase(repository)

    items = use_case.lookup_customer_shared_coverage(
        customers=[("100", "01"), ("200", "01")],
        actor_user_id="u1",
        team_scope=False,
    )

    repository.list_by_user_id.assert_called_once_with("u1", active_only=True)
    repository.list_portfolios.assert_not_called()
    assert len(items) == 1
    assert items[0].customer_code == "100"


def test_summarize_portfolio_load_returns_stubbed_totvs_metrics() -> None:
    repository = MagicMock()
    repository.list_portfolios.return_value = [
        _portfolio(
            id="p1",
            members=(
                SellerPortfolioMember(user_id="u1", role="owner"),
                SellerPortfolioMember(user_id="u2", role="member"),
            ),
        ),
    ]
    use_case = ManageSellerPortfolioUseCase(repository)

    summary = use_case.summarize_portfolio_load(active_only=False)
    payload = load_summary_to_dict(summary)

    repository.list_portfolios.assert_called_once_with(active_only=False)
    assert payload["portfolios"][0]["customer_count"] == 2
    assert payload["portfolios"][0]["member_count"] == 2
    assert payload["portfolios"][0]["open_value"] is None
    assert payload["portfolios"][0]["attention_count"] is None
    assert payload["by_person"][0]["user_id"] == "u1"
    assert payload["totvs_metrics"]["available"] is False
    assert payload["totvs_metrics"]["reason"] == "open_orders_aggregation_not_wired"


def test_portfolio_to_dict_includes_member_count() -> None:
    payload = portfolio_to_dict(
        _portfolio(
            members=(
                SellerPortfolioMember(user_id="u1", role="owner"),
                SellerPortfolioMember(user_id="u2", role="member"),
            ),
        )
    )
    assert payload["member_count"] == 2
    assert len(payload["members"]) == 2
