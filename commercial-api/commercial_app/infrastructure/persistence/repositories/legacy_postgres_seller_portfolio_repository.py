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

_LEGACY_PORTFOLIO_COLUMNS = (
    "id, user_id, display_name, active, created_by_user_id, created_at, updated_at"
)
_LEGACY_CUSTOMER_COLUMNS = (
    "id, seller_id, customer_code, customer_store, customer_name, created_at"
)
_MEMBERSHIP_NN_REQUIRED = (
    "Membership N:N exige COMMERCIAL_PORTFOLIO_SOURCE=commercial"
)


class LegacyPostgresSellerPortfolioRepository(
    PluginBaseRepository,
    SellerPortfolioRepositoryPort,
):
    """Dual-read: schema legado pedidos_venda_abertos.sellers (1:1)."""

    def get_by_id(self, portfolio_id: str) -> SellerPortfolio | None:
        row = self.fetch_one(
            f"SELECT {_LEGACY_PORTFOLIO_COLUMNS} FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (portfolio_id,),
        )
        return self._hydrate(row)

    def get_by_user_id(self, user_id: str) -> SellerPortfolio | None:
        row = self.fetch_one(
            f"""
            SELECT {_LEGACY_PORTFOLIO_COLUMNS}
              FROM pedidos_venda_abertos.sellers
             WHERE user_id = %s
            """,
            (user_id,),
        )
        return self._hydrate(row)

    def list_by_user_id(self, user_id: str, *, active_only: bool = True) -> list[SellerPortfolio]:
        portfolio = self.get_by_user_id(user_id)
        if portfolio is None:
            return []
        if active_only and not portfolio.active:
            return []
        return [portfolio]

    def list_member_user_ids(self, *, active_portfolios_only: bool = True) -> list[str]:
        if active_portfolios_only:
            rows = self.fetch_all(
                """
                SELECT DISTINCT user_id
                  FROM pedidos_venda_abertos.sellers
                 WHERE active = TRUE
                   AND user_id IS NOT NULL
                   AND TRIM(user_id) <> ''
                 ORDER BY user_id ASC
                """
            )
        else:
            rows = self.fetch_all(
                """
                SELECT DISTINCT user_id
                  FROM pedidos_venda_abertos.sellers
                 WHERE user_id IS NOT NULL
                   AND TRIM(user_id) <> ''
                 ORDER BY user_id ASC
                """
            )
        return [str(row["user_id"]) for row in rows if row.get("user_id")]

    def list_portfolios(self, *, active_only: bool = False) -> list[SellerPortfolio]:
        query = f"""
            SELECT {_LEGACY_PORTFOLIO_COLUMNS}
              FROM pedidos_venda_abertos.sellers
        """
        if active_only:
            query += " WHERE active = TRUE ORDER BY display_name ASC"
        else:
            query += " ORDER BY active DESC, display_name ASC"
        rows = self.fetch_all(query)
        return [portfolio for row in rows if (portfolio := self._hydrate(row)) is not None]

    def create_portfolio(
        self,
        *,
        user_id: str,
        display_name: str,
        created_by_user_id: str | None,
        member_user_ids: Sequence[str] | None = None,
    ) -> SellerPortfolio:
        # Legado 1:1 — member_user_ids extras são ignorados; user_id é o owner.
        _ = member_user_ids
        row = self.execute_returning_one(
            f"""
            INSERT INTO pedidos_venda_abertos.sellers (
                user_id, display_name, created_by_user_id
            ) VALUES (%s, %s, %s)
            RETURNING {_LEGACY_PORTFOLIO_COLUMNS}
            """,
            (user_id, display_name, created_by_user_id),
        )
        portfolio = self._hydrate(row)
        if portfolio is None:
            raise RuntimeError("Falha ao criar vendedor na carteira legada.")
        return portfolio

    def update_portfolio(
        self,
        *,
        portfolio_id: str,
        display_name: str | None = None,
        active: bool | None = None,
    ) -> SellerPortfolio | None:
        current = self.fetch_one(
            f"SELECT {_LEGACY_PORTFOLIO_COLUMNS} FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (portfolio_id,),
        )
        if current is None:
            return None
        next_name = display_name if display_name is not None else current["display_name"]
        next_active = active if active is not None else current["active"]
        row = self.execute_returning_one(
            f"""
            UPDATE pedidos_venda_abertos.sellers
               SET display_name = %s,
                   active = %s,
                   updated_at = NOW()
             WHERE id = %s
         RETURNING {_LEGACY_PORTFOLIO_COLUMNS}
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
            DELETE FROM pedidos_venda_abertos.sellers
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
            "SELECT id FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (portfolio_id,),
        ) is None:
            return None
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM pedidos_venda_abertos.seller_customers WHERE seller_id = %s",
                    (portfolio_id,),
                )
                for customer in customers:
                    cursor.execute(
                        """
                        INSERT INTO pedidos_venda_abertos.seller_customers (
                            seller_id, customer_code, customer_store, customer_name
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (seller_id, customer_code, customer_store) DO UPDATE
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
                    UPDATE pedidos_venda_abertos.sellers
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
            "SELECT id FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (portfolio_id,),
        ) is None:
            return None
        self.execute(
            """
            INSERT INTO pedidos_venda_abertos.seller_customers (
                seller_id, customer_code, customer_store, customer_name
            ) VALUES (%s, %s, %s, %s)
            ON CONFLICT (seller_id, customer_code, customer_store) DO UPDATE
               SET customer_name = COALESCE(
                   EXCLUDED.customer_name,
                   pedidos_venda_abertos.seller_customers.customer_name
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
            UPDATE pedidos_venda_abertos.sellers
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
            "SELECT id FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (portfolio_id,),
        ) is None:
            return None
        self.execute(
            """
            DELETE FROM pedidos_venda_abertos.seller_customers
             WHERE seller_id = %s
               AND customer_code = %s
               AND customer_store = %s
            """,
            (portfolio_id, customer_code, customer_store),
        )
        self.execute(
            """
            UPDATE pedidos_venda_abertos.sellers
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
            "SELECT id FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (source_portfolio_id,),
        )
        target = self.fetch_one(
            "SELECT id FROM pedidos_venda_abertos.sellers WHERE id = %s",
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
                          FROM pedidos_venda_abertos.seller_customers
                         WHERE seller_id = %s
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
                        INSERT INTO pedidos_venda_abertos.seller_customers (
                            seller_id, customer_code, customer_store, customer_name
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (seller_id, customer_code, customer_store) DO UPDATE
                           SET customer_name = COALESCE(
                               EXCLUDED.customer_name,
                               pedidos_venda_abertos.seller_customers.customer_name
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
                        DELETE FROM pedidos_venda_abertos.seller_customers
                         WHERE seller_id = %s
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
                    UPDATE pedidos_venda_abertos.sellers
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
        raise NotImplementedError(_MEMBERSHIP_NN_REQUIRED)

    def add_member(
        self,
        *,
        portfolio_id: str,
        user_id: str,
        role: str = "member",
    ) -> SellerPortfolio | None:
        raise NotImplementedError(_MEMBERSHIP_NN_REQUIRED)

    def remove_member(
        self,
        *,
        portfolio_id: str,
        user_id: str,
    ) -> SellerPortfolio | None:
        raise NotImplementedError(_MEMBERSHIP_NN_REQUIRED)

    def set_owner(
        self,
        *,
        portfolio_id: str,
        user_id: str,
    ) -> SellerPortfolio | None:
        raise NotImplementedError(_MEMBERSHIP_NN_REQUIRED)

    def _list_customers(self, portfolio_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"""
            SELECT {_LEGACY_CUSTOMER_COLUMNS}
              FROM pedidos_venda_abertos.seller_customers
             WHERE seller_id = %s
             ORDER BY customer_name NULLS LAST, customer_code, customer_store
            """,
            (portfolio_id,),
        )

    def _hydrate(self, row: dict[str, Any] | None) -> SellerPortfolio | None:
        if not row:
            return None
        portfolio_id = str(row["id"])
        user_id = str(row["user_id"])
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
        members = (SellerPortfolioMember(user_id=user_id, role="owner"),)
        return SellerPortfolio(
            id=portfolio_id,
            user_id=user_id,
            display_name=str(row["display_name"]),
            active=bool(row.get("active", True)),
            customers=customers,
            members=members,
        )
