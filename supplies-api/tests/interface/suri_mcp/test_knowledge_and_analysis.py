"""SURI knowledge + deterministic analysis through the semantic surface.

Parity with the legacy knowledge/analysis capabilities plus semantic
validation negatives and the compound read→analyze→knowledge flow.
"""

from __future__ import annotations

import json

from suri_mcp.suri_fixtures import PO_PAYLOAD

from app.interfaces.mcp import knowledge, tool_bridge


def _payload(result) -> dict:
    return json.loads(result.content[0].text)


class TestKnowledge:
    def test_sources_inventory_has_corpus_meta(self):
        data = knowledge.list_knowledge_sources()
        assert data["corpus_version"] == 1
        assert len(data["corpus_sha256"]) == 64
        assert {s["source_id"] for s in data["sources"]} >= {
            "portal-user-manual",
            "supplies-bff-contract",
        }
        assert data["item_count"] >= 10

    def test_search_deterministic_and_cited(self):
        first = knowledge.search_knowledge(query="pedidos de compra")
        second = knowledge.search_knowledge(query="pedidos de compra")
        assert first == second
        assert first["items"], "expected hits"
        for item in first["items"]:
            assert item["source"]["file"]
            assert item["evidence_class"] in {
                "PROVEN",
                "OWNER_REPORTED",
                "TO_INVENTORY",
            }

    def test_search_topic_filter(self):
        data = knowledge.search_knowledge(topic="suri")
        ids = {i["knowledge_id"] for i in data["items"]}
        assert ids == {"suri.boundaries"}

    def test_get_item_and_404(self):
        item = knowledge.get_knowledge_item("po.contract")
        assert item is not None
        assert item["title"]
        assert knowledge.get_knowledge_item("nope") is None


class TestKnowledgeTool:
    """Parity with legacy knowledge tools through ``knowledge``."""

    def test_gate_on_access(self, no_access_context):
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_knowledge, "search", query="x")
        )
        assert _payload(result)["status_code"] == 403

    def test_search_positive_cited(self, access_context):
        access_context()
        result = tool_bridge.tool_knowledge(
            "search", query="pedidos de compra"
        )
        body = _payload(result)
        assert body["success"] is True
        assert body["data"]["items"]

    def test_get_positive_and_404(self, access_context):
        access_context()
        result = tool_bridge.tool_knowledge("get", knowledge_id="po.contract")
        body = _payload(result)
        assert body["success"] is True
        assert body["data"]["knowledge_id"] == "po.contract"

        result = tool_bridge.tool_knowledge("get", knowledge_id="nope")
        assert _payload(result)["status_code"] == 404

    def test_sources_positive(self, access_context):
        access_context()
        result = tool_bridge.tool_knowledge("sources")
        assert _payload(result)["data"]["corpus_version"] == 1

    def test_negative_knowledge_id_on_search(self, access_context):
        access_context()
        result = tool_bridge.tool_knowledge(
            "search", query="x", knowledge_id="po.contract"
        )
        assert _payload(result)["status_code"] == 422

    def test_negative_missing_knowledge_id_on_get(self, access_context):
        access_context()
        result = tool_bridge.tool_knowledge("get")
        assert _payload(result)["status_code"] == 422

    def test_negative_query_on_get(self, access_context):
        access_context()
        result = tool_bridge.tool_knowledge(
            "get", query="x", knowledge_id="po.contract"
        )
        assert _payload(result)["status_code"] == 422

    def test_negative_params_on_sources(self, access_context):
        access_context()
        result = tool_bridge.tool_knowledge("sources", topic="suri")
        assert _payload(result)["status_code"] == 422

    def test_negative_unknown_action(self, access_context):
        access_context()
        result = tool_bridge.tool_knowledge("purge")
        assert _payload(result)["status_code"] == 422


