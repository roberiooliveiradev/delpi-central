"""Canonical portfolio membership summary (counts + role for a viewer)."""

from __future__ import annotations

from typing import Any

from commercial_app.domain.entities.seller_portfolio import SellerPortfolio


def portfolio_membership_summary(
    portfolio: SellerPortfolio,
    *,
    viewer_user_id: str | None = None,
) -> dict[str, Any]:
    """Return role (for viewer), customer_count and member_count for one portfolio.

    Shared by profile GET and seller-portfolio serialization so Admin and
    profile cards never diverge.
    """
    members = tuple(portfolio.members or ())
    member_count = len(members)
    if member_count == 0 and portfolio.user_id:
        member_count = 1

    uid = (viewer_user_id or "").strip()
    role = "member"
    if uid:
        for member in members:
            if str(member.user_id).strip() == uid:
                role = "owner" if member.role == "owner" else "member"
                break
        else:
            if str(portfolio.user_id).strip() == uid or str(
                portfolio.owner_user_id
            ).strip() == uid:
                role = "owner"

    return {
        "role": role,
        "customer_count": len(portfolio.customers or ()),
        "member_count": member_count,
    }


def portfolio_profile_summary_dict(
    portfolio: SellerPortfolio,
    *,
    viewer_user_id: str,
) -> dict[str, Any]:
    """Compact portfolio row for GET /users/{id}/profile."""
    summary = portfolio_membership_summary(
        portfolio, viewer_user_id=viewer_user_id
    )
    return {
        "id": str(portfolio.id),
        "name": portfolio.display_name,
        "active": bool(portfolio.active),
        "user_id": portfolio.user_id,
        "owner_user_id": portfolio.owner_user_id,
        "role": summary["role"],
        "customer_count": summary["customer_count"],
        "member_count": summary["member_count"],
    }
