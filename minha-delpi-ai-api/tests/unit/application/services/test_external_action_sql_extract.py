from app.application.services.external_actions.external_action_sql_route_selection_service import (
    ExternalActionSqlRouteSelectionService,
)


class _Repo:
    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        return []

    def list_actions(self):
        return []


def test_extract_sql_query_preserves_protheus_delete_flag_literal():
    service = ExternalActionSqlRouteSelectionService(_Repo())
    message = (
        "execute:\n\nSELECT A1_COD, A1_NOME\nFROM SA1010\nWHERE D_E_L_E_T_ = ''"
    )

    sql = service._extract_sql_query(message)

    assert sql is not None
    assert "D_E_L_E_T_ = ''" in sql
    assert sql.endswith("= ''")


def test_extract_sql_query_handles_execute_prefix():
    service = ExternalActionSqlRouteSelectionService(_Repo())
    message = "execute:\nSELECT A1_COD FROM SA1010 WHERE D_E_L_E_T_ = ''"

    sql = service._extract_sql_query(message)

    assert sql is not None
    assert sql.startswith("SELECT A1_COD")


def test_extract_sql_query_rejects_portuguese_select_prose():
    service = ExternalActionSqlRouteSelectionService(_Repo())
    message = (
        "executa no banco esse select top 10 de produtos do grupo 1008 "
        "(SB1010, B1_COD, B1_DESC, B1_GRUPO)"
    )

    assert service._extract_sql_query(message) is None


def test_term_occurs_rejects_op_inside_top():
    from app.domain.services.operational_route_matcher_service import (
        OperationalRouteMatcherService,
    )

    assert OperationalRouteMatcherService._term_occurs("op ", "select top 10") is False
    assert OperationalRouteMatcherService._term_occurs("ct ", "select top 10") is False
    assert OperationalRouteMatcherService._term_occurs("op ", "listar op atrasada") is True
