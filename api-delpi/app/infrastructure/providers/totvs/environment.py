"""Centralized logical TOTVS environment selection (TOTVS_TARGET_ENV).

A single governed choice resolves the SQL business database and the
Intranet PARAMETROS_AMBIENTE row set (which drives the effective REST
endpoint). It does NOT replace credentials, connection strings or the
PROTHEUS_REST_EXPECTED_BASE_URL write pin — those stay independent.

Backward compatibility: when TOTVS_TARGET_ENV is unset, resolution falls
back to the legacy per-variable behavior and no semantic changes apply.

Fail-closed rules (backend config only — never request-derived):
- Unknown selector value -> RuntimeError.
- Explicit TOTVS_DB_DATABASE contradicting the approved catalog -> RuntimeError.
- Explicit INTRANET_PARAMS_AMBIENTE contradicting the catalog -> RuntimeError.
- A "DISABLED" database token keeps reads disabled (HML policy).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings

# Approved environment catalog — database names and PARAMETROS_AMBIENTE
# codes are governed values, never request-supplied.
TOTVS_ENVIRONMENT_CATALOG: dict[str, dict[str, str]] = {
    "TST01": {"sql_database": "DELPI_TST01", "ambiente": "2"},
    "PROD": {"sql_database": "DELPI", "ambiente": "1"},
}

DISABLED_DATABASE_TOKENS = {"", "DISABLED"}


@dataclass(frozen=True)
class TotvsEnvironmentProfile:
    target_environment: str | None
    sql_database: str | None
    rest_parameter_environment: str | None
    expected_rest_base_url: str | None
    sql_read_enabled: bool
    rest_write_eligible: bool


def resolve_totvs_environment() -> TotvsEnvironmentProfile:
    """Resolve the effective TOTVS target profile for this runtime."""
    selector = (settings.TOTVS_TARGET_ENV or "").strip().upper()
    expected_rest = (settings.PROTHEUS_REST_EXPECTED_BASE_URL or "").strip() or None

    if not selector:
        # Legacy mode — explicit per-variable configuration (unchanged).
        database = settings.TOTVS_DB_DATABASE or settings.DB_DATABASE
        return TotvsEnvironmentProfile(
            target_environment=None,
            sql_database=database,
            rest_parameter_environment=(
                (settings.INTRANET_PARAMS_AMBIENTE or "").strip() or None
            ),
            expected_rest_base_url=expected_rest,
            sql_read_enabled=(database or "").strip().upper()
            not in DISABLED_DATABASE_TOKENS,
            rest_write_eligible=expected_rest is not None,
        )

    catalog = TOTVS_ENVIRONMENT_CATALOG.get(selector)
    if catalog is None:
        raise RuntimeError(
            "TOTVS_TARGET_ENV inválido — valores aceitos: "
            + ", ".join(sorted(TOTVS_ENVIRONMENT_CATALOG))
            + ". Falha fechada: nenhum destino TOTVS resolvido."
        )

    explicit_database = (settings.TOTVS_DB_DATABASE or "").strip()
    if explicit_database and explicit_database != catalog["sql_database"]:
        raise RuntimeError(
            "Configuração TOTVS divergente: TOTVS_DB_DATABASE="
            f"{explicit_database} contradiz o catálogo de {selector} "
            f"({catalog['sql_database']}). Falha fechada."
        )

    explicit_ambiente = (settings.INTRANET_PARAMS_AMBIENTE or "").strip()
    if explicit_ambiente and explicit_ambiente != catalog["ambiente"]:
        raise RuntimeError(
            "Configuração TOTVS divergente: INTRANET_PARAMS_AMBIENTE="
            f"{explicit_ambiente} contradiz o catálogo de {selector} "
            f"({catalog['ambiente']}). Falha fechada."
        )

    return TotvsEnvironmentProfile(
        target_environment=selector,
        sql_database=catalog["sql_database"],
        rest_parameter_environment=catalog["ambiente"],
        expected_rest_base_url=expected_rest,
        sql_read_enabled=True,
        rest_write_eligible=expected_rest is not None,
    )
