"""Guarda de host e leitura de configuração. Segredos não são impressos."""

from __future__ import annotations

import os
from pathlib import Path
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
    "P11",
    "P12",
)

_ENV_LOCAL = Path(__file__).resolve().parents[1] / ".env.local"
_ENV_LOADED = False


def load_env_local() -> None:
    """Carrega `.env.local` por cima do ambiente do shell.

    Tokens JWT expiram; o arquivo renovado pelo provision prevalece sobre
    `LNF_TOKEN_*` já exportados na sessão.
    """
    global _ENV_LOADED
    if _ENV_LOADED or not _ENV_LOCAL.is_file():
        _ENV_LOADED = True
        return
    for line in _ENV_LOCAL.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        if key.startswith("LNF_TOKEN_") or key.startswith("LNF_PASSWORD_") or key in {
            "API_DELPI_INTERNAL_SERVICE_TOKEN",
            "LNF_BOOTSTRAP_ADMIN_PASSWORD",
        }:
            os.environ[key] = value
        else:
            os.environ.setdefault(key, value)
    _ENV_LOADED = True


class ProductionTargetError(RuntimeError):
    pass


def base_url() -> str:
    load_env_local()
    raw = (os.getenv("LNF_BASE_URL") or "").strip().rstrip("/")
    return raw


def target_name() -> str:
    load_env_local()
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
    load_env_local()
    if profile == "P10":
        dedicated = (os.getenv("LNF_TOKEN_P10") or "").strip()
        shared = (os.getenv("API_DELPI_INTERNAL_SERVICE_TOKEN") or "").strip()
        return dedicated or shared or None
    return (os.getenv(f"LNF_TOKEN_{profile}") or "").strip() or None


def core_base_url() -> str | None:
    load_env_local()
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
