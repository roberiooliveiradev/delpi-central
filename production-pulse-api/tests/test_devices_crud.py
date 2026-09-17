def test_devices_crud_round_trip(client, unique_ip):
    create_body = {
        "name": "ESP contador piloto",
        "branch": "01",
        "ipAddress": unique_ip,
        "driverKey": "esp8266_counter_v1",
        "pollIntervalMs": 30_000,
        "enabled": True,
    }

    created = client.post("/devices", json=create_body)
    assert created.status_code == 201
    created_json = created.json()
    assert created_json["success"] is True
    device = created_json["data"]
    assert device["branch"] == "01"
    assert device["ipAddress"] == unique_ip
    assert device["driverKey"] == "esp8266_counter_v1"
    assert device["roleKey"] == "pulse_counter"
    device_id = device["id"]

    listed = client.get("/devices", params={"branch": "01"})
    assert listed.status_code == 200
    assert len(listed.json()["data"]["items"]) == 1

    fetched = client.get(f"/devices/{device_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == device_id

    patched = client.patch(
        f"/devices/{device_id}",
        json={"name": "ESP contador renomeado", "pollIntervalMs": 45_000},
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["name"] == "ESP contador renomeado"
    assert patched.json()["data"]["pollIntervalMs"] == 45_000

    replaced = client.put(
        f"/devices/{device_id}",
        json={
            **create_body,
            "name": "ESP contador replace",
            "pollIntervalMs": 60_000,
        },
    )
    assert replaced.status_code == 200
    assert replaced.json()["data"]["name"] == "ESP contador replace"
    assert replaced.json()["data"]["pollIntervalMs"] == 60_000

    deleted = client.delete(f"/devices/{device_id}")
    assert deleted.status_code == 200
    assert deleted.json()["data"]["enabled"] is False


def test_create_device_rejects_duplicate_ip(client, unique_ip):
    body = {
        "name": "ESP A",
        "branch": "01",
        "ipAddress": unique_ip,
        "driverKey": "esp8266_counter_v1",
    }
    assert client.post("/devices", json=body).status_code == 201
    conflict = client.post("/devices", json={**body, "name": "ESP B"})
    assert conflict.status_code == 409


def test_create_device_persists_controller_code(client, unique_ip):
    code = f"ESP-{unique_ip.replace('.', '')[-6:].upper()}"
    created = client.post(
        "/devices",
        json={
            "name": "ESP com código",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
            "controllerCode": code,
        },
    )
    assert created.status_code == 201
    data = created.json()["data"]
    assert data["controllerCode"] == code

    fetched = client.get(f"/devices/{data['id']}")
    assert fetched.json()["data"]["controllerCode"] == code


def test_create_device_persists_firmware_source(client, unique_ip):
    sketch = "// Teste.ino\nvoid setup() {}\nvoid loop() {}\n"
    created = client.post(
        "/devices",
        json={
            "name": "ESP com firmware",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
            "firmwareSource": sketch,
        },
    )
    assert created.status_code == 201
    data = created.json()["data"]
    assert data["firmwareSource"] == sketch.rstrip("\n")

    fetched = client.get(f"/devices/{data['id']}")
    assert fetched.json()["data"]["firmwareSource"] == sketch.rstrip("\n")

    listed = client.get("/devices", params={"branch": "01"})
    assert listed.status_code == 200
    item = next(row for row in listed.json()["data"]["items"] if row["id"] == data["id"])
    assert item.get("firmwareSource") in (None, "")

    replaced = client.put(
        f"/devices/{data['id']}",
        json={
            "name": "ESP com firmware",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
            "firmwareSource": "",
        },
    )
    assert replaced.status_code == 200
    assert replaced.json()["data"]["firmwareSource"] is None


def test_create_device_persists_wifi_and_token_mirror(client, unique_ip):
    created = client.post(
        "/devices",
        json={
            "name": "ESP wifi",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
            "wifiSsid": "PlantNet",
            "debounceMs": 120,
            "apiToken": "tok-abc",
        },
    )
    assert created.status_code == 201
    data = created.json()["data"]
    assert data["wifiSsid"] == "PlantNet"
    assert data["debounceMs"] == 120
    assert data["apiTokenSet"] is True
    assert "apiToken" not in data
    assert "wifiPassword" not in data
    assert data["deviceConfigPush"]["status"] in {"ok", "skipped", "failed"}

    fetched = client.get(f"/devices/{data['id']}")
    body = fetched.json()["data"]
    assert body["apiTokenSet"] is True
    assert "apiToken" not in body


def test_create_device_auto_generates_token_when_omitted(client, unique_ip):
    created = client.post(
        "/devices",
        json={
            "name": "ESP auto token",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    )
    assert created.status_code == 201
    data = created.json()["data"]
    assert data["apiTokenSet"] is True
    assert "apiToken" not in data

    fetched = client.get(f"/devices/{data['id']}")
    assert fetched.json()["data"]["apiTokenSet"] is True
    assert "apiToken" not in fetched.json()["data"]


def test_replace_does_not_regenerate_existing_token(client, unique_ip, monkeypatch):
    created = client.post(
        "/devices",
        json={
            "name": "ESP keep token",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
            "apiToken": "keep-me-token",
        },
    )
    assert created.status_code == 201
    device_id = created.json()["data"]["id"]

    from production_pulse_app.application.services.device_service import DeviceService

    calls: list[str] = []
    original = DeviceService._generate_device_api_token

    def _spy(self):
        calls.append("generated")
        return original(self)

    monkeypatch.setattr(DeviceService, "_generate_device_api_token", _spy)

    replaced = client.put(
        f"/devices/{device_id}",
        json={
            "name": "ESP keep token",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
            "pollIntervalMs": 500,
        },
    )
    assert replaced.status_code == 200
    assert replaced.json()["data"]["apiTokenSet"] is True
    assert "apiToken" not in replaced.json()["data"]
    assert calls == []
