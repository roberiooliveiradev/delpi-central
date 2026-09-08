from app.application.use_cases.health_check_use_case import HealthCheckUseCase
from app.infrastructure.config.settings import Settings


class ReadyCheckUseCase:
    def execute(self) -> dict:
        health = HealthCheckUseCase().execute()
        payload = {**health, "ready": True, "database": "skipped"}

        if not Settings.plugins_db_configured():
            return payload

        try:
            from app.infrastructure.persistence.migrations_runner import get_connection

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            payload["database"] = "ok"
        except Exception:
            payload["ready"] = False
            payload["database"] = "unavailable"
            return payload

        return payload
