class HealthCheckUseCase:
    def execute(self) -> dict:
        return {
            "status": "ok",
            "service": "minha-delpi-ai-api",
        }
