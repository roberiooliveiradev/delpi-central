from app.domain.services.chat_snapshot_operational_focus import ChatSnapshotOperationalFocus


def test_get_reads_legacy_last_entities():
    focus = ChatSnapshotOperationalFocus.get(
        {"lastEntities": {"productCode": "10080001", "branch": "02"}}
    )

    assert focus["productCode"] == "10080001"
    assert focus["branch"] == "02"


def test_normalize_migrates_legacy_keys():
    snapshot = ChatSnapshotOperationalFocus.normalize(
        {
            "lastEntities": {"productCode": "10080055"},
            "activeEntities": {"branch": "01"},
        }
    )

    assert snapshot["operationalFocus"]["productCode"] == "10080055"
    assert "lastEntities" not in snapshot
    assert "activeEntities" not in snapshot


def test_set_strips_legacy_keys():
    snapshot = ChatSnapshotOperationalFocus.set(
        {"lastEntities": {"productCode": "old"}},
        {"productCode": "10080099"},
    )

    assert snapshot["operationalFocus"]["productCode"] == "10080099"
    assert "lastEntities" not in snapshot
