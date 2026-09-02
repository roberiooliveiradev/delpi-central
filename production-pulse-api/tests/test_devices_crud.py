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


def test_create_device_rejects_unknown_driver(client, unique_ip):
    response = client.post(
        "/devices",
        json={
            "name": "ESP inválido",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "unknown_driver_v9",
        },
    )
    assert response.status_code == 422
