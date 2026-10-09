"""PHASE 5 frozen corpus — deterministic design-methodology eval cases.

Frozen before implementation (STAGE 6). Each case is a pure-data fixture:
message intent + assembled materials (preview rows/columns, P4 grounding,
layout/native state, visual evidence). The same corpus is run against the
baseline (pre-methodology path) and the candidate evaluator so the delta is
honest — no invented quality scores, raw counts only.
"""

from __future__ import annotations


def _rows(names: list[str], n: int, fill=None) -> list[dict]:
    return [
        {name: (fill(name, i) if fill else f"{name}-{i}") for name in names}
        for i in range(n)
    ]


# -- visual-shape fixtures ----------------------------------------------------

TIME_SERIES = {
    "columns": ["date", "revenue"],
    "rows": _rows(["date", "revenue"], 12, lambda n, i: 100 + i if n == "revenue" else f"2026-{i + 1:02d}"),
}
SINGLE_METRIC = {
    "columns": ["revenue"],
    "rows": [{"revenue": 123456.78}],
}
FEW_CATEGORIES = {
    "columns": ["categoria", "amount"],
    "rows": _rows(["categoria", "amount"], 3, lambda n, i: 10 * i if n == "amount" else f"cat{i}"),
}
HIGH_CARDINALITY = {
    "columns": ["categoria", "amount"],
    "rows": _rows(["categoria", "amount"], 40, lambda n, i: i if n == "amount" else f"cat{i}"),
}
RANKING = {
    "columns": ["name", "value"],
    "rows": _rows(["name", "value"], 8, lambda n, i: 100 - i if n == "value" else f"item{i}"),
}
MANY_ROWS = {
    "columns": ["name", "detalhe", "value", "unit"],
    "rows": _rows(["name", "detalhe", "value", "unit"], 50, lambda n, i: i if n == "value" else f"{n}-{i}"),
}
TARGET_VS_ACTUAL = {
    "columns": ["meta", "revenue"],
    "rows": [{"meta": 1000, "revenue": 870}],
}
EMPTY_DATA = {"columns": ["date", "revenue"], "rows": []}
AMBIGUOUS_DATA = {
    "columns": ["c1", "c2"],
    "rows": [{"c1": "x", "c2": "y"}, {"c1": "a", "c2": "b"}],
}


# -- P4 grounding fixtures -----------------------------------------------------

SELECTED_CHART = {
    "selectionState": "ACTIVE",
    "selectedObjects": [{"id": "chart1", "type": "chart_view", "modelId": "mdl1", "dataSourceId": "ds1"}],
    "missingIds": [],
}
SELECTED_TEXT = {
    "selectionState": "ACTIVE",
    "selectedObjects": [{"id": "txt1", "type": "text"}],
    "missingIds": [],
}
NO_SELECTION = {"selectionState": "ABSENT", "selectedObjects": [], "missingIds": []}
AMBIGUOUS_SELECTION = {
    "selectionState": "AMBIGUOUS",
    "selectedObjects": [{"id": "a", "type": "kpi_view"}, {"id": "b", "type": "chart_view"}],
    "missingIds": [],
}
MISSING_TARGET = {
    "selectionState": "ABSENT",
    "selectedObjects": [],
    "missingIds": ["dead1"],
}

LAYOUT_ISSUES = {"issues": [{"id": "block_overlap:a~b"}], "signals": {"issueCount": 1}}
CLEAN_AUDIT = {"issues": [], "signals": {"issueCount": 0}}


# -- corpus --------------------------------------------------------------------

