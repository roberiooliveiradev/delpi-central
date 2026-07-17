from tv_app.application.services.series_points_extractor import (
    envelope_data,
    extract_series_points,
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


def test_extract_series_points_preserves_zero_in_value_fallbacks():
    assert extract_series_points(
        {
            "points": [
                {"periodo": "jan", "total": 0, "qty": 99},
                {"periodo": "fev", "value": 0, "total": 88},
            ]
        }
    ) == [
        {"label": "jan", "value": 0},
        {"label": "fev", "value": 0},
    ]


def test_extract_series_points_preserves_zero_for_branch():
    assert extract_series_points(
        {
            "points": [
                {
                    "periodo": "jan",
                    "oee_filial_01": 0,
                    "otd_filial_01": 95,
                }
            ]
        },
        branch="1",
    ) == [{"label": "jan", "value": 0}]


def test_extract_series_points_preserves_zero_label():
    assert extract_series_points(
        {"points": [{"label": 0, "periodo": "substituto", "value": 10}]}
    ) == [{"label": 0, "value": 10}]
