-- Campos mais ricos no kaizen + múltiplos responsáveis/participantes.
-- `accountable` (V027) permanece como responsável principal (espelho / compat Sheets e import).

ALTER TABLE quality.kaizens
    ADD COLUMN IF NOT EXISTS process_description TEXT,
    ADD COLUMN IF NOT EXISTS problem_description TEXT,
    ADD COLUMN IF NOT EXISTS improvement_description TEXT,
    ADD COLUMN IF NOT EXISTS expected_result TEXT,
    ADD COLUMN IF NOT EXISTS category VARCHAR(50);

CREATE TABLE IF NOT EXISTS quality.kaizen_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kaizen_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'participante',
    user_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_kaizen_participants_kaizen
        FOREIGN KEY (kaizen_id)
        REFERENCES quality.kaizens (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_kaizen_participant_role CHECK (
        role IN ('responsavel', 'participante', 'apoio')
    )
);

CREATE INDEX IF NOT EXISTS ix_kaizen_participants_kaizen
    ON quality.kaizen_participants (kaizen_id);

-- Backfill: responsável principal (accountable) vira participante 'responsavel'
INSERT INTO quality.kaizen_participants (kaizen_id, name, role)
SELECT k.id, k.accountable, 'responsavel'
  FROM quality.kaizens k
 WHERE k.accountable IS NOT NULL
   AND btrim(k.accountable) <> ''
   AND k.deleted_at IS NULL
   AND NOT EXISTS (
       SELECT 1 FROM quality.kaizen_participants p WHERE p.kaizen_id = k.id
   );
