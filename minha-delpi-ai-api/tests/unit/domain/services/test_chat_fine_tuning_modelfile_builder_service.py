from app.domain.services.chat_fine_tuning_modelfile_builder_service import (
    ChatFineTuningModelfileBuilderService,
)


def test_build_modelfile_contains_base_and_examples():
    modelfile = ChatFineTuningModelfileBuilderService.build_modelfile(
        base_model="qwen2.5:3b",
        target_model="chat",
        samples=[
            {
                "status": "approved",
                "messages": [
                    {"role": "user", "content": "como consultar estoque?"},
                    {"role": "assistant", "content": "Use o agente operacional."},
                ],
                "intentLabel": "operational_query",
            }
        ],
    )

    assert "FROM qwen2.5:3b" in modelfile
    assert "SYSTEM" in modelfile
    assert "como consultar estoque?" in modelfile
    assert "intent=operational_query" in modelfile


def test_build_model_name_is_stable():
    assert (
        ChatFineTuningModelfileBuilderService.build_model_name(dataset_id=3, run_id=9)
        == "delpi-ft-d3-r9"
    )
