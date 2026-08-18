from __future__ import annotations

from commercial_app.domain.services.opportunity_collaborator_summary_service import (
    OpportunityCollaboratorSummaryService,
)


def test_summarize_groups_by_seller_and_status() -> None:
    items = [
        {"seller_code": "A", "seller_name": "Ana", "status_category": "open"},
        {"seller_code": "A", "seller_name": "Ana", "status_category": "won"},
        {"seller_code": "B", "seller_name": "Bia", "status_category": "open"},
        {"seller_code": "", "status_category": "lost"},
    ]
    rows = OpportunityCollaboratorSummaryService().summarize(items)
    by_code = {row["sellerCode"]: row for row in rows}
    assert by_code["A"]["totalCount"] == 2
    assert by_code["A"]["openCount"] == 1
    assert by_code["A"]["wonCount"] == 1
    assert by_code["B"]["openCount"] == 1
    assert by_code[""]["lostCount"] == 1
    assert rows[0]["sellerCode"] == "A"
