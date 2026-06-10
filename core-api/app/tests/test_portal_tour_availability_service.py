# app/tests/test_portal_tour_availability_service.py

from app.domain.portal_tour.portal_tour_availability_service import (
    PortalTourUserContext,
    resolve_available_quests,
    resolve_new_quest_ids,
    resolve_required_quest_ids,
)
from app.domain.portal_tour.portal_tour_quest_catalog import (
    CURRENT_PORTAL_TOUR_VERSION,
)


def test_resolve_available_quests_excludes_admin_without_permission():
    context = PortalTourUserContext(
        permissions=frozenset(),
        is_superadmin=False,
    )

    available = resolve_available_quests(context)
    ids = {quest.id for quest in available}

    assert "open-apps" in ids
    assert "sidebar-admin" not in ids
    assert "page-admin-users" not in ids


def test_resolve_available_quests_includes_admin_with_rbac_manage():
    context = PortalTourUserContext(
        permissions=frozenset({"rbac.manage"}),
        is_superadmin=False,
    )

    available = resolve_available_quests(context)
    ids = {quest.id for quest in available}

    assert "sidebar-admin" in ids
    assert "page-admin-apps" in ids


def test_required_quest_ids_ignore_optional_admin():
    context = PortalTourUserContext(
        permissions=frozenset({"rbac.manage"}),
        is_superadmin=False,
    )
    available = resolve_available_quests(context)
    required = resolve_required_quest_ids(available)

    assert "sidebar-admin" not in required
    assert "open-apps" in required


def test_resolve_new_quest_ids_for_current_version():
    context = PortalTourUserContext(
        permissions=frozenset(),
        is_superadmin=False,
    )
    available = resolve_available_quests(context)

    new_ids = resolve_new_quest_ids(
        available,
        completed_quest_ids={"open-apps"},
        tour_version=CURRENT_PORTAL_TOUR_VERSION,
    )

    assert "open-apps" not in new_ids
    assert "pin-app" in new_ids
