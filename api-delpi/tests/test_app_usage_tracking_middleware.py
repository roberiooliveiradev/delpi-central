from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.responses import Response

from app.middleware import app_usage_tracking_middleware as middleware_module


@pytest.mark.asyncio
async def test_middleware_records_authenticated_success():
    request = MagicMock()
    request.method = "GET"
    request.url.path = "/apps/api-delpi/commercial/proposals"
    request.headers = {}
    request.state.user = MagicMock(id="11111111-1111-4111-8111-111111111111")

    async def call_next(_request):
        return Response(status_code=200)

    with patch.object(middleware_module, "is_public_path", return_value=False), patch.object(
        middleware_module, "request_has_valid_internal_service_token", return_value=False
    ), patch.object(
        middleware_module, "schedule_app_usage_record"
    ) as schedule:
        response = await middleware_module.app_usage_tracking_middleware(request, call_next)

    assert response.status_code == 200
    schedule.assert_called_once_with(
        user_id="11111111-1111-4111-8111-111111111111",
        route_path="/commercial/proposals",
        caller_app_id=None,
    )


@pytest.mark.asyncio
async def test_middleware_forwards_caller_app_header():
    request = MagicMock()
    request.method = "GET"
    request.url.path = "/apps/api-delpi/commercial/proposals"
    request.headers = {"X-Delpi-Caller-App": "minha-delpi-chat"}
    request.state.user = MagicMock(id="11111111-1111-4111-8111-111111111111")

    async def call_next(_request):
        return Response(status_code=200)

    with patch.object(middleware_module, "is_public_path", return_value=False), patch.object(
        middleware_module, "request_has_valid_internal_service_token", return_value=False
    ), patch.object(
        middleware_module, "schedule_app_usage_record"
    ) as schedule:
        await middleware_module.app_usage_tracking_middleware(request, call_next)

    schedule.assert_called_once_with(
        user_id="11111111-1111-4111-8111-111111111111",
        route_path="/commercial/proposals",
        caller_app_id="minha-delpi-chat",
    )


@pytest.mark.asyncio
async def test_middleware_skips_public_paths():
    request = MagicMock()
    request.method = "GET"
    request.url.path = "/health"

    async def call_next(_request):
        return Response(status_code=200)

    with patch.object(middleware_module, "is_public_path", return_value=True), patch.object(
        middleware_module, "schedule_app_usage_record"
    ) as schedule:
        await middleware_module.app_usage_tracking_middleware(request, call_next)

    schedule.assert_not_called()
