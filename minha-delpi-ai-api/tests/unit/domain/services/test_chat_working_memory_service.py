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

    assert snapshot["operationalFocus"]["productCode"] == "10080001"
    assert snapshot["followUpDetected"] is True
    assert snapshot["resolvedReferences"][0]["value"] == "10080001"


def test_format_prompt_block_behavior_without_entity_focus_lines():
    snapshot = {
        "operationalFocus": {"productCode": "10080001", "productCodeSource": "tool"},
        "behaviorInstructions": {"responseFormat": "table"},
        "resolvedReferences": [],
        "usedMemoryKeys": ["productCode"],
        "followUpDetected": True,
    }

    block = ChatWorkingMemoryService.format_prompt_block(snapshot)

    assert "10080001" not in block
    assert "tabela" in block


def test_build_context_chips_from_snapshot():
    chips = ChatWorkingMemoryService.build_context_chips(
        {
            "operationalFocus": {
                "productCode": "10080001",
                "productCodeSource": "tool",
                "branch": "02",
            },
            "behaviorInstructions": {"responseFormat": "table", "tone": "direct"},
        }
    )

    kinds = {chip["kind"] for chip in chips}
    context_chips = [chip for chip in chips if chip["kind"] == "context"]

    assert len(context_chips) >= 2
    assert "format" in kinds
    assert "tone" in kinds


def test_build_context_chips_suppresses_ambiguous_product_code():
    chips = ChatWorkingMemoryService.build_context_chips(
        {
            "operationalFocus": {
                "productCode": "000224",
                "productCodeSource": "inferred",
                "branch": "02",
            },
        }
    )

    values = {chip["value"] for chip in chips}

    assert "000224" not in values
    assert "02" in values


def test_ambiguous_drilldown_code_does_not_create_product_chip():
    history = [
        {"role": "user", "content": "execute: SELECT A1_COD, A1_NOME FROM SA1010"},
        {
            "role": "assistant",
            "content": "A consulta retornou 284 registro(s).",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/data/sql"},
                    }
                ]
            },
        },
    ]

    snapshot = ChatWorkingMemoryService.build_post_turn_snapshot(
        message="detalhe este registro do último resultado — A1 cod: 000224, A1 nome: ACRILMASTER",
        previous_messages=history,
        tool_calls=[],
    )

    entities = snapshot["operationalFocus"]

    assert entities.get("productCode") == "000224"
    assert entities.get("productCodeSource") == "inferred"

    chip_values = {
        chip["value"]
        for chip in ChatWorkingMemoryService.build_context_chips(snapshot)
    }

    assert "000224" not in chip_values


def test_post_turn_syncs_product_focus_to_context_items():
    history = [
        {"role": "user", "content": "me fale do produto 10080001"},
        {
            "role": "assistant",
            "content": "Produto 10080001.",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/10080001"},
                    }
                ]
            },
        },
    ]

    snapshot = ChatWorkingMemoryService.build_post_turn_snapshot(
        message="qual o estoque do produto 10080001?",
        previous_messages=history,
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "path": "/products/10080001/stock"},
            }
        ],
    )

    labels = [
        str(item.get("label") or "")
        for item in (snapshot.get("userContextItems") or [])
        if isinstance(item, dict)
    ]

    assert "10080001" in labels


def test_real_product_tool_keeps_product_chip():
    history = [
        {"role": "user", "content": "me fale do produto 10080001"},
        {
            "role": "assistant",
            "content": "Produto 10080001.",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/10080001"},
                    }
                ]
            },
        },
    ]

    snapshot = ChatWorkingMemoryService.build_post_turn_snapshot(
        message="qual o estoque do produto 10080001?",
        previous_messages=history,
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "path": "/products/10080001/stock"},
            }
        ],
    )

    kinds = {chip["kind"] for chip in ChatWorkingMemoryService.build_context_chips(snapshot)}

    assert "context" in kinds


def test_build_context_chips_includes_warehouse():
    chips = ChatWorkingMemoryService.build_context_chips(
        {"operationalFocus": {"warehouse": "01", "branch": "02"}}
    )

    by_value = {chip["value"]: chip for chip in chips}

    assert by_value["01"]["kind"] == "context"
    assert by_value["01"]["label"] == "01"
    assert by_value["02"]["kind"] == "context"
