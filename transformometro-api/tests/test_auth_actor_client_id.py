from types import SimpleNamespace

from tm_app.core.auth_actor import (
    TRANSFORMOMETRO_CLIENT_ID_HEADER,
    client_id_from_request,
)


def test_client_id_from_request_reads_canonical_header():
    request = SimpleNamespace(
        headers={TRANSFORMOMETRO_CLIENT_ID_HEADER: "  tab-abc  "}
    )
    assert client_id_from_request(request) == "tab-abc"


def test_client_id_from_request_rejects_empty_and_oversized():
    assert client_id_from_request(SimpleNamespace(headers={})) is None
    assert (
        client_id_from_request(
            SimpleNamespace(headers={"x-transformometro-client-id": "   "})
        )
        is None
    )
    assert (
        client_id_from_request(
            SimpleNamespace(headers={"x-transformometro-client-id": "x" * 200})
        )
        is None
    )
