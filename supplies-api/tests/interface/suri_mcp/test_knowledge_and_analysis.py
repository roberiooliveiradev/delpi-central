"""SURI knowledge surface + deterministic analysis tests (S5/S6)."""

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

    def test_tools_gate_on_access(self, no_access_context):
        result = tool_bridge.handle_tool_error(
            _call(tool_bridge.tool_search_supplies_knowledge, query="x")
        )
        assert _payload(result)["status_code"] == 403

    def test_tools_positive(self, access_context):
        access_context()
        result = tool_bridge.tool_get_knowledge_item("po.contract")
        body = _payload(result)
        assert body["success"] is True
        assert body["data"]["knowledge_id"] == "po.contract"

        result = tool_bridge.tool_get_knowledge_item("nope")
        assert _payload(result)["status_code"] == 404

        result = tool_bridge.tool_list_knowledge_sources()
        assert _payload(result)["data"]["corpus_version"] == 1


class TestAnalyzePurchaseOrders:
    def test_positive_labels_and_reproducibility(
        self, access_context, fake_gateway
    ):
        access_context()
        fake_gateway(payload=PO_PAYLOAD)
        result = tool_bridge.tool_analyze_purchase_orders(branch=["01"])
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
            tool_bridge.tool_analyze_purchase_orders(branch=["01"])
        )["data"]["input_hash"]
        fake_gateway(payload=PO_PAYLOAD)
        second = _payload(
            tool_bridge.tool_analyze_purchase_orders(branch=["01"])
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
            tool_bridge.tool_analyze_purchase_orders(branch=["01"])
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
                tool_bridge.tool_analyze_purchase_orders, branch=["03"]
            )
        )
        assert _payload(result)["status_code"] == 403
        assert gw.calls == []


def _call(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return exc
    raise AssertionError("expected exception")
