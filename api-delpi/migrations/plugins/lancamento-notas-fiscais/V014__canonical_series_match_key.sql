-- Canonicaliza série numérica (001 ≡ 1) em solicitações e vínculos CT-e.
-- Schema: lancamento_notas_fiscais
-- Não altera migrations anteriores.
-- Ordem obrigatória: dedupe por chave canônica → UPDATE (evita uq_lnf_*).

-- Expressão canônica (paridade com series_match_key / series_match_key_sql):
-- CASE WHEN btrim(COALESCE(series, '')) ~ '^[0-9]+$'
--      THEN COALESCE(NULLIF(LTRIM(btrim(series), '0'), ''), '0')
--      ELSE upper(btrim(COALESCE(series, ''))) END

-- 1) Vínculos CT-e: remover duplicatas que colidiriam após canonicalizar
DELETE FROM lancamento_notas_fiscais.invoice_posting_linked_invoices a
 USING lancamento_notas_fiscais.invoice_posting_linked_invoices b
 WHERE a.request_id = b.request_id
   AND a.document_match_key = b.document_match_key
   AND (
       CASE
           WHEN btrim(COALESCE(a.series, '')) ~ '^[0-9]+$'
           THEN COALESCE(NULLIF(LTRIM(btrim(a.series), '0'), ''), '0')
           ELSE upper(btrim(COALESCE(a.series, '')))
       END
   ) = (
       CASE
           WHEN btrim(COALESCE(b.series, '')) ~ '^[0-9]+$'
           THEN COALESCE(NULLIF(LTRIM(btrim(b.series), '0'), ''), '0')
           ELSE upper(btrim(COALESCE(b.series, '')))
       END
   )
   AND a.ctid > b.ctid;

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

-- 2) Solicitações: cancelar ativas que colidiriam em uq_lnf_requests_active_fiscal_key
--    Mantém a mais avançada (status) / recente; demais viram cancelled (system).
WITH ranked AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY
                branch_code,
                supplier_code,
                supplier_store,
                document_match_key,
                CASE
                    WHEN btrim(COALESCE(series, '')) ~ '^[0-9]+$'
                    THEN COALESCE(NULLIF(LTRIM(btrim(series), '0'), ''), '0')
                    ELSE upper(btrim(COALESCE(series, '')))
                END
            ORDER BY
                CASE status
                    WHEN 'posted' THEN 100
                    WHEN 'in_progress' THEN 80
                    WHEN 'blocked' THEN 50
                    WHEN 'pending' THEN 10
                    ELSE 0
                END DESC,
                updated_at DESC NULLS LAST,
                created_at DESC,
                id
        ) AS rn
    FROM lancamento_notas_fiscais.invoice_posting_requests
    WHERE status <> 'cancelled'
)
UPDATE lancamento_notas_fiscais.invoice_posting_requests AS r
   SET status = 'cancelled',
       cancel_justification = 'Duplicata por série equivalente (001≡1) na migration V014; mantida a solicitação mais avançada.',
       cancelled_at = NOW(),
       cancelled_by_user_id = 'system',
       cancelled_by_name = 'Migration V014',
       block_reason = NULL,
       block_description = NULL,
       updated_at = NOW()
  FROM ranked
 WHERE r.id = ranked.id
   AND ranked.rn > 1;

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
