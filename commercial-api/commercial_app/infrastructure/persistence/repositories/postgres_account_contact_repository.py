from __future__ import annotations

from typing import Any
from uuid import UUID

from commercial_app.domain.entities.account_contact import AccountContact
from commercial_app.domain.ports.account_contact_repository_port import (
    AccountContactRepositoryPort,
)
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

_COLUMNS = """
    id, customer_code, customer_store, full_name, role_title, channel,
    email, phone_e164, is_whatsapp, is_primary, source, deleted_at,
    created_at, updated_at, created_by_user_id
"""
_UPDATABLE_COLUMNS = frozenset(
    {
        "full_name",
        "role_title",
        "channel",
        "email",
        "phone_e164",
        "is_whatsapp",
        "is_primary",
        "source",
    }
)


def _row(row: dict[str, Any] | None) -> AccountContact | None:
    if not row:
        return None
    return AccountContact(
        id=row["id"],
        customer_code=str(row["customer_code"]),
        customer_store=str(row["customer_store"]),
        full_name=str(row["full_name"]),
        role_title=row.get("role_title"),
        channel=str(row["channel"]),
        email=row.get("email"),
        phone_e164=row.get("phone_e164"),
        is_whatsapp=bool(row["is_whatsapp"]),
        is_primary=bool(row["is_primary"]),
        source=str(row["source"]),
        deleted_at=row.get("deleted_at"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        created_by_user_id=str(row["created_by_user_id"]),
    )


class PostgresAccountContactRepository(
    PluginBaseRepository, AccountContactRepositoryPort
):
    def list_for_account(
        self, *, customer_code: str, customer_store: str
    ) -> list[AccountContact]:
        rows = self.fetch_all(
            f"""
            SELECT {_COLUMNS}
              FROM commercial.account_contacts
             WHERE customer_code = %s
               AND customer_store = %s
               AND deleted_at IS NULL
          ORDER BY is_primary DESC, full_name ASC, created_at ASC
            """,
            (customer_code, customer_store),
        )
        return [contact for item in rows if (contact := _row(item)) is not None]

    def get_by_id(self, contact_id: UUID) -> AccountContact | None:
        row = self.fetch_one(
            f"""
            SELECT {_COLUMNS}
              FROM commercial.account_contacts
             WHERE id = %s
               AND deleted_at IS NULL
            """,
            (contact_id,),
        )
        return _row(row)

    def create(self, *, values: dict[str, Any]) -> AccountContact:
        try:
            with self.db():
                with self.connection.cursor() as cursor:
                    if values["is_primary"]:
                        cursor.execute(
                            """
                            UPDATE commercial.account_contacts
                               SET is_primary = FALSE,
                                   updated_at = NOW()
                             WHERE customer_code = %s
                               AND customer_store = %s
                               AND is_primary = TRUE
                               AND deleted_at IS NULL
                            """,
                            (values["customer_code"], values["customer_store"]),
                        )
                    cursor.execute(
                        f"""
                        INSERT INTO commercial.account_contacts (
                            customer_code, customer_store, full_name, role_title,
                            channel, email, phone_e164, is_whatsapp, is_primary,
                            source, created_by_user_id
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        RETURNING {_COLUMNS}
                        """,
                        (
                            values["customer_code"],
                            values["customer_store"],
                            values["full_name"],
                            values.get("role_title"),
                            values["channel"],
                            values.get("email"),
                            values.get("phone_e164"),
                            values["is_whatsapp"],
                            values["is_primary"],
                            values["source"],
                            values["created_by_user_id"],
                        ),
                    )
                    row = cursor.fetchone()
                self.commit()
        except Exception as exc:
            self.rollback()
            raise PluginsRepositoryError("Falha ao criar contato da conta.") from exc
        contact = _row(dict(row) if row is not None else None)
        if contact is None:
            raise PluginsRepositoryError("Falha ao criar contato da conta.")
        return contact

    def update(
        self, *, contact_id: UUID, values: dict[str, Any]
    ) -> AccountContact | None:
        updates = {
            key: value for key, value in values.items() if key in _UPDATABLE_COLUMNS
        }
        if not updates:
            return self.get_by_id(contact_id)
        try:
            with self.db():
                with self.connection.cursor() as cursor:
                    if updates.get("is_primary") is True:
                        cursor.execute(
                            """
                            UPDATE commercial.account_contacts AS other
                               SET is_primary = FALSE,
                                   updated_at = NOW()
                              FROM commercial.account_contacts AS target
                             WHERE target.id = %s
                               AND target.deleted_at IS NULL
                               AND other.customer_code = target.customer_code
                               AND other.customer_store = target.customer_store
                               AND other.id <> target.id
                               AND other.is_primary = TRUE
                               AND other.deleted_at IS NULL
                            """,
                            (contact_id,),
                        )
                    assignments = ", ".join(f"{column} = %s" for column in updates)
                    cursor.execute(
                        f"""
                        UPDATE commercial.account_contacts
                           SET {assignments},
                               updated_at = NOW()
                         WHERE id = %s
                           AND deleted_at IS NULL
                     RETURNING {_COLUMNS}
                        """,
                        (*updates.values(), contact_id),
                    )
                    row = cursor.fetchone()
                self.commit()
        except Exception as exc:
            self.rollback()
            raise PluginsRepositoryError("Falha ao atualizar contato da conta.") from exc
        return _row(dict(row) if row is not None else None)

    def soft_delete(self, *, contact_id: UUID) -> AccountContact | None:
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.account_contacts
               SET deleted_at = NOW(),
                   is_primary = FALSE,
                   updated_at = NOW()
             WHERE id = %s
               AND deleted_at IS NULL
         RETURNING {_COLUMNS}
            """,
            (contact_id,),
        )
        return _row(row)
