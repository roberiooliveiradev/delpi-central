from app.domain.services.openapi_baseline_service import build_baseline_payload
from app.domain.services.openapi_diff_service import diff_openapi_against_baseline


def test_diff_detects_added_removed_and_changed(tmp_path, monkeypatch) -> None:
    baseline_spec = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {
            "/old": {
                "get": {
                    "operationId": "old_op",
                    "summary": "Old",
                    "tags": ["A"],
                }
            },
            "/shared": {
                "get": {
                    "operationId": "shared_op",
                    "summary": "Shared",
                    "tags": ["A"],
                }
            },
        },
    }
    current_spec = {
        "openapi": "3.0.3",
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {
            "/new": {
                "get": {
                    "operationId": "new_op",
                    "summary": "New",
                    "tags": ["B"],
                }
            },
            "/shared": {
                "get": {
                    "operationId": "shared_op_v2",
                    "summary": "Shared v2",
                    "tags": ["A", "B"],
                }
            },
        },
    }

    baseline_payload = build_baseline_payload(baseline_spec)
    baseline_path = tmp_path / "openapi_baseline.json"
    baseline_path.write_text(__import__("json").dumps(baseline_payload), encoding="utf-8")

    monkeypatch.setattr(
        "app.domain.services.openapi_diff_service.load_openapi_baseline",
        lambda: baseline_payload,
    )

    diff = diff_openapi_against_baseline(current_spec)

    assert diff["added_count"] == 1
    assert diff["removed_count"] == 1
    assert diff["changed_count"] == 1
    assert diff["added"][0]["path"] == "/new"
    assert diff["removed"][0]["path"] == "/old"
