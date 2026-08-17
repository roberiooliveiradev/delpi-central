from __future__ import annotations

from typing import Any, Protocol, Sequence

from commercial_app.application.use_cases.manage_commercial_groups import (
    ManageCommercialGroupsUseCase,
    group_summary_to_dict,
)
from commercial_app.domain.entities.seller_portfolio import SellerPortfolio
from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.domain.services.portfolio_membership_summary_service import (
    portfolio_profile_summary_dict,
)
from commercial_app.domain.services.team_roster_messages_content_service import (
    TeamRosterMessagesContentService,
)


def _normalize(value: str | None) -> str:
    return str(value or "").strip()


class TeamRosterDirectoryPort(Protocol):
    def lookup_directory_users(
        self,
        user_ids: Sequence[str],
    ) -> dict[str, dict[str, str]]:
        ...

    def list_directory_users_with_app_access(self) -> list[dict[str, str]]:
        ...


def _member_ids(portfolio: SellerPortfolio) -> list[str]:
    members = [
        _normalize(member.user_id)
        for member in portfolio.members
        if _normalize(member.user_id)
    ]
    if members:
        ordered: list[str] = []
        seen: set[str] = set()
        for user_id in members:
            if user_id in seen:
                continue
            seen.add(user_id)
            ordered.append(user_id)
        return ordered
    owner = _normalize(portfolio.owner_user_id or portfolio.user_id)
    return [owner] if owner else []


class ManageTeamRosterUseCase:
    """BFF Equipe: directory commercial + grupos + carteiras."""

    def __init__(
        self,
        *,
        groups: ManageCommercialGroupsUseCase,
        portfolios: SellerPortfolioRepositoryPort,
        directory: TeamRosterDirectoryPort | None = None,
    ) -> None:
        self._groups = groups
        self._portfolios = portfolios
        self._directory = directory

    def list_roster(
        self,
        *,
        group_id: str | None = None,
        portfolio_id: str | None = None,
        q: str | None = None,
    ) -> list[dict[str, Any]]:
        gid = _normalize(group_id)
        pid = _normalize(portfolio_id)
        query = _normalize(q).lower()

        group_filter_ids: set[str] | None = None
        if gid:
            try:
                self._groups.get_group(gid)
            except LookupError as exc:
                raise LookupError(
                    TeamRosterMessagesContentService.error("groupNotFound")
                ) from exc
            group_filter_ids = set(self._groups.list_member_user_ids_by_group_id(gid))

        portfolio_filter_ids: set[str] | None = None
        portfolios = self._portfolios.list_portfolios(active_only=False)
        if pid:
            target = next((item for item in portfolios if item.id == pid), None)
            if target is None:
                raise LookupError(
                    TeamRosterMessagesContentService.error("portfolioNotFound")
                )
            portfolio_filter_ids = set(_member_ids(target))

        candidate_ids = self._resolve_candidate_ids(
            group_filter_ids=group_filter_ids,
            portfolio_filter_ids=portfolio_filter_ids,
            portfolios=portfolios,
        )

        directory_by_id = self._lookup_users(sorted(candidate_ids))
        memberships = self._groups.list_memberships_by_user_ids(sorted(candidate_ids))
        groups_by_user: dict[str, list[dict[str, Any]]] = {}
        for user_id, group in memberships:
            uid = _normalize(user_id)
            if not uid:
                continue
            groups_by_user.setdefault(uid, []).append(group_summary_to_dict(group))

        portfolios_by_user: dict[str, list[dict[str, Any]]] = {}
        for portfolio in portfolios:
            for member_id in _member_ids(portfolio):
                portfolios_by_user.setdefault(member_id, []).append(
                    portfolio_profile_summary_dict(portfolio, viewer_user_id=member_id)
                )

        items: list[dict[str, Any]] = []
        for user_id in sorted(candidate_ids):
            directory = directory_by_id.get(user_id) or {}
            name = str(directory.get("name") or user_id).strip() or user_id
            email = str(directory.get("email") or "").strip()
            if query and query not in name.lower() and query not in email.lower():
                continue
            items.append(
                {
                    "user_id": user_id,
                    "name": name,
                    "email": email,
                    "groups": groups_by_user.get(user_id, []),
                    "portfolios": portfolios_by_user.get(user_id, []),
                }
            )
        return items

    def _resolve_candidate_ids(
        self,
        *,
        group_filter_ids: set[str] | None,
        portfolio_filter_ids: set[str] | None,
        portfolios: Sequence[SellerPortfolio],
    ) -> set[str]:
        if group_filter_ids is not None and portfolio_filter_ids is not None:
            return {
                uid
                for uid in (group_filter_ids & portfolio_filter_ids)
                if uid
            }
        if group_filter_ids is not None:
            return {uid for uid in group_filter_ids if uid}
        if portfolio_filter_ids is not None:
            return {uid for uid in portfolio_filter_ids if uid}

        candidates: set[str] = set()
        for group in self._groups.list_groups(active_only=False):
            for member in group.members:
                uid = _normalize(member.user_id)
                if uid:
                    candidates.add(uid)
        for portfolio in portfolios:
            for uid in _member_ids(portfolio):
                candidates.add(uid)
        for item in self._list_directory_commercial():
            uid = _normalize(item.get("id"))
            if uid:
                candidates.add(uid)
        return candidates

    def _list_directory_commercial(self) -> list[dict[str, str]]:
        if self._directory is None:
            return []
        list_all = getattr(self._directory, "list_directory_users_with_app_access", None)
        if callable(list_all):
            try:
                items = list_all()
            except Exception:
                return []
            return [item for item in items if isinstance(item, dict)]
        # Fallback legado (typeahead) — não cobre o universo completo.
        search = getattr(self._directory, "search_directory_users", None)
        if not callable(search):
            return []
        try:
            items = search(query=None, limit=20, browse=True)
        except Exception:
            return []
        return [item for item in items if isinstance(item, dict)]

    def _lookup_users(self, user_ids: Sequence[str]) -> dict[str, dict[str, str]]:
        if self._directory is None or not user_ids:
            return {}
        try:
            return self._directory.lookup_directory_users(user_ids)
        except Exception:
            return {}
