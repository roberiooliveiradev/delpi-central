"""Schema / migration — lancamento-notas-fiscais (Etapa 2A).

Upgrade: run_plugins_migrations up --plugin lancamento-notas-fiscais
Downgrade (padrão do projeto): reset --plugin (DROP SCHEMA CASCADE)

Testes live usam somente o schema do plugin; não executam docker compose down -v.
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

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


def _plugins_env_ready() -> bool:
    return all(
        os.getenv(name, "").strip()
        for name in (
            "PLUGINS_DB_HOST",
            "PLUGINS_DB_PORT",
            "PLUGINS_DB_NAME",
            "PLUGINS_DB_USER",
            "PLUGINS_DB_PASSWORD",
        )
    )


pytestmark_live = pytest.mark.skipif(
    not _plugins_env_ready(),
    reason="PLUGINS_DB_* ausente — testes live de migration ignorados",
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


def _drop_plugin_schema_only(conn) -> None:
    """Downgrade isolado: remove só o schema do plugin (sem pg_terminate_backend)."""
    with conn.cursor() as cur:
        cur.execute(f'DROP SCHEMA IF EXISTS "{SCHEMA}" CASCADE;')
    conn.commit()


@pytestmark_live
class TestLancamentoNotasFiscaisMigrationLive:
    @pytest.fixture(scope="class")
    @classmethod
    def conn_factory(cls):
        from scripts.run_plugins_migrations import get_connection

        return get_connection

    @pytest.fixture(scope="class", autouse=True)
    @classmethod
    def schema_cycle(cls, conn_factory):
        from scripts.run_plugins_migrations import run_plugin_migrations

        with conn_factory() as conn:
            _drop_plugin_schema_only(conn)
        run_plugin_migrations(PLUGIN_SLUG)
        yield
        with conn_factory() as conn:
            _drop_plugin_schema_only(conn)
        run_plugin_migrations(PLUGIN_SLUG)

    def test_upgrade_creates_three_tables(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                      FROM information_schema.tables
                     WHERE table_schema = %s
                       AND table_name = ANY(%s)
                     ORDER BY table_name
                    """,
                    (
                        SCHEMA,
                        [
                            "invoice_posting_comments",
                            "invoice_posting_history",
                            "invoice_posting_requests",
                        ],
                    ),
                )
                names = [row["table_name"] for row in cur.fetchall()]
        assert names == [
            "invoice_posting_comments",
            "invoice_posting_history",
            "invoice_posting_requests",
        ]

    def test_downgrade_and_reapply(self, conn_factory) -> None:
        from scripts.run_plugins_migrations import run_plugin_migrations

        with conn_factory() as conn:
            _drop_plugin_schema_only(conn)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS n
                      FROM information_schema.schemata
                     WHERE schema_name = %s
                    """,
                    (SCHEMA,),
                )
                assert int(cur.fetchone()["n"]) == 0

        run_plugin_migrations(PLUGIN_SLUG)
        with conn_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS n
                      FROM information_schema.tables
                     WHERE table_schema = %s
                       AND table_name = 'invoice_posting_requests'
                    """,
                    (SCHEMA,),
                )
                assert int(cur.fetchone()["n"]) == 1

    def _insert_request(self, cur, **overrides):
        base = {
            "id": str(uuid.uuid4()),
            "branch_code": "01",
            "document_number": "00123456",
            "document_match_key": "000123456",
            "series": "",
            "supplier_code": "000001",
            "supplier_store": "01",
            "supplier_name": "Fornecedor Teste",
            "issue_date": date(2026, 7, 1),
            "amount": "100.00",
            "received_at": datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc),
            "status": "pending",
            "created_by_user_id": "user-creator",
            "created_by_name": "Criador",
        }
        base.update(overrides)
        cols = ", ".join(base.keys())
        placeholders = ", ".join(["%s"] * len(base))
        cur.execute(
            f"""
            INSERT INTO {SCHEMA}.invoice_posting_requests ({cols})
            VALUES ({placeholders})
            RETURNING id
            """,
            tuple(base.values()),
        )
        return cur.fetchone()["id"]

    def test_active_duplicate_blocked(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                self._insert_request(cur, document_number="00111111", document_match_key="000111111")
                with pytest.raises(Exception):
                    self._insert_request(
                        cur,
                        document_number="00111111",
                        document_match_key="000111111",
                    )
            conn.rollback()

    def test_cancelled_allows_same_key(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                self._insert_request(
                    cur,
                    document_number="00222222",
                    document_match_key="000222222",
                    status="cancelled",
                    cancel_justification="duplicata de teste",
                    cancelled_at=datetime.now(timezone.utc),
                    cancelled_by_user_id="user-admin",
                    cancelled_by_name="Admin",
                )
                second_id = self._insert_request(
                    cur,
                    document_number="00222222",
                    document_match_key="000222222",
                    status="pending",
                )
                assert second_id
            conn.commit()

    def test_invalid_branch_rejected(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                with pytest.raises(Exception):
                    self._insert_request(cur, branch_code="99")
            conn.rollback()

    def test_invalid_document_rejected(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                with pytest.raises(Exception):
                    self._insert_request(
                        cur,
                        document_number="ABC",
                        document_match_key="000000ABC",
                    )
            conn.rollback()

    def test_document_match_inconsistency_rejected(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                with pytest.raises(Exception):
                    self._insert_request(
                        cur,
                        document_number="00123456",
                        document_match_key="999999999",
                    )
            conn.rollback()

    def test_invalid_status_rejected(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                with pytest.raises(Exception):
                    self._insert_request(cur, status="unknown")
            conn.rollback()

    def test_blocked_without_reason_rejected(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                with pytest.raises(Exception):
                    self._insert_request(
                        cur,
                        document_number="00333333",
                        document_match_key="000333333",
                        status="blocked",
                        block_reason=None,
                        block_description="falta pedido",
                    )
            conn.rollback()

    def test_blocked_without_description_rejected(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                with pytest.raises(Exception):
                    self._insert_request(
                        cur,
                        document_number="00333334",
                        document_match_key="000333334",
                        status="blocked",
                        block_reason="purchase_order",
                        block_description="   ",
                    )
            conn.rollback()

    def test_cancelled_without_justification_rejected(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                with pytest.raises(Exception):
                    self._insert_request(
                        cur,
                        document_number="00444444",
                        document_match_key="000444444",
                        status="cancelled",
                        cancel_justification=None,
                        cancelled_at=datetime.now(timezone.utc),
                        cancelled_by_user_id="user-admin",
                    )
            conn.rollback()

    def test_empty_comment_rejected(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                request_id = self._insert_request(
                    cur,
                    document_number="00555555",
                    document_match_key="000555555",
                )
                with pytest.raises(Exception):
                    cur.execute(
                        f"""
                        INSERT INTO {SCHEMA}.invoice_posting_comments (
                            request_id, author_user_id, author_name, body
                        ) VALUES (%s, %s, %s, %s)
                        """,
                        (request_id, "u1", "Autor", "   "),
                    )
            conn.rollback()

    def test_history_and_comment_foreign_keys(self, conn_factory) -> None:
        with conn_factory() as conn:
            with conn.cursor() as cur:
                request_id = self._insert_request(
                    cur,
                    document_number="00666666",
                    document_match_key="000666666",
                )
                cur.execute(
                    f"""
                    INSERT INTO {SCHEMA}.invoice_posting_history (
                        request_id, event_type, actor_origin, actor_user_id,
                        from_status, to_status, changes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING id
                    """,
                    (
                        request_id,
                        "created",
                        "user",
                        "user-creator",
                        None,
                        "pending",
                        "{}",
                    ),
                )
                history_id = cur.fetchone()["id"]
                cur.execute(
                    f"""
                    INSERT INTO {SCHEMA}.invoice_posting_comments (
                        request_id, author_user_id, author_name, body
                    ) VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (request_id, "user-creator", "Criador", "Recebido na portaria"),
                )
                comment_id = cur.fetchone()["id"]
                assert history_id and comment_id

                missing = str(uuid.uuid4())
                with pytest.raises(Exception):
                    cur.execute(
                        f"""
                        INSERT INTO {SCHEMA}.invoice_posting_history (
                            request_id, event_type, actor_origin
                        ) VALUES (%s, %s, %s)
                        """,
                        (missing, "created", "system"),
                    )
            conn.rollback()
