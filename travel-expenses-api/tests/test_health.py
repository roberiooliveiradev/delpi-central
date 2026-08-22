from travel_expenses_app.main import health


def test_health():
    assert health() == {"status": "online", "service": "travel-expenses-api"}
