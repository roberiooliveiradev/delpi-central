from app.application.use_cases.health_check_use_case import HealthCheckUseCase


class ReadyCheckUseCase:
    def execute(self) -> dict:
        health = HealthCheckUseCase().execute()
        return {
            **health,
            "ready": True,
        }
