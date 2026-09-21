-- Schema only. Does not UPDATE existing seller_customers rows.
-- Existing rows keep customer_center NULL (pair fallback) until corrected in production.

ALTER TABLE commercial.seller_customers
    ADD COLUMN IF NOT EXISTS customer_center TEXT;

ALTER TABLE commercial.seller_customers
    DROP CONSTRAINT IF EXISTS seller_customers_seller_portfolio_id_customer_code_customer_store_key;

ALTER TABLE commercial.seller_customers
    DROP CONSTRAINT IF EXISTS seller_customers_seller_portfolio_id_customer_code_customer_key;

ALTER TABLE commercial.seller_customers
    DROP CONSTRAINT IF EXISTS seller_customers_seller_portfolio_id_customer_code_customer_sto;

CREATE UNIQUE INDEX IF NOT EXISTS uq_seller_customers_code_store_center
    ON commercial.seller_customers (
        seller_portfolio_id,
        customer_code,
        customer_store,
        COALESCE(customer_center, '')
    );
