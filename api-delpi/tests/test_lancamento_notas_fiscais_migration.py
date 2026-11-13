"""Schema / migration SQL — lancamento-notas-fiscais.

O schema pertence à controllership-finance-api (ADR-001 / trilha 165 D2).
A api-delpi não opera up/status/reset desse schema; a prova de recusa está em
test_lnf_destructive_migrations_blocked.py. Este arquivo cobre só o conteúdo
dos arquivos SQL (checksum / declaração de objetos).
"""
from __future__ import annotations

from pathlib import Path

PLUGIN_SLUG = "lancamento-notas-fiscais"
SCHEMA = "lancamento_notas_fiscais"
MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "plugins"
    / PLUGIN_SLUG
    / "V001__create_invoice_posting_core.sql"
)
MIGRATION_V002 = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "plugins"
    / PLUGIN_SLUG
    / "V002__reconciliation_refresh_control.sql"
)
MIGRATION_V003 = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "plugins"
    / PLUGIN_SLUG
    / "V003__document_number_pad_9.sql"
)
MIGRATION_V004 = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "plugins"
    / PLUGIN_SLUG
    / "V004__linked_purchase_order.sql"
)
MIGRATION_V005 = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "plugins"
    / PLUGIN_SLUG
    / "V005__linked_purchase_orders_many.sql"
)
MIGRATION_V006 = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "plugins"
    / PLUGIN_SLUG
    / "V006__linked_purchase_order_lines.sql"
)
MIGRATION_V007 = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "plugins"
    / PLUGIN_SLUG
    / "V007__fiscal_model.sql"
)
MIGRATION_V008 = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "plugins"
    / PLUGIN_SLUG
    / "V008__danfe_attachment.sql"
)
MIGRATION_V009 = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "plugins"
    / PLUGIN_SLUG
    / "V009__cte_linked_invoices.sql"
)



def test_v001_migration_file_declares_core_objects() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "invoice_posting_requests" in sql
    assert "invoice_posting_history" in sql
    assert "invoice_posting_comments" in sql
    assert "uq_lnf_requests_active_fiscal_key" in sql
    assert "WHERE status <> 'cancelled'" in sql
    assert "document_match_key = lpad(document_number, 9, '0')" in sql
    assert "ON DELETE CASCADE" in sql
    assert "updated_at" in sql
    # comentários imutáveis na v1
    assert "invoice_posting_comments" in sql
    comments_section = sql.split("invoice_posting_comments")[1]
    assert "updated_at" not in comments_section.split("CREATE INDEX")[0]


def test_v002_migration_declares_refresh_control() -> None:
    sql = MIGRATION_V002.read_text(encoding="utf-8")
    assert "reconciliation_refresh_control" in sql
    assert "last_started_at" in sql
    assert "singleton" in sql


def test_v003_migration_pads_document_number_to_9() -> None:
    sql = MIGRATION_V003.read_text(encoding="utf-8")
    assert "lancamento_notas_fiscais.invoice_posting_requests" in sql
    assert "lpad(" in sql
    assert "document_number" in sql
    assert "9" in sql


def test_v004_migration_declares_linked_purchase_order() -> None:
    sql = MIGRATION_V004.read_text(encoding="utf-8")
    assert "linked_po_number" in sql
    assert "linked_po_delivery_date" in sql
    assert "linked_po_open_value" in sql
    assert "linked_po_product_count" in sql
    assert "linked_po_linked_at" in sql


def test_v005_migration_declares_linked_purchase_orders_many() -> None:
    sql = MIGRATION_V005.read_text(encoding="utf-8")
    assert "invoice_posting_request_linked_pos" in sql
    assert "uq_lnf_linked_pos_request_order_delivery" in sql
    assert "COALESCE(delivery_date" in sql
    assert "INSERT INTO lancamento_notas_fiscais.invoice_posting_request_linked_pos" in sql
    assert "linked_po_number" in sql


def test_v007_migration_declares_fiscal_model() -> None:
    sql = MIGRATION_V007.read_text(encoding="utf-8")
    assert "fiscal_model" in sql
    assert "ck_lnf_requests_fiscal_model" in sql
    assert "'nfe'" in sql
    assert "'nfse'" in sql
    assert "ADD COLUMN IF NOT EXISTS fiscal_model" in sql


