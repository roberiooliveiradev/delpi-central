
from tm_app.interface.http.routes import meeting_minutes_routes, public_meeting_minutes_routes, signature_profile_routes

def test_meeting_minutes_routes_have_operation_ids():
    for route in meeting_minutes_routes.router.routes:
        assert getattr(route, "operation_id", None) or getattr(route, "endpoint", None)
        op = getattr(route, "operation_id", None)
        if op is None and hasattr(route, "endpoint"):
            # FastAPI APIRoute
            op = getattr(route, "operation_id", None)
        if hasattr(route, "operation_id"):
            assert route.operation_id, f"missing operation_id on {route.path}"

def test_public_and_signature_operation_ids():
    for router in (
        public_meeting_minutes_routes.public_router,
        signature_profile_routes.router,
    ):
        for route in router.routes:
            assert getattr(route, "operation_id", None), f"missing operation_id on {getattr(route, 'path', route)}"
