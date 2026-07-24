"""Fixtures canônicas dos testes HTTP da transformometro-api."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from tests.support.route_smoke_mocks import universal_route_mocks
from tests.support.route_smoke_openapi import load_openapi_operations
from tests.support.test_app import create_test_app


@pytest.fixture(scope="session")
def tm_app():
    return create_test_app()


@pytest.fixture(scope="session")
def openapi_ops(tm_app):
    return load_openapi_operations(tm_app)


@pytest.fixture
def tm_client(tm_app):
    with universal_route_mocks():
        with TestClient(tm_app) as client:
            yield client
