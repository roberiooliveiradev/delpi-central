-- ============================================================================
-- PRC-REF-020 — workflow simplificado: Concluir atendimento com
-- verificação oficial. under_review deixa de ser etapa operacional.
--
-- Política de legado (auditável, não silenciosa):
--   solicitações ABERTAS em under_review → in_progress
--   + evento returned_to_attendance (migração REF-020)
--   verifications, revisões e histórico de eventos preservados
--
-- Não converte para completed. Não apaga evidências.
-- Forward-only; não edita V012–V019.
-- ============================================================================

-- 1) Contagem prévia (observabilidade da migração — PL/pgSQL).
DO $$
DECLARE
    open_under_review INTEGER;
BEGIN
    SELECT COUNT(*) INTO open_under_review
      FROM engineering.product_registration_requests
     WHERE status = 'under_review';

    RAISE NOTICE 'PRC-REF-020: % solicitação(ões) under_review abertas a migrar',
        open_under_review;
END $$;

-- 2) Evento de auditoria por caso migrado (append-only).
INSERT INTO engineering.product_registration_events (
    id,
    request_id,
    sequence_number,
    event_type,
    actor_subject,
    occurred_at,
    reason,
    metadata,
    previous_status,
    next_status
)
SELECT
    gen_random_uuid(),
    r.id,
    COALESCE(
        (SELECT MAX(e.sequence_number)
           FROM engineering.product_registration_events e
          WHERE e.request_id = r.id),
        0
    ) + 1,
    'returned_to_attendance',
    'system:migration:V020',
    NOW(),
    'PRC-REF-020: under_review legado reaberto para in_progress (migração governada).',
    jsonb_build_object(
        'migration', 'V020__prc_ref020_complete_workflow',
        'policy', 'legacy_under_review_to_in_progress',
        'channel', 'migration'
    ),
    'under_review',
    'in_progress'
FROM engineering.product_registration_requests r
WHERE r.status = 'under_review';

-- 3) Transição de status + CAS (row_version).
UPDATE engineering.product_registration_requests
   SET status = 'in_progress',
       row_version = row_version + 1,
       updated_at = NOW()
 WHERE status = 'under_review';

COMMENT ON COLUMN engineering.product_registration_requests.status IS
    'PRC-REF-020: jornada operacional submitted|in_progress|needs_information|completed|rejected; under_review permanece no CHECK apenas para histórico/leitura.';
