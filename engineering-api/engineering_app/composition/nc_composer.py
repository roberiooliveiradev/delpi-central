"""Composição do bounded context NC — seleção de adapter por ambiente.

``ENG_NC_REPOSITORY``:
- ``postgres`` → ``PostgresNonconformityRepository`` com DSN dedicada
  ``ENG_NC_DB_*`` (principal próprio do contexto — nunca PLUGINS_DB_*);
- ``memory`` → ``InMemoryNonconformityRepository`` (dev/testes);
- ausente/outro → ``UnavailableNonconformityRepository`` (fail-honest).

Salvaguardas de boundary:
- recusa construir Postgres quando ``ENG_NC_DB_USER`` coincide com
  ``PLUGINS_DB_USER`` — a credencial compartilhada não pode ser herdada;
- ``delete_all_records`` só é liberado com
  ``ENG_NC_IMPORT_REPLACE_ENABLED=true`` explícito.
"""

from __future__ import annotations

import os

from engineering_app.application.ports.nonconformity_repository import (
    NonconformityRepository,
)


def build_nonconformity_repository() -> NonconformityRepository:
    mode = (os.getenv("ENG_NC_REPOSITORY") or "").strip().lower()

    if mode == "memory":
        from engineering_app.infrastructure.persistence.nonconformity.in_memory_nonconformity_repository import (
            InMemoryNonconformityRepository,
        )

        return InMemoryNonconformityRepository()

    if mode == "postgres":
        return _build_postgres()

    from engineering_app.infrastructure.persistence.nonconformity.unavailable_nonconformity_repository import (
        UnavailableNonconformityRepository,
    )

    return UnavailableNonconformityRepository()


def _build_postgres() -> NonconformityRepository:
    from engineering_app.infrastructure.persistence.nonconformity.postgres_nonconformity_repository import (
        PostgresNonconformityRepository,
    )

    dsn = (os.getenv("ENG_NC_DB_DSN") or "").strip()
    if not dsn:
        host = os.getenv("ENG_NC_DB_HOST", "")
        port = os.getenv("ENG_NC_DB_PORT", "5432")
        name = os.getenv("ENG_NC_DB_NAME", "")
        user = os.getenv("ENG_NC_DB_USER", "")
        password = os.getenv("ENG_NC_DB_PASSWORD", "")
        if user and user == os.getenv("PLUGINS_DB_USER", "__none__"):
            raise RuntimeError(
                "ENG_NC_DB_USER não pode reutilizar o principal "
                "compartilhado PLUGINS_DB_USER — exige role dedicada."
            )
        if not all([host, name, user]):
            raise RuntimeError(
                "ENG_NC_REPOSITORY=postgres exige ENG_NC_DB_DSN ou "
                "ENG_NC_DB_HOST/NAME/USER completos."
            )
        dsn = (
            f"host={host} port={port} dbname={name} "
            f"user={user} password={password}"
        )

    allow_replace = (
        os.getenv("ENG_NC_IMPORT_REPLACE_ENABLED", "").strip().lower()
        == "true"
    )
    return PostgresNonconformityRepository(dsn, allow_replace=allow_replace)


def build_nc_earliest_ov_source():
    """Âncora «primeira OV» para E-NC-04 — fonte delegada oficial."""
    from engineering_app.config import settings
    from engineering_app.infrastructure.gateways.delegated_earliest_ov import (
        DelegatedEarliestOvDate,
    )
    from engineering_app.infrastructure.gateways.downstream_client import (
        DownstreamClient,
    )

    return DelegatedEarliestOvDate(
        DownstreamClient(
            settings.DELPI_API_URL,
            timeout_seconds=settings.LMP_FACTS_TIMEOUT_SECONDS,
        )
    )


def build_list_nonconformities_use_case():
    from engineering_app.application.use_cases.nonconformity.read import (
        ListNonconformitiesUseCase,
    )

    return ListNonconformitiesUseCase(build_nonconformity_repository())


def build_get_nonconformity_use_case():
    from engineering_app.application.use_cases.nonconformity.read import (
        GetNonconformityUseCase,
    )

    return GetNonconformityUseCase(build_nonconformity_repository())


def build_list_nonconformity_history_use_case():
    from engineering_app.application.use_cases.nonconformity.read import (
        ListNonconformityHistoryUseCase,
    )

    return ListNonconformityHistoryUseCase(build_nonconformity_repository())


def build_get_nonconformity_indicators_use_case():
    from engineering_app.application.use_cases.nonconformity.read import (
        GetNonconformityIndicatorsUseCase,
    )

    return GetNonconformityIndicatorsUseCase(
        build_nonconformity_repository(),
        earliest_ov_source=build_nc_earliest_ov_source(),
    )


def build_list_problem_tags_use_case():
    from engineering_app.application.use_cases.nonconformity.read import (
        ListProblemTagsUseCase,
    )

    return ListProblemTagsUseCase(build_nonconformity_repository())


def build_export_nonconformities_use_case():
    from engineering_app.application.use_cases.nonconformity.read import (
        ExportNonconformitiesUseCase,
    )

    return ExportNonconformitiesUseCase(build_nonconformity_repository())


def build_get_nonconformity_context_use_case():
    from engineering_app.application.use_cases.nonconformity.context import (
        GetNonconformityContextUseCase,
    )
    from engineering_app.composition.lmp_composer import (
        _build_facts_source,
        build_delegated_auxiliary_source,
    )

    return GetNonconformityContextUseCase(
        build_nonconformity_repository(),
        facts_source=_build_facts_source(),
        product_source=build_delegated_auxiliary_source(),
    )


def build_create_nonconformity_use_case():
    from engineering_app.application.use_cases.nonconformity.write import (
        CreateNonconformityUseCase,
    )

    return CreateNonconformityUseCase(build_nonconformity_repository())


def build_update_nonconformity_use_case():
    from engineering_app.application.use_cases.nonconformity.write import (
        UpdateNonconformityUseCase,
    )

    return UpdateNonconformityUseCase(build_nonconformity_repository())


def build_delete_nonconformity_use_case():
    from engineering_app.application.use_cases.nonconformity.write import (
        DeleteNonconformityUseCase,
    )

    return DeleteNonconformityUseCase(build_nonconformity_repository())


def build_import_nonconformities_use_case():
    from engineering_app.application.use_cases.nonconformity.write import (
        ImportNonconformitiesUseCase,
    )

    return ImportNonconformitiesUseCase(build_nonconformity_repository())


def build_prepare_nonconformity_mutation_use_case():
    from engineering_app.application.use_cases.nonconformity.prepare import (
        PrepareNonconformityMutationUseCase,
    )

    return PrepareNonconformityMutationUseCase(build_nonconformity_repository())
