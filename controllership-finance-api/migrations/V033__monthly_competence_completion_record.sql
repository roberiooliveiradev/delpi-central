BEGIN;

-- CF-CHECKLIST-LIVE-004 — Proteção histórica de conclusão (RQ-10)
-- Marcador durável write-once + estado de avaliação fail-closed.
-- Política de backfill (doc 174 §2.2 / doc 176 §6.3):
--   conclusão atual derivável          -> COMPLETED (MARKER)
--   evidência positiva reconstruível    -> COMPLETED (BACKFILL)
--   evidência negativa comprovável      -> NEVER
--   qualquer outro caso                 -> UNEVALUATED (bloqueado)
-- NULL/ausência de evidência NUNCA prova "nunca concluído".

ALTER TABLE controllership_finance.monthly_competence
    ADD COLUMN IF NOT EXISTS first_completed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS completion_record VARCHAR(12)
        NOT NULL DEFAULT 'UNEVALUATED'
        CHECK (completion_record IN ('NEVER','COMPLETED','UNEVALUATED')),
    ADD COLUMN IF NOT EXISTS completion_basis VARCHAR(10)
        CHECK (completion_basis IS NULL
               OR completion_basis IN ('MARKER','BACKFILL','GOVERNED'));

-- Backfill conservador sobre registros legados:
-- 1) existência de pacote SUBMITTED/FINALIZED ou qualquer trilha de
--    conclusão -> evidência positiva -> COMPLETED (BACKFILL);
-- 2) sem pacote algum E sem decisão/documento/mensagem/correção/
--    pendência -> evidência negativa comprovável -> NEVER;
-- 3) resto (trilha parcial ambígua) -> permanece UNEVALUATED.
UPDATE controllership_finance.monthly_competence c
   SET completion_record = 'COMPLETED',
       completion_basis  = 'BACKFILL'
 WHERE c.completion_record = 'UNEVALUATED'
   AND EXISTS (
       SELECT 1
         FROM controllership_finance.closing_package_version p
         JOIN controllership_finance.closing_package pk
           ON pk.package_id = p.package_id
        WHERE pk.competence_id = c.competence_id
          AND p.status IN ('SUBMITTED','FINALIZED')
   );

UPDATE controllership_finance.monthly_competence c
   SET completion_record = 'NEVER',
       completion_basis  = 'BACKFILL'
 WHERE c.completion_record = 'UNEVALUATED'
   AND NOT EXISTS (
       SELECT 1
         FROM controllership_finance.closing_package pk
        WHERE pk.competence_id = c.competence_id)
   AND NOT EXISTS (
       SELECT 1 FROM controllership_finance.evidence_decision d
        WHERE d.competence_id = c.competence_id)
   AND NOT EXISTS (
       SELECT 1 FROM controllership_finance.closing_document doc
        WHERE doc.competence_id = c.competence_id)
   AND NOT EXISTS (
       SELECT 1 FROM controllership_finance.item_correction ic
        WHERE ic.competence_id = c.competence_id)
   AND NOT EXISTS (
       SELECT 1 FROM controllership_finance.closing_pendency pe
        WHERE pe.competence_id = c.competence_id);

COMMIT;
