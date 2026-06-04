from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService


def test_post_turn_records_previous_product_when_tool_switches_code():
    pre = {
        "operationalFocus": {"productCode": "10080001"},
        "previousProductCodes": [],
        "usedMemoryKeys": ["productCode"],
    }
    snapshot = ChatWorkingMemoryService.build_post_turn_snapshot(
        message="mostre o estoque",
        previous_messages=[],
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"path": "/products/10080002/stock"},
            }
        ],
        pre_snapshot=pre,
    )

    assert snapshot["operationalFocus"]["productCode"] == "10080002"
    assert "10080001" in snapshot.get("previousProductCodes", [])


def test_pre_turn_restores_previous_product_codes_from_context_snapshot():
    previous_messages = [
        {
            "role": "assistant",
            "content": "Estoque",
            "metadata": {
                "contextSnapshot": {
                    "operationalFocus": {"productCode": "10080002"},
                    "previousProductCodes": ["10080001"],
                }
            },
        }
    ]

    snapshot = ChatWorkingMemoryService.build_pre_turn_snapshot(
        message="compare com o anterior",
        previous_messages=previous_messages,
    )

    assert snapshot["operationalFocus"]["productCode"] == "10080002"
    assert "10080001" in snapshot.get("previousProductCodes", [])
