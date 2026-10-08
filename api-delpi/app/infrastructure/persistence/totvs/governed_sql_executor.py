# app/infrastructure/persistence/totvs/governed_sql_executor.py
"""Executor bounded para Governed Analytical SQL READ (S1).

Contrato interno (ainda sem rota/DAVI):

    statement   — texto T-SQL único (perfil DAVI_GOVERNED do SqlValidator)
    parameters  — sequência posicional vinculada via `?` (pyodbc binding)

Defesas:
    - validação estrutural DAVI_GOVERNED (fail closed)
    - conexão dedicada GOVERNED_SQL_DB_* (read-only principal — S6 prova grant)
    - um único resultset
    - fetchmany(max_rows+1) — sem fetchall()
    - limites de colunas, tamanho de célula e bytes estimados
    - timeout de query dedicado
    - erros categorizados sem vazamento de diagnóstico do SQL Server
    - observabilidade: actor, correlation_id, query_hash, tables, duração,
      linhas, bytes, truncamento, categoria de erro (nunca SQL completo,
      nunca parâmetros, nunca credenciais)

Estratégia de row bound (S1.9): fetchmany(N+1) + descarte da conexão.
Não existe rewrite textual TOP universalmente correto para T-SQL
(ORDER BY/DISTINCT/CTE/UNION/window) — sem AST-root injection confiável,
a contenção é client-side + timeout + limites de complexidade da política.
Custo residual de scan server-side é registrado honestamente.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from app.application.services.governed_sql_errors import (
    EXECUTION_FAILED,
    POLICY_UNAVAILABLE,
    RESULT_TOO_LARGE,
    GovernedSqlError,
    map_execution_error,
    map_permission_error,
)
from app.application.services.sql_validator import (
    PROFILE_DAVI_GOVERNED,
    SqlValidator,
)

logger = logging.getLogger("totvs.governed_sql.executor")
if not logger.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setLevel(logging.WARNING)
    _h.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(_h)

GOVERNED_SQL_MAX_ROWS = int(os.getenv("GOVERNED_SQL_MAX_ROWS", "500"))
GOVERNED_SQL_MAX_COLUMNS = int(os.getenv("GOVERNED_SQL_MAX_COLUMNS", "50"))
GOVERNED_SQL_MAX_CELL_CHARS = int(os.getenv("GOVERNED_SQL_MAX_CELL_CHARS", "4000"))
GOVERNED_SQL_MAX_RESPONSE_BYTES = int(
    os.getenv("GOVERNED_SQL_MAX_RESPONSE_BYTES", "262144")
)
GOVERNED_SQL_MAX_PARAMS = int(os.getenv("GOVERNED_SQL_MAX_PARAMS", "50"))


@dataclass
class GovernedSqlResult:
    """Resultado interno bounded — ainda NÃO é o envelope de saída (S3)."""

    columns: list[str]
    rows: list[list]
    row_count: int
    truncated: bool
    truncation_reasons: list[str] = field(default_factory=list)
    query_hash: str = ""
    tables: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


def _query_hash(statement: str, parameters: tuple) -> str:
    digest = hashlib.sha256()
    digest.update(statement.encode("utf-8", errors="replace"))
    for value in parameters:
        digest.update(repr(value).encode("utf-8", errors="replace"))
        digest.update(b"\x00")
    return digest.hexdigest()[:16]


def _cell_bytes(value) -> int:
    if value is None:
        return 4
    if isinstance(value, (bytes, bytearray, memoryview)):
        return len(value)
    if isinstance(value, str):
        return len(value.encode("utf-8", errors="replace"))
    if isinstance(value, (int, float, Decimal, bool)):
        return 24
    if isinstance(value, (datetime, date)):
        return 32
    return len(str(value).encode("utf-8", errors="replace"))


class GovernedSqlExecutor:
    """Executor de leitura analítica governada — interno, sem rota."""

    def __init__(self, connection_factory=None, validator: SqlValidator | None = None):
        self._connection_factory = connection_factory
        self._validator = validator or SqlValidator()

    # ------------------------------------------------------------------
    def _connection(self):
        from app.infrastructure.providers.totvs.governed_sql_connection import (
            create_governed_sql_connection,
        )

        factory = self._connection_factory or create_governed_sql_connection
        try:
            return factory()
        except GovernedSqlError:
            raise
        except Exception as e:
            raise GovernedSqlError(
                POLICY_UNAVAILABLE,
                "Caminho de execução governed SQL indisponível.",
                detail=str(e)[:500],
            )

    # ------------------------------------------------------------------
    def execute(
        self,
        statement: str,
        parameters: tuple | list | None = None,
        *,
        actor: str | None = None,
        correlation_id: str | None = None,
    ) -> GovernedSqlResult:
        params = tuple(parameters or ())
        qhash = _query_hash(statement, params)
        started = time.perf_counter()
        tables: set[str] = set()

        def _log(outcome: str, **extra):
            logger.info(
                "governed_sql outcome=%s actor=%s corr=%s qhash=%s "
                "tables=%s duration_ms=%.0f %s",
                outcome,
                actor or "-",
                correlation_id or "-",
                qhash,
                sorted(tables),
                (time.perf_counter() - started) * 1000,
                " ".join(f"{k}={v}" for k, v in extra.items()),
            )

        # ---- validação estrutural ------------------------------------
        if len(params) > GOVERNED_SQL_MAX_PARAMS:
            raise GovernedSqlError(
                RESULT_TOO_LARGE, "Número de parâmetros excede o limite."
            )
        try:
            self._validator.validate(statement, profile=PROFILE_DAVI_GOVERNED)
        except PermissionError as e:
            _log("validation_failed")
            raise map_permission_error(e)

        # ---- execução bounded ----------------------------------------
        connection = None
        cursor = None
        truncated = False
        reasons: list[str] = []
        total_bytes = 0
        row_count = 0
        columns: list[str] = []
        rows: list[list] = []

        try:
            connection = self._connection()
            cursor = connection.cursor()

            try:
                cursor.execute(statement, params)
            except Exception as e:
                _log("execution_error")
                raise map_execution_error(e)

            if cursor.description is None:
                _log("no_resultset")
                raise GovernedSqlError(
                    EXECUTION_FAILED,
                    "Consulta não produziu resultset.",
                )

            columns = [desc[0] for desc in cursor.description]
            if len(columns) > GOVERNED_SQL_MAX_COLUMNS:
                truncated = True
                reasons.append("column_limit")
                columns = columns[:GOVERNED_SQL_MAX_COLUMNS]

            while True:
                batch = cursor.fetchmany(GOVERNED_SQL_MAX_ROWS - row_count + 1)
                if not batch:
                    break

                for raw_row in batch:
                    if row_count >= GOVERNED_SQL_MAX_ROWS:
                        truncated = True
                        if "row_limit" not in reasons:
                            reasons.append("row_limit")
                        break

                    row = []
                    for value in raw_row[: len(columns)]:
                        cell_b = _cell_bytes(value)
                        if isinstance(value, str) and len(value) > GOVERNED_SQL_MAX_CELL_CHARS:
                            value = value[:GOVERNED_SQL_MAX_CELL_CHARS]
                            truncated = True
                            if "cell_size" not in reasons:
                                reasons.append("cell_size")
                            cell_b = GOVERNED_SQL_MAX_CELL_CHARS * 4
                        if total_bytes + cell_b > GOVERNED_SQL_MAX_RESPONSE_BYTES:
                            truncated = True
                            if "response_bytes" not in reasons:
                                reasons.append("response_bytes")
                            break
                        total_bytes += cell_b
                        row.append(value)
                    else:
                        # row incompleto por response_bytes → não append
                        if "response_bytes" in reasons and len(row) < len(columns):
                            truncated = True
                            break
                        rows.append(row)
                        row_count += 1
                        continue
                    break

                if truncated:
                    break

            # resultset único — qualquer extra é descartado
            try:
                if cursor.nextset():
                    truncated = True
                    if "resultset_limit" not in reasons:
                        reasons.append("resultset_limit")
            except Exception:
                pass

        except GovernedSqlError:
            raise
        except Exception as e:
            _log("execution_error")
            raise map_execution_error(e)
        finally:
            # descarta conexão em truncamento/erro (cancelamento client-side)
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
            try:
                if connection:
                    connection.close()
            except Exception:
                pass

        duration_ms = (time.perf_counter() - started) * 1000
        result = GovernedSqlResult(
            columns=columns,
            rows=rows,
            row_count=row_count,
            truncated=truncated,
            truncation_reasons=reasons,
            query_hash=qhash,
            duration_ms=duration_ms,
        )
        _log(
            "ok",
            rows=row_count,
            cols=len(columns),
            bytes=total_bytes,
            truncated=truncated,
        )
        return result
