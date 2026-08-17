-- Planejamento Orçamentário — ícone personalizado do centro de custo (catálogo Lucide).
-- Incremental: não recria schema; preserva dados existentes.

ALTER TABLE planejamento_orcamentario.org_cost_centers
    ADD COLUMN IF NOT EXISTS icon_key VARCHAR(64);

COMMENT ON COLUMN planejamento_orcamentario.org_cost_centers.icon_key IS
    'Chave do ícone Lucide (ex.: users, laptop). NULL = padrão Building2 no MFE.';
