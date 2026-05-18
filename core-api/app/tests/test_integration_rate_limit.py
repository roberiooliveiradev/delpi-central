# app/tests/test_integration_rate_limit.py

from app.create_app import create_app
from app.extensions import integration_rate_limit as irl


def test_integration_rate_limit_blocks_after_max_requests():
    app = create_app("testing")
    irl._BUCKETS.clear()

    @irl.integration_rate_limit(max_requests=2, per_seconds=60, key_prefix="test")
    def handler():
        return "ok", 200

    with app.test_request_context("/integrations/notifications"):
        assert handler()[1] == 200
        assert handler()[1] == 200
        blocked = handler()
        assert blocked[1] == 429
