from purchase_requests_app.infrastructure.persistence.migrations_runner import run_migrations

from purchase_requests_app.config import settings


def run_migrations_on_startup() -> None:
    if not settings.PURCHASE_REQUESTS_RUN_MIGRATIONS_ON_STARTUP:
        return
    run_migrations()
