"""Load Protheus REST parameters from PARAMETROS_MINHADELPI (read-only)."""

from __future__ import annotations

from typing import Callable

import pyodbc

from app.config import settings
from app.domain.integrations.protheus_rest import (
    OPTIONAL_PARAM_KEYS,
    REQUIRED_PARAM_KEYS,
    ProtheusRestError,
)
from app.infrastructure.providers.intranet.connection import create_intranet_connection
from app.utils.logger import log_error


class ProtheusIntegrationParamsRepository:
    """Reads integration parameters without exposing secrets to callers' logs."""

    def __init__(
        self,
        *,
        connection_factory: Callable[[], pyodbc.Connection] | None = None,
    ) -> None:
        self._connection_factory = connection_factory or create_intranet_connection

    def load_raw_params(self) -> dict[str, str]:
        table = settings.INTRANET_PARAMS_TABLE
        key_col = settings.INTRANET_PARAMS_KEY_COLUMN
        value_col = settings.INTRANET_PARAMS_VALUE_COLUMN

        for name in (table, key_col, value_col):
            if not _safe_sql_identifier(name):
                raise ProtheusRestError(
                    "Configuração Intranet de parâmetros inválida.",
                    code="PROTHEUS_CONFIG_INVALID",
                    status_code=503,
                )

        selected_keys = REQUIRED_PARAM_KEYS + OPTIONAL_PARAM_KEYS
        placeholders = ",".join("?" for _ in selected_keys)
        query = (
            f"SELECT [{key_col}] AS param_key, [{value_col}] AS param_value "
            f"FROM [{table}] "
            f"WHERE [{key_col}] IN ({placeholders})"
        )
        params: list[object] = list(selected_keys)

        ambiente = (settings.INTRANET_PARAMS_AMBIENTE or "").strip()
        if ambiente:
            if not ambiente.isdigit() or len(ambiente) > 8:
                raise ProtheusRestError(
                    "Configuração Intranet de parâmetros inválida.",
                    code="PROTHEUS_CONFIG_INVALID",
                    status_code=503,
                )
            query += " AND [AMBIENTE] = ?"
            params.append(int(ambiente))

        try:
            connection = self._connection_factory()
        except Exception as exc:
            log_error(f"Falha ao conectar Intranet para parâmetros Protheus: {type(exc).__name__}")
            raise ProtheusRestError(
                "Não foi possível ler a configuração Protheus.",
                code="PROTHEUS_CONFIG_UNAVAILABLE",
                status_code=503,
            ) from None

        try:
            cursor = connection.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall() or []
        except Exception:
            log_error("Falha ao consultar PARAMETROS Protheus")
            raise ProtheusRestError(
                "Não foi possível ler a configuração Protheus.",
                code="PROTHEUS_CONFIG_UNAVAILABLE",
                status_code=503,
            ) from None
        finally:
            try:
                connection.close()
            except Exception:
                pass

        result: dict[str, str] = {}
        for row in rows:
            key = _row_value(row, "param_key", 0)
            value = _row_value(row, "param_value", 1)
            if key:
                result[key] = value
        return result


def _row_value(row: object, attr: str, index: int) -> str:
    if hasattr(row, attr):
        raw = getattr(row, attr)
    else:
        try:
            raw = row[index]  # type: ignore[index]
        except Exception:
            raw = None
    return str(raw or "").strip()


def _safe_sql_identifier(name: str) -> bool:
    token = (name or "").strip()
    if not token or len(token) > 128:
        return False
    return all(ch.isalnum() or ch == "_" for ch in token)
