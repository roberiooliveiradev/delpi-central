from app.application.services.llm_cost_estimator_service import LlmCostEstimatorService
from app.domain.ports.admin_runtime_settings_repository_port import (
    AdminRuntimeSettingsRepositoryPort,
)


class GetAdminLlmCostTableUseCase:
    def __init__(
        self,
        settings_repository: AdminRuntimeSettingsRepositoryPort,
    ):
        self.settings_repository = settings_repository

    def execute(self) -> dict:
        stored = self.settings_repository.get_llm_cost_table()
        estimator = LlmCostEstimatorService(entries=stored)

        return {
            "entries": estimator.list_cost_table(),
            "source": "database" if stored else "env",
        }


class SaveAdminLlmCostTableUseCase:
    def __init__(
        self,
        settings_repository: AdminRuntimeSettingsRepositoryPort,
    ):
        self.settings_repository = settings_repository

    def execute(self, *, entries: list[dict]) -> dict:
        if not isinstance(entries, list) or not entries:
            raise ValueError("entries must be a non-empty list")

        normalized: list[dict] = []

        for item in entries:
            if not isinstance(item, dict):
                raise ValueError("each entry must be an object")

            provider = str(item.get("provider") or "").strip()
            model = str(item.get("model") or "").strip()

            if not provider or not model:
                raise ValueError("provider and model are required for each entry")

            normalized.append(
                {
                    "provider": provider.lower(),
                    "model": model,
                    "promptCostPer1k": float(item.get("promptCostPer1k") or 0),
                    "completionCostPer1k": float(item.get("completionCostPer1k") or 0),
                    "currency": str(item.get("currency") or "BRL"),
                    "source": "admin_ui",
                }
            )

        self.settings_repository.save_llm_cost_table(normalized)

        return {
            "entries": normalized,
            "source": "database",
        }
