from __future__ import annotations

from typing import Any, Sequence

from app.domain.entities.pedidos_venda_abertos.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)
from app.domain.ports.pedidos_venda_abertos.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_SELLER_COLUMNS = (
    "id, user_id, display_name, active, created_by_user_id, created_at, updated_at"
)
_CUSTOMER_COLUMNS = "id, seller_id, customer_code, customer_store, customer_name, created_at"


class PostgresSellerPortfolioRepository(PluginBaseRepository, SellerPortfolioRepositoryPort):
    """Carteira vendedor ↔ clientes no schema pedidos_venda_abertos."""

    def get_by_id(self, seller_id: str) -> SellerPortfolio | None:
        row = self.fetch_one(
            f"SELECT {_SELLER_COLUMNS} FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (seller_id,),
        )
        return self._hydrate(row)

    def get_by_user_id(self, user_id: str) -> SellerPortfolio | None:
        row = self.fetch_one(
            f"""
            SELECT {_SELLER_COLUMNS}
            FROM pedidos_venda_abertos.sellers
            WHERE user_id = %s
            """,
            (user_id,),
        )
        return self._hydrate(row)

    def list_by_user_id(
        self, user_id: str, *, active_only: bool = True
    ) -> list[SellerPortfolio]:
        portfolio = self.get_by_user_id(user_id)
        if portfolio is None:
            return []
        if active_only and not portfolio.active:
            return []
        return [portfolio]

    def list_sellers(self, *, active_only: bool = False) -> list[SellerPortfolio]:
        if active_only:
            rows = self.fetch_all(
                f"""
                SELECT {_SELLER_COLUMNS}
                FROM pedidos_venda_abertos.sellers
                WHERE active = TRUE
                ORDER BY display_name ASC
                """
            )
        else:
            rows = self.fetch_all(
                f"""
                SELECT {_SELLER_COLUMNS}
                FROM pedidos_venda_abertos.sellers
                ORDER BY active DESC, display_name ASC
                """
            )
        return [portfolio for row in rows if (portfolio := self._hydrate(row)) is not None]

    def create_seller(
        self,
        *,
        user_id: str,
        display_name: str,
        created_by_user_id: str | None,
    ) -> SellerPortfolio:
        row = self.execute_returning_one(
            f"""
            INSERT INTO pedidos_venda_abertos.sellers (
                user_id, display_name, created_by_user_id
            ) VALUES (%s, %s, %s)
            RETURNING {_SELLER_COLUMNS}
            """,
            (user_id, display_name, created_by_user_id),
        )
        portfolio = self._hydrate(row)
        if portfolio is None:
            raise RuntimeError("Falha ao criar vendedor na carteira.")
        return portfolio

    def update_seller(
        self,
        *,
        seller_id: str,
        display_name: str | None = None,
        active: bool | None = None,
    ) -> SellerPortfolio | None:
        current = self.fetch_one(
            f"SELECT {_SELLER_COLUMNS} FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (seller_id,),
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
         RETURNING {_SELLER_COLUMNS}
            """,
            (next_name, next_active, seller_id),
        )
        return self._hydrate(row)

    def deactivate_seller(self, seller_id: str) -> SellerPortfolio | None:
        return self.update_seller(seller_id=seller_id, active=False)

    def replace_customers(
        self,
        *,
        seller_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> SellerPortfolio | None:
        if self.fetch_one(
            "SELECT id FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (seller_id,),
        ) is None:
            return None
        try:
            with self.db():
                with self.connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM pedidos_venda_abertos.seller_customers WHERE seller_id = %s",
                        (seller_id,),
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
                                seller_id,
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
                        (seller_id,),
                    )
                self.commit()
        except Exception:
            self.rollback()
            raise
        return self.get_by_id(seller_id)

    def add_customer(
        self,
        *,
        seller_id: str,
        customer: SellerCustomerAssignment,
    ) -> SellerPortfolio | None:
        if self.fetch_one(
            "SELECT id FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (seller_id,),
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
                seller_id,
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
            (seller_id,),
        )
        return self.get_by_id(seller_id)

    def remove_customer(
        self,
        *,
        seller_id: str,
        customer_code: str,
        customer_store: str,
    ) -> SellerPortfolio | None:
        if self.fetch_one(
            "SELECT id FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (seller_id,),
        ) is None:
            return None
        self.execute(
            """
            DELETE FROM pedidos_venda_abertos.seller_customers
             WHERE seller_id = %s
               AND customer_code = %s
               AND customer_store = %s
            """,
            (seller_id, customer_code, customer_store),
        )
        self.execute(
            """
            UPDATE pedidos_venda_abertos.sellers
               SET updated_at = NOW()
             WHERE id = %s
            """,
            (seller_id,),
        )
        return self.get_by_id(seller_id)

    def transfer_customers(
        self,
        *,
        source_seller_id: str,
        target_seller_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> tuple[SellerPortfolio, SellerPortfolio] | None:
        source = self.fetch_one(
            "SELECT id FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (source_seller_id,),
        )
        target = self.fetch_one(
            "SELECT id FROM pedidos_venda_abertos.sellers WHERE id = %s",
            (target_seller_id,),
        )
        if source is None or target is None:
            return None
        try:
            with self.db():
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
                                source_seller_id,
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
                                target_seller_id,
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
                                source_seller_id,
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
                        (source_seller_id, target_seller_id),
                    )
                self.commit()
        except Exception:
            self.rollback()
            raise
        source_portfolio = self.get_by_id(source_seller_id)
        target_portfolio = self.get_by_id(target_seller_id)
        if source_portfolio is None or target_portfolio is None:
            return None
        return source_portfolio, target_portfolio

    def _list_customers(self, seller_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"""
            SELECT {_CUSTOMER_COLUMNS}
            FROM pedidos_venda_abertos.seller_customers
            WHERE seller_id = %s
            ORDER BY customer_name NULLS LAST, customer_code, customer_store
            """,
            (seller_id,),
        )

    def _hydrate(self, row: dict[str, Any] | None) -> SellerPortfolio | None:
        if not row:
            return None
        seller_id = str(row["id"])
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
            for item in self._list_customers(seller_id)
        )
        return SellerPortfolio(
            id=seller_id,
            user_id=str(row["user_id"]),
            display_name=str(row["display_name"]),
            active=bool(row.get("active", True)),
            customers=customers,
        )
