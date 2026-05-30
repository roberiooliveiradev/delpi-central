# app/tests/test_app_usage_controller_integration.py

import os
from unittest.mock import MagicMock, patch

import pytest

from app.application.use_cases.admin.record_integrated_app_usage_use_case import (
    RecordIntegratedAppUsageResult,
)
from app.create_app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_record_integrated_app_usage_requires_service_token(client):
    response = client.post(
        "/integrations/app-usage/record",
        json={"appId": "api-delpi", "userId": "11111111-1111-4111-8111-111111111111"},
    )
    assert response.status_code in (401, 403)


def test_record_integrated_app_usage_skips_without_consent(client):
    token = "test-service-token"
    with patch.dict(os.environ, {"CORE_API_INTEGRATIONS_SERVICE_TOKEN": token}), patch(
        "app.interfaces.http.app_usage_controller.RecordIntegratedAppUsageUseCase"
    ) as use_case_cls:
        use_case_cls.return_value.execute.return_value = (
            RecordIntegratedAppUsageResult.SKIPPED_CONSENT
        )

        response = client.post(
            "/integrations/app-usage/record",
            headers={"Authorization": f"Bearer {token}"},
            json={"appId": "api-delpi", "userId": "11111111-1111-4111-8111-111111111111"},
        )

    assert response.status_code == 200
    assert response.get_json() == {
        "recorded": False,
        "skipped": "usage_tracking_consent",
    }


def test_record_integrated_app_usage_accepts_caller_header(client):
    token = "test-service-token"
    with patch.dict(os.environ, {"CORE_API_INTEGRATIONS_SERVICE_TOKEN": token}), patch(
        "app.interfaces.http.app_usage_controller.RecordIntegratedAppUsageUseCase"
    ) as use_case_cls:
        use_case_cls.return_value.execute.return_value = RecordIntegratedAppUsageResult.RECORDED

        response = client.post(
            "/integrations/app-usage/record",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Delpi-Caller-App": "dashboard-commercial",
            },
            json={"appId": "api-delpi", "userId": "11111111-1111-4111-8111-111111111111"},
        )

    assert response.status_code == 201
    use_case_cls.return_value.execute.assert_called_once()
    assert (
        use_case_cls.return_value.execute.call_args.kwargs["caller_app_id"]
        == "dashboard-commercial"
    )
