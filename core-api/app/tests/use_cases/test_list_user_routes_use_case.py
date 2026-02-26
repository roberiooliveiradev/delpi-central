# app/tests/test_list_user_routes_use_case.py

from app.application.use_cases.list_user_routes_use_case import ListUserRoutesUseCase


class DummyRoute:
    def __init__(self, app_id, path, label, icon, order, permission_code):
        self.app_id = app_id
        self.path = path
        self.label = label
        self.icon = icon
        self.order_index = order
        self.permission_code = permission_code


class DummyAppRoutesRepo:
    def list_active_routes(self):
        return [
            DummyRoute("crm", "/crm", "Dashboard", "home", 1, "crm.access"),
            DummyRoute("crm", "/crm/leads", "Leads", "users", 2, "crm.leads.read"),
            DummyRoute("gpt", "/gpt", "GPT", "bot", 1, "gpt.access"),
        ]


class DummyUoW:
    def __init__(self):
        self.app_routes = DummyAppRoutesRepo()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


def test_list_user_routes_filters_by_permission():
    uow = DummyUoW()
    uc = ListUserRoutesUseCase(uow)

    permissions = ["crm.access", "crm.leads.read"]

    result = uc.execute(user_id="123", permissions=permissions)

    assert len(result) == 2
    assert result[0]["path"] == "/crm"
    assert result[1]["path"] == "/crm/leads"


def test_list_user_routes_returns_empty_when_no_permission():
    uow = DummyUoW()
    uc = ListUserRoutesUseCase(uow)

    permissions = []

    result = uc.execute(user_id="123", permissions=permissions)

    assert result == []