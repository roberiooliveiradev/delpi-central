from types import SimpleNamespace

from fastapi import Request

from maint_app.core.auth_actor import actor_nome_from_request, actor_sub_from_request


def test_actor_sub_and_nome_from_request():
    req = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    req.state.user = SimpleNamespace(
        id="uuid-123",
        name="  Maria Silva  ",
        email="maria@empresa.com",
    )

    assert actor_sub_from_request(req) == "uuid-123"
    assert actor_nome_from_request(req) == "Maria Silva"


def test_actor_nome_falls_back_to_email():
    req = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    req.state.user = SimpleNamespace(id="uuid-456", email="joao@empresa.com")

    assert actor_nome_from_request(req) == "joao@empresa.com"
