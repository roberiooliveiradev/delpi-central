import pytest

from app.create_app import create_app


@pytest.fixture(autouse=True)
def _neutralize_ambient_runtime_env(monkeypatch):
    """Tests must be deterministic regardless of ambient container env.

    Settings() reads the process environment; a dev container leaks
    DELIA_LLM_*/DELPI_AUTH_CORE_API_URL/CORE_API_URL etc. into
    `testing=True` wiring. Neutralize the runtime-tunable knobs —
    tests that need a value set it explicitly via monkeypatch.
    """
    prefixes = (
        "DELIA_LLM_",
        "DELIA_EXCHANGE_",
        "DELIA_MCP_",
        "DELIA_EVAL_",
    )
    exact = ("DELPI_AUTH_CORE_API_URL", "CORE_API_URL")
    import os

    for name in list(os.environ):
        if name in exact or name.startswith(prefixes):
            monkeypatch.delenv(name, raising=False)


@pytest.fixture()
def app():
    return create_app(testing=True)


@pytest.fixture()
def client(app):
    with app.test_client() as test_client:
        yield test_client