class TestAnalyzeParity:
    """Parity with legacy analyze_purchase_orders."""

    def test_positive_labels_and_reproducibility(
        self, access_context, fake_gateway
    ):
        access_context()
        fake_gateway(payload=PO_PAYLOAD)
        result = tool_bridge.tool_analyze(
            "purchase_orders_summary", filters={"branch": ["01"]}
        )
        data = _payload(result)["data"]

        facts = {f["label"]: f["value"] for f in data["facts"]}
        assert facts["total_lines"] == 2
        assert facts["late_lines"] == 1
        assert facts["total_open_value"] == 850.0

        calcs = {c["label"]: c["value"] for c in data["calculations"]}
        assert calcs["sample_size"] == 2
        assert calcs["sample_late_share_pct"] == 50.0
        assert calcs["sample_open_value"] == 850.0
        assert calcs["sample_lines_by_branch"] == {"01": 2}
        assert calcs["sample_truncated"] is False

        rec_labels = {r["label"] for r in data["recommendations"]}
        assert "prioritize_late_lines" in rec_labels
        assert len(data["input_hash"]) == 64

    def test_same_input_same_hash(self, access_context, fake_gateway):
        access_context()
        fake_gateway(payload=PO_PAYLOAD)
        first = _payload(
            tool_bridge.tool_analyze(
                "purchase_orders_summary", filters={"branch": ["01"]}
            )
        )["data"]["input_hash"]
        fake_gateway(payload=PO_PAYLOAD)
        second = _payload(
            tool_bridge.tool_analyze(
                "purchase_orders_summary", filters={"branch": ["01"]}
            )
        )["data"]["input_hash"]
        assert first == second

    def test_empty_result_recommends_scope_check(
        self, access_context, fake_gateway
    ):
        access_context()
        fake_gateway(
            payload={
                "data": {
                    "items": [],
                    "total": 0,
                    "summary": {
                        "total_lines": 0,
                        "total_open_value": 0.0,
                        "late_lines": 0,
                        "on_time_lines": 0,
                        "no_date_lines": 0,
                    },
                }
            }
        )
        data = _payload(
            tool_bridge.tool_analyze(
                "purchase_orders_summary", filters={"branch": ["01"]}
            )
        )["data"]
        rec_labels = {r["label"] for r in data["recommendations"]}
        assert "no_open_lines" in rec_labels
        calcs = {c["label"]: c["value"] for c in data["calculations"]}
        assert calcs["sample_late_share_pct"] == 0.0

    def test_negative_forbidden_branch(
        self, access_context, fake_gateway
    ):
        access_context()
        gw = fake_gateway(payload=PO_PAYLOAD)
        result = tool_bridge.handle_tool_error(
            _call(
                tool_bridge.tool_analyze,
                "purchase_orders_summary",
                {"branch": ["03"]},
            )
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []

    def test_negative_unknown_analysis(self, access_context):
        access_context()
        result = tool_bridge.tool_analyze("suppliers_risk")
        assert _payload(result)["status_code"] == 422

    def test_negative_unknown_filter_key(
        self, access_context, fake_gateway
    ):
        access_context()
        gw = fake_gateway(payload=PO_PAYLOAD)
        result = tool_bridge.tool_analyze(
            "purchase_orders_summary",
            filters={"branch": ["01"], "force_all_units": True},
        )
        assert _payload(result)["status_code"] == 422
        assert gw.calls == []


class TestCompoundRequest:
    """read → analyze → knowledge chained calls keep auth and integrity."""

    def test_compound_chain(self, access_context, fake_gateway):
        access_context()
        gw = fake_gateway(payload=PO_PAYLOAD)

        read_result = tool_bridge.tool_read(
            "purchase_orders",
            "search",
            filters={"branch": ["01"], "late_only": True},
        )
        analyze_result = tool_bridge.tool_analyze(
            "purchase_orders_summary", filters={"branch": ["01"]}
        )
        knowledge_result = tool_bridge.tool_knowledge(
            "search", query="acompanhamento"
        )

        assert _payload(read_result)["success"] is True
        assert _payload(analyze_result)["success"] is True
        assert _payload(knowledge_result)["success"] is True
        # read + analyze hit the BFF; knowledge stays local
        assert len(gw.calls) == 2
        assert all(
            c["path"] == "/supplies/purchase-orders" for c in gw.calls
        )

    def test_compound_partial_failure_isolated(
        self, access_context, fake_gateway
    ):
        """A forbidden read never fabricates the knowledge answer."""
        access_context()
        fake_gateway(payload=PO_PAYLOAD)

        read_result = tool_bridge.handle_tool_error(
            _call(
                tool_bridge.tool_read,
                "purchase_orders",
                "search",
                {"branch": ["03"]},
            )
        )
        knowledge_result = tool_bridge.tool_knowledge(
            "sources"
        )
        assert _payload(read_result)["status_code"] == 403
        assert _payload(knowledge_result)["success"] is True


def _call(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return exc
    raise AssertionError("expected exception")
