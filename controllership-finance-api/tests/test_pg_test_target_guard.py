"""Guarda do destino destrutivo dos testes PG (R4 rework).

Sem banco real: prova, sobre conexões falsificadas, que o isolamento só
executa DDL destrutivo sobre o recurso que a própria execução criou —
comprovado pelo token de ownership — e que nenhum banco preexistente,
compartilhado ou de nome ambíguo pode ser alvo, seja qual for a
configuração fornecida.
"""

from __future__ import annotations

import psycopg
import pytest

from pg_test_isolation import (
    OwnedTestDatabase,
    assert_safe_test_prefix,
    create_owned_test_database,
    drop_owned_test_database,
    ephemeral_db_name,
    require_test_environment,
)


# --- conexões falsificadas ---------------------------------------------------


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, statement, params=None):
        text = (
            statement.as_string(None)
            if hasattr(statement, "as_string")
            else str(statement)
        )
        self._conn.statements.append((text, params))
        if "SELECT run_token" in text:
            if self._conn.marker_missing:
                raise psycopg.errors.UndefinedTable("no marker")
            self._conn.result = (self._conn.marker_token,)
        if "CREATE DATABASE" in text:
            name = text.split('"')[1]
            if name in self._conn.existing or self._conn.collide_once:
                self._conn.collide_once = False
                raise psycopg.errors.DuplicateDatabase("exists")
            self._conn.existing.add(name)

    def fetchone(self):
        return getattr(self._conn, "result", None)


class _FakeConn:
    def __init__(
        self, dbname, state, *, marker_token=None, marker_missing=False
    ):
        self.dbname = dbname
        self.statements = state.setdefault("statements", [])
        self.existing = state.setdefault("existing", set())
        self.marker_token = marker_token
        self.marker_missing = marker_missing
        self.collide_once = state.get("collide_once", False)
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def cursor(self):
        return _FakeCursor(self)


def _factory(state, **kw):
    def connect(dbname):
        state.setdefault("connected", []).append(dbname)
        return _FakeConn(dbname, state, **kw)

    return connect


def _failing_factory(state):
    def connect(dbname):
        state.setdefault("connected", []).append(dbname)
        raise psycopg.OperationalError("admin connection refused")

    return connect


def _owned(name="cf_test_x_test_abc123def456", token="token-1"):
    return OwnedTestDatabase(name=name, run_token=token)


def _drop_statements(state):
    return [
        s for s, _ in state.get("statements", []) if "DROP DATABASE" in s
    ]


# --- prefixo: fail-closed sobre configuração ambígua -------------------------


@pytest.mark.parametrize(
    "name",
    [
        "plugins_hub",      # banco compartilhado canônico
        "postgres",         # banco de manutenção
        "delpi_core",       # banco do Core
        "template0",
        "template1",
        "plugins_hub_prod", # sem marcador de teste
        "plugins",          # ambíguo
        "",                 # vazio
        "prod",             # ambíguo
        "TEST DB",          # não é nome SQL seguro
        "test';DROP",       # tentativa de injeção
        "test db",          # espaço
    ],
)
def test_unsafe_prefixes_rejected(name):
    with pytest.raises(ValueError):
        assert_safe_test_prefix(name)


@pytest.mark.parametrize(
    "name",
    [
        "controllership_finance_test",
        "plugins_hub_test",
        "test_closing_checklist",
        "cf_test_20261024",
    ],
)
def test_dedicated_prefixes_accepted(name):
    assert_safe_test_prefix(name)  # não levanta


# --- opt-in e declaração de cluster -----------------------------------------


@pytest.mark.parametrize(
    "env, why",
    [
        ({}, "cluster"),
        ({"CF_TEST_PG_ALLOW_DESTRUCTIVE": "1"}, "cluster"),
        ({"CF_TEST_PG_CLUSTER": "test"}, "destructive"),
        ({"CF_TEST_PG_CLUSTER": "prod",
          "CF_TEST_PG_ALLOW_DESTRUCTIVE": "1"}, "cluster"),
        ({"CF_TEST_PG_CLUSTER": "test",
          "CF_TEST_PG_ALLOW_DESTRUCTIVE": "0"}, "destructive"),
    ],
)
def test_missing_opt_ins_refused(env, why):
    refusal = require_test_environment(env)
    assert refusal is not None
    assert why in refusal.lower()


def test_full_opt_in_authorized():
    env = {
        "CF_TEST_PG_CLUSTER": "test",
        "CF_TEST_PG_ALLOW_DESTRUCTIVE": "1",
    }
    assert require_test_environment(env) is None


# --- criação: nunca destrói, sempre recurso novo ----------------------------


def test_create_never_drops_and_marks_ownership():
    state = {}
    owned = create_owned_test_database(
        _factory(state), "postgres", "closing_test"
    )
    statements = [s for s, _ in state["statements"]]
    assert _drop_statements(state) == []
    assert statements[0].startswith('CREATE DATABASE "cf_test_closing_test_')
    assert any("CREATE TABLE" in s for s in statements)
    assert any("INSERT INTO" in s for s in statements)
    # prova de ownership gravada no próprio recurso criado
    insert = [p for s, p in state["statements"] if "INSERT INTO" in s][0]
    assert insert == (owned.run_token,)


