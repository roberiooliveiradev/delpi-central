BEGIN;

-- CF-CLARA-RUNTIME-001 — backfill movido para migration nova.
--
-- Em e09f9884ac o UPDATE abaixo foi acrescentado dentro da V036 já
-- aplicada em PROD/HML/DEV — divergência de checksum derrubou o
-- startup da API em PROD (migrations-immutable-checksum). A V036
-- volta ao conteúdo original aplicado e o backfill vem para cá:
--
-- - onde o índice parcial da V036 já existe, não há PUBLISHED
--   excedente por série → UPDATE é no-op (idempotente);
-- - em bases que aplicaram o conteúdo interino da V036 (só DEV
--   local), o efeito já correu → UPDATE também é no-op;
-- - em bases novas, roda antes de qualquer dado de série existir.

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

COMMIT;
