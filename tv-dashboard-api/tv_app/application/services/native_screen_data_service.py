from __future__ import annotations

from typing import Any

from tv_app.application.services.native_screen_cache_service import (
    build_native_data_cache_key,
    get_cached_native_data,
    set_cached_native_data,
)
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.infrastructure.gateways.delpi_production_gateway import DelpiProductionGateway
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    load_native_screens_catalog,
)


def _optional_branch(cfg: dict[str, Any]) -> str | None:
    branch = cfg.get("branch")
    if isinstance(branch, str):
        return branch.strip() or None
    return None


def _error(message: str, detail: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": True, "message": message}
    if detail:
        payload["detail"] = detail
    return payload


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
        if screen_key != "custom_message":
            cache_key = build_native_data_cache_key(
                screen_key=screen_key,
                config=cfg,
                authorization=authorization,
            )
            cached = get_cached_native_data(cache_key)
            if cached is not None:
                return cached

        result = self._resolve_uncached(
            screen_key=screen_key,
            cfg=cfg,
            authorization=authorization,
        )
        if screen_key != "custom_message" and not result.get("error"):
            cache_key = build_native_data_cache_key(
                screen_key=screen_key,
                config=cfg,
                authorization=authorization,
            )
            set_cached_native_data(cache_key, result)
        return result

    def _resolve_uncached(
        self,
        *,
        screen_key: str,
        cfg: dict[str, Any],
        authorization: str | None,
    ) -> dict[str, Any]:
        try:
            if screen_key == "production_oee_overview":
                return self._gateway.fetch_oee_overview(
                    branch=_optional_branch(cfg),
                    period_days=int(cfg.get("periodDays") or 7),
                    authorization=authorization,
                )
            if screen_key == "production_otd_summary":
                return self._gateway.fetch_otd_summary(
                    branch=_optional_branch(cfg),
                    period_days=int(cfg.get("periodDays") or 30),
                    authorization=authorization,
                )
            if screen_key == "quality_ppm_summary":
                return self._gateway.fetch_ppm_summary(
                    branch=_optional_branch(cfg),
                    period_days=int(cfg.get("periodDays") or 30),
                    ppm_type=str(cfg.get("ppmType") or "internal"),
                    authorization=authorization,
                )
            if screen_key == "supplies_stock_value":
                return self._gateway.fetch_stock_value_summary(
                    branch=_optional_branch(cfg),
                    authorization=authorization,
                )
            if screen_key == "custom_message":
                return {
                    "headline": str(cfg.get("headline") or "Comunicado"),
                    "subtitle": str(cfg.get("subtitle") or ""),
                }
        except Exception as exc:  # noqa: BLE001
            return _error(message("nativeDataUnavailable"), str(exc))
        return _error(f"Tela nativa desconhecida: {screen_key}")

    @staticmethod
    def catalog() -> list[dict[str, Any]]:
        return load_native_screens_catalog()