def test_v009_migration_adds_cte_and_linked_invoices() -> None:
    sql = MIGRATION_V009.read_text(encoding="utf-8")
    assert "'cte'" in sql
    assert "ck_lnf_requests_fiscal_model" in sql
    assert "invoice_posting_linked_invoices" in sql
    assert "uq_lnf_linked_invoices_request_document" in sql
    assert "ON DELETE CASCADE" in sql


def test_v013_migration_adds_reverse_lookup_index() -> None:
    sql = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "plugins"
        / "lancamento-notas-fiscais"
        / "V013__linked_invoices_reverse_lookup.sql"
    ).read_text(encoding="utf-8")
    assert "ix_lnf_linked_invoices_document_series" in sql
    assert "document_match_key" in sql
    assert "series" in sql
    assert "invoice_posting_linked_invoices" in sql
    assert "DROP TABLE" not in sql.upper()


def test_v014_migration_canonicalizes_numeric_series() -> None:
    sql = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "plugins"
        / "lancamento-notas-fiscais"
        / "V014__canonical_series_match_key.sql"
    ).read_text(encoding="utf-8")
    assert "LTRIM(btrim(series), '0')" in sql
    assert "invoice_posting_linked_invoices" in sql
    assert "invoice_posting_requests" in sql
    assert "DELETE FROM" in sql.upper()
    assert "uq_lnf_requests_active_fiscal_key" in sql or "status = 'cancelled'" in sql
    assert "Duplicata por série equivalente" in sql
    assert "ROW_NUMBER()" in sql
    # Dedupe/cancel antes do UPDATE (evita unique violation na canonicalização)
    assert sql.upper().index("DELETE FROM") < sql.upper().index(
        "UPDATE LANCAMENTO_NOTAS_FISCAIS.INVOICE_POSTING_LINKED_INVOICES"
    )
    assert sql.upper().index("STATUS = 'CANCELLED'") < sql.upper().rindex(
        "UPDATE LANCAMENTO_NOTAS_FISCAIS.INVOICE_POSTING_REQUESTS"
    )
    assert "DROP TABLE" not in sql.upper()
    assert "DROP SCHEMA" not in sql.upper()


def test_v010_migration_adds_fiscal_attachments_without_touching_danfe() -> None:
    sql = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "plugins"
        / "lancamento-notas-fiscais"
        / "V010__fiscal_attachments.sql"
    ).read_text(encoding="utf-8")
    assert "invoice_posting_fiscal_attachments" in sql
    assert "xml_original" in sql
    assert "xml_standard" in sql
    assert "provider_document_number" in sql
    assert "dacte" in sql
    assert "DROP TABLE" not in sql.upper()
    assert "invoice_posting_danfe_attachments" in sql
    assert "DELETE FROM" not in sql.upper()


def test_v011_migration_keeps_provider_entity_id_optional() -> None:
    sql = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "plugins"
        / PLUGIN_SLUG
        / "V011__danfe_provider_entity_id.sql"
    ).read_text(encoding="utf-8")
    assert "provider_entity_id" in sql
    assert "ADD COLUMN IF NOT EXISTS provider_entity_id" in sql
    assert "provider_entity_id IS NULL" in sql
    assert "DELETE FROM" not in sql.upper()
    assert "DROP TABLE" not in sql.upper()


def test_v008_migration_declares_danfe_attachment() -> None:
    sql = MIGRATION_V008.read_text(encoding="utf-8")
    assert "invoice_posting_danfe_attachments" in sql
    assert "document_id" in sql
    assert "access_key" in sql
    assert "stored_name" in sql
    assert "ON DELETE CASCADE" in sql
    assert "PRIMARY KEY" in sql


def test_v006_migration_declares_linked_purchase_order_lines() -> None:
    sql = MIGRATION_V006.read_text(encoding="utf-8")
    assert "invoice_posting_request_linked_po_lines" in sql
    assert "uq_lnf_linked_po_lines_po_item" in sql
    assert "order_item" in sql
    assert "ON DELETE CASCADE" in sql
    assert "linked_po_id" in sql
