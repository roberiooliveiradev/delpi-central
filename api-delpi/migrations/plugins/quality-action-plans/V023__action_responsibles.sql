-- Múltiplos responsáveis por ação (Minha fila, notificações, vínculo equipe 8D)

CREATE TABLE IF NOT EXISTS quality.quality_action_responsibles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_id UUID NOT NULL,
    user_id VARCHAR(100),
    display_name VARCHAR(200) NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_quality_action_responsibles_action
        FOREIGN KEY (action_id)
        REFERENCES quality.quality_actions (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_quality_action_responsibles_display_name CHECK (
        length(trim(display_name)) > 0
    )
);

CREATE INDEX IF NOT EXISTS ix_quality_action_responsibles_action
    ON quality.quality_action_responsibles (action_id, sort_order);

CREATE INDEX IF NOT EXISTS ix_quality_action_responsibles_user
    ON quality.quality_action_responsibles (user_id)
    WHERE user_id IS NOT NULL AND trim(user_id) <> '';

CREATE UNIQUE INDEX IF NOT EXISTS uq_quality_action_responsibles_action_user
    ON quality.quality_action_responsibles (action_id, user_id)
    WHERE user_id IS NOT NULL AND trim(user_id) <> '';

-- Backfill a partir do responsável legado (um registro por ação)
INSERT INTO quality.quality_action_responsibles (action_id, user_id, display_name, sort_order)
SELECT a.id,
       NULLIF(trim(a.responsible_user_id), ''),
       trim(a.responsible_name),
       0
  FROM quality.quality_actions a
 WHERE trim(coalesce(a.responsible_name, '')) <> ''
   AND NOT EXISTS (
       SELECT 1
         FROM quality.quality_action_responsibles ar
        WHERE ar.action_id = a.id
   );

INSERT INTO quality.quality_action_responsibles (action_id, user_id, display_name, sort_order)
SELECT a.id,
       NULLIF(trim(a.responsible_user_id), ''),
       coalesce(NULLIF(trim(a.responsible_name), ''), 'Responsável'),
       0
  FROM quality.quality_actions a
 WHERE trim(coalesce(a.responsible_user_id, '')) <> ''
   AND trim(coalesce(a.responsible_name, '')) = ''
   AND NOT EXISTS (
       SELECT 1
         FROM quality.quality_action_responsibles ar
        WHERE ar.action_id = a.id
   );
