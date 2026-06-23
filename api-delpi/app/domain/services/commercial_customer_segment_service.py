from __future__ import annotations

from typing import Literal, Optional

CommercialCustomerSegment = Literal["weg", "new_business"]

WEG_CLIENT_CODE_CANONICAL = "000001"


class CommercialCustomerSegmentService:
    @staticmethod
    def normalize_customer_segment(
        value: Optional[str],
    ) -> Optional[CommercialCustomerSegment]:
        normalized = (value or "").strip().lower().replace("-", "_")
        if not normalized:
            return None
        if normalized in {"weg", "weg_client", "cliente_weg"}:
            return "weg"
        if normalized in {
            "new_business",
            "novos_negocios",
            "novo_negocio",
            "newbusiness",
        }:
            return "new_business"
        raise ValueError(
            "customer_segment inválido. Use weg ou new_business."
        )

    @staticmethod
    def sql_is_weg_client_code(column_expression: str) -> str:
        column = column_expression.strip()
        return (
            f"RIGHT('000000' + RTRIM(LTRIM({column})), 6) = "
            f"'{WEG_CLIENT_CODE_CANONICAL}'"
        )

    @staticmethod
    def sql_segment_predicate(
        column_expression: str,
        segment: Optional[str],
    ) -> str:
        normalized = CommercialCustomerSegmentService.normalize_customer_segment(
            segment
        )
        if not normalized:
            return ""

        is_weg = CommercialCustomerSegmentService.sql_is_weg_client_code(
            column_expression
        )
        if normalized == "weg":
            return f"({is_weg})"
        return f"NOT ({is_weg})"

    @staticmethod
    def apply_segment_to_query_builder(qb, column_expression: str, segment) -> None:
        predicate = CommercialCustomerSegmentService.sql_segment_predicate(
            column_expression,
            segment,
        )
        if predicate:
            qb.raw(predicate)
