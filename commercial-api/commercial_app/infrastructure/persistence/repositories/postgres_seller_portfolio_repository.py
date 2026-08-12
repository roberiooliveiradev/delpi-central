from __future__ import annotations

from typing import Any, Sequence

from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)
from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_PORTFOLIO_COLUMNS = (
    "id, user_id, display_name, active, created_by_user_id, created_at, updated_at"
)
_PORTFOLIO_COLUMNS_SP = (
    "sp.id, sp.user_id, sp.display_name, sp.active, "
    "sp.created_by_user_id, sp.created_at, sp.updated_at"
)
_CUSTOMER_COLUMNS = (
    "id, seller_portfolio_id, customer_code, customer_store, customer_name, created_at"
)
_MEMBER_COLUMNS = "user_id, role"


class PostgresSellerPortfolioRepository(PluginBaseRepository, SellerPortfolioRepositoryPort):
    """Carteira vendedor ↔ clientes no schema commercial (membership N:N)."""

    def get_by_id(self, portfolio_id: str) -> SellerPortfolio | None:
        row = self.fetch_one(
            f"SELECT {_PORTFOLIO_COLUMNS} FROM commercial.seller_portfolios WHERE id = %s",
            (portfolio_id,),
        )
        return self._hydrate(row)

    def get_by_user_id(self, user_id: str) -> SellerPortfolio | None:
        row = self.fetch_one(
            f"""
            SELECT {_PORTFOLIO_COLUMNS_SP}
              FROM commercial.seller_portfolios sp
              INNER JOIN commercial.seller_portfolio_members m
                ON m.seller_portfolio_id = sp.id
             WHERE m.user_id = %s
             ORDER BY sp.active DESC, sp.display_name ASC
             LIMIT 1
            """,
            (user_id,),
        )
        return self._hydrate(row)

    def list_by_user_id(self, user_id: str, *, active_only: bool = True) -> list[SellerPortfolio]:
        where_active = "AND sp.active = TRUE" if active_only else ""
        rows = self.fetch_all(
            f"""
            SELECT {_PORTFOLIO_COLUMNS_SP}
              FROM commercial.seller_portfolios sp
              INNER JOIN commercial.seller_portfolio_members m
                ON m.seller_portfolio_id = sp.id
             WHERE m.user_id = %s
               {where_active}
             ORDER BY sp.active DESC, sp.display_name ASC
            """,
            (user_id,),
        )
        portfolios = [
            portfolio for row in rows if (portfolio := self._hydrate(row)) is not None
        ]
        if portfolios:
            return portfolios
        where_owner_active = "AND active = TRUE" if active_only else ""
        owner_rows = self.fetch_all(
            f"""
            SELECT {_PORTFOLIO_COLUMNS}
              FROM commercial.seller_portfolios
             WHERE user_id = %s
               {where_owner_active}
             ORDER BY active DESC, display_name ASC
            """,
            (user_id,),
        )
        return [
            portfolio
            for row in owner_rows
            if (portfolio := self._hydrate(row)) is not None
        ]

    def list_member_user_ids(self, *, active_portfolios_only: bool = True) -> list[str]:
        where_active = "WHERE sp.active = TRUE" if active_portfolios_only else ""
        rows = self.fetch_all(
            f"""
            SELECT DISTINCT m.user_id
              FROM commercial.seller_portfolio_members m
              INNER JOIN commercial.seller_portfolios sp
                ON sp.id = m.seller_portfolio_id
             {where_active}
             ORDER BY m.user_id ASC
            """
        )
        return [str(row["user_id"]) for row in rows if row.get("user_id")]

    def list_portfolios(self, *, active_only: bool = False) -> list[SellerPortfolio]:
        if active_only:
            rows = self.fetch_all(
                f"""
                SELECT {_PORTFOLIO_COLUMNS}
                  FROM commercial.seller_portfolios
                 WHERE active = TRUE
                 ORDER BY display_name ASC
                """
            )
        else:
            rows = self.fetch_all(
                f"""
                SELECT {_PORTFOLIO_COLUMNS}
                  FROM commercial.seller_portfolios
                 ORDER BY active DESC, display_name ASC
                """
            )
        return [portfolio for row in rows if (portfolio := self._hydrate(row)) is not None]

    def create_portfolio(
        self,
        *,
        user_id: str,
        display_name: str,
        created_by_user_id: str | None,
        member_user_ids: Sequence[str] | None = None,
    ) -> SellerPortfolio:
        owner_id = str(user_id).strip()
        extra_members = [
            str(uid).strip()
            for uid in (member_user_ids or ())
            if str(uid).strip() and str(uid).strip() != owner_id
        ]
        # Deduplicate while preserving order.
        seen: set[str] = set()
        unique_extras: list[str] = []
        for uid in extra_members:
            if uid not in seen:
                seen.add(uid)
                unique_extras.append(uid)
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO commercial.seller_portfolios (
                        user_id, display_name, created_by_user_id
                    ) VALUES (%s, %s, %s)
                    RETURNING {_PORTFOLIO_COLUMNS}
                    """,
                    (owner_id, display_name, created_by_user_id),
                )
                row = cursor.fetchone()
                if row is None:
                    raise RuntimeError("Falha ao criar carteira de vendedor.")
                portfolio_row = dict(row)
                portfolio_id = str(portfolio_row["id"])
                cursor.execute(
                    """
                    INSERT INTO commercial.seller_portfolio_members (
                        seller_portfolio_id, user_id, role
                    ) VALUES (%s, %s, 'owner')
                    """,
                    (portfolio_id, owner_id),
                )
                for member_id in unique_extras:
                    cursor.execute(
                        """
                        INSERT INTO commercial.seller_portfolio_members (
                            seller_portfolio_id, user_id, role
                        ) VALUES (%s, %s, 'member')
                        ON CONFLICT (seller_portfolio_id, user_id) DO NOTHING
                        """,
                        (portfolio_id, member_id),
                    )
            self.commit()
        except Exception:
            self.rollback()
            raise
        portfolio = self._hydrate(portfolio_row)
        if portfolio is None:
            raise RuntimeError("Falha ao criar carteira de vendedor.")
        return portfolio

    def update_portfolio(
        self,
        *,
        portfolio_id: str,
        display_name: str | None = None,
        active: bool | None = None,
    ) -> SellerPortfolio | None:
        current = self.fetch_one(
            f"SELECT {_PORTFOLIO_COLUMNS} FROM commercial.seller_portfolios WHERE id = %s",
            (portfolio_id,),
        )
        if current is None:
            return None
        next_name = display_name if display_name is not None else current["display_name"]
        next_active = active if active is not None else current["active"]
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.seller_portfolios
               SET display_name = %s,
                   active = %s,
                   updated_at = NOW()
             WHERE id = %s
         RETURNING {_PORTFOLIO_COLUMNS}
            """,
            (next_name, next_active, portfolio_id),
        )
        return self._hydrate(row)

    def deactivate_portfolio(self, portfolio_id: str) -> SellerPortfolio | None:
        return self.update_portfolio(portfolio_id=portfolio_id, active=False)

    def delete_portfolio(self, portfolio_id: str) -> SellerPortfolio | None:
        current = self.get_by_id(portfolio_id)
        if current is None:
            return None
        deleted = self.execute_returning_one(
            """
            DELETE FROM commercial.seller_portfolios
             WHERE id = %s
         RETURNING id
            """,
            (portfolio_id,),
        )
        if deleted is None:
            return None
        return current

    def replace_customers(
        self,
        *,
        portfolio_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> SellerPortfolio | None:
        if self.fetch_one(
            "SELECT id FROM commercial.seller_portfolios WHERE id = %s",
            (portfolio_id,),
        ) is None:
            return None
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM commercial.seller_customers WHERE seller_portfolio_id = %s",
                    (portfolio_id,),
                )
                for customer in customers:
                    cursor.execute(
                        """
                        INSERT INTO commercial.seller_customers (
                            seller_portfolio_id, customer_code, customer_store, customer_name
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (seller_portfolio_id, customer_code, customer_store) DO UPDATE
                           SET customer_name = EXCLUDED.customer_name
                        """,
                        (
                            portfolio_id,
                            customer.customer_code,
                            customer.customer_store,
                            customer.customer_name,
                        ),
                    )
                cursor.execute(
                    """
                    UPDATE commercial.seller_portfolios
                       SET updated_at = NOW()
                     WHERE id = %s
                    """,
                    (portfolio_id,),
                )
            self.commit()
        except Exception:
            self.rollback()
            raise
        return self.get_by_id(portfolio_id)

    def add_customer(
        self,
        *,
        portfolio_id: str,
        customer: SellerCustomerAssignment,
    ) -> SellerPortfolio | None:
        if self.fetch_one(
            "SELECT id FROM commercial.seller_portfolios WHERE id = %s",
            (portfolio_id,),
        ) is None:
            return None
        self.execute(
            """
            INSERT INTO commercial.seller_customers (
                seller_portfolio_id, customer_code, customer_store, customer_name
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (seller_portfolio_id, customer_code, customer_store) DO UPDATE
               SET customer_name = COALESCE(
                   EXCLUDED.customer_name,
                   commercial.seller_customers.customer_name
               )
            """,
            (
                portfolio_id,
                customer.customer_code,
                customer.customer_store,
                customer.customer_name,
            ),
        )
        self.execute(
            """
            UPDATE commercial.seller_portfolios
               SET updated_at = NOW()
             WHERE id = %s
            """,
            (portfolio_id,),
        )
        return self.get_by_id(portfolio_id)

    def remove_customer(
        self,
        *,
        portfolio_id: str,
        customer_code: str,
        customer_store: str,
    ) -> SellerPortfolio | None:
        if self.fetch_one(
            "SELECT id FROM commercial.seller_portfolios WHERE id = %s",
            (portfolio_id,),
        ) is None:
            return None
        self.execute(
            """
            DELETE FROM commercial.seller_customers
             WHERE seller_portfolio_id = %s
               AND customer_code = %s
               AND customer_store = %s
            """,
            (portfolio_id, customer_code, customer_store),
        )
        self.execute(
            """
            UPDATE commercial.seller_portfolios
               SET updated_at = NOW()
             WHERE id = %s
            """,
            (portfolio_id,),
        )
        return self.get_by_id(portfolio_id)

    def transfer_customers(
        self,
        *,
        source_portfolio_id: str,
        target_portfolio_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> tuple[SellerPortfolio, SellerPortfolio] | None:
        source = self.fetch_one(
            "SELECT id FROM commercial.seller_portfolios WHERE id = %s",
            (source_portfolio_id,),
        )
        target = self.fetch_one(
            "SELECT id FROM commercial.seller_portfolios WHERE id = %s",
            (target_portfolio_id,),
        )
        if source is None or target is None:
            return None
        try:
            with self.connection.cursor() as cursor:
                for customer in customers:
                    cursor.execute(
                        """
                        SELECT customer_name
                          FROM commercial.seller_customers
                         WHERE seller_portfolio_id = %s
                           AND customer_code = %s
                           AND customer_store = %s
                        """,
                        (
                            source_portfolio_id,
                            customer.customer_code,
                            customer.customer_store,
                        ),
                    )
                    row = cursor.fetchone()
                    if row is None:
                        raise ValueError(
                            "Cliente "
                            f"{customer.customer_code}/{customer.customer_store} "
                            "não pertence à carteira de origem."
                        )
                    source_name = row.get("customer_name") if isinstance(row, dict) else None
                    name = customer.customer_name or (
                        str(source_name).strip() if source_name else None
                    )
                    cursor.execute(
                        """
                        INSERT INTO commercial.seller_customers (
                            seller_portfolio_id, customer_code, customer_store, customer_name
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (seller_portfolio_id, customer_code, customer_store) DO UPDATE
                           SET customer_name = COALESCE(
                               EXCLUDED.customer_name,
                               commercial.seller_customers.customer_name
                           )
                        """,
                        (
                            target_portfolio_id,
                            customer.customer_code,
                            customer.customer_store,
                            name,
                        ),
                    )
                    cursor.execute(
                        """
                        DELETE FROM commercial.seller_customers
                         WHERE seller_portfolio_id = %s
                           AND customer_code = %s
                           AND customer_store = %s
                        """,
                        (
                            source_portfolio_id,
                            customer.customer_code,
                            customer.customer_store,
                        ),
                    )
                cursor.execute(
                    """
                    UPDATE commercial.seller_portfolios
                       SET updated_at = NOW()
                     WHERE id IN (%s, %s)
                    """,
                    (source_portfolio_id, target_portfolio_id),
                )
            self.commit()
        except Exception:
            self.rollback()
            raise
        source_portfolio = self.get_by_id(source_portfolio_id)
        target_portfolio = self.get_by_id(target_portfolio_id)
        if source_portfolio is None or target_portfolio is None:
            return None
        return source_portfolio, target_portfolio

    def replace_members(
        self,
        *,
        portfolio_id: str,
        members: Sequence[SellerPortfolioMember],
    ) -> SellerPortfolio | None:
        if self.fetch_one(
            "SELECT id FROM commercial.seller_portfolios WHERE id = %s",
            (portfolio_id,),
        ) is None:
            return None
        owners = [m for m in members if m.role == "owner"]
        if len(owners) != 1:
            raise ValueError("A carteira deve ter exatamente um owner.")
        owner_user_id = str(owners[0].user_id).strip()
        if not owner_user_id:
            raise ValueError("Owner inválido.")
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM commercial.seller_portfolio_members
                     WHERE seller_portfolio_id = %s
                    """,
                    (portfolio_id,),
                )
                for member in members:
                    uid = str(member.user_id).strip()
                    role = "owner" if member.role == "owner" else "member"
                    if not uid:
                        continue
                    cursor.execute(
                        """
                        INSERT INTO commercial.seller_portfolio_members (
                            seller_portfolio_id, user_id, role
                        ) VALUES (%s, %s, %s)
                        ON CONFLICT (seller_portfolio_id, user_id) DO UPDATE
                           SET role = EXCLUDED.role
                        """,
                        (portfolio_id, uid, role),
                    )
                cursor.execute(
                    """
                    UPDATE commercial.seller_portfolios
                       SET user_id = %s,
                           updated_at = NOW()
                     WHERE id = %s
                    """,
                    (owner_user_id, portfolio_id),
                )
            self.commit()
        except Exception:
            self.rollback()
            raise
        return self.get_by_id(portfolio_id)

    def add_member(
        self,
        *,
        portfolio_id: str,
        user_id: str,
        role: str = "member",
    ) -> SellerPortfolio | None:
        if self.fetch_one(
            "SELECT id FROM commercial.seller_portfolios WHERE id = %s",
            (portfolio_id,),
        ) is None:
            return None
        next_role = "owner" if role == "owner" else "member"
        uid = str(user_id).strip()
        if not uid:
            return self.get_by_id(portfolio_id)
        if next_role == "owner":
            return self.set_owner(portfolio_id=portfolio_id, user_id=uid)
        self.execute(
            """
            INSERT INTO commercial.seller_portfolio_members (
                seller_portfolio_id, user_id, role
            ) VALUES (%s, %s, %s)
            ON CONFLICT (seller_portfolio_id, user_id) DO UPDATE
               SET role = EXCLUDED.role
             WHERE commercial.seller_portfolio_members.role <> 'owner'
            """,
            (portfolio_id, uid, next_role),
        )
        self.execute(
            """
            UPDATE commercial.seller_portfolios
               SET updated_at = NOW()
             WHERE id = %s
            """,
            (portfolio_id,),
        )
        return self.get_by_id(portfolio_id)

    def remove_member(
        self,
        *,
        portfolio_id: str,
        user_id: str,
    ) -> SellerPortfolio | None:
        if self.fetch_one(
            "SELECT id FROM commercial.seller_portfolios WHERE id = %s",
            (portfolio_id,),
        ) is None:
            return None
        # Não remove o único owner (índice parcial garante no máx. um owner).
        self.execute(
            """
            DELETE FROM commercial.seller_portfolio_members
             WHERE seller_portfolio_id = %s
               AND user_id = %s
               AND role <> 'owner'
            """,
            (portfolio_id, str(user_id).strip()),
        )
        self.execute(
            """
            UPDATE commercial.seller_portfolios
               SET updated_at = NOW()
             WHERE id = %s
            """,
            (portfolio_id,),
        )
        return self.get_by_id(portfolio_id)

    def set_owner(
        self,
        *,
        portfolio_id: str,
        user_id: str,
    ) -> SellerPortfolio | None:
        if self.fetch_one(
            "SELECT id FROM commercial.seller_portfolios WHERE id = %s",
            (portfolio_id,),
        ) is None:
            return None
        owner_id = str(user_id).strip()
        if not owner_id:
            raise ValueError("Owner inválido.")
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE commercial.seller_portfolio_members
                       SET role = 'member'
                     WHERE seller_portfolio_id = %s
                       AND role = 'owner'
                    """,
                    (portfolio_id,),
                )
                cursor.execute(
                    """
                    INSERT INTO commercial.seller_portfolio_members (
                        seller_portfolio_id, user_id, role
                    ) VALUES (%s, %s, 'owner')
                    ON CONFLICT (seller_portfolio_id, user_id) DO UPDATE
                       SET role = 'owner'
                    """,
                    (portfolio_id, owner_id),
                )
                cursor.execute(
                    """
                    UPDATE commercial.seller_portfolios
                       SET user_id = %s,
                           updated_at = NOW()
                     WHERE id = %s
                    """,
                    (owner_id, portfolio_id),
                )
            self.commit()
        except Exception:
            self.rollback()
            raise
        return self.get_by_id(portfolio_id)

    def _list_customers(self, portfolio_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"""
            SELECT {_CUSTOMER_COLUMNS}
              FROM commercial.seller_customers
             WHERE seller_portfolio_id = %s
             ORDER BY customer_name NULLS LAST, customer_code, customer_store
            """,
            (portfolio_id,),
        )

    def _list_members(self, portfolio_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"""
            SELECT {_MEMBER_COLUMNS}
              FROM commercial.seller_portfolio_members
             WHERE seller_portfolio_id = %s
             ORDER BY CASE WHEN role = 'owner' THEN 0 ELSE 1 END, user_id ASC
            """,
            (portfolio_id,),
        )

    def _hydrate(self, row: dict[str, Any] | None) -> SellerPortfolio | None:
        if not row:
            return None
        portfolio_id = str(row["id"])
        customers = tuple(
            SellerCustomerAssignment(
                customer_code=str(item["customer_code"]),
                customer_store=str(item["customer_store"]),
                customer_name=(
                    str(item["customer_name"]).strip()
                    if item.get("customer_name")
                    else None
                ),
            )
            for item in self._list_customers(portfolio_id)
        )
        members = tuple(
            SellerPortfolioMember(
                user_id=str(item["user_id"]),
                role=str(item["role"]),
            )
            for item in self._list_members(portfolio_id)
        )
        return SellerPortfolio(
            id=portfolio_id,
            user_id=str(row["user_id"]),
            display_name=str(row["display_name"]),
            active=bool(row.get("active", True)),
            customers=customers,
            members=members,
        )
