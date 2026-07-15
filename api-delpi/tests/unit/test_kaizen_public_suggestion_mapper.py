from app.domain.services.kaizen.kaizen_public_suggestion_mapper import (
    build_suggestion_record_fields,
)


def test_build_suggestion_record_fields_maps_forms_columns() -> None:
    fields = build_suggestion_record_fields(
        proposer_name="Rodrigo Josué Cozer",
        sector="Administrativo",
        employee_registration="10608",
        work_center_or_location="Todos os setores",
        problem_description="Ainda preenchemos formulário manuscrito.",
        proposed_solution="Elaborar coleta eletrônica de ideias.",
        branch_code="01",
    )

    assert fields["status"] == "recebido"
    assert fields["accountable"] == "Rodrigo Josué Cozer"
    assert fields["sector"] == "Administrativo"
    assert fields["process_description"] == "Todos os setores"
    assert "manuscrito" in (fields["problem_description"] or "")
    assert "eletrônica" in (fields["improvement_description"] or "")
    assert "Cadastro: 10608" in (fields["notes"] or "")
    assert fields["savings_type"] == "qualitativo"
    assert fields["participants"][0]["role"] == "responsavel"
    assert fields["title"].startswith("Todos os setores:")
    assert fields["date_idea_received"]


def test_build_suggestion_falls_back_branch() -> None:
    fields = build_suggestion_record_fields(
        proposer_name="Ana",
        sector="Produtivo",
        employee_registration="1",
        work_center_or_location="CT-33",
        problem_description="Problema longo o bastante.",
        proposed_solution="Solução longa o bastante.",
        branch_code="99",
    )
    assert fields["branch_code"] == "01"
