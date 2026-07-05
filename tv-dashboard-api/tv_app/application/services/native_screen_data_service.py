from __future__ import annotations

from typing import Any

from tv_app.infrastructure.gateways.delpi_production_gateway import DelpiProductionGateway
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    load_native_screens_catalog,
)


class NativeScreenDataService:
    def __init__(self, gateway: DelpiProductionGateway | None = None) -> None:
        self._gateway = gateway or DelpiProductionGateway()

    def resolve(
        self,
        *,
        screen_key: str,
        config: dict[str, Any] | None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        cfg = config or {}
        if screen_key == "production_oee_overview":
            period_days = int(cfg.get("periodDays") or 7)
            branch = cfg.get("branch")
            if isinstance(branch, str):
                branch = branch.strip() or None
            try:
                return self._gateway.fetch_oee_overview(
                    branch=branch,
                    period_days=period_days,
                    authorization=authorization,
                )
            except Exception as exc:  # noqa: BLE001
                return {
                    "error": True,
                    "message": "Dados de OEE indisponíveis no momento.",
                    "detail": str(exc),
                }
        if screen_key == "custom_message":
            return {
                "headline": str(cfg.get("headline") or "Comunicado"),
                "subtitle": str(cfg.get("subtitle") or ""),
            }
        return {"error": True, "message": f"Tela nativa desconhecida: {screen_key}"}

    @staticmethod
    def catalog() -> list[dict[str, Any]]:
        return load_native_screens_catalog()
