from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService


def test_build_pre_turn_snapshot_resolves_product_on_follow_up():
    previous = [
        {
            "role": "assistant",
            "content": "Produto 10080001: TERM. BANDEIRA",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/10080001/analyser"},
                    }
                ],
            },
        },
    ]

    snapshot = ChatWorkingMemoryService.build_pre_turn_snapshot(
        message="agora fornecedores",
        previous_messages=previous,
    )

    assert snapshot["lastEntities"]["productCode"] == "10080001"
    assert snapshot["followUpDetected"] is True
    assert snapshot["resolvedReferences"][0]["value"] == "10080001"


def test_format_prompt_block_includes_active_product():
    snapshot = {
        "lastEntities": {"productCode": "10080001"},
        "behaviorInstructions": {"responseFormat": "table"},
        "resolvedReferences": [],
        "usedMemoryKeys": ["productCode"],
        "followUpDetected": True,
    }

    block = ChatWorkingMemoryService.format_prompt_block(snapshot)

    assert "10080001" in block
    assert "tabela" in block


def test_build_context_chips_from_snapshot():
    chips = ChatWorkingMemoryService.build_context_chips(
        {
            "lastEntities": {"productCode": "10080001", "branch": "02"},
            "behaviorInstructions": {"responseFormat": "table", "tone": "direct"},
        }
    )

    kinds = {chip["kind"] for chip in chips}

    assert "product" in kinds
    assert "branch" in kinds
    assert "format" in kinds
    assert "tone" in kinds


def test_build_context_chips_includes_warehouse():
    chips = ChatWorkingMemoryService.build_context_chips(
        {"lastEntities": {"warehouse": "01", "branch": "02"}}
    )

    by_kind = {chip["kind"]: chip for chip in chips}

    assert by_kind["warehouse"]["label"] == "Armazém 01"
    assert by_kind["branch"]["value"] == "02"
