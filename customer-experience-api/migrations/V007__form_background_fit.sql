-- Modo de exibição da imagem de fundo do formulário.
-- fixed  = tamanho natural (px)
-- scale  = preenche a viewport (cover) — padrão atual
-- tile   = mosaico (repeat)

ALTER TABLE customer_experience.forms
    ADD COLUMN IF NOT EXISTS background_fit TEXT NOT NULL DEFAULT 'scale';

ALTER TABLE customer_experience.forms
    DROP CONSTRAINT IF EXISTS forms_background_fit_check;

ALTER TABLE customer_experience.forms
    ADD CONSTRAINT forms_background_fit_check
    CHECK (background_fit IN ('fixed', 'scale', 'tile'));
