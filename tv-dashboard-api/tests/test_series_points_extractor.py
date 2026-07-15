from tv_app.application.services.series_points_extractor import extract_series_points


def test_extract_series_points_from_points_list():
    points = extract_series_points(
        {
            "points": [
                {"label": "01/07", "value": 72.5},
                {"label": "02/07", "value": 80},
            ]
        }
    )
    assert points == [
        {"label": "01/07", "value": 72.5},
        {"label": "02/07", "value": 80},
    ]


def test_extract_series_points_branch_filial_fields():
    points = extract_series_points(
        {
            "points": [
                {"label": "sem1", "oee_filial_01": 70, "oee_filial_02": 65},
            ]
        },
        branch="01",
    )
    assert points[0]["value"] == 70


def test_extract_series_points_from_serie_and_ranking():
    serie = extract_series_points({"serie": [{"periodo": "2026-06", "value": 1000}]})
    assert serie == [{"label": "2026-06", "value": 1000}]

    ranking = extract_series_points(
        {"ranking": [{"centro_custo": "ADM", "total": 550}]},
    )
    assert ranking[0]["label"] == "ADM"
    assert ranking[0]["value"] == 550
