-- Membership N:N — usuários compartilham a mesma carteira (owner + members).
-- Não editar V001; backfill do owner atual e remove UNIQUE(user_id) da pai.

CREATE TABLE IF NOT EXISTS commercial.seller_portfolio_members (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_portfolio_id  UUID NOT NULL
        REFERENCES commercial.seller_portfolios (id) ON DELETE CASCADE,
    user_id              TEXT NOT NULL,
    role                 TEXT NOT NULL DEFAULT 'member'
        CHECK (role IN ('owner', 'member')),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (seller_portfolio_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_commercial_seller_portfolio_members_user
    ON commercial.seller_portfolio_members (user_id);

CREATE INDEX IF NOT EXISTS idx_commercial_seller_portfolio_members_portfolio
    ON commercial.seller_portfolio_members (seller_portfolio_id);

-- Um responsável por carteira.
CREATE UNIQUE INDEX IF NOT EXISTS uq_commercial_seller_portfolio_one_owner
    ON commercial.seller_portfolio_members (seller_portfolio_id)
    WHERE role = 'owner';

-- Backfill: dono legado vira owner.
INSERT INTO commercial.seller_portfolio_members (seller_portfolio_id, user_id, role)
SELECT id, user_id, 'owner'
  FROM commercial.seller_portfolios
 WHERE user_id IS NOT NULL
   AND TRIM(user_id) <> ''
ON CONFLICT (seller_portfolio_id, user_id) DO NOTHING;

-- Permite o mesmo user_id como espelho de owner em carteiras distintas.
ALTER TABLE commercial.seller_portfolios
    DROP CONSTRAINT IF EXISTS seller_portfolios_user_id_key;
