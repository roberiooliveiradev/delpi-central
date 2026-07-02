-- Ciclo de vida de VERSÕES do kaizen (revisão = versão completa do processo).
--
-- Conceito (esclarecido jun/2026): uma "melhoria" é uma versão completa e nova do
-- kaizen. O usuário clica em "criar nova versão", refaz todo o processo (dados,
-- economia, evidências) e essa versão nasce EM ANDAMENTO (rascunho) enquanto a versão
-- anterior segue IMPLANTADA e contabilizando. Ao IMPLANTAR a nova versão, a anterior é
-- SUBSTITUÍDA (para de contar) e a nova assume — só há uma versão implantada por vez,
-- com seu próprio aniversário de 1 ano.

ALTER TABLE quality.kaizen_revisions
    ADD COLUMN IF NOT EXISTS version_status VARCHAR(20) NOT NULL DEFAULT 'implantado';

ALTER TABLE quality.kaizen_revisions
    DROP CONSTRAINT IF EXISTS ck_kaizen_revision_version_status;

ALTER TABLE quality.kaizen_revisions
    ADD CONSTRAINT ck_kaizen_revision_version_status CHECK (
        version_status IN (
            'em_andamento', 'implantado', 'descontinuado', 'cancelado', 'substituido'
        )
    );

-- Backfill: revisões fechadas (com fim de vigência) já foram substituídas.
UPDATE quality.kaizen_revisions
   SET version_status = 'substituido'
 WHERE effective_until IS NOT NULL;

-- Revisão aberta (vigente) espelha o status atual do kaizen.
UPDATE quality.kaizen_revisions r
   SET version_status = CASE k.status
        WHEN 'implantado' THEN 'implantado'
        WHEN 'descontinuado' THEN 'descontinuado'
        WHEN 'cancelado' THEN 'cancelado'
        ELSE 'em_andamento'
    END
  FROM quality.kaizens k
 WHERE r.kaizen_id = k.id
   AND r.effective_until IS NULL;

-- Só uma versão implantada (ativa) por kaizen.
CREATE UNIQUE INDEX IF NOT EXISTS uq_kaizen_active_implanted_version
    ON quality.kaizen_revisions (kaizen_id)
    WHERE version_status = 'implantado';
