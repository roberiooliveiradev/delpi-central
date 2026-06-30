-- Catálogo de exportação Excel 8D — template preferido por plano

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS export_template_key VARCHAR(50);

COMMENT ON COLUMN quality.quality_action_plans.export_template_key IS
    'Chave do template Excel 8D para exportação (ex.: weg_wfr20997, delpi_8d). NULL = inferir pelo cliente ou padrão.';

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_export_template_key
    ON quality.quality_action_plans (export_template_key)
    WHERE deleted_at IS NULL AND export_template_key IS NOT NULL;
