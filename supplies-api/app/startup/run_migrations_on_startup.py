from app.infrastructure.persistence.migrations_runner import run_migrations
from app.infrastructure.config.settings import Settings


def run_migrations_on_startup() -> None:
    if not Settings.RUN_MIGRATIONS_ON_STARTUP:
        return
    if not Settings.plugins_db_configured():
        return
    run_migrations()
