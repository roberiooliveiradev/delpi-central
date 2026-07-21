"""Registry de providers de relatório — Delpi Reports."""

from __future__ import annotations

from app.domain.ports.reports.report_provider_port import ReportProviderPort


class ReportProviderRegistry:
    """Registro em memória por ``provider_key`` (composition root na Fase 1+)."""

    def __init__(self) -> None:
        self._providers: dict[str, ReportProviderPort] = {}

    def register(self, provider: ReportProviderPort) -> None:
        key = str(getattr(provider, "key", "") or "").strip()
        if not key:
            raise ValueError("ReportProvider.key é obrigatório.")
        if key in self._providers:
            raise ValueError(f"ReportProvider já registrado: {key}")
        self._providers[key] = provider

    def get(self, provider_key: str) -> ReportProviderPort | None:
        key = str(provider_key or "").strip()
        if not key:
            return None
        return self._providers.get(key)

    def require(self, provider_key: str) -> ReportProviderPort:
        provider = self.get(provider_key)
        if provider is None:
            raise KeyError(f"ReportProvider não encontrado: {provider_key}")
        return provider

    def list_keys(self) -> list[str]:
        return sorted(self._providers.keys())

    def list_providers(self) -> list[ReportProviderPort]:
        return [self._providers[k] for k in self.list_keys()]
