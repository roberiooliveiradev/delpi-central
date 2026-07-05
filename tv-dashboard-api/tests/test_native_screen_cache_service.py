from tv_app.application.services.native_screen_cache_service import (
    build_native_data_cache_key,
    reset_native_data_cache,
    set_cached_native_data,
    get_cached_native_data,
)


def test_cache_key_is_stable():
    key_a = build_native_data_cache_key(
        screen_key="production_oee_overview",
        config={"branch": "01", "periodDays": 7},
        authorization=None,
    )
    key_b = build_native_data_cache_key(
        screen_key="production_oee_overview",
        config={"periodDays": 7, "branch": "01"},
        authorization=None,
    )
    assert key_a == key_b


def test_cache_skips_error_payload():
    reset_native_data_cache()
    key = build_native_data_cache_key(
        screen_key="production_oee_overview",
        config={},
        authorization=None,
    )
    set_cached_native_data(key, {"error": True, "message": "fail"})
    assert get_cached_native_data(key) is None

    set_cached_native_data(key, {"oeePct": 82.5})
    assert get_cached_native_data(key) == {"oeePct": 82.5}
