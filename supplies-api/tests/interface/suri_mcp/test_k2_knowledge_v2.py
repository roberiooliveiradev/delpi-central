"""SURI Knowledge V2 — corpus integrity + retrieval contract."""
import json
import pytest
from app.interfaces.mcp import tool_bridge, knowledge


class _User:
    is_superadmin = True
    access_token = "tok"
    id = "actor-1"

    def has_permission(self, code):
        return True


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(tool_bridge, "_effective_user",
                        lambda: _User())


def _payload(r):
    import json as _j
    c = getattr(r, "content", None)
    if c and hasattr(c[0], "text"):
        d = _j.loads(c[0].text)
        return d.get("data", d)
    return r


CORPUS = json.load(
    open("app/content/suri_knowledge.json", encoding="utf-8"))
ITEMS = CORPUS["items"]


def test_corpus_version_and_counts():
    assert CORPUS["corpus_version"] == 4
    kinds = {}
    for it in ITEMS:
        kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
    assert kinds["page"] == 23
    assert kinds["method"] == 65
    assert kinds["concept"] == 21
    assert kinds["faq"] == 42
    assert kinds["journey"] == 5
    assert kinds["guidance"] == 5


def test_corpus_no_duplicate_ids():
    ids = [it["knowledge_id"] for it in ITEMS]
    assert len(ids) == len(set(ids)), "duplicate knowledge_id"


def test_corpus_required_fields():
    for it in ITEMS:
        assert it["knowledge_id"]
        assert it.get("title")
        assert it.get("source", {}).get("file")
        assert it.get("kind") in {
            "page", "concept", "method", "faq",
            "journey", "guidance", "topic",
            "reference", "explanation", "report_template"}


def test_methods_have_status():
    statuses = set()
    for it in ITEMS:
        if it["kind"] == "method":
            statuses.add(it.get("knowledge_status"))
    assert statuses == {"ANALYSIS_ENABLED", "KNOWLEDGE_ONLY"}


def test_placeholders_marked():
    ph = [it for it in ITEMS
          if it.get("implementation_status") == "PLACEHOLDER"]
    assert len(ph) == 5


def test_search_by_question():
    r = tool_bridge.tool_knowledge(
        "search", "como filtro solicitações por filial")
    data = _payload(r)
    assert data["total_matches"] > 0
    assert data["corpus_version"] == 4


def test_search_kind_filter_method():
    r = tool_bridge.tool_knowledge(
        "search", "ABC", kind="method")
    data = _payload(r)
    for it in data["items"]:
        assert it["kind"] == "method"


def test_search_kind_filter_page():
    r = tool_bridge.tool_knowledge(
        "search", "pedidos de compra", kind="page")
    data = _payload(r)
    for it in data["items"]:
        assert it["kind"] == "page"


def test_search_method_selection():
    r = tool_bridge.tool_knowledge(
        "search", "atrasos fornecedor", kind="guidance")
    data = _payload(r)
    assert data["items"]
    methods = data["items"][0].get("methods") or []
    assert methods


def test_get_by_id():
    r = tool_bridge.tool_knowledge("get",
                                   knowledge_id="method.st-02")
    data = _payload(r)
    assert data["knowledge_id"] == "method.st-02"
    assert data["kind"] == "method"


def test_get_unknown_id():
    r = tool_bridge.tool_knowledge("get",
                                   knowledge_id="nonexistent")
    assert getattr(r, "is_error",
                   getattr(r, "isError", False)) is True


def test_kind_rejected_on_get():
    r = tool_bridge.tool_knowledge("get", kind="method",
                                   knowledge_id="method.st-02")
    assert getattr(r, "is_error",
                   getattr(r, "isError", False)) is True


def test_sources_version():
    r = tool_bridge.tool_knowledge("sources")
    data = _payload(r)
    assert data["corpus_version"] == 4
    assert data["item_count"] == len(ITEMS)
