-- V004 — U5 idempotência por mutação + document_version verdadeiramente imutável
--
-- REWORK (revisão arquitetural SLICE-2, doc 104 §1): dois resíduos
-- reconciliados aqui, sem redefinir decisões aprovadas:
--
--   1. Idempotência da substituição (D-U7=A aplicada ao aggregate da
--      mutação): cada document_version registra a `idempotency_key` +
--      `request_hash` do request que a criou, com
--      `UNIQUE (document_id, idempotency_key)`. A v1 herda a key do
--      upload (mesma mutação que criou o documento); replaces trazem a
--      própria key — nunca a key U1 reutilizada.
--   2. Imutabilidade de `document_version`: a linha nunca é atualizada.
--      `state` (ATTACHED/SUPERSEDED) deixa de ser coluna mutável e passa
--      a ser **derivado** de `closing_document.current_version_no`
--      (versão corrente = ATTACHED; demais = SUPERSEDED). A coluna é
--      removida para não persistir dado contraditório.
--
-- Compatível com bases existentes: v1 recebe key/hash do documento pai
-- (a mutação de upload que a criou); nenhuma linha é apagada.

BEGIN;

ALTER TABLE controllership_finance.document_version
    DROP COLUMN state,
    ADD COLUMN  idempotency_key VARCHAR(128),
    ADD COLUMN  request_hash    CHAR(64);

UPDATE controllership_finance.document_version v
   SET idempotency_key = d.idempotency_key,
       request_hash    = d.request_hash
  FROM controllership_finance.closing_document d
 WHERE d.document_id = v.document_id;

ALTER TABLE controllership_finance.document_version
    ALTER COLUMN idempotency_key SET NOT NULL,
    ALTER COLUMN request_hash    SET NOT NULL,
    ADD CONSTRAINT document_version_idempotency_uk
        UNIQUE (document_id, idempotency_key);

COMMIT;
