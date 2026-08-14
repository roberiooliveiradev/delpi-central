"""Schema / migration — invoice-issuance."""

from __future__ import annotations

from pathlib import Path

PLUGIN_SLUG = "invoice-issuance"
_MIGRATIONS = (
    Path(__file__).resolve().parents[1] / "migrations" / "plugins" / PLUGIN_SLUG
)
MIGRATION = _MIGRATIONS / "V001__create_invoice_issuance_core.sql"
V002 = _MIGRATIONS / "V002__add_sales_order_to_items.sql"
V003 = _MIGRATIONS / "V003__add_carrier_code.sql"


def test_v001_creates_core_tables() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "invoice_issuance.invoice_issuance_requests" in sql
    assert "invoice_issuance.invoice_issuance_request_items" in sql
    assert "invoice_issuance.invoice_issuance_attachments" in sql
    assert "invoice_issuance.invoice_issuance_history" in sql
    assert "party_type IN ('customer', 'supplier')" in sql
    assert "'sale'" in sql
    assert "freight_mode IN ('cif', 'fob')" in sql
    assert "status IN (" in sql
    assert "B2_LOCAL" not in sql


def test_v002_adds_sales_order_columns() -> None:
    sql = V002.read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS sales_order" in sql
    assert "ADD COLUMN IF NOT EXISTS sales_order_item" in sql
    assert "ADD COLUMN IF NOT EXISTS customer_order_number" in sql
    assert "DROP SCHEMA" not in sql


V004 = _MIGRATIONS / "V004__add_carrier_contact.sql"


def test_v003_adds_carrier_code() -> None:
    sql = V003.read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS carrier_code" in sql
    assert "DROP SCHEMA" not in sql


def test_v004_adds_carrier_contact() -> None:
    sql = V004.read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS carrier_legal_name" in sql
    assert "ADD COLUMN IF NOT EXISTS carrier_tax_id" in sql
    assert "ADD COLUMN IF NOT EXISTS carrier_address" in sql
    assert "ADD COLUMN IF NOT EXISTS carrier_phone" in sql
    assert "DROP SCHEMA" not in sql
