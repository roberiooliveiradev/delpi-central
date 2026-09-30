from __future__ import annotations

import os

from bpmn_modeler.interface.http.app import create_app

REQUIRED_ENV = (
    "KEYCLOAK_JWKS_URL",
    "KEYCLOAK_ISSUER",
    "KEYCLOAK_AUDIENCE",
    "PLUGINS_DB_HOST",
    "PLUGINS_DB_PORT",
    "PLUGINS_DB_NAME",
    "PLUGINS_DB_USER",
    "PLUGINS_DB_PASSWORD",
)


def startup_env_check() -> None:
    missing = [name for name in REQUIRED_ENV if not os.getenv(name, "").strip()]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")


app = create_app()
