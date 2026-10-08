"""S0 security-hardening matrix for SqlValidator (read-only SQL route).

Assert semantic outcomes: validation PASS or PermissionError rejection.
Validator-level only — nenhum statement é executado em banco.
"""

import pytest

from app.application.services.sql_validator import SqlValidator


@pytest.fixture(autouse=True)
def _whitelist_on(monkeypatch):
    monkeypatch.delenv("DATA_SQL_SKIP_TABLE_WHITELIST", raising=False)


@pytest.fixture()
def validator():
    return SqlValidator()


def assert_denied(validator, sql):
    with pytest.raises(PermissionError):
        validator.validate(sql)


# ---------------------------------------------------------------------------
# WRITE / SIDE-EFFECT — reject
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * INTO NEW_TABLE FROM SB1010",
        "SELECT * INTO #TMP FROM SB1010",
        "WITH cte AS (SELECT B1_COD FROM SB1010) SELECT * INTO T2 FROM cte",
        "INSERT INTO SB1010 (B1_COD) VALUES ('X')",
        "UPDATE SB1010 SET B1_DESC = 'x'",
        "DELETE FROM SB1010",
        "MERGE SB1010 AS t USING SB2010 s ON t.B1_COD = s.B2_PROD WHEN MATCHED THEN DELETE",
        "CREATE TABLE T (c INT)",
        "ALTER TABLE SB1010 ADD c INT",
        "DROP TABLE SB1010",
        "TRUNCATE TABLE SB1010",
        "EXEC sp_help",
        "EXECUTE sp_executesql N'SELECT 1'",
        "GRANT SELECT ON SB1010 TO x",
        "REVOKE SELECT ON SB1010 TO x",
        "BEGIN TRANSACTION; SELECT 1",
        "SELECT 1; COMMIT",
        "SELECT 1; ROLLBACK",
    ],
)
def test_rejects_write_and_side_effect_statements(validator, sql):
    assert_denied(validator, sql)


def test_rejects_select_into_case_variants(validator):
    assert_denied(validator, "select * into T2 from SB1010")
    assert_denied(validator, "SELECT *\nINTO\nT2\nFROM SB1010")


# ---------------------------------------------------------------------------
# TABLE POLICY — reject every ungoverned physical source
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM ZZ9999",
        "SELECT * FROM SB1010 JOIN ZZ9999 ON 1=1",
        # comma-separated second source
        "SELECT * FROM SB1010, ZZ9999",
        "SELECT * FROM SB1010, SB2010",
        "SELECT * FROM SB1010 a, ZZ9999 b",
        "SELECT * FROM SB1010 JOIN SB2010 s ON 1=1, ZZ9999",
        # bracketed identifier — not supported in S0
        "SELECT * FROM [ZZ9999]",
        "SELECT * FROM [SB1010]",
        "SELECT * FROM [dbo].[SB1010]",
        # double-quoted identifier — not supported in S0
        'SELECT * FROM "ZZ9999"',
        'SELECT * FROM "SB1010"',
        # APPLY — operand not governable without structural parsing
        "SELECT * FROM SB1010 CROSS APPLY ZZ9999",
        "SELECT * FROM SB1010 OUTER APPLY ZZ9999",
        "SELECT * FROM SB1010 CROSS APPLY (SELECT 1 c) x",
        "SELECT * FROM SB1010 OUTER APPLY fn_helpcollations()",
        # qualified objects remain rejected
        "SELECT * FROM dbo.SB1010",
        "SELECT * FROM PROTHEUS.dbo.SB1010",
        "SELECT * FROM SRV.PROTHEUS.dbo.SB1010",
        # system objects remain rejected
        "SELECT * FROM sys.tables",
        "SELECT * FROM INFORMATION_SCHEMA.TABLES",
        "SELECT * FROM OPENROWSET('SQLNCLI','S','SELECT 1')",
        "SELECT * FROM OPENQUERY([S],'SELECT 1')",
        # hidden physical source in subquery / union
        "SELECT * FROM (SELECT * FROM ZZ9999) x",
        "SELECT * FROM SB1010 WHERE B1_COD IN (SELECT Z_COD FROM ZZ9999)",
        "SELECT B1_COD FROM SB1010 UNION ALL SELECT Z_COD FROM ZZ9999",
        "WITH cte AS (SELECT * FROM ZZ9999) SELECT * FROM cte",
        "SELECT * FROM #TEMP",
        # semicolon inside string literal — split conservador existente (fail-safe)
        "SELECT 'a;b' FROM SB1010 WHERE 1 = 0",
    ],
)
def test_rejects_ungoverned_table_sources(validator, sql):
    assert_denied(validator, sql)


