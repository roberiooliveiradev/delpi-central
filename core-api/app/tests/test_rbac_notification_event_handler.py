# app/tests/test_rbac_notification_event_handler.py

from uuid import uuid4

from app.application.event_handlers.rbac_notification_event_handler import (
    RbacNotificationEventHandler,
)
from app.application.services.rbac_access_delta_service import AccessGain
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.ports.app_query_port import AppDTO, RouteDTO


class FakeUser:
    def __init__(self, user_id):
        self.id = user_id
        self.name = "Maria"
        self.active = True
        self.is_superadmin = False


class FakeUoW:
    def __init__(self):
        self.users = self
        self.permission_queries = self
        self.cache = None
        self.app_queries = self
        self.notifications = self
        self.rbac_queries = self
        self._events = []
        self._user = None

    def get_by_id(self, user_id):
        return self._user

    def list_permissions_by_role_id(self, role_id):
        return []

    def list_user_ids_by_role(self, role_id):
        return []

    def list_user_ids_by_group_role(self, role_id):
        return []

    def list_user_ids_by_group(self, group_id):
        return []

    def create(self, dto):
        self.last_dto = dto
        return uuid4()

    def collect_event(self, event):
        self._events.append(event)


def test_roles_replaced_with_added_role_ids_triggers_notification():
    user_id = uuid4()
    uow = FakeUoW()
    uow._user = FakeUser(user_id)

    app = AppDTO(
        id="a1",
        name="App",
        base_path="/app",
        icon=None,
        type="internal",
        entry_url=None,
        render_mode=None,
        routes=[],
    )
    gain = AccessGain(new_apps=[app], new_routes=[], new_permission_codes=["x.access"])

    handler = RbacNotificationEventHandler(uow)
    handler._delta_service.previous_codes_excluding_user_roles = (
        lambda *a, **k: []
    )
    handler._delta_service.compute_gain = lambda *a, **k: gain

    handler.handle(
        AdminChangedEvent(
            entity="rbac",
            action="roles_replaced",
            payload={"userId": str(user_id), "addedRoleIds": [str(uuid4())]},
            target_user_id=str(user_id),
        )
    )

    assert len(uow._events) == 1
    assert uow._events[0].action == "notification_created"


def test_roles_replaced_without_added_skips():
    uow = FakeUoW()
    handler = RbacNotificationEventHandler(uow)

    handler.handle(
        AdminChangedEvent(
            entity="rbac",
            action="roles_replaced",
            payload={"userId": str(uuid4())},
            target_user_id=str(uuid4()),
        )
    )

    assert uow._events == []


def test_send_notification_skips_route_list_for_whole_new_app():
    uow = FakeUoW()
    uow._user = FakeUser(uuid4())
    handler = RbacNotificationEventHandler(uow)

    app = AppDTO(
        id="chat-1",
        name="Minha DELPI Chat",
        base_path="/chat",
        icon=None,
        type="internal",
        entry_url=None,
        render_mode=None,
        routes=[
            RouteDTO(
                path="/",
                label="Minha DELPI Chat",
                icon=None,
                permission_code="chat.access",
                show_in_menu=True,
                order=0,
                entry=None,
            ),
        ],
    )
    gain = AccessGain(
        new_apps=[app],
        new_routes=[(app, app.routes[0])],
        new_permission_codes=["chat.access"],
    )

    handler._send_notification(uow._user, gain)

    vars_meta = uow.last_dto.metadata["vars"]
    assert vars_meta["appNames"] == "Minha DELPI Chat"
    assert vars_meta.get("featureNames", "") == ""


def test_send_notification_for_system_permissions_only():
    uow = FakeUoW()
    uow._user = FakeUser(uuid4())
    handler = RbacNotificationEventHandler(uow)

    from app.application.services.rbac_access_delta_service import (
        AccessGain,
        SystemPermissionGain,
    )

    gain = AccessGain(
        new_system_permissions=[
            SystemPermissionGain(code="rbac.manage", name="Gerenciar RBAC"),
        ],
        new_permission_codes=["rbac.manage"],
    )

    handler._send_notification(uow._user, gain)

    assert uow.last_dto.title == "Novas permissões de administração"
    assert "permissões de sistema" in uow.last_dto.message
    assert uow.last_dto.action_target == "/admin"
    assert uow.last_dto.metadata["vars"]["systemPermissionNames"] == "Gerenciar RBAC"


def test_format_feature_label_ignores_generic_abrir():
    app = AppDTO(
        id="dash",
        name="Dashboard DELPI",
        base_path="/dash",
        icon=None,
        type="internal",
        entry_url=None,
        render_mode=None,
        routes=[],
    )
    route = RouteDTO(
        path="/",
        label="Abrir",
        icon=None,
        permission_code="dash.access",
        show_in_menu=True,
        order=0,
        entry=None,
    )

    assert RbacNotificationEventHandler._format_feature_label(app, route) is None


def test_role_permissions_replaced_without_added_skips():
    uow = FakeUoW()
    handler = RbacNotificationEventHandler(uow)

    handler.handle(
        AdminChangedEvent(
            entity="rbac",
            action="role_permissions_replaced",
            payload={"roleId": str(uuid4())},
        )
    )

    assert uow._events == []
