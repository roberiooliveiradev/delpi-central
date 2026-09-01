def test_catalog_drivers_lists_registry(client):
    response = client.get("/catalog/drivers")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["schemaVersion"] == 1
    keys = {item["key"] for item in data["drivers"]}
    assert "esp8266_counter_v1" in keys
    assert "esp8266_gauge_v1" in keys

    counter = next(item for item in data["drivers"] if item["key"] == "esp8266_counter_v1")
    assert counter["roleKey"] == "pulse_counter"
    assert counter["operatorSurface"] == "counter_pad"


def test_get_device_includes_capabilities(client, unique_ip):
    created = client.post(
        "/devices",
        json={
            "name": "ESP capabilities",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    )
    device_id = created.json()["data"]["id"]

    fetched = client.get(f"/devices/{device_id}")
    assert fetched.status_code == 200
    device = fetched.json()["data"]
    assert device["capabilities"] == {
        "metrics": ["counter"],
        "commands": ["increment", "decrement", "reset"],
        "operatorSurface": "counter_pad",
    }
