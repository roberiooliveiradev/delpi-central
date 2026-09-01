from types import SimpleNamespace
from uuid import uuid4

from production_pulse_app.application.security import production_pulse_permissions as perms
from production_pulse_app.domain.models.device_reading import CommandResult


def test_admin_sees_all_branches():
    user = SimpleNamespace(permissions=[perms.ADMIN], is_superadmin=False)
    assert perms.branch_codes_for_access(user) == ["01", "02"]
    assert perms.can_view_devices(user)
    assert perms.can_manage_devices(user)
    assert perms.can_admin_command(user)
    assert perms.can_operator(user)


def test_viewer_can_read_but_not_manage():
    user = SimpleNamespace(
        permissions=[perms.DEVICES_VIEW, perms.BRANCH_VIEW_PERMISSIONS["01"]],
        is_superadmin=False,
    )
    assert perms.can_view_devices(user)
    assert not perms.can_manage_devices(user)
    assert not perms.can_admin_command(user)
    assert not perms.can_operator(user)


def test_operator_can_command_without_view():
    user = SimpleNamespace(
        permissions=[perms.OPERATOR, perms.BRANCH_VIEW_PERMISSIONS["01"]],
        is_superadmin=False,
    )
    assert perms.can_operator(user)
    assert not perms.can_view_devices(user)
    assert not perms.can_admin_command(user)


def _create_device(client, unique_ip: str, branch: str = "01"):
    response = client.post(
        "/devices",
        json={
            "name": "ESP RBAC",
            "branch": branch,
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_viewer_cannot_create_device(client_factory, unique_ip):
    client = client_factory(
        [perms.DEVICES_VIEW, perms.BRANCH_VIEW_PERMISSIONS["01"]],
    )
    response = client.post(
        "/devices",
        json={
            "name": "ESP negado",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    )
    assert response.status_code == 403


def test_viewer_cannot_execute_admin_command(client_factory, unique_ip, monkeypatch):
    manager = client_factory([perms.ADMIN])
    device = _create_device(manager, unique_ip)

    viewer = client_factory(
        [perms.DEVICES_VIEW, perms.BRANCH_VIEW_PERMISSIONS["01"]],
    )

    class _FakeDriver:
        driver_key = "esp8266_counter_v1"

        def execute(self, device, command_key, payload=None):
            return CommandResult(success=True, metrics={"counter": 0})

    from production_pulse_app.interface.http.routes import device_routes as routes_module

    monkeypatch.setattr(
        routes_module._command_service._registry,
        "get_implementation",
        lambda key: _FakeDriver(),
    )

    response = viewer.post(f"/devices/{device['id']}/commands/reset")
    assert response.status_code == 403


def test_operator_commands_without_devices_view(client_factory, unique_ip, monkeypatch):
    manager = client_factory([perms.ADMIN])
    device = _create_device(manager, unique_ip)
    manager.put(
        f"/devices/{device['id']}/binding",
        json={"anchorType": "equipment", "equipmentLabel": "Prensa operador"},
    )

    operator = client_factory(
        [perms.OPERATOR, perms.BRANCH_VIEW_PERMISSIONS["01"]],
    )

    class _FakeDriver:
        driver_key = "esp8266_counter_v1"

        def execute(self, device, command_key, payload=None):
            return CommandResult(success=True, metrics={"counter": 0})

    from production_pulse_app.interface.http.routes import operator_routes as routes_module

    monkeypatch.setattr(
        routes_module._command_service._registry,
        "get_implementation",
        lambda key: _FakeDriver(),
    )

    denied_admin = operator.post(f"/devices/{device['id']}/commands/reset")
    assert denied_admin.status_code == 403

    allowed = operator.post(f"/operator/devices/{device['id']}/commands/reset")
    assert allowed.status_code == 200
    assert allowed.json()["success"] is True


def test_branch_access_denied_for_other_filial(client_factory, unique_ip):
    client = client_factory(
        [perms.DEVICES_VIEW, perms.BRANCH_VIEW_PERMISSIONS["01"]],
    )
    manager = client_factory([perms.ADMIN])
    device = _create_device(manager, unique_ip, branch="02")

    response = client.get(f"/devices/{device['id']}")
    assert response.status_code == 403


def test_operator_placements_requires_operator_permission(client_factory, unique_ip):
    manager = client_factory([perms.ADMIN])
    device = _create_device(manager, unique_ip)
    manager.put(
        f"/devices/{device['id']}/binding",
        json={"anchorType": "equipment", "equipmentLabel": "Motor hub"},
    )

    viewer = client_factory(
        [perms.DEVICES_VIEW, perms.BRANCH_VIEW_PERMISSIONS["01"]],
    )
    assert viewer.get("/operator/placements", params={"branch": "01"}).status_code == 403

    operator = client_factory(
        [perms.OPERATOR, perms.BRANCH_VIEW_PERMISSIONS["01"]],
    )
    response = operator.get("/operator/placements", params={"branch": "01"})
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["deviceCount"] == 1


def test_operator_cannot_access_other_branch_placements(client_factory, unique_ip):
    manager = client_factory([perms.ADMIN])
    device = _create_device(manager, unique_ip, branch="02")
    manager.put(
        f"/devices/{device['id']}/binding",
        json={"anchorType": "equipment", "equipmentLabel": "Motor ES"},
    )

    operator = client_factory(
        [perms.OPERATOR, perms.BRANCH_VIEW_PERMISSIONS["01"]],
    )
    response = operator.get("/operator/placements", params={"branch": "02"})
    assert response.status_code == 403


def test_manage_implies_admin_command(client_factory, unique_ip, monkeypatch):
    manager = client_factory([perms.ADMIN])
    device = _create_device(manager, unique_ip)

    supervisor = client_factory(
        [
            perms.DEVICES_MANAGE,
            perms.BRANCH_VIEW_PERMISSIONS["01"],
        ],
    )

    class _FakeDriver:
        driver_key = "esp8266_counter_v1"

        def execute(self, device, command_key, payload=None):
            return CommandResult(success=True, metrics={"counter": 1})

    from production_pulse_app.interface.http.routes import device_routes as routes_module

    monkeypatch.setattr(
        routes_module._command_service._registry,
        "get_implementation",
        lambda key: _FakeDriver(),
    )

    response = supervisor.post(f"/devices/{device['id']}/commands/reset")
    assert response.status_code == 200


def test_list_devices_scoped_to_allowed_branches(client_factory, unique_ip):
    admin = client_factory([perms.ADMIN])
    ip_es = f"192.168.20.{150 + int(uuid4().hex[:2], 16) % 100}"
    _create_device(admin, unique_ip, branch="01")
    _create_device(admin, ip_es, branch="02")

    viewer_sc = client_factory(
        [perms.DEVICES_VIEW, perms.BRANCH_VIEW_PERMISSIONS["01"]],
    )
    listed = viewer_sc.get("/devices")
    assert listed.status_code == 200
    branches = {item["branch"] for item in listed.json()["data"]["items"]}
    assert branches == {"01"}
