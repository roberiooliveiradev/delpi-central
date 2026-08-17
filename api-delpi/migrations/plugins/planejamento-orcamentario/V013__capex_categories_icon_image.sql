-- Planejamento Orçamentário — imagem customizada de ícone nas categorias CAPEX.
-- Binário em PLANEJAMENTO_ORCAMENTARIO_UPLOAD_DIR/category-icons/{id}/…

ALTER TABLE planejamento_orcamentario.capex_categories
    ADD COLUMN IF NOT EXISTS icon_image_key VARCHAR(120);

ALTER TABLE planejamento_orcamentario.capex_categories
    ADD COLUMN IF NOT EXISTS icon_image_mime VARCHAR(80);

COMMENT ON COLUMN planejamento_orcamentario.capex_categories.icon_image_key IS
    'Nome do arquivo de ícone customizado sob category-icons/{id}/. NULL = só Lucide.';
COMMENT ON COLUMN planejamento_orcamentario.capex_categories.icon_image_mime IS
    'MIME da imagem customizada (image/png, image/jpeg, image/webp, image/gif).';
