from app.infrastructure.config.settings import Settings


class HealthCheckUseCase:
    def execute(self) -> dict:
        return {
            "status": "ok",
            "service": Settings.SERVICE_NAME,
        }
