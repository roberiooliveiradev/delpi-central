import socket
from pathlib import Path

import pytest

from app.create_app import create_app
from app.infrastructure.config.settings import is_local_llm_host


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
        "DELIA_STT_",
        "DELIA_EXCHANGE_",
        "DELIA_MCP_",
        "DELIA_EVAL_",
    )
    exact = ("DELPI_AUTH_CORE_API_URL", "CORE_API_URL")
    import os

    for name in list(os.environ):
        if name in exact or name.startswith(prefixes):
            monkeypatch.delenv(name, raising=False)


class ExternalEgressBlockedError(RuntimeError):
    """Raised when a local test tries to open a non-local TCP connection."""


@pytest.fixture(autouse=True)
def _block_external_network_egress(monkeypatch):
    """C3-OLLAMA-LOCAL-LLM-TESTING-01: local tests fail closed on any
    external egress — especially LLM endpoints. No test may consume
    external model tokens, even when it fails. Loopback/non-global IPs
    and internal service hostnames (ollama, docker names) stay allowed.
    """
    real_connect = socket.socket.connect

    def _guarded_connect(self, address):
        if isinstance(address, tuple) and address:
            host = address[0]
            if isinstance(host, str) and not is_local_llm_host(host):
                raise ExternalEgressBlockedError(
                    "local test attempted external network egress to "
                    f"{host!r}; external LLM providers are prohibited "
                    "outside production"
                )
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)


@pytest.fixture()
def app():
    return create_app(testing=True)


@pytest.fixture()
def client(app):
    with app.test_client() as test_client:
        yield test_client


def load_test_orchestration_instructions() -> dict:
    """R1/M01 (plan 125): instruction text is a governed versioned
    resource — tests load it through the canonical fail-closed
    loader; never a second copy and never a test-local snapshot of
    the text itself."""
    from app.application.capability_provision.orchestration import (
        ORCHESTRATION_INSTRUCTION_KEYS,
    )
    from app.infrastructure.config.cri_instruction_resource import (
        load_orchestration_instructions,
    )

    return load_orchestration_instructions(
        Path(__file__).resolve().parents[1]
        / "config"
        / "orchestration_instructions.delpi.json",
        required_names=ORCHESTRATION_INSTRUCTION_KEYS,
    ).instructions
