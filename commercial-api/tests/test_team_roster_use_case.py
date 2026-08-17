from __future__ import annotations

import pytest

from commercial_app.application.use_cases.manage_commercial_groups import (
    ManageCommercialGroupsUseCase,
)
from commercial_app.application.use_cases.manage_team_roster import ManageTeamRosterUseCase
from commercial_app.domain.entities.commercial_group import (
    CommercialGroup,
    CommercialGroupMember,
)
from commercial_app.domain.entities.seller_portfolio import (
    SellerPortfolio,
    SellerPortfolioMember,
)


def _group(
    *,
    group_id: str = "g-sellers",
    kind: str = "sellers",
    name: str = "Vendedores",
    members: tuple[str, ...] = ("u1", "u2"),
) -> CommercialGroup:
    return CommercialGroup(
        id=group_id,
        kind=kind,
        name=name,
        active=True,
        sort_order=10,
        members=tuple(CommercialGroupMember(user_id=uid) for uid in members),
    )


def _portfolio(
    *,
    portfolio_id: str = "p1",
    display_name: str = "Sul",
    members: tuple[tuple[str, str], ...] = (("u1", "owner"), ("u3", "member")),
) -> SellerPortfolio:
    return SellerPortfolio(
        id=portfolio_id,
        user_id=members[0][0] if members else "u1",
        display_name=display_name,
        active=True,
        customers=(),
        members=tuple(
            SellerPortfolioMember(user_id=uid, role=role) for uid, role in members
        ),
    )


class FakeGroupsRepo:
    def __init__(self, groups: list[CommercialGroup]) -> None:
        self._groups = {item.id: item for item in groups}

    def get_by_id(self, group_id: str) -> CommercialGroup | None:
        return self._groups.get(group_id)

    def get_by_kind(self, kind: str) -> CommercialGroup | None:
        for item in self._groups.values():
            if item.kind == kind:
                return item
        return None

    def list_groups(self, *, active_only: bool = False) -> list[CommercialGroup]:
        items = list(self._groups.values())
        if active_only:
            items = [item for item in items if item.active]
        return items

    def create_group(self, **kwargs):  # noqa: ANN003
        raise NotImplementedError

    def replace_members(self, **kwargs):  # noqa: ANN003
        raise NotImplementedError

    def add_member(self, **kwargs):  # noqa: ANN003
        raise NotImplementedError

    def remove_member(self, **kwargs):  # noqa: ANN003
        raise NotImplementedError

    def list_member_user_ids_by_group_id(self, group_id: str) -> list[str]:
        group = self._groups.get(group_id)
        if group is None:
            return []
        return list(group.member_user_ids)

    def list_groups_by_user_id(self, user_id: str) -> list[CommercialGroup]:
        return [
            CommercialGroup(
                id=item.id,
                kind=item.kind,
                name=item.name,
                active=item.active,
                sort_order=item.sort_order,
                members=(),
            )
            for item in self._groups.values()
            if user_id in item.member_user_ids
        ]

    def list_memberships_by_user_ids(self, user_ids):
        wanted = {str(uid).strip() for uid in user_ids if str(uid or "").strip()}
        rows = []
        for group in self._groups.values():
            for member in group.members:
                if member.user_id in wanted:
                    rows.append(
                        (
                            member.user_id,
                            CommercialGroup(
                                id=group.id,
                                kind=group.kind,
                                name=group.name,
                                active=group.active,
                                sort_order=group.sort_order,
                                members=(),
                            ),
                        )
                    )
        return rows


class FakePortfolioRepo:
    def __init__(self, portfolios: list[SellerPortfolio]) -> None:
        self._portfolios = portfolios

    def list_portfolios(self, *, active_only: bool = False) -> list[SellerPortfolio]:
        items = list(self._portfolios)
        if active_only:
            items = [item for item in items if item.active]
        return items

    def list_by_user_id(self, user_id: str, *, active_only: bool = True):
        return []

    def get_by_id(self, portfolio_id: str):
        return next((item for item in self._portfolios if item.id == portfolio_id), None)


class FakeDirectory:
    def __init__(self, users: dict[str, dict[str, str]] | None = None) -> None:
        self._users = users or {
            "u1": {"id": "u1", "name": "Ana", "email": "ana@delpi.com"},
            "u2": {"id": "u2", "name": "Bruno", "email": "bruno@delpi.com"},
            "u3": {"id": "u3", "name": "Carla", "email": "carla@delpi.com"},
            "u4": {"id": "u4", "name": "Diego", "email": "diego@delpi.com"},
        }

    def lookup_directory_users(self, user_ids):
        return {
            uid: self._users[uid]
            for uid in user_ids
            if uid in self._users
        }

    def search_directory_users(self, *, query=None, limit=20, browse=False):
        _ = query, limit, browse
        return [self._users["u4"]]


def _use_case() -> ManageTeamRosterUseCase:
    groups = ManageCommercialGroupsUseCase(FakeGroupsRepo([_group()]))
    portfolios = FakePortfolioRepo([_portfolio()])
    return ManageTeamRosterUseCase(
        groups=groups,
        portfolios=portfolios,
        directory=FakeDirectory(),
    )


def test_list_roster_combines_groups_portfolios_and_directory() -> None:
    items = _use_case().list_roster()
    by_id = {item["user_id"]: item for item in items}
    assert set(by_id) == {"u1", "u2", "u3", "u4"}
    assert by_id["u1"]["name"] == "Ana"
    assert by_id["u1"]["groups"][0]["kind"] == "sellers"
    assert by_id["u1"]["portfolios"][0]["id"] == "p1"
    assert by_id["u2"]["portfolios"] == []
    assert by_id["u3"]["groups"] == []
    assert by_id["u4"]["groups"] == []
    assert by_id["u4"]["portfolios"] == []


def test_list_roster_filters_by_group_id() -> None:
    items = _use_case().list_roster(group_id="g-sellers")
    assert {item["user_id"] for item in items} == {"u1", "u2"}
    assert all(any(g["id"] == "g-sellers" for g in item["groups"]) for item in items)


def test_list_roster_filters_by_portfolio_id() -> None:
    items = _use_case().list_roster(portfolio_id="p1")
    assert {item["user_id"] for item in items} == {"u1", "u3"}


def test_list_roster_intersection_group_and_portfolio() -> None:
    items = _use_case().list_roster(group_id="g-sellers", portfolio_id="p1")
    assert {item["user_id"] for item in items} == {"u1"}


def test_list_roster_search_q() -> None:
    items = _use_case().list_roster(q="bru")
    assert len(items) == 1
    assert items[0]["user_id"] == "u2"


def test_list_roster_unknown_group_raises() -> None:
    with pytest.raises(LookupError):
        _use_case().list_roster(group_id="missing")


def test_list_roster_unknown_portfolio_raises() -> None:
    with pytest.raises(LookupError):
        _use_case().list_roster(portfolio_id="missing")


def test_administration_route_registered() -> None:
    from pathlib import Path

    routes = (
        Path(__file__).resolve().parents[1]
        / "commercial_app"
        / "interface"
        / "http"
        / "routes"
        / "administration_routes.py"
    ).read_text(encoding="utf-8")
    main = (
        Path(__file__).resolve().parents[1]
        / "commercial_app"
        / "main.py"
    ).read_text(encoding="utf-8")
    assert 'prefix="/administration"' in routes
    assert 'operation_id="list_commercial_team_roster"' in routes
    assert "COMMERCIAL_MANAGE_PERMISSIONS" in routes
    assert "group_id" in routes and "portfolio_id" in routes and "q:" in routes
    assert "administration_router" in main
