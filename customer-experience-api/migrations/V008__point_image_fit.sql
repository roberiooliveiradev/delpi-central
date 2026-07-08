-- Modo de exibição da imagem ilustrativa (página e pergunta).
-- fixed = tamanho natural
-- scale = preenche a área (cover)
-- tile  = mosaico

ALTER TABLE customer_experience.form_pages
    ADD COLUMN IF NOT EXISTS point_image_fit TEXT NOT NULL DEFAULT 'scale';

ALTER TABLE customer_experience.form_pages
    DROP CONSTRAINT IF EXISTS form_pages_point_image_fit_check;

ALTER TABLE customer_experience.form_pages
    ADD CONSTRAINT form_pages_point_image_fit_check
    CHECK (point_image_fit IN ('fixed', 'scale', 'tile'));

ALTER TABLE customer_experience.form_questions
    ADD COLUMN IF NOT EXISTS point_image_fit TEXT NOT NULL DEFAULT 'scale';

ALTER TABLE customer_experience.form_questions
    DROP CONSTRAINT IF EXISTS form_questions_point_image_fit_check;

ALTER TABLE customer_experience.form_questions
    ADD CONSTRAINT form_questions_point_image_fit_check
    CHECK (point_image_fit IN ('fixed', 'scale', 'tile'));
