"""Centralized logical TOTVS environment selection (TOTVS_TARGET_ENV).

A single governed choice resolves the SQL business database and the
Intranet PARAMETROS_AMBIENTE row set (which drives the effective REST
endpoint). It does NOT replace credentials, connection strings or the
PROTHEUS_REST_EXPECTED_BASE_URL write pin — those stay independent.
The selector never authorizes a write: feature gates, Core AuthZ and the
REST pin still gate every write path.

Authorized runtime matrix (API_DELPI_ENV → allowed selector):

| Runtime     | TST01 | PROD    |
| DEV         | yes   | blocked |
| HML         | yes   | blocked |
| PROD        | —     | yes     |
| unclassifiable | blocked | blocked |

Fail-closed rules (backend config only — never request-derived):
- Unknown selector value -> RuntimeError.
- Selector not allowed for the current runtime -> RuntimeError.
- Explicit TOTVS_DB_DATABASE contradicting the approved catalog -> RuntimeError.
- Explicit INTRANET_PARAMS_AMBIENTE contradicting the catalog -> RuntimeError.
- A "DISABLED" database token marks reads disabled (HML policy) and the
  connection provider refuses to open a connection.
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

# Canonical runtime classification from the existing API_DELPI_ENV.
_RUNTIME_ALIASES: dict[str, str] = {
    "development": "DEV",
    "dev": "DEV",
    "homologation": "HML",
    "homologacao": "HML",
    "hml": "HML",
    "staging": "HML",
    "production": "PROD",
    "prod": "PROD",
}

# Selectors authorized per runtime. PROD+TST01 requires an explicit
# operational policy change — blocked until one exists.
ALLOWED_SELECTORS_BY_RUNTIME: dict[str, frozenset[str]] = {
    "DEV": frozenset({"TST01"}),
    "HML": frozenset({"TST01"}),
    "PROD": frozenset({"PROD"}),
}


@dataclass(frozen=True)
class TotvsEnvironmentProfile:
    target_environment: str | None
    runtime_environment: str | None
    sql_database: str | None
    rest_parameter_environment: str | None
    expected_rest_base_url: str | None
    sql_read_enabled: bool
    # True only when the independent write pin is configured — NOT a
    # proof of correct target and NEVER an authorization to write.
    rest_write_pin_configured: bool


def _runtime_environment() -> str | None:
    raw = (settings.API_ENV or "").strip().lower()
    return _RUNTIME_ALIASES.get(raw)


def resolve_totvs_environment() -> TotvsEnvironmentProfile:
    """Resolve the effective TOTVS target profile for this runtime."""
    selector = (settings.TOTVS_TARGET_ENV or "").strip().upper()
    expected_rest = (settings.PROTHEUS_REST_EXPECTED_BASE_URL or "").strip() or None
    runtime = _runtime_environment()

    if not selector:
        # Legacy mode — explicit per-variable configuration (unchanged).
        database = settings.TOTVS_DB_DATABASE or settings.DB_DATABASE
        return TotvsEnvironmentProfile(
            target_environment=None,
            runtime_environment=runtime,
            sql_database=database,
            rest_parameter_environment=(
                (settings.INTRANET_PARAMS_AMBIENTE or "").strip() or None
            ),
            expected_rest_base_url=expected_rest,
            sql_read_enabled=(database or "").strip().upper()
            not in DISABLED_DATABASE_TOKENS,
            rest_write_pin_configured=expected_rest is not None,
        )

    catalog = TOTVS_ENVIRONMENT_CATALOG.get(selector)
    if catalog is None:
        raise RuntimeError(
            "TOTVS_TARGET_ENV inválido — valores aceitos: "
            + ", ".join(sorted(TOTVS_ENVIRONMENT_CATALOG))
            + ". Falha fechada: nenhum destino TOTVS resolvido."
        )

    allowed = ALLOWED_SELECTORS_BY_RUNTIME.get(runtime or "")
    if not allowed or selector not in allowed:
        raise RuntimeError(
            "TOTVS_TARGET_ENV={} não autorizado para o runtime '{}' "
            "(API_DELPI_ENV={!r}). Falha fechada: nenhum destino TOTVS "
            "resolvido.".format(
                selector, runtime or "unclassifiable", settings.API_ENV
            )
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
        runtime_environment=runtime,
        sql_database=catalog["sql_database"],
        rest_parameter_environment=catalog["ambiente"],
        expected_rest_base_url=expected_rest,
        sql_read_enabled=True,
        rest_write_pin_configured=expected_rest is not None,
    )
