from types import SimpleNamespace

from app.infrastructure.external_actions.http_external_action_gateway import (
    HttpExternalActionGateway,
)


def test_gateway_returns_binary_stub_for_xlsx_content_type():
    gateway = HttpExternalActionGateway()
    response = SimpleNamespace(
        headers={
            "content-type": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            "content-disposition": 'attachment; filename="Estrutura_90261757.xlsx"',
        },
        text="PK\x03\x04not-json",
        json=lambda: (_ for _ in ()).throw(AssertionError("json() não deve ser chamado")),
    )

    payload = gateway._parse_response(response)

    assert payload["binary"] is True
    assert payload["filename"] == "Estrutura_90261757.xlsx"
    assert "spreadsheetml" in payload["contentType"]
    assert "text" not in payload


def test_gateway_still_parses_json_envelope():
    gateway = HttpExternalActionGateway()
    response = SimpleNamespace(
        headers={"content-type": "application/json"},
        json=lambda: {
            "success": True,
            "data": {"downloadPath": "/products/1/structure/excel?format=xlsx"},
        },
    )

    payload = gateway._parse_response(response)

    assert payload["success"] is True
    assert "downloadPath" in payload["data"]
