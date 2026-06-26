-- Remove vínculos diretos plano PAC ↔ Kaizen / Auditoria 5S (colunas em quality_action_plans).
-- Amarrações futuras devem usar tabelas auxiliares dedicadas.

DROP INDEX IF EXISTS quality.ix_quality_action_plans_linked_kaizen;
DROP INDEX IF EXISTS quality.ix_quality_action_plans_linked_audit_5s_nc;

ALTER TABLE quality.quality_action_plans
    DROP CONSTRAINT IF EXISTS fk_quality_action_plans_linked_kaizen;

ALTER TABLE quality.quality_action_plans
    DROP CONSTRAINT IF EXISTS fk_quality_action_plans_linked_audit_5s_nc;

ALTER TABLE quality.quality_action_plans
    DROP COLUMN IF EXISTS linked_kaizen_id,
    DROP COLUMN IF EXISTS linked_audit_5s_nc_id;