# Each case: id, user message, fixture materials, expected contract.
# expected keys are checked by the eval runner / pytest corpus tests.
CORPUS: list[dict] = [
    {
        "id": "kpi_single_metric",
        "message": "Como mostro a receita total?",
        "intent": "CHOOSE_VISUAL",
        "fixture": {"columns": SINGLE_METRIC["columns"], "rows": SINGLE_METRIC["rows"]},
        "expect": {
            "readiness": "READY",
            "family_in": {"kpi_view", "gauge"},
            "fabricated": False,
        },
    },
    {
        "id": "time_series_trend",
        "message": "Quero mostrar evolução mensal.",
        "intent": "CHOOSE_VISUAL",
        "fixture": {"columns": TIME_SERIES["columns"], "rows": TIME_SERIES["rows"]},
        "expect": {"readiness": "READY", "family_in": {"line", "area"}, "fabricated": False},
    },
    {
        "id": "few_categories",
        "message": "Compare as filiais.",
        "intent": "CHOOSE_VISUAL",
        "fixture": {"columns": FEW_CATEGORIES["columns"], "rows": FEW_CATEGORIES["rows"]},
        "expect": {
            "readiness": "READY",
            "family_in": {"bar", "horizontal_bar", "doughnut", "pie", "table_view"},
            "fabricated": False,
        },
    },
    {
        "id": "high_cardinality_rejects_pie",
        "message": "Compare as filiais.",
        "intent": "CHOOSE_VISUAL",
        "fixture": {"columns": HIGH_CARDINALITY["columns"], "rows": HIGH_CARDINALITY["rows"]},
        "expect": {
            "readiness": "READY",
            "family_not_in": {"pie", "doughnut"},
            "family_in": {"horizontal_bar", "bar", "table_view"},
            "fabricated": False,
        },
    },
    {
        "id": "ranking",
        "message": "Mostre o ranking dos produtos.",
        "intent": "CHOOSE_VISUAL",
        "fixture": {"columns": RANKING["columns"], "rows": RANKING["rows"]},
        "expect": {
            "readiness": "READY",
            "family_in": {"horizontal_bar", "table_view", "bar"},
            "fabricated": False,
        },
    },
    {
        "id": "many_rows_table",
        "message": "Mostre os 50 registros.",
        "intent": "CHOOSE_VISUAL",
        "fixture": {"columns": MANY_ROWS["columns"], "rows": MANY_ROWS["rows"]},
        "expect": {
            "readiness": "READY",
            "family_in": {"table_view", "horizontal_bar"},
            "fabricated": False,
        },
    },
    {
        "id": "target_vs_actual",
        "message": "Mostre a meta contra o realizado.",
        "intent": "CHOOSE_VISUAL",
        "fixture": {"columns": TARGET_VS_ACTUAL["columns"], "rows": TARGET_VS_ACTUAL["rows"]},
        "expect": {
            "readiness": "READY",
            "family_in": {"gauge", "kpi_view", "bar"},
            "fabricated": False,
        },
    },
    {
        "id": "empty_dataset_no_fabrication",
        "message": "Qual gráfico devo usar?",
        "intent": "CHOOSE_VISUAL",
        "fixture": {"columns": EMPTY_DATA["columns"], "rows": []},
        "expect": {
            "readiness_in": {"MISSING_INFORMATION", "BLOCKED", "PARTIAL"},
            "fabricated": False,
        },
    },
    {
        "id": "ambiguous_shape_no_fabrication",
        "message": "Qual gráfico devo usar?",
        "intent": "CHOOSE_VISUAL",
        "fixture": {"columns": AMBIGUOUS_DATA["columns"], "rows": AMBIGUOUS_DATA["rows"]},
        "expect": {
            "readiness_in": {"READY", "PARTIAL", "MISSING_INFORMATION"},
            "fabricated": False,
            "no_pie_without_evidence": True,
        },
    },
    {
        "id": "missing_shape_reads_before_ask",
        "message": "Qual gráfico devo usar?",
        "intent": "CHOOSE_VISUAL",
        "fixture": {"rows": None, "missing_readable": ["data_shape"], "has_data_source": True},
        "expect": {
            "readiness": "MISSING_INFORMATION",
            "next_action": "READ",
            "read_capability_in": {"preview_data_block", "inspect_data_model"},
            "fabricated": False,
        },
    },
    {
        "id": "user_only_fact_asks",
        "message": "Qual gráfico devo usar?",
        "intent": "CHOOSE_VISUAL",
        "fixture": {
            "columns": FEW_CATEGORIES["columns"],
            "rows": FEW_CATEGORIES["rows"],
            "missing_user": ["comparison_goal"],
        },
        "expect": {
            "readiness_in": {"READY", "PARTIAL", "MISSING_INFORMATION"},
            "next_question_only_for": "comparison_goal",
            "fabricated": False,
        },
    },
    {
        "id": "selected_chart_grounded_review",
        "message": "Melhore este gráfico.",
        "intent": "IMPROVE_EXISTING",
        "fixture": {"selection": SELECTED_CHART, "audit": CLEAN_AUDIT},
        "expect": {"readiness_in": {"READY", "PARTIAL"}, "target_id": "chart1", "fabricated": False},
    },
    {
        "id": "selected_text_review",
        "message": "Melhore esse texto.",
        "intent": "IMPROVE_EXISTING",
        "fixture": {"selection": SELECTED_TEXT, "audit": CLEAN_AUDIT},
        "expect": {"readiness_in": {"READY", "PARTIAL"}, "target_id": "txt1", "fabricated": False},
    },
    {
        "id": "no_selection_no_guessed_target",
        "message": "Melhore isso.",
        "intent": "IMPROVE_EXISTING",
        "fixture": {"selection": NO_SELECTION, "audit": CLEAN_AUDIT},
        "expect": {
            "readiness": "MISSING_INFORMATION",
            "missing_fact": "target_object",
            "fabricated": False,
            "no_target_guess": True,
        },
    },
    {
        "id": "ambiguous_selection_no_guess",
        "message": "Melhore isso.",
        "intent": "IMPROVE_EXISTING",
        "fixture": {"selection": AMBIGUOUS_SELECTION, "audit": CLEAN_AUDIT},
        "expect": {
            "readiness_in": {"MISSING_INFORMATION", "PARTIAL", "READY"},
            "no_target_guess": True,
            "fabricated": False,
        },
    },
    {
        "id": "missing_target_ids_surface",
        "message": "Melhore esse bloco.",
        "intent": "IMPROVE_EXISTING",
        "fixture": {"selection": MISSING_TARGET, "audit": CLEAN_AUDIT},
        "expect": {
            "readiness_in": {"MISSING_INFORMATION", "BLOCKED"},
            "missing_fact": "target_object",
            "fabricated": False,
            "no_target_guess": True,
        },
    },
    {
        "id": "structural_layout_claim",
        "message": "Organize melhor esse slide.",
        "intent": "FIX_LAYOUT",
        "fixture": {"audit": LAYOUT_ISSUES, "selection": NO_SELECTION},
        "expect": {
            "readiness_in": {"READY", "PARTIAL"},
            "evidence_level_in": {"STRUCTURAL", "DOMAIN_STATE"},
            "fabricated": False,
        },
    },
    {
        "id": "aesthetic_claim_requires_pixels",
        "message": "Esse slide está bom? Deixe mais bonito.",
        "intent": "REVIEW_SLIDE",
        "fixture": {"audit": CLEAN_AUDIT, "selection": NO_SELECTION, "pixels": None},
        "expect": {
            "aesthetic_claim_blocked_without_pixels": True,
            "fabricated": False,
        },
    },
    {
        "id": "aesthetic_claim_with_canonical_pixels",
        "message": "Esse slide está bom?",
        "intent": "REVIEW_SLIDE",
        "fixture": {"audit": CLEAN_AUDIT, "selection": NO_SELECTION, "pixels": "canonical_stage"},
        "expect": {
            "evidence_level_in": {"CANONICAL_PIXELS", "PIXELS_INSPECTED", "STRUCTURAL", "DOMAIN_STATE"},
            "fabricated": False,
        },
    },
    {
        "id": "explicit_user_choice_preserved",
        "message": "Use gráfico de barras.",
        "intent": "CHOOSE_VISUAL",
        "fixture": {
            "columns": TIME_SERIES["columns"],
            "rows": TIME_SERIES["rows"],
            "explicit_choice": "bar",
        },
        "expect": {
            "explicit_choice_preserved": True,
            "fabricated": False,
        },
    },
    {
        "id": "kpi_highlight_executive",
        "message": "Como posso destacar esse KPI?",
        "intent": "IMPROVE_EXISTING",
        "fixture": {
            "selection": {
                "selectionState": "ACTIVE",
                "selectedObjects": [{"id": "kpi1", "type": "kpi_view", "modelId": "m1"}],
                "missingIds": [],
            },
            "audit": CLEAN_AUDIT,
        },
        "expect": {"target_id": "kpi1", "readiness_in": {"READY", "PARTIAL"}, "fabricated": False},
    },
    {
        "id": "compose_executive_slide",
        "message": "Deixe isso mais executivo.",
        "intent": "COMPOSE_SLIDE",
        "fixture": {"audit": CLEAN_AUDIT, "selection": NO_SELECTION, "dominant_family": "kpi_view"},
        "expect": {"readiness_in": {"READY", "PARTIAL", "MISSING_INFORMATION"}, "fabricated": False},
    },
]


HUMAN_RUBRIC_CASES = ["aesthetic_claim_requires_pixels", "aesthetic_claim_with_canonical_pixels"]
