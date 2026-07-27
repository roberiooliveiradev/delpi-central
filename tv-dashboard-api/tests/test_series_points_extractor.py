from tv_app.application.services.series_points_extractor import (
    envelope_data,
    extract_series_points,
    response_fields_from_meta,
    unwrap_operational_data,
)


def test_unwrap_operational_data_envelope_dict():
    payload = {"success": True, "data": {"status": "ATIVO", "owner": "Ops"}}
    assert unwrap_operational_data(payload) == {"status": "ATIVO", "owner": "Ops"}


def test_unwrap_operational_data_envelope_list():
    payload = {"success": True, "data": [{"id": "1"}, {"id": "2"}]}
    assert unwrap_operational_data(payload) == [{"id": "1"}, {"id": "2"}]


def test_unwrap_operational_data_singleton_item_wrapper():
    payload = {
        "success": True,
        "data": {
            "item": {
                "department_id": "commercial",
                "idd": 8.1,
                "indicators": [{"indicator_id": "commercial.otd", "score": 7.0}],
            }
        },
    }
    assert unwrap_operational_data(payload) == {
        "department_id": "commercial",
        "idd": 8.1,
        "indicators": [{"indicator_id": "commercial.otd", "score": 7.0}],
    }


def test_unwrap_operational_data_keeps_item_when_siblings_present():
    payload = {
        "item": {"idd": 8.1},
        "partial_success": True,
        "errors": [{"message": "upstream"}],
    }
    assert unwrap_operational_data(payload) == payload


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


def test_extract_series_points_competencia_and_economia_bruta():
    """Série Transformômetro legado: eixo `competencia` + métrica `economia_bruta`."""
    assert extract_series_points(
        {
            "points": [
                {
                    "competencia": "2026-07-01",
                    "economia_bruta": 730.85,
                    "investimento": 177.54,
                }
            ]
        }
    ) == [{"label": "2026-07-01", "value": 730.85}]


def test_response_fields_from_meta_accepts_dict_canonical_api_delpi():
    """api-delpi grava meta.fields como dict {campo: rótulo} — não pode ser descartado."""
    fields = response_fields_from_meta(
        {
            "fields": {
                "ppm": "PPM",
                "target": "Meta PPM",
                "total_devolvido_un": "Total devolvido (un.)",
                "value": "Valor",
            }
        }
    )
    assert fields == {
        "ppm": "PPM",
        "target": "Meta PPM",
        "total_devolvido_un": "Total devolvido (un.)",
        "value": "Valor",
    }


def test_response_fields_from_meta_keeps_list_legacy():
    fields = response_fields_from_meta(
        {
            "fields": [
                {"key": "ppm", "label": "PPM"},
                {"name": "target", "title": "Meta PPM"},
            ]
        }
    )
    assert fields == [
        {"key": "ppm", "label": "PPM"},
        {"name": "target", "title": "Meta PPM"},
    ]
