from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.external_action_http_execution_service import (
    ExternalActionHttpExecutionService,
)

configure_domain_infrastructure_ports()


def test_default_timeout_seconds():
    assert ExternalActionHttpExecutionService.default_timeout_seconds() == 30


def test_composite_analysis_timeout_seconds():
    assert ExternalActionHttpExecutionService.composite_analysis_timeout_seconds() == 60


def test_resolve_timeout_for_factory_status_path():
    timeout = ExternalActionHttpExecutionService.resolve_timeout_seconds(
        provider={},
        action_path="/products/{code}/factory-status",
    )

    assert timeout == 60


def test_resolve_timeout_honors_provider_override():
    timeout = ExternalActionHttpExecutionService.resolve_timeout_seconds(
        provider={"timeoutSeconds": 45},
        action_path="/products/{code}/factory-status",
    )

    assert timeout == 45


def test_resolve_timeout_default_for_simple_path():
    timeout = ExternalActionHttpExecutionService.resolve_timeout_seconds(
        provider={},
        action_path="/production/schedule/today",
    )

    assert timeout == 30


def test_should_retry_once_on_timeout():
    assert ExternalActionHttpExecutionService.should_retry(
        attempt_index=0,
        timed_out=True,
    )
    assert not ExternalActionHttpExecutionService.should_retry(
        attempt_index=1,
        timed_out=True,
    )


def test_should_retry_once_on_gateway_status_codes():
    assert ExternalActionHttpExecutionService.should_retry(
        attempt_index=0,
        status_code=503,
    )
    assert not ExternalActionHttpExecutionService.should_retry(
        attempt_index=0,
        status_code=404,
    )
