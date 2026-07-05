def test_health():
    from tv_app.main import health

    result = health()
    assert result["status"] == "online"
    assert result["service"] == "tv-dashboard-api"
