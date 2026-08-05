from __future__ import annotations

from typing import Any, Sequence

from commercial_app.domain.entities.customer_avatar import CustomerAvatarRecord
from commercial_app.domain.ports.customer_avatar_repository_port import (
    CustomerAvatarRepositoryPort,
)
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_COLUMNS = "customer_code, customer_store, file_name, content_type"


class LegacyPostgresCustomerAvatarRepository(
    PluginBaseRepository,
    CustomerAvatarRepositoryPort,
):
    """Dual-read: schema legado pedidos_venda_abertos.customer_avatars."""

    def get(
        self,
        *,
        customer_code: str,
        customer_store: str,
    ) -> CustomerAvatarRecord | None:
        row = self.fetch_one(
            f"""
            SELECT {_COLUMNS}
              FROM pedidos_venda_abertos.customer_avatars
             WHERE customer_code = %s
               AND customer_store = %s
            """,
            (customer_code, customer_store),
        )
        return self._hydrate(row)

    def list_for_customers(
        self,
        *,
        customers: Sequence[tuple[str, str]],
    ) -> list[CustomerAvatarRecord]:
        pairs = [(c.strip(), s.strip()) for c, s in customers if c.strip() and s.strip()]
        if not pairs:
            return []
        values_sql = ", ".join(["(%s, %s)"] * len(pairs))
        params: list[str] = []
        for code, store in pairs:
            params.extend([code, store])
        rows = self.fetch_all(
            f"""
            SELECT a.customer_code, a.customer_store, a.file_name, a.content_type
              FROM pedidos_venda_abertos.customer_avatars a
              INNER JOIN (VALUES {values_sql}) AS v(customer_code, customer_store)
                ON a.customer_code = v.customer_code
               AND a.customer_store = v.customer_store
            """,
            tuple(params),
        )
        return [
            record
            for row in rows
            if (record := self._hydrate(row)) is not None
        ]

    def upsert(
        self,
        *,
        customer_code: str,
        customer_store: str,
        file_name: str,
        storage_key: str,
        content_type: str,
        byte_size: int | None,
        uploaded_by_user_id: str | None,
    ) -> CustomerAvatarRecord:
        del storage_key, byte_size  # legado não persiste essas colunas
        row = self.execute_returning_one(
            f"""
            INSERT INTO pedidos_venda_abertos.customer_avatars (
                customer_code, customer_store, file_name, content_type, uploaded_by_user_id
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (customer_code, customer_store) DO UPDATE
               SET file_name = EXCLUDED.file_name,
                   content_type = EXCLUDED.content_type,
                   uploaded_by_user_id = EXCLUDED.uploaded_by_user_id,
                   updated_at = NOW()
         RETURNING {_COLUMNS}
            """,
            (
                customer_code,
                customer_store,
                file_name,
                content_type,
                uploaded_by_user_id,
            ),
        )
        record = self._hydrate(row)
        if record is None:
            raise RuntimeError("Falha ao gravar avatar do cliente (legado).")
        return record

    def delete(
        self,
        *,
        customer_code: str,
        customer_store: str,
    ) -> bool:
        existing = self.fetch_one(
            """
            SELECT id
              FROM pedidos_venda_abertos.customer_avatars
             WHERE customer_code = %s
               AND customer_store = %s
            """,
            (customer_code, customer_store),
        )
        if existing is None:
            return False
        self.execute(
            """
            DELETE FROM pedidos_venda_abertos.customer_avatars
             WHERE customer_code = %s
               AND customer_store = %s
            """,
            (customer_code, customer_store),
        )
        return True

    @staticmethod
    def _hydrate(row: dict[str, Any] | None) -> CustomerAvatarRecord | None:
        if not row:
            return None
        code = str(row["customer_code"]).strip()
        store = str(row["customer_store"]).strip()
        file_name = str(row["file_name"]).strip()
        from commercial_app.application.services.customer_avatar_storage import (
            CustomerAvatarStorage,
        )

        dir_name = CustomerAvatarStorage.identity_dir_name(
            customer_code=code,
            customer_store=store,
        )
        return CustomerAvatarRecord(
            customer_code=code,
            customer_store=store,
            file_name=file_name,
            content_type=str(row["content_type"]).strip(),
            storage_key=f"{dir_name}/{file_name}",
            byte_size=None,
        )
