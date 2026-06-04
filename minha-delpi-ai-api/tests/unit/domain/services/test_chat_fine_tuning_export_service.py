from app.domain.services.chat_fine_tuning_export_service import ChatFineTuningExportService


def test_build_jsonl_includes_approved_only():
    samples = [
        {
            "status": "approved",
            "messages": [{"role": "user", "content": "ola"}, {"role": "assistant", "content": "oi"}],
            "intentLabel": "small_talk",
            "category": "routing",
        },
        {
            "status": "captured",
            "messages": [{"role": "user", "content": "x"}],
        },
    ]
    jsonl = ChatFineTuningExportService.build_jsonl(samples)
    lines = [line for line in jsonl.splitlines() if line.strip()]
    assert len(lines) == 1
    assert "small_talk" in lines[0]
    assert "messages" in lines[0]
