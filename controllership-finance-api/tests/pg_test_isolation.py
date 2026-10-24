"""Isolamento efêmero com prova de ownership — testes PostgreSQL (R4 rework).

Invariante: o fixture NUNCA destrói um banco que a própria execução não
criou. O mecanismo não depende de convenção de nome nem de opt-in como
prova de propriedade:

- o nome é efêmero (`cf_test_<prefixo>_<uuid>`) e gerado por execução;
- `CREATE DATABASE` roda sem `IF NOT EXISTS` — colisão nunca é resolvida
  destruindo o existente, apenas se tenta outro identificador;
- a execução grava um token de ownership dentro do banco recém-criado;
- o teardown só executa `DROP DATABASE` se o token lido no banco-alvo
  conferir com o token desta execução — incerteza ⇒ nenhum DROP;
- o teardown usa o nome capturado na criação, jamais releitura de env;
- `CF_TEST_PG_CLUSTER=test` declara o cluster como de teste e
  `CF_TEST_PG_ALLOW_DESTRUCTIVE=1` autoriza o DROP do recurso próprio —
  ambos exigidos antes de qualquer DDL.

Falha em qualquer etapa ⇒ fail-closed sem operação destrutiva.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Callable, Mapping

import psycopg
from psycopg import sql

RUN_PREFIX = "cf_test"
MAX_IDENTIFIER_LEN = 63
_CREATE_ATTEMPTS = 3
_MARKER_TABLE = "cf_test_run_ownership"

# Prefixos que jamais podem basear um banco de teste efêmero.
FORBIDDEN_PREFIXES = frozenset(
    {"postgres", "plugins_hub", "delpi_core", "template0", "template1"}
)
_PREFIX_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class OwnedTestDatabase:
    """Recurso criado por esta execução — prova de ownership em `run_token`."""

    name: str
    run_token: str


def assert_safe_test_prefix(prefix: str) -> None:
    """Fail-closed sobre configuração ambígua, antes de qualquer DDL."""
    if not _PREFIX_PATTERN.fullmatch(prefix):
        raise ValueError(f"CF_TEST_PG_NAME inválido: {prefix!r}")
    if prefix in FORBIDDEN_PREFIXES:
        raise ValueError(
            f"CF_TEST_PG_NAME aponta para banco protegido: {prefix!r}"
        )
    if "test" not in prefix:
        raise ValueError(
            f"CF_TEST_PG_NAME deve ser um prefixo dedicado de teste "
            f"(contendo 'test'): {prefix!r}"
        )


def require_test_environment(env: Mapping[str, str]) -> str | None:
    """Confirma cluster declarado de teste + opt-in destrutivo.

    Retorna a razão da recusa (para skip) ou ``None`` quando autorizado.
    """
    if env.get("CF_TEST_PG_CLUSTER") != "test":
        return (
            "CF_TEST_PG_CLUSTER=test ausente — cluster não declarado "
            "como ambiente de teste"
        )
    if env.get("CF_TEST_PG_ALLOW_DESTRUCTIVE") != "1":
        return (
            "CF_TEST_PG_ALLOW_DESTRUCTIVE=1 ausente — DROP do banco "
            "efêmero próprio não autorizado"
        )
    return None


def ephemeral_db_name(prefix: str, token: str) -> str:
    """Nome único por execução — impossível colidir com banco alheio."""
    raw = f"{RUN_PREFIX}_{prefix}_{token[:12]}"
    return raw[:MAX_IDENTIFIER_LEN]


def create_owned_test_database(
    connect: Callable[[str], psycopg.Connection],
    admin_db: str,
    prefix: str,
) -> OwnedTestDatabase:
    """Cria banco efêmero exclusivo e grava prova de ownership.

    `connect(dbname)` abre conexão autocommit no cluster autorizado.
    Nenhum DROP é executado — colisão gera novo identificador.
    """
    with connect(admin_db) as admin:
        with admin.cursor() as cur:
            for _ in range(_CREATE_ATTEMPTS):
                token = uuid.uuid4().hex
                owned = OwnedTestDatabase(
                    name=ephemeral_db_name(prefix, token),
                    run_token=token,
                )
                try:
                    cur.execute(
                        sql.SQL("CREATE DATABASE {}").format(
                            sql.Identifier(owned.name)
                        )
                    )
                    break
                except psycopg.errors.DuplicateDatabase:
                    continue
            else:
                raise RuntimeError(
                    "Não foi possível criar banco de teste exclusivo."
                )

    # Prova de ownership gravada dentro do próprio recurso criado.
    with connect(owned.name) as conn, conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                "CREATE TABLE {} (run_token TEXT PRIMARY KEY)"
            ).format(sql.Identifier(_MARKER_TABLE))
        )
        cur.execute(
            sql.SQL("INSERT INTO {} (run_token) VALUES (%s)").format(
                sql.Identifier(_MARKER_TABLE)
            ),
            (owned.run_token,),
        )
    return owned


def drop_owned_test_database(
    connect: Callable[[str], psycopg.Connection],
    admin_db: str,
    owned: OwnedTestDatabase,
) -> bool:
    """DROP exclusivamente sobre o recurso cuja prova de ownership confere.

    Qualquer incerteza — banco ausente, marcador ausente, token divergente,
    falha de conexão — resulta em NENHUM DROP (fail-closed). O nome vem do
    objeto `owned` capturado na criação, nunca de configuração externa.
    """
    try:
        with connect(owned.name) as conn, conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT run_token FROM {}").format(
                    sql.Identifier(_MARKER_TABLE)
                )
            )
            row = cur.fetchone()
    except psycopg.Error:
        return False
    if row is None or row[0] != owned.run_token:
        return False
    with connect(admin_db) as admin, admin.cursor() as cur:
        cur.execute(
            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                sql.Identifier(owned.name)
            )
        )
    return True
