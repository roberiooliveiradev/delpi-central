from __future__ import annotations

import os

from bpmn_modeler.interface.http.app import create_app

app = create_app()

REQUIRED_ENV = (
    "KEYCLOAK_JWKS_URL",
    "KEYCLOAK_ISSUER",
    "KEYCLOAK_AUDIENCE",
    "BPMN_MODELER_DB_HOST",
    "BPMN_MODELER_DB_PORT",
    "BPMN_MODELER_DB_NAME",
    "BPMN_MODELER_DB_USER",
    "BPMN_MODELER_DB_PASSWORD",
)


def startup_env_check() -> None:
    missing = [name for name in REQUIRED_ENV if not os.getenv(name, "").strip()]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")