# ---------------------------------------------------------------------------
# POSITIVE — legacy supported READ grammar preserved
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "sql",
    [
        "SELECT TOP 1 B1_COD FROM SB1010 WHERE D_E_L_E_T_ = ''",
        "SELECT a.B1_COD FROM SB1010 a JOIN SB2010 b ON a.B1_COD = b.B2_PROD",
        "SELECT a.B1_COD, b.B2_QATU FROM SB1010 a LEFT JOIN SB2010 b ON a.B1_COD = b.B2_PROD WHERE a.B1_COD = '1'",
        "WITH cte AS (SELECT B1_COD FROM SB1010) SELECT * FROM cte",
        "WITH a AS (SELECT B1_COD FROM SB1010), b AS (SELECT B2_PROD FROM SB2010) SELECT * FROM a JOIN b ON a.B1_COD = b.B2_PROD",
        "WITH x AS (SELECT 1 n UNION ALL SELECT n + 1 FROM x WHERE n < 10) SELECT * FROM x",
        "SELECT B1_COD FROM SB1010 UNION ALL SELECT A1_COD FROM SA1010",
        "SELECT * FROM (SELECT B1_COD FROM SB1010) x",
        "SELECT * FROM SB1010 WHERE B1_COD IN (SELECT A1_COD FROM SA1010)",
        "SELECT COUNT(*) FROM SB1010 GROUP BY B1_TIPO HAVING COUNT(*) > 1",
        "SELECT ROW_NUMBER() OVER (ORDER BY B1_COD) rn, B1_COD FROM SB1010",
        "SELECT * FROM (SELECT B1_COD, B1_TIPO FROM SB1010) s PIVOT (COUNT(B1_COD) FOR B1_TIPO IN ([PA])) p",
        "SELECT B1_COD FROM SB1010 FOR XML PATH",
        "SELECT * FROM SB1010 WITH (NOLOCK)",
        "DECLARE @x INT; SET @x = 1; SELECT @x",
        "DECLARE @t TABLE (c INT); SELECT * FROM @t",
        "DECLARE @x INT; SET @x = 'a'; SELECT TOP 1 B1_COD FROM SB1010",
        "SELECT 1; SELECT 2",
        "SELECT B1_DESC AS d FROM SB1010 -- comentário\nWHERE 1 = 0",
        "SEL/**/ECT B1_COD FROM SB1010",
        "SELECT TOP 3 B1_COD FROM SB1010 OPTION (MAXRECURSION 0)",
    ],
)
def test_accepts_supported_read_grammar(validator, sql):
    assert validator.validate(sql) is True


def test_max_selects_still_enforced(validator):
    assert_denied(
        validator,
        "; ".join(f"SELECT {i}" for i in range(11)),
    )


def test_empty_and_invalid_rejected(validator):
    with pytest.raises((PermissionError, ValueError)):
        validator.validate("")
    with pytest.raises((PermissionError, ValueError)):
        validator.validate("FOO BAR")


def test_cte_name_shadowing_still_validates_inner_sources(validator):
    # CTE nomeada com nome de tabela da allowlist não pode ocultar fonte física.
    assert_denied(
        validator,
        "WITH SB1010 AS (SELECT * FROM ZZ9999) SELECT * FROM SB1010",
    )


def test_skip_flag_still_bypasses_allowlist(validator, monkeypatch):
    monkeypatch.setenv("DATA_SQL_SKIP_TABLE_WHITELIST", "true")
    assert (
        validator.validate("SELECT TOP 1 1 FROM ZZ9999 WHERE D_E_L_E_T_ = ''")
        is True
    )


def test_skip_flag_does_not_allow_apply_or_write(validator, monkeypatch):
    monkeypatch.setenv("DATA_SQL_SKIP_TABLE_WHITELIST", "true")
    assert_denied(validator, "SELECT * FROM ZZ9999 CROSS APPLY fn_x()")
    assert_denied(validator, "SELECT * INTO T2 FROM ZZ9999")
    assert_denied(validator, "DELETE FROM ZZ9999")
