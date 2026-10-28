"""Unit — pivot cliente × mês (unittest, sem pytest)."""

from __future__ import annotations

import unittest

from app.application.dto.commercial.get_billing_by_customer_month_request import (
    GetBillingByCustomerMonthRequest,
)
from app.application.use_cases.commercial.get_billing_by_customer_month_use_case import (
    GetBillingByCustomerMonthUseCase,
)


class _FakeRepo:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def list_billing_rows(self, request):  # noqa: ANN001
        return self.rows


class BillingByCustomerMonthUseCaseTests(unittest.TestCase):
    def test_pivots_months_and_preserves_code_store(self) -> None:
        repo = _FakeRepo(
            [
                {
                    "customer_code": "0001",
                    "customer_store": "01",
                    "customer_name": "Alpha",
                    "year_month": "202601",
                    "billed_value": 100,
                },
                {
                    "customer_code": "0001",
                    "customer_store": "01",
                    "customer_name": "Alpha",
                    "year_month": "202602",
                    "billed_value": 40,
                },
                {
                    "customer_code": "0001",
                    "customer_store": "02",
                    "customer_name": "Alpha Loja 2",
                    "year_month": "202601",
                    "billed_value": 10,
                },
            ]
        )
        result = GetBillingByCustomerMonthUseCase(repo).execute(
            GetBillingByCustomerMonthRequest(
                start_date="2026-01-01",
                end_date="2026-02-28",
                nature="gross",
                limit=5000,
            )
        )
        self.assertEqual(result.months, ("2026-01", "2026-02"))
        self.assertEqual(result.customers_count, 2)
        self.assertEqual(result.grand_total, 150.0)
        by_key = {
            (item.customer_code, item.customer_store): item for item in result.items
        }
        self.assertEqual(by_key[("0001", "01")].total, 140.0)
        self.assertEqual(by_key[("0001", "01")].monthly_values["2026-01"], 100.0)
        self.assertEqual(by_key[("0001", "02")].total, 10.0)

    def test_net_nature_and_limit_truncation(self) -> None:
        rows = [
            {
                "customer_code": f"{i:04d}",
                "customer_store": "01",
                "customer_name": f"C{i}",
                "year_month": "202603",
                "billed_value": 100 - i,
            }
            for i in range(5)
        ]
        result = GetBillingByCustomerMonthUseCase(_FakeRepo(rows)).execute(
            GetBillingByCustomerMonthRequest(
                start_date="2026-03-01",
                end_date="2026-03-31",
                nature="net",
                limit=3,
            )
        )
        self.assertEqual(result.nature, "net")
        self.assertEqual(result.customers_count, 3)
        self.assertTrue(result.truncated)
        self.assertEqual(result.items[0].customer_code, "0000")


if __name__ == "__main__":
    unittest.main()
