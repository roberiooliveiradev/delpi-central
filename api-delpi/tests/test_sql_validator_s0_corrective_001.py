# tests/test_sql_validator_s0_corrective_001.py
"""S0 Corrective 001 — fail-closed completion of the read-only SQL validator.

Defect A: fake CTE names minted from string literals must never authorize a
physical source. CTE names may only originate from real WITH ... AS ( syntax.

Defect B: an allowlisted first token must not mask unsupported qualified /
trailing object syntax (SB1010.<x>, SB1010..<x>, SB1010.[x], SB1010."x").
"""

import pytest

from app.application.services.sql_validator import SqlValidator


@pytest.fixture
def validator():
    return SqlValidator()


def _allowed(v, sql):
    try:
        v.validate(sql)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------
# Defect A — fake CTE from string literal
# ---------------------------------------------------------------------

def test_cte_fake_001_string_literal_does_not_mint_cte(validator):
    assert not _allowed(
        validator,
        "SELECT 'WITH ZZ9999 AS (' AS note FROM ZZ9999",
    )


def test_cte_fake_002_cte_like_text_in_string_is_data(validator):
    assert _allowed(
        validator,
        "SELECT 'WITH ZZ9999 AS (' AS note FROM SB1010",
    )


def test_cte_fake_mixed_case_string_does_not_mint_cte(validator):
    assert not _allowed(
        validator,
        "SELECT 'with zz9999 as (' AS note FROM ZZ9999",
    )


def test_cte_fake_multiline_string_does_not_mint_cte(validator):
    assert not _allowed(
        validator,
        "SELECT 'WITH\nZZ9999\nAS\n(' AS note FROM ZZ9999",
    )


def test_cte_fake_escaped_quote_string_does_not_mint_cte(validator):
    # 'it''s ...' — escaped quote keeps WITH inside the literal
    assert not _allowed(
        validator,
        "SELECT 'it''s WITH ZZ9999 AS (' AS note FROM ZZ9999",
    )


def test_cte_fake_second_string_does_not_mint_cte(validator):
    assert not _allowed(
        validator,
        "SELECT B1_COD, 'WITH ZZ9999 AS (' FROM SB1010 "
        "UNION ALL SELECT B1_COD, 'x' FROM ZZ9999",
    )


def test_string_with_with_from_join_as_words_allowed(validator):
    # keywords inside literals são dados, não gramática
    assert _allowed(
        validator,
        "SELECT 'WITH t AS (SELECT x FROM y) JOIN w AS z' AS note "
        "FROM SB1010",
    )


def test_string_containing_into_still_denied(validator):
    # pre-existing conservative behavior: banned keywords also fire inside
    # literals — over-block direction, kept intentionally in S0
    assert not _allowed(
        validator,
        "SELECT 'x INTO y' AS note FROM SB1010",
    )


# ---------------------------------------------------------------------
# Defect A — real CTE behavior preserved
# ---------------------------------------------------------------------

def test_real_cte_allowed_table_passes(validator):
    assert _allowed(
        validator,
        "WITH cte AS (SELECT B1_COD FROM SB1010) SELECT * FROM cte",
    )


def test_real_multiple_ctes_pass(validator):
    assert _allowed(
        validator,
        "WITH a AS (SELECT B1_COD FROM SB1010), "
        "b AS (SELECT B2_PROD FROM SB2010) "
        "SELECT * FROM a JOIN b ON a.B1_COD = b.B2_PROD",
    )


def test_real_cte_unauthorized_inner_source_denied(validator):
    assert not _allowed(
        validator,
        "WITH cte AS (SELECT * FROM ZZ9999) SELECT * FROM cte",
    )


def test_real_cte_shadowing_does_not_hide_unauthorized(validator):
    # fake-CTE-in-string reuses a real CTE name — physical source still denied
    assert not _allowed(
        validator,
        "WITH cte AS (SELECT B1_COD FROM SB1010) "
        "SELECT 'WITH cte AS (' AS note FROM cte UNION ALL "
        "SELECT * FROM ZZ9999",
    )


def test_real_cte_with_comments_passes(validator):
    assert _allowed(
        validator,
        "WITH cte AS ( /* comentário */ SELECT B1_COD FROM SB1010 -- fim\n"
        ") SELECT * FROM cte",
    )


def test_cte_body_string_containing_cte_text_passes(validator):
    assert _allowed(
        validator,
        "WITH cte AS (SELECT 'WITH x AS (' AS note, B1_COD FROM SB1010) "
        "SELECT * FROM cte",
    )


