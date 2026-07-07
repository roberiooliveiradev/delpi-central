-- Categorias múltiplas por kaizen (multi-seleção + categorias customizadas).

ALTER TABLE quality.kaizens
    ADD COLUMN IF NOT EXISTS categories TEXT[] NOT NULL DEFAULT '{}';

UPDATE quality.kaizens
   SET categories = ARRAY[TRIM(category)]
 WHERE cardinality(categories) = 0
   AND category IS NOT NULL
   AND TRIM(category) <> '';

CREATE INDEX IF NOT EXISTS ix_quality_kaizens_categories
    ON quality.kaizens USING GIN (categories)
    WHERE deleted_at IS NULL;