def test_create_retries_on_name_collision_without_destroying():
    # primeira tentativa colide com um banco preexistente de mesmo nome:
    # a resposta é novo identificador, nunca DROP do existente
    state = {"collide_once": True, "existing": {"cf_test_collision_test_a"}}
    owned = create_owned_test_database(
        _factory(state), "postgres", "collision_test"
    )
    creates = [
        s for s, _ in state["statements"] if "CREATE DATABASE" in s
    ]
    assert len(creates) == 2  # colidiu, gerou outro identificador
    assert _drop_statements(state) == []
    assert owned.name in state["existing"]
    # o preexistente permanece — apenas o novo nome foi criado
    assert "cf_test_collision_test_a" in state["existing"]


def test_ephemeral_names_unique_per_execution():
    names = {
        ephemeral_db_name("closing_test", uuid_token)
        for uuid_token in ("a" * 32, "b" * 32, "c" * 32)
    }
    assert len(names) == 3
    assert all(n.startswith("cf_test_closing_test_") for n in names)


def test_admin_connection_failure_aborts_without_ddl():
    state = {}
    with pytest.raises(psycopg.OperationalError):
        create_owned_test_database(
            _failing_factory(state), "postgres", "closing_test"
        )
    assert _drop_statements(state) == []


# --- teardown: DROP exclusivo sobre recurso comprovadamente próprio ---------


def test_drop_only_when_ownership_token_matches():
    state = {}
    owned = _owned(token="token-1")
    dropped = drop_owned_test_database(
        _factory(state, marker_token="token-1"), "postgres", owned
    )
    assert dropped is True
    drops = _drop_statements(state)
    assert len(drops) == 1
    assert f'DROP DATABASE "{owned.name}"' in drops[0]


@pytest.mark.parametrize(
    "marker_token, marker_missing",
    [
        ("token-OTHER", False),   # token divergente — recurso alheio
        (None, False),            # linha nula
        (None, True),             # sem marcador — ownership indeterminado
    ],
)
def test_no_drop_without_ownership_proof(marker_token, marker_missing):
    state = {}
    owned = _owned(token="token-1")
    dropped = drop_owned_test_database(
        _factory(
            state, marker_token=marker_token, marker_missing=marker_missing
        ),
        "postgres",
        owned,
    )
    assert dropped is False
    assert _drop_statements(state) == []


def test_no_drop_on_admin_connection_failure():
    state = {}
    owned = _owned()
    dropped = drop_owned_test_database(
        _failing_factory(state), "postgres", owned
    )
    assert dropped is False
    assert _drop_statements(state) == []


def test_preexisting_database_never_targeted():
    """Banco preexistente (mesmo com nome *contendo* 'test') não é alvo:
    o teardown usa o objeto `owned` desta execução, jamais um nome lido de
    configuração ou descoberto por convenção."""
    state = {}
    owned = _owned(
        name="cf_test_closing_test_own", token="token-1"
    )
    drop_owned_test_database(
        _factory(state, marker_token="token-1"), "postgres", owned
    )
    drops = _drop_statements(state)
    assert drops == [f'DROP DATABASE "{owned.name}" WITH (FORCE)']
    # plugins_hub_test e plugins_hub jamais aparecem em qualquer DDL
    joined = " ".join(s for s, _ in state["statements"])
    assert "plugins_hub" not in joined


def test_env_mutation_after_setup_cannot_redirect_teardown(monkeypatch):
    state = {}
    owned = _owned(name="cf_test_closing_test_own", token="token-1")
    monkeypatch.setenv("CF_TEST_PG_NAME", "plugins_hub")
    monkeypatch.setenv("CF_TEST_PG_ADMIN_DB", "plugins_hub")
    drop_owned_test_database(
        _factory(state, marker_token="token-1"), "postgres", owned
    )
    drops = _drop_statements(state)
    assert drops == [f'DROP DATABASE "{owned.name}" WITH (FORCE)']
    assert "plugins_hub" not in " ".join(drops)


def test_injection_cannot_reach_sql():
    """Identificadores passam por sql.Identifier — um nome malicioso é um
    único identificador quotado, nunca SQL adicional; e prefixos com
    metacaracteres já falham na validação de `assert_safe_test_prefix`."""
    state = {}
    owned = _owned(
        name='cf_test_x";DROP DATABASE plugins_hub;--', token="t"
    )
    drop_owned_test_database(
        _factory(state, marker_token="t"), "postgres", owned
    )
    drops = _drop_statements(state)
    assert len(drops) == 1
    assert drops[0].startswith('DROP DATABASE "cf_test_x""')
    # exatamente uma instrução emitida — o payload virou um identificador
    assert len(state["statements"]) == 2  # SELECT + DROP
