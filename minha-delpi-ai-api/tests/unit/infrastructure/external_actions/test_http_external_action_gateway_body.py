from app.infrastructure.external_actions.http_external_action_gateway import (
    HttpExternalActionGateway,
)


def test_gateway_never_sends_body_for_get_head_delete():
    gateway = HttpExternalActionGateway()

    for method in ["GET", "HEAD", "DELETE", "get"]:
        action = {
            "method": method,
            "requestBodyType": "json",
        }

        assert gateway._should_send_json_body(action, {"x": 1}) is False
        assert gateway._should_send_raw_body(action, "raw") is False


def test_gateway_sends_json_body_for_post_put_patch():
    gateway = HttpExternalActionGateway()

    for method in ["POST", "PUT", "PATCH", "post"]:
        action = {
            "method": method,
            "requestBodyType": "json",
        }

        assert gateway._should_send_json_body(action, {"x": 1}) is True
        assert gateway._should_send_raw_body(action, {"x": 1}) is False


def test_gateway_sends_raw_body_for_post_put_patch():
    gateway = HttpExternalActionGateway()

    for method in ["POST", "PUT", "PATCH", "post"]:
        action = {
            "method": method,
            "requestBodyType": "raw",
        }

        assert gateway._should_send_json_body(action, "raw") is False
        assert gateway._should_send_raw_body(action, "raw") is True
