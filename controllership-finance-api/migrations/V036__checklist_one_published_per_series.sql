BEGIN;

-- CF-CHECKLIST-LIVE-004 / OC-4 — Um PUBLISHED vigente por série (RQ-07).
--
-- O modelo de vigência é janelado: cada versão cobre
-- [effective_from, próximo boundary). Antes da série, várias linhas
-- PUBLISHED coexistiam e o winner era resolvido por janela; isso
-- permitia dois winners concorrentes na mesma série. A partir de V036:
--
-- - `SUPERSEDED` marca o vencedor rebaixado pela publicação seguinte —
--   a janela histórica permanece resolvível (histórico nunca reescrito);
-- - `INACTIVE` mantém a semântica de inativação administrativa —
--   a janela morre e nunca mais resolve;
-- - o índice parcial garante no máximo um PUBLISHED por série —
--   o vencedor vivo de cada série é único.

ALTER TABLE controllership_finance.checklist_template_version
    DROP CONSTRAINT checklist_template_version_status_check;
ALTER TABLE controllership_finance.checklist_template_version
    ADD CONSTRAINT checklist_template_version_status_check
    CHECK (status IN
        ('DRAFT', 'REVIEW', 'PUBLISHED', 'SUPERSEDED', 'INACTIVE'));

-- Backfill obrigatório: séries legadas podem ter vários PUBLISHED
-- (modelo janelado anterior à série). Demote todos exceto o winner
-- vivo — o de maior (effective_from_period, version), mesma
-- ordenação de `resolve_published_version`. SUPERSEDED continua
-- resolvível por janela, então a resolução histórica é preservada.
UPDATE controllership_finance.checklist_template_version v
    SET status = 'SUPERSEDED', updated_at = now()
    WHERE v.status = 'PUBLISHED'
      AND v.series_id IS NOT NULL
      AND v.version_id <> (
          SELECT w.version_id
          FROM controllership_finance.checklist_template_version w
          WHERE w.series_id = v.series_id
            AND w.status = 'PUBLISHED'
          ORDER BY w.effective_from_period DESC, w.version DESC
          LIMIT 1
      );

CREATE UNIQUE INDEX IF NOT EXISTS
    ck_template_version_one_published_per_series
    ON controllership_finance.checklist_template_version (series_id)
    WHERE status = 'PUBLISHED';

COMMIT;
