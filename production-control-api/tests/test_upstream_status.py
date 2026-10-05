from production_control_app.domain.errors import DelpiGatewayError
from production_control_app.interface.http.upstream_status import status_from_gateway_error


def test_gateway_client_error_keeps_upstream_status() -> None:
    exc = DelpiGatewayError(
        "delivery_start não pode ser posterior a delivery_end.",
        status_code=400,
    )
    assert status_from_gateway_error(exc) == 400


def test_gateway_server_error_keeps_upstream_status() -> None:
    exc = DelpiGatewayError("Erro interno ao listar OPs.", status_code=500)
    assert status_from_gateway_error(exc) == 500


def test_gateway_without_upstream_status_is_bad_gateway() -> None:
    exc = DelpiGatewayError("Erro ao consultar api-delpi.")
    assert status_from_gateway_error(exc) == 502
