import pytest

from app.domain.services.commercial_proposal_acceptance_date_service import (
    CommercialProposalAcceptanceDateService,
)


def test_sql_acceptance_date_prefers_dtassi() -> None:
    sql = CommercialProposalAcceptanceDateService.sql_acceptance_date_for_alias("AD1")
    assert "AD1.AD1_DTASSI" in sql
    assert "AD1.AD1_DTFIM" in sql
    assert "CASE" in sql


def test_sql_acceptance_date_from_columns() -> None:
    sql = CommercialProposalAcceptanceDateService.sql_acceptance_date_expression(
        "AD1_DTASSI",
        "AD1_DTFIM",
    )
    assert "AD1_DTASSI" in sql
    assert "AD1_DTFIM" in sql
