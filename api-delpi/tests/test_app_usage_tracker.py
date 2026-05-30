import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.services import app_usage_tracker as tracker


@pytest.fixture(autouse=True)
def reset_tracker_state():
    tracker.reset_app_usage_debounce_cache()
    yield
    tracker.reset_app_usage_debounce_cache()


def test_schedule_skips_when_disabled():
    with patch.object(tracker.settings, "APP_USAGE_TRACKING_ENABLED", False):
        with patch.object(tracker.asyncio, "get_running_loop") as get_loop:
            tracker.schedule_app_usage_record(user_id="11111111-1111-4111-8111-111111111111", route_path="/commercial")
            get_loop.assert_not_called()


def test_schedule_skips_invalid_user():
    with patch.object(tracker.settings, "APP_USAGE_TRACKING_ENABLED", True), patch.object(
        tracker.settings, "CORE_API_BASE_URL", "http://core-api:8000"
    ), patch.object(tracker.settings, "CORE_API_INTEGRATIONS_SERVICE_TOKEN", "token"), patch.object(
        tracker.asyncio, "get_running_loop"
    ) as get_loop:
        tracker.schedule_app_usage_record(user_id="internal-service", route_path="/commercial")
        get_loop.assert_not_called()


def test_debounce_prevents_duplicate_schedule():
    user_id = "11111111-1111-4111-8111-111111111111"
    loop = MagicMock()

    with patch.object(tracker.settings, "APP_USAGE_TRACKING_ENABLED", True), patch.object(
        tracker.settings, "CORE_API_BASE_URL", "http://core-api:8000"
    ), patch.object(tracker.settings, "CORE_API_INTEGRATIONS_SERVICE_TOKEN", "token"), patch.object(
        tracker.asyncio, "get_running_loop", return_value=loop
    ):
        tracker.schedule_app_usage_record(user_id=user_id, route_path="/commercial")
        tracker.schedule_app_usage_record(user_id=user_id, route_path="/production")

    assert loop.create_task.call_count == 1


@pytest.mark.asyncio
async def test_record_async_posts_to_core_api():
    user_id = "11111111-1111-4111-8111-111111111111"
    mock_response = MagicMock(status_code=201)
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch.object(tracker.settings, "CORE_API_BASE_URL", "http://core-api:8000"), patch.object(
        tracker.settings, "CORE_API_INTEGRATIONS_SERVICE_TOKEN", "secret-token"
    ), patch.object(tracker.settings, "APP_USAGE_APP_ID", "api-delpi"), patch.object(
        tracker.httpx, "AsyncClient", return_value=mock_client
    ):
        await tracker._record_async(
            user_id=user_id,
            route_path="/commercial/proposals",
            caller_app_id="dashboard-commercial",
        )

    mock_client.post.assert_awaited_once_with(
        "http://core-api:8000/integrations/app-usage/record",
        headers={
            "Authorization": "Bearer secret-token",
            "X-Delpi-Caller-App": "dashboard-commercial",
        },
        json={
            "appId": "api-delpi",
            "userId": user_id,
            "routePath": "/commercial/proposals",
        },
    )
