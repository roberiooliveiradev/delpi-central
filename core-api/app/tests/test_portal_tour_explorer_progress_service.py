# app/tests/test_portal_tour_explorer_progress_service.py

from app.domain.portal_tour.portal_tour_availability_service import PortalTourUserContext
from app.domain.portal_tour.portal_tour_explorer_progress_service import (
    resolve_explorer_progress_snapshot,
)


def test_resolve_explorer_progress_for_standard_user():
    context = PortalTourUserContext(permissions=frozenset(), is_superadmin=False)
    snapshot = resolve_explorer_progress_snapshot(
        ["open-apps", "sidebar-favorites"],
        context,
    )

    assert snapshot.required_quest_total > 0
    assert snapshot.required_quest_done == 2
    assert 0 < snapshot.progress_percent < 100
    assert snapshot.explorer_level


def test_resolve_explorer_progress_for_superadmin_includes_admin_quests():
    context = PortalTourUserContext(permissions=frozenset(), is_superadmin=True)
    snapshot = resolve_explorer_progress_snapshot([], context)

    admin_context = PortalTourUserContext(
        permissions=frozenset({"rbac.manage"}),
        is_superadmin=False,
    )
    admin_snapshot = resolve_explorer_progress_snapshot([], admin_context)

    assert snapshot.required_quest_total >= admin_snapshot.required_quest_total
