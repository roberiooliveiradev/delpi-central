import pytest

from app.domain.services.agent_knowledge_filename_service import AgentKnowledgeFilenameService


@pytest.mark.parametrize(
    ("original", "expected"),
    [
        ("data_sql_api_instructions.md", "sql-data-api-instructions.md"),
        ("Understanding DELPI Intermediate Product Codes.md", "engenharia-codigos-intermediarios-delpi.md"),
        ("Analista SQL DELPI — Produção, Suprimentos e Perdas.txt", "sql-playbook-producao-suprimentos-perdas.txt"),
        ("api-delpi-rotas-agente.md", "api-delpi-rotas-agente.md"),
    ],
)
def test_normalize_known_filenames(original: str, expected: str) -> None:
    assert AgentKnowledgeFilenameService.normalize(original) == expected


def test_normalize_unknown_filename_slugifies() -> None:
    assert (
        AgentKnowledgeFilenameService.normalize("Meu Documento Especial!.pdf")
        == "meu-documento-especial.pdf"
    )
