import json
import os

from app.domain.ports.admin_runtime_settings_repository_port import (
    AdminRuntimeSettingsRepositoryPort,
)
from app.infrastructure.config.llm_text_config import (
    is_openai_compatible_provider,
    resolve_llm_text_config,
)
from app.infrastructure.config.settings import Settings


class LlmCostEstimatorService:
    """Resolve custo estimado por provider/modelo a partir de tabela configurável."""

    def __init__(
        self,
        *,
        entries: list[dict] | None = None,
        settings_repository: AdminRuntimeSettingsRepositoryPort | None = None,
    ):
        self._settings_repository = settings_repository
        self._entries = entries if entries is not None else self._load_entries()

    def list_cost_table(self) -> list[dict]:
        return [dict(item) for item in self._entries]

    def resolve_rates(self, *, provider: str | None, model: str | None) -> dict:
        normalized_provider = str(provider or Settings.LLM_PROVIDER).lower().strip()
        normalized_model = str(model or self._default_model_for(normalized_provider)).strip()

        for entry in self._entries:
            if (
                str(entry.get("provider", "")).lower() == normalized_provider
                and str(entry.get("model", "")) == normalized_model
            ):
                return entry

        return {
            "provider": normalized_provider,
            "model": normalized_model,
            "promptCostPer1k": Settings.LLM_PROMPT_TOKEN_COST_PER_1K,
            "completionCostPer1k": Settings.LLM_COMPLETION_TOKEN_COST_PER_1K,
            "currency": os.getenv("LLM_COST_CURRENCY", "BRL"),
            "source": "env_default",
        }

    def estimate_cost(
        self,
        *,
        provider: str | None,
        model: str | None,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float | None:
        rates = self.resolve_rates(provider=provider, model=model)
        prompt_cost = (prompt_tokens / 1000) * float(rates.get("promptCostPer1k") or 0)
        completion_cost = (completion_tokens / 1000) * float(
            rates.get("completionCostPer1k") or 0
        )
        total = prompt_cost + completion_cost

        if total <= 0:
            return None

        return round(total, 6)

    def _load_entries(self) -> list[dict]:
        stored = None
        if self._settings_repository is not None:
            stored = self._settings_repository.get_llm_cost_table()

        if stored:
            return [
                self._normalize_entry(item)
                for item in stored
                if isinstance(item, dict)
            ]

        raw = os.getenv("LLM_COST_TABLE_JSON", "").strip()
        parsed: list[dict] = []

        if raw:
            try:
                loaded = json.loads(raw)
                if isinstance(loaded, list):
                    parsed = [
                        self._normalize_entry(item)
                        for item in loaded
                        if isinstance(item, dict)
                    ]
            except json.JSONDecodeError:
                parsed = []

        if parsed:
            return parsed

        provider = Settings.LLM_PROVIDER
        model = self._default_model_for(provider)

        return [
            self._normalize_entry(
                {
                    "provider": provider,
                    "model": model,
                    "promptCostPer1k": Settings.LLM_PROMPT_TOKEN_COST_PER_1K,
                    "completionCostPer1k": Settings.LLM_COMPLETION_TOKEN_COST_PER_1K,
                    "currency": os.getenv("LLM_COST_CURRENCY", "BRL"),
                    "source": "env_default",
                }
            )
        ]

    def _normalize_entry(self, entry: dict) -> dict:
        return {
            "provider": str(entry.get("provider") or Settings.LLM_PROVIDER).lower().strip(),
            "model": str(entry.get("model") or "").strip(),
            "promptCostPer1k": float(
                entry.get("promptCostPer1k", Settings.LLM_PROMPT_TOKEN_COST_PER_1K)
            ),
            "completionCostPer1k": float(
                entry.get("completionCostPer1k", Settings.LLM_COMPLETION_TOKEN_COST_PER_1K)
            ),
            "currency": str(entry.get("currency") or os.getenv("LLM_COST_CURRENCY", "BRL")),
            "source": str(entry.get("source") or "configured"),
        }

    def _default_model_for(self, provider: str) -> str:
        if is_openai_compatible_provider(provider):
            return resolve_llm_text_config().model

        return Settings.OLLAMA_MODEL
