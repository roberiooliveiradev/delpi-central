import pytest
from fastapi.testclient import TestClient

from engineering_app.main import app


@pytest.fixture
def client():
    return TestClient(app)
