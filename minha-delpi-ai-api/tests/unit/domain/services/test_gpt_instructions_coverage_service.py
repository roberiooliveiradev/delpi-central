from app.domain.services.gpt_instructions_coverage_service import (
    GptInstructionCoverage,
    GptInstructionsCoverageService,
)


def test_agent_ingest_sources_lists_missing_operational_docs():
    sources = {entry.source_file for entry in GptInstructionsCoverageService.agent_ingest_sources()}

    assert "data_sql_api_instructions.md" in sources
    assert "product_api_instructions.md" in sources
    assert "system_api_instructions.md" in sources
    assert "GPT_instructions.md" not in sources


def test_build_markdown_report_contains_indexed_agent():
    report = GptInstructionsCoverageService.build_markdown_report()

    assert "api-delpi-rotas-agente.md" in report
    assert "data_sql_api_instructions.md" in report
    assert "indexed_agent" in report
