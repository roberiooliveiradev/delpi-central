from tv_app.application.services.data.tv_data_transform_formula_service import (
    can_edit_formula,
    parse_add_column_formula,
    parse_filter_formula,
    parse_formula_bar_text,
    parse_rename_formula,
    parse_replace_formula,
    parse_select_formula,
    parse_sort_formula,
)


def test_parse_add_column_and_rename():
    assert parse_add_column_formula("= AddColumn(Fonte, gap, meta - oee)") == {
        "ok": True,
        "step": {"op": "addColumn", "name": "gap", "expr": "meta - oee"},
    }
    assert parse_rename_formula("= RenameColumns(Fonte, oee → oee_pct)") == {
        "ok": True,
        "step": {"op": "rename", "from": "oee", "to": "oee_pct"},
    }


def test_parse_select_filter_sort_replace():
    assert parse_select_formula("= SelectColumns(Fonte, [a, b])")["step"]["columns"] == ["a", "b"]
    assert parse_filter_formula("= FilterRows(Fonte, branch is not null)")["step"]["cmp"] == "notNull"
    assert parse_filter_formula('= FilterRows(Fonte, [branch] eq "01")')["step"]["value"] == "01"
    assert parse_sort_formula("= Sort(Fonte, oee, desc)")["step"]["direction"] == "desc"
    assert parse_replace_formula('= ReplaceValue(Fonte, branch, "0" → "F")')["step"]["find"] == "0"


def test_parse_formula_bar_context():
    assert can_edit_formula({"op": "filter", "column": "a", "cmp": "eq"}) is True
    assert can_edit_formula({"op": "merge", "sourceId": "x", "leftKey": "a", "rightKey": "b"}) is False
    result = parse_formula_bar_text(
        "= AddColumn(Fonte, x, 1 + 2)",
        step=None,
        new_column_draft=True,
    )
    assert result["ok"] is True
    assert result["step"]["name"] == "x"
