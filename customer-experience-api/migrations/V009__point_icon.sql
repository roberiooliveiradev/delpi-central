-- Ícone Lucide (kebab-case) como alternativa à imagem ilustrativa.
-- Mutuamente exclusivo na UI com point_image_filename.

ALTER TABLE customer_experience.form_pages
    ADD COLUMN IF NOT EXISTS point_icon TEXT NULL;

ALTER TABLE customer_experience.form_questions
    ADD COLUMN IF NOT EXISTS point_icon TEXT NULL;
