"""Current actionable SC approvals, paged by document rather than SCR row."""

from __future__ import annotations

from typing import Any

from app.domain.services.pagination_tier_service import PaginationTierService
from app.domain.totvs.protheus_branches import PROTHEUS_BRANCH_CODES
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_approval_lead_time_sql import (
    build_lead_time_pending_sql,
    build_lead_time_products_sql,
)


class PurchaseRequestPendingApprovalsRepository(BaseRepository):
    def list_pending_approvals(
        self,
        *,
        after_branch: str = "",
        after_request_number: str = "",
        limit: int = 25,
    ) -> dict[str, Any]:
        if bool(after_branch) != bool(after_request_number):
            raise ValueError("Informe os dois campos do cursor.")
        if after_branch and after_branch not in PROTHEUS_BRANCH_CODES:
            raise ValueError("Filial do cursor inválida.")
        if after_request_number and (
            not after_request_number.isdigit() or len(after_request_number) > 16
        ):
            raise ValueError("Número da SC do cursor inválido.")
        size = PaginationTierService.require_int("limit_25_100", limit)
        placeholders = ", ".join("?" for _ in PROTHEUS_BRANCH_CODES)
        # No issuance-date window: an old SC remains someone's responsibility.
        where = f"SC1.D_E_L_E_T_ = '' AND SC1.C1_FILIAL IN ({placeholders})"
        where += """
          AND (SC1.C1_FILIAL > ? OR (SC1.C1_FILIAL = ? AND SC1.C1_NUM > ?))
          AND SC1.C1_RESIDUO <> 'S'
          AND SC1.C1_QUANT > SC1.C1_QUJE
          AND NOT EXISTS (
              SELECT 1 FROM SC1010 Rejected
              WHERE Rejected.D_E_L_E_T_ = ''
                AND Rejected.C1_FILIAL = SC1.C1_FILIAL
                AND Rejected.C1_NUM = SC1.C1_NUM
                AND Rejected.C1_APROV = 'R'
          )
        """
        # Share the active SCR02/SAK resolution with the alçada indicator.
        sql = build_lead_time_pending_sql(
            where,
            max_requests=size + 1,
            actionable_only=True,
            order_by_document=True,
        )
        params = [
            *PROTHEUS_BRANCH_CODES,
            after_branch,
            after_branch,
            after_request_number,
        ]
        with self as repo:
            rows = repo.execute_query(sql, tuple(params))
            documents: dict[tuple[str, str], dict] = {}
            for row in rows:
                key = (row["branch"], row["request_number"])
                document = documents.setdefault(
                    key,
                    {
                        "branch": key[0],
                        "request_number": key[1],
                        "requester_protheus_user_id": row.get("requester_user_id"),
                        "requester_name": row.get("requester_name"),
                        "request_issue_date": row.get("issue_date"),
                        "pending_approvers": [],
                        "products": [],
                    },
                )
                approver = {
                    "code": row.get("approver_code"),
                    "name": row.get("approver_name"),
                    "protheus_user_id": row.get("approver_user_code"),
                    "level": row.get("level"),
                }
                if approver not in document["pending_approvers"]:
                    document["pending_approvers"].append(approver)
            keys = sorted(documents)[:size]
            if keys:
                product_sql, product_params = build_lead_time_products_sql(keys)
                for product in repo.execute_query(product_sql, tuple(product_params)):
                    key = (product["branch"], product["request_number"])
                    if key in documents:
                        documents[key]["products"].append(
                            {
                                "code": product["product_code"],
                                "description": product.get("product_description"),
                            }
                        )
        has_more = len(documents) > size
        return {
            "items": [documents[key] for key in keys],
            "limit": size,
            "next_cursor": (
                {
                    "after_branch": keys[-1][0],
                    "after_request_number": keys[-1][1],
                }
                if has_more
                else None
            ),
        }
