-- Canonicaliza série numérica (001 ≡ 1) em solicitações e vínculos CT-e.
-- Schema: lancamento_notas_fiscais
-- Não altera migrations anteriores; só UPDATE + dedupe seguro.

-- 1) Notas vinculadas ao CT-e
UPDATE lancamento_notas_fiscais.invoice_posting_linked_invoices
   SET series = CASE
       WHEN btrim(COALESCE(series, '')) ~ '^[0-9]+$'
       THEN COALESCE(NULLIF(LTRIM(btrim(series), '0'), ''), '0')
       ELSE upper(btrim(COALESCE(series, '')))
   END
 WHERE series IS DISTINCT FROM (
       CASE
           WHEN btrim(COALESCE(series, '')) ~ '^[0-9]+$'
           THEN COALESCE(NULLIF(LTRIM(btrim(series), '0'), ''), '0')
           ELSE upper(btrim(COALESCE(series, '')))
       END
   );

-- Dedupe após canonicalizar (mantém o menor id / posição)
DELETE FROM lancamento_notas_fiscais.invoice_posting_linked_invoices a
 USING lancamento_notas_fiscais.invoice_posting_linked_invoices b
 WHERE a.request_id = b.request_id
   AND a.document_match_key = b.document_match_key
   AND a.series = b.series
   AND a.ctid > b.ctid;

-- 2) Solicitações
UPDATE lancamento_notas_fiscais.invoice_posting_requests
   SET series = CASE
       WHEN btrim(COALESCE(series, '')) ~ '^[0-9]+$'
       THEN COALESCE(NULLIF(LTRIM(btrim(series), '0'), ''), '0')
       ELSE upper(btrim(COALESCE(series, '')))
   END,
       updated_at = NOW()
 WHERE series IS DISTINCT FROM (
       CASE
           WHEN btrim(COALESCE(series, '')) ~ '^[0-9]+$'
           THEN COALESCE(NULLIF(LTRIM(btrim(series), '0'), ''), '0')
           ELSE upper(btrim(COALESCE(series, '')))
       END
   );
