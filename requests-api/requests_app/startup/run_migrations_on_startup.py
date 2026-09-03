from requests_app.config import settings
from requests_app.infrastructure.persistence.migrations_runner import run_migrations


def run_migrations_on_startup() -> None:
    if not settings.REQUESTS_RUN_MIGRATIONS_ON_STARTUP:
        return
    run_migrations()
