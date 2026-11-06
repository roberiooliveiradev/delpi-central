"""SURI V3 — T1 OTD reject, T4 sample labels, T5 ranking, corpus v3."""
import json
import pytest
from unittest.mock import MagicMock, patch
from app.interfaces.mcp import tool_bridge


class _User:
    is_superadmin = True
    access_token = "tok"
    id = "a1"

    def has_permission(self, code):
        return True


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(tool_bridge, "_effective_user",
                        lambda: _User())


def _err(r):
    return getattr(r, "is_error", getattr(r, "isError", False))


def _data(r):
    d = json.loads(r.content[0].text)
    return d.get("data", d)


# ---- T1: otd aggregate must reject list branch with 422 (was 500) ----
def test_t1_aggregate_rejects_list_branch():
    r = tool_bridge.tool_otd_aggregate(
        {"branch": ["01", "02"],
         "start_date": "2026-08-03", "end_date": "2026-11-01"})
    assert _err(r) is True
    assert "series" in json.loads(r.content[0].text).get("message", "")


def test_t1_aggregate_accepts_str_branch():
    svc = MagicMock()
    svc.compose.return_value = {"ok": True}
    with patch.object(tool_bridge, "_OTD_AGG_SERVICE", svc):
        r = tool_bridge.tool_otd_aggregate({"branch": "01"})
    assert _err(r) is False
    assert svc.compose.call_args.kwargs["branch"] == "01"


def test_t1_series_still_accepts_list():
    svc = MagicMock()
    svc.compose.return_value = {"ok": True}
    with patch.object(tool_bridge, "_OTD_SERIES_SERVICE", svc):
        r = tool_bridge.tool_otd_series(
            {"branch": ["01", "02"], "granularity": "month"})
    assert _err(r) is False


# ---- T5: ranking relevance — page/journey/FAQ first on real questions --
QUESTIONS = {
    "Como abro uma SC e encontro o PC vinculado?": ["page.", "journey.", "faq."],
    "Qual a diferença entre OTD e Entregas?": ["explain.", "concept.", "page."],
    "Como comparo duas ordens de produção?": ["page.", "faq.", "explain."],
    "Como salvo uma visualização Comex?": ["page.", "faq."],
    "análise ABC": ["method."],
    "Matriz de Kraljic": ["method."],
}


def _top_ids(query):
    r = tool_bridge.tool_knowledge("search", query, limit=5)
    return [i["knowledge_id"] for i in _data(r)["items"]]


def test_t5_recall_at_5():
    hits = 0
    for q, prefixes in QUESTIONS.items():
        ids = _top_ids(q)
        if any(pid.startswith(p) for pid in ids for p in prefixes):
            hits += 1
    recall = hits / len(QUESTIONS)
    assert recall >= 0.8, f"Recall@5={recall:.2f} < 0.80"


# ---- T4: population-vs-sample labels exist ----
def test_t4_population_labels_in_corpus_and_code():
    src = open("app/interfaces/mcp/tool_bridge.py").read()
    assert "population_total_lines" in src
    assert "NOT population shares" in src


# ---- corpus v3 integrity ----
CORPUS = json.load(open("app/content/suri_knowledge.json",
                        encoding="utf-8"))


def test_v3_corpus_shape():
    assert CORPUS["corpus_version"] == 4
    kinds = {}
    for it in CORPUS["items"]:
        kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
    assert kinds["method"] == 65
    assert kinds["reference"] == 1
    assert kinds["explanation"] == 1
    assert kinds["report_template"] == 2


def test_v3_deep_method_fields():
    st01 = next(i for i in CORPUS["items"]
                if i.get("method_id") == "ST-01")
    for field in ("concept", "formula_or_method", "step_by_step",
                  "interpretation", "portal_application", "limitations"):
        assert st01.get(field), f"ST-01 missing {field}"
