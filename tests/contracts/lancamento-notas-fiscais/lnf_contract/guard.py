"""Guarda de host e leitura de configuração. Segredos não são impressos."""

from __future__ import annotations

import os
from urllib.parse import urlparse

PROD_HOSTS = frozenset(
    {
        "minhadelpi.com.br",
        "www.minhadelpi.com.br",
        "192.168.1.237",
    }
)

PROFILES = (
    "P0",
    "P1",
    "P2",
    "P3",
    "P4",
    "P5",
    "P6",
    "P7",
    "P8",
    "P9",
    "P10",
)


class ProductionTargetError(RuntimeError):
    pass


def base_url() -> str:
    raw = (os.getenv("LNF_BASE_URL") or "").strip().rstrip("/")
    return raw


def target_name() -> str:
    raw = (os.getenv("LNF_TARGET") or "api-delpi").strip().lower()
    if raw not in {"api-delpi", "bff"}:
        raise RuntimeError("LNF_TARGET deve ser api-delpi ou bff")
    return raw


def assert_not_production(url: str) -> None:
    if not url:
        return
    host = (urlparse(url).hostname or "").lower()
    if host in PROD_HOSTS or host.endswith(".minhadelpi.com.br"):
        raise ProductionTargetError(
            f"LNF_BASE_URL aponta para host de produção ({host}). A suíte abortou."
        )


def profile_token(profile: str) -> str | None:
    if profile == "P10":
        dedicated = (os.getenv("LNF_TOKEN_P10") or "").strip()
        shared = (os.getenv("API_DELPI_INTERNAL_SERVICE_TOKEN") or "").strip()
        return dedicated or shared or None
    return (os.getenv(f"LNF_TOKEN_{profile}") or "").strip() or None


def core_base_url() -> str | None:
    explicit = (os.getenv("LNF_CORE_BASE_URL") or "").strip().rstrip("/")
    if explicit:
        assert_not_production(explicit)
        return explicit
    base = base_url()
    if not base:
        return None
    if "/apps/api-delpi" in base:
        origin = base.split("/apps/api-delpi", 1)[0]
        return f"{origin}/core-api"
    return None
