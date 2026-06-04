from app.domain.services.chat_snapshot_operational_focus import ChatSnapshotOperationalFocus


def test_get_returns_operational_focus_only():
    focus = ChatSnapshotOperationalFocus.get(
        {"operationalFocus": {"productCode": "10080001", "branch": "02"}}
    )

    assert focus["productCode"] == "10080001"
    assert focus["branch"] == "02"


def test_get_ignores_removed_keys():
    focus = ChatSnapshotOperationalFocus.get(
        {
            "lastEntities": {"productCode": "99999999"},
            "activeEntities": {"branch": "99"},
            "operationalFocus": {"productCode": "10080055"},
        }
    )

    assert focus["productCode"] == "10080055"
    assert focus.get("branch") is None


def test_normalize_strips_removed_keys():
    snapshot = ChatSnapshotOperationalFocus.normalize(
        {
            "lastEntities": {"productCode": "10080055"},
            "activeEntities": {"branch": "01"},
            "operationalFocus": {"productCode": "10080055"},
        }
    )

    assert snapshot["operationalFocus"]["productCode"] == "10080055"
    assert "lastEntities" not in snapshot
    assert "activeEntities" not in snapshot


def test_set_strips_removed_keys():
    snapshot = ChatSnapshotOperationalFocus.set(
        {"lastEntities": {"productCode": "old"}, "activeEntities": {}},
        {"productCode": "10080099"},
    )

    assert snapshot["operationalFocus"]["productCode"] == "10080099"
    assert "lastEntities" not in snapshot
    assert "activeEntities" not in snapshot
