from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)


class _Repo:
    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        return []

    def list_actions(self):
        return []


def test_extract_sql_query_preserves_protheus_delete_flag_literal():
    service = ExternalActionSelectionService(_Repo())
    message = (
        "execute:\n\nSELECT A1_COD, A1_NOME\nFROM SA1010\nWHERE D_E_L_E_T_ = ''"
    )

    sql = service._extract_sql_query(message)

    assert sql is not None
    assert "D_E_L_E_T_ = ''" in sql
    assert sql.endswith("= ''")


def test_extract_sql_query_handles_execute_prefix():
    service = ExternalActionSelectionService(_Repo())
    message = "execute:\nSELECT A1_COD FROM SA1010 WHERE D_E_L_E_T_ = ''"

    sql = service._extract_sql_query(message)

    assert sql is not None
    assert sql.startswith("SELECT A1_COD")
