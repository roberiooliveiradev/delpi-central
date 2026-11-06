"""Composição do bounded context Product Registration.

``ENG_PRC_REPOSITORY``:
- ``postgres`` → ``PostgresProductRegistrationRepository`` com DSN
  dedicada ``ENG_PRC_DB_*`` (principal próprio — nunca PLUGINS_DB_*);
- ``memory`` → ``InMemoryProductRegistrationRepository`` (dev/testes);
- ausente/outro → ``UnavailableProductRegistrationRepository``.

Sources de intake: ``ENG_PRC_SOURCES_ALLOWLIST`` (CSV); default
``portal-engineering,eva,engineering-test``.
"""

from __future__ import annotations

import os

from engineering_app.application.ports.product_registration import (
    ProductRegistrationRepository,
)
from engineering_app.application.use_cases.product_registration.service import (
    ProductRegistrationService,
)


def _sources_allowlist() -> tuple[str, ...]:
    raw = os.getenv("ENG_PRC_SOURCES_ALLOWLIST", "")
    items = tuple(s.strip() for s in raw.split(",") if s.strip())
    return items or ("portal-engineering", "eva", "engineering-test")


_REPO_SINGLETON: ProductRegistrationRepository | None = None


def reset_prc_singletons() -> None:
    """Reset de testes/harness — não usar em runtime."""
    global _REPO_SINGLETON
    _REPO_SINGLETON = None


def build_prc_repository() -> ProductRegistrationRepository:
    """Adapter por ambiente — instância única por processo.

    ``memory`` exige singleton (store em processo); ``postgres``
    compartilha DSN com reutilização segura da mesma instância.
    """
    global _REPO_SINGLETON
    if _REPO_SINGLETON is not None:
        return _REPO_SINGLETON
    mode = (os.getenv("ENG_PRC_REPOSITORY") or "").strip().lower()
    if mode == "memory":
        from engineering_app.infrastructure.persistence.product_registration.in_memory_repository import (
            InMemoryProductRegistrationRepository,
        )

        _REPO_SINGLETON = InMemoryProductRegistrationRepository()
    elif mode == "postgres":
        _REPO_SINGLETON = _build_postgres()
    else:
        from engineering_app.infrastructure.persistence.product_registration.unavailable_repository import (
            UnavailableProductRegistrationRepository,
        )

        _REPO_SINGLETON = UnavailableProductRegistrationRepository()
    return _REPO_SINGLETON


def _build_postgres() -> ProductRegistrationRepository:
    from engineering_app.infrastructure.persistence.product_registration.postgres_repository import (
        PostgresProductRegistrationRepository,
    )

    dsn = (os.getenv("ENG_PRC_DB_DSN") or "").strip()
    if not dsn:
        host = os.getenv("ENG_PRC_DB_HOST", "")
        port = os.getenv("ENG_PRC_DB_PORT", "5432")
        name = os.getenv("ENG_PRC_DB_NAME", "")
        user = os.getenv("ENG_PRC_DB_USER", "")
        password = os.getenv("ENG_PRC_DB_PASSWORD", "")
        if user and user == os.getenv("PLUGINS_DB_USER", "__none__"):
            raise RuntimeError(
                "ENG_PRC_DB_USER não pode reutilizar o principal "
                "compartilhado PLUGINS_DB_USER — exige role dedicada."
            )
        if not all([host, name, user]):
            raise RuntimeError(
                "ENG_PRC_REPOSITORY=postgres exige ENG_PRC_DB_DSN ou "
                "ENG_PRC_DB_HOST/NAME/USER completos."
            )
        dsn = (
            f"host={host} port={port} dbname={name} "
            f"user={user} password={password}"
        )
    return PostgresProductRegistrationRepository(dsn)


def build_official_product_reader():
    from engineering_app.config import settings
    from engineering_app.infrastructure.gateways.delegated_auxiliary import (
        ApiDelpiDelegatedAuxiliary,
    )
    from engineering_app.infrastructure.gateways.downstream_client import (
        DownstreamClient,
    )
    from engineering_app.infrastructure.gateways.official_product_reader import (
        ApiDelpiOfficialProductReader,
    )

    return ApiDelpiOfficialProductReader(
        ApiDelpiDelegatedAuxiliary(
            DownstreamClient(
                settings.DELPI_API_URL,
                timeout_seconds=settings.LMP_FACTS_TIMEOUT_SECONDS,
            )
        )
    )


_SERVICE_SINGLETON: ProductRegistrationService | None = None


def set_prc_service_for_tests(service: ProductRegistrationService) -> None:
    """Harness de testes — injeta service com reader controlado."""
    global _SERVICE_SINGLETON
    _SERVICE_SINGLETON = service


def build_prc_service() -> ProductRegistrationService:
    global _SERVICE_SINGLETON
    if _SERVICE_SINGLETON is not None:
        return _SERVICE_SINGLETON
    _SERVICE_SINGLETON = ProductRegistrationService(
        build_prc_repository(),
        official_reader=build_official_product_reader(),
        allowed_sources=_sources_allowlist(),
    )
    return _SERVICE_SINGLETON
