"""Guarda do destino destrutivo dos testes PG (R4).

Sem banco: prova que `assert_safe_test_database` bloqueia destinos
compartilhados/ambíguos ANTES de qualquer DDL, e aceita apenas bancos
dedicados de teste. O opt-in `CF_TEST_PG_ALLOW_DESTRUCTIVE=1` é exigido
pela fixture, não testado aqui (comportamento de skip é do pytest).
"""

from __future__ import annotations

import pytest

from test_pg_closing_checklist import assert_safe_test_database


@pytest.mark.parametrize(
    "name",
    [
        "plugins_hub",      # banco compartilhado canônico
        "postgres",         # banco de manutenção
        "delpi_core",       # banco do Core
        "template0",
        "template1",
        "plugins_hub_prod", # compartilhado-like sem marcador de teste
        "plugins",          # ambíguo
        "",                 # vazio
        "prod",             # ambíguo
        "TEST DB",          # não é nome SQL seguro
        "test';DROP",       # tentativa de injeção
        "test db",          # espaço
    ],
)
def test_unsafe_targets_rejected(name):
    with pytest.raises(ValueError):
        assert_safe_test_database(name)


@pytest.mark.parametrize(
    "name",
    [
        "controllership_finance_test",
        "plugins_hub_test",
        "test_closing_checklist",
        "cf_test_20261024",
    ],
)
def test_dedicated_test_databases_accepted(name):
    assert_safe_test_database(name)  # não levanta
