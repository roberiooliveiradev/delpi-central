from tv_app.application.services.series_points_extractor import (
    envelope_data,
    unwrap_operational_data,
)


def test_unwrap_operational_data_envelope_dict():
    payload = {"success": True, "data": {"status": "ATIVO", "owner": "Ops"}}
    assert unwrap_operational_data(payload) == {"status": "ATIVO", "owner": "Ops"}


def test_unwrap_operational_data_envelope_list():
    payload = {"success": True, "data": [{"id": "1"}, {"id": "2"}]}
    assert unwrap_operational_data(payload) == [{"id": "1"}, {"id": "2"}]


def test_envelope_data_returns_dict_only():
    assert envelope_data({"success": True, "data": {"value": 1}}) == {"value": 1}
    assert envelope_data([{"value": 1}]) == {}
