-- Nome exibido de quem submeteu eficácia para aprovação (além do id)

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS effectiveness_submitted_by_name VARCHAR(200);

COMMENT ON COLUMN quality.quality_action_plans.effectiveness_submitted_by_name IS
    'Nome exibido de quem submeteu a eficácia para aprovação do coordenador.';

UPDATE quality.quality_action_plans p
   SET effectiveness_submitted_by_name = sub.actor_name
  FROM (
        SELECT DISTINCT ON (entity_id)
               entity_id,
               actor_name
          FROM quality.quality_audit_log
         WHERE entity_type = 'quality_action_plan'
           AND event_type = 'effectiveness_submitted'
           AND actor_name IS NOT NULL
           AND TRIM(actor_name) <> ''
         ORDER BY entity_id, created_at DESC
       ) sub
 WHERE p.id = sub.entity_id
   AND p.effectiveness_submitted_by_name IS NULL;
