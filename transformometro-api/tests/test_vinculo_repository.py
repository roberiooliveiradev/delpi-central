from tm_app.infrastructure.persistence.repositories.recurso_repository import VinculoRepository


def test_vinculo_select_includes_recurso_fields():
    sql = VinculoRepository._VINCULO_SELECT
    assert "r.categoria_recurso" in sql
    assert "r.valor_total_recorrente" in sql
    assert "v.peso_rateio" in sql
    assert "r.observacoes AS recurso_observacoes" in sql
