import pytest

from app.create_app import create_app


@pytest.fixture()
def app():
    return create_app(testing=True)


@pytest.fixture()
def client(app):
    with app.test_client() as test_client:
        yield test_client
