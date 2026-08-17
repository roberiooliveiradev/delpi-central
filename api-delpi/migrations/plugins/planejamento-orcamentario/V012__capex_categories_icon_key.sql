-- Planejamento Orçamentário — ícone Lucide nas categorias CAPEX.
-- Incremental: não recria schema; preserva dados existentes.

ALTER TABLE planejamento_orcamentario.capex_categories
    ADD COLUMN IF NOT EXISTS icon_key VARCHAR(64);

COMMENT ON COLUMN planejamento_orcamentario.capex_categories.icon_key IS
    'Chave do ícone Lucide (ex.: wrench, truck). NULL = padrão Tags no MFE.';
