from uuid import uuid4


def _create_device(client, unique_ip: str, name: str = "ESP teste"):
    response = client.post(
        "/devices",
        json={
            "name": name,
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_equipment_binding_without_work_center_ok(client, unique_ip):
    device = _create_device(client, unique_ip, "ESP ventilador")

    response = client.put(
        f"/devices/{device['id']}/binding",
        json={
            "anchorType": "equipment",
            "equipmentLabel": "Ventilador exaustão setor A",
        },
    )
    assert response.status_code == 200
    binding = response.json()["data"]
    assert binding["anchorType"] == "equipment"
    assert binding["placementLabel"] == "Ventilador exaustão setor A"
    assert binding["placementKey"] == "e:01:ventilador-exaustao-setor-a"
    assert binding["workCenterCode"] is None

    detail = client.get(f"/devices/{device['id']}")
    assert detail.json()["data"]["binding"]["placementKey"] == binding["placementKey"]


def test_work_center_binding_requires_work_center_code(client, unique_ip):
    device = _create_device(client, unique_ip, "ESP posto")

    response = client.put(
        f"/devices/{device['id']}/binding",
        json={"anchorType": "work_center"},
    )
    assert response.status_code == 422


def test_two_devices_same_machine_anchor_ok(client, unique_ip):
    device_a = _create_device(client, unique_ip, "ESP torno A")
    device_b = _create_device(
        client,
        f"192.168.20.{150 + int(uuid4().hex[:2], 16) % 100}",
        "ESP torno B",
    )
    machine_label = "Torno CNC #2"
    payload = {"anchorType": "machine", "machineLabel": machine_label}

    first = client.put(f"/devices/{device_a['id']}/binding", json=payload)
    second = client.put(f"/devices/{device_b['id']}/binding", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["placementKey"] == second.json()["data"]["placementKey"]
    assert first.json()["data"]["placementLabel"] == machine_label


def test_binding_history_closes_previous(client, unique_ip):
    device = _create_device(client, unique_ip)

    client.put(
        f"/devices/{device['id']}/binding",
        json={"anchorType": "equipment", "equipmentLabel": "Motor A"},
    )
    client.put(
        f"/devices/{device['id']}/binding",
        json={"anchorType": "equipment", "equipmentLabel": "Motor B"},
    )

    history = client.get(f"/devices/{device['id']}/bindings/history")
    assert history.status_code == 200
    items = history.json()["data"]["items"]
    assert len(items) == 2
    assert items[0]["equipmentLabel"] == "Motor B"
    assert items[0]["effectiveTo"] is None
    assert items[1]["effectiveTo"] is not None


def test_delete_binding(client, unique_ip):
    device = _create_device(client, unique_ip)
    client.put(
        f"/devices/{device['id']}/binding",
        json={"anchorType": "area", "areaLabel": "Sala HVAC"},
    )

    deleted = client.delete(f"/devices/{device['id']}/binding")
    assert deleted.status_code == 200

    active = client.get(f"/devices/{device['id']}/binding")
    assert active.status_code == 200
    assert active.json()["data"] is None
