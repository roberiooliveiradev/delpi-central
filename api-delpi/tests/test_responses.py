import json

from app.core.responses import error_response, not_found_response, success_response


def _body(response) -> dict:
    return json.loads(response.body.decode())


def test_success_response_envelope() -> None:
    body = _body(success_response({"ok": True}))
    assert body["success"] is True
    assert body["data"] == {"ok": True}
    assert body["error"] is None
    assert "meta" not in body


def test_success_response_with_meta() -> None:
    body = _body(success_response({"x": 1}, meta={"shape": "scalar"}))
    assert body["meta"] == {"shape": "scalar"}


def test_error_response_with_code() -> None:
    body = _body(error_response("falhou", status_code=400, code="VALIDATION_ERROR"))
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"] == {"code": "VALIDATION_ERROR", "recoverable": True}


def test_not_found_response() -> None:
    response = not_found_response("Produto não encontrado", code="PRODUCT_NOT_FOUND")
    assert response.status_code == 404
    body = _body(response)
    assert body["error"]["code"] == "PRODUCT_NOT_FOUND"
    assert body["error"]["recoverable"] is False