# ---------------------------------------------------------------------
# Defect B — qualified / trailing source syntax
# ---------------------------------------------------------------------

def test_qual_001_allowed_prefix_dot_suffix_denied(validator):
    assert not _allowed(validator, "SELECT * FROM SB1010.ZZ9999")


def test_qual_002_allowed_prefix_double_dot_denied(validator):
    assert not _allowed(validator, "SELECT * FROM SB1010..ZZ9999")


def test_qual_003_allowed_prefix_bracket_suffix_denied(validator):
    assert not _allowed(validator, "SELECT * FROM SB1010.[ZZ9999]")


def test_qual_004_allowed_prefix_quoted_suffix_denied(validator):
    assert not _allowed(validator, 'SELECT * FROM SB1010."ZZ9999"')


def test_qual_mixed_case_dot_denied(validator):
    assert not _allowed(validator, "SELECT * FROM sb1010.zz9999")


def test_qual_spaced_dot_denied(validator):
    # T-SQL permite whitespace em nomes multipartes
    assert not _allowed(validator, "SELECT * FROM SB1010 . ZZ9999")


def test_qual_four_part_denied(validator):
    assert not _allowed(validator, "SELECT * FROM SB1010.DBO.ZZ9999.X1")


def test_qual_in_join_denied(validator):
    assert not _allowed(
        validator,
        "SELECT * FROM SB1010 a JOIN SB2010.B2 ON 1=1",
    )


def test_qual_in_subquery_denied(validator):
    assert not _allowed(
        validator,
        "SELECT * FROM (SELECT * FROM SB1010.X) t",
    )


def test_qual_trailing_dot_denied(validator):
    assert not _allowed(validator, "SELECT * FROM SB1010.")


def test_qual_cte_name_dot_denied(validator):
    assert not _allowed(
        validator,
        "WITH cte AS (SELECT B1_COD FROM SB1010) SELECT * FROM cte.x",
    )


# ---------------------------------------------------------------------
# Defect B — valid continuations preserved
# ---------------------------------------------------------------------

def test_normal_alias_after_table_passes(validator):
    assert _allowed(validator, "SELECT * FROM SB1010 a")


def test_as_alias_after_table_passes(validator):
    assert _allowed(validator, "SELECT * FROM SB1010 AS a")


def test_where_after_table_passes(validator):
    assert _allowed(validator, "SELECT * FROM SB1010 WHERE B1_COD = '1'")


def test_join_after_table_passes(validator):
    assert _allowed(
        validator,
        "SELECT * FROM SB1010 a JOIN SB2010 b ON a.B1_COD = b.B2_PROD",
    )


def test_nolock_hint_after_table_passes(validator):
    assert _allowed(validator, "SELECT * FROM SB1010 WITH (NOLOCK)")


def test_column_dot_in_select_list_passes(validator):
    assert _allowed(
        validator,
        "SELECT a.B1_COD, b.B2_PROD FROM SB1010 a "
        "JOIN SB2010 b ON a.B1_COD = b.B2_PROD",
    )


def test_dot_decimal_in_where_passes(validator):
    assert _allowed(
        validator,
        "SELECT * FROM SB1010 WHERE B1_GRUPO = '01.02'",
    )


# ---------------------------------------------------------------------
# S0 gates unchanged
# ---------------------------------------------------------------------

def test_select_into_still_denied(validator):
    assert not _allowed(
        validator,
        "SELECT * INTO ZZ9999 FROM SB1010",
    )


def test_comma_join_still_denied(validator):
    assert not _allowed(validator, "SELECT * FROM SB1010, SB2010")


def test_bracketed_source_still_denied(validator):
    assert not _allowed(validator, "SELECT * FROM [SB1010]")


def test_quoted_source_still_denied(validator):
    assert not _allowed(validator, 'SELECT * FROM "SB1010"')


def test_apply_still_denied(validator):
    assert not _allowed(
        validator,
        "SELECT * FROM SB1010 CROSS APPLY (SELECT 1) x",
    )


def test_dml_still_denied(validator):
    assert not _allowed(validator, "INSERT INTO SB1010 SELECT * FROM SB2010")


def test_ddl_still_denied(validator):
    assert not _allowed(validator, "CREATE TABLE ZZ9999 (c int)")


def test_exec_still_denied(validator):
    assert not _allowed(validator, "EXEC sp_executesql N'SELECT 1'")
