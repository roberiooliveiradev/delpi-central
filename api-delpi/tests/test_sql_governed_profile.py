# tests/test_sql_governed_profile.py
"""S1 — DAVI_GOVERNED structural policy profile tests.

O perfil governed é um subconjunto estrito: um único statement analítico
SELECT/WITH, sem DECLARE/SET/table vars/multi-statement/hints/PIVOT/FOR/EXEC,
com fontes físicas fail-closed na allowlist — e indisponível quando
DATA_SQL_SKIP_TABLE_WHITELIST estiver ativa.
"""

import pytest

from app.application.services.sql_validator import (
    PROFILE_DAVI_GOVERNED,
    SqlValidator,
)


@pytest.fixture
def validator():
    return SqlValidator()


def _ok(v, sql):
    try:
        v.validate(sql, profile=PROFILE_DAVI_GOVERNED)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------
# Gramática positiva
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "sql",
    [
        "SELECT B1_COD, B1_DESC FROM SB1010 WHERE B1_TIPO = ?",
        "SELECT TOP 10 B1_COD FROM SB1010 ORDER BY B1_COD",
        "SELECT a.B1_COD FROM SB1010 a JOIN SB2010 b ON a.B1_COD = b.B2_PROD",
        "SELECT a.B1_COD FROM SB1010 a LEFT JOIN SB2010 b ON a.B1_COD = b.B2_PROD",
        "WITH cte AS (SELECT B1_COD FROM SB1010) SELECT * FROM cte",
        "WITH r AS (SELECT 1 n UNION ALL SELECT n+1 FROM r WHERE n < 5) SELECT * FROM r",
        "SELECT B1_TIPO, COUNT(*) c FROM SB1010 GROUP BY B1_TIPO HAVING COUNT(*) > ?",
        "SELECT ROW_NUMBER() OVER (PARTITION BY B1_TIPO ORDER BY B1_COD) rn FROM SB1010",
        "SELECT * FROM (SELECT B1_COD FROM SB1010) x",
        "SELECT * FROM SB1010 UNION ALL SELECT * FROM SA1010",
        "SELECT DISTINCT B1_TIPO FROM SB1010",
        "SELECT * FROM SB1010 WHERE B1_COD = ? AND B1_TIPO = ?",
    ],
)
def test_governed_positive_grammar(validator, sql):
    assert _ok(validator, sql)


# ---------------------------------------------------------------------
# Statement-type gate
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM SB1010; SELECT * FROM SB2010",
        "DECLARE @x INT; SELECT @x",
        "DECLARE @T TABLE (c INT); SELECT * FROM @T",
        "DECLARE @v VARCHAR(10); SET @v = 'x'; SELECT @v",
        "SET NOCOUNT ON; SELECT * FROM SB1010",
        "SELECT * INTO ZZ9999 FROM SB1010",
        "SELECT * INTO #t FROM SB1010",
        "INSERT INTO SB1010 SELECT * FROM SB2010",
        "UPDATE SB1010 SET B1_COD='x'",
        "DELETE FROM SB1010",
        "MERGE SB1010 t USING SB2010 s ON 1=1 WHEN MATCHED THEN DELETE",
        "CREATE TABLE ZZ (c int)",
        "EXEC sp_executesql N'SELECT 1'",
        "GRANT SELECT ON SB1010 TO u",
        "BEGIN TRANSACTION",
    ],
)
def test_governed_statement_type_gate(validator, sql):
    assert not _ok(validator, sql)


# ---------------------------------------------------------------------
# Fontes físicas — fail closed
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM ZZ9999",
        "SELECT * FROM SB1010, SB2010",
        "SELECT * FROM [SB1010]",
        'SELECT * FROM "SB1010"',
        "SELECT * FROM SB1010 CROSS APPLY (SELECT 1) x",
        "SELECT * FROM SB1010 OUTER APPLY (SELECT 1) x",
        "SELECT * FROM dbo.SB1010",
        "SELECT * FROM db.dbo.SB1010",
        "SELECT * FROM srv.db.dbo.SB1010",
        "SELECT * FROM SB1010.ZZ9999",
        "SELECT * FROM OPENROWSET('x','y','z') t",
        "SELECT * FROM OPENQUERY(S, 'SELECT 1')",
        "SELECT 'WITH ZZ9999 AS (' AS note FROM ZZ9999",
        "SELECT * FROM SB1010 WHERE x IN (SELECT y FROM ZZ9999)",
        "WITH cte AS (SELECT * FROM ZZ9999) SELECT * FROM cte",
        "SELECT * FROM SB1010 WITH (NOLOCK)",
        "SELECT * FROM SB1010 FOR XML PATH('x')",
        "SELECT * FROM SB1010 PIVOT (MAX(B1_COD) FOR B1_TIPO IN ([A])) p",
        "SELECT * FROM @T",
    ],
)
def test_governed_source_fail_closed(validator, sql):
    assert not _ok(validator, sql)


def test_governed_fake_cte_cannot_mint_table(validator):
    assert not _ok(
        validator,
        "SELECT 'WITH ZZ9999 AS (' AS note FROM ZZ9999",
    )


def test_governed_max_tables(validator):
    nine = " UNION ALL ".join(
        f"SELECT '{i}' FROM SB1010" for i in range(9)
    )
    # UNION branches reuse SB1010 — only 1 physical table → PASS
    assert _ok(validator, nine)


def test_governed_max_tables_exceeded(validator):
    allowed = sorted(SqlValidator().allowed_tables)[:9]
    q = " UNION ALL ".join(f"SELECT 'x' FROM {t}" for t in allowed)
    assert not _ok(validator, q)


def test_governed_statement_too_long(validator):
    long_comment = "SELECT " + ", ".join(f"B1_COD AS c{i}" for i in range(2000)) + " FROM SB1010"
    assert not _ok(validator, long_comment)


# ---------------------------------------------------------------------
# Whitelist bypass → governed fail closed
# ---------------------------------------------------------------------

def test_governed_fails_closed_when_whitelist_bypassed(validator, monkeypatch):
    monkeypatch.setenv("DATA_SQL_SKIP_TABLE_WHITELIST", "true")
    assert not _ok(validator, "SELECT * FROM SB1010")


def test_legacy_still_bypasses_when_flag_on(validator, monkeypatch):
    monkeypatch.setenv("DATA_SQL_SKIP_TABLE_WHITELIST", "true")
    assert _ok_legacy(validator, "SELECT * FROM SB1010")


def _ok_legacy(v, sql):
    try:
        v.validate(sql)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------
# Parse robustness
# ---------------------------------------------------------------------

def test_governed_parse_failure_denied(validator):
    assert not _ok(validator, "SELECT WHERE FROM )(((")


def test_governed_empty_denied(validator):
    assert not _ok(validator, "")


def test_governed_comments_stripped(validator):
    assert _ok(
        validator,
        "SELECT /* comentário */ B1_COD FROM SB1010 -- fim\nWHERE B1_TIPO='PA'",
    )
