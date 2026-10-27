-- V017 — DR-1/DR-2 (doc 114 §8): operação idempotente de configuração
-- documental transacional. Registra Idempotency-Key + request_hash +
-- resposta persistida na mesma transação das versões publicadas —
-- replay retorna o resultado original sem duplicar versão nem auditoria.
BEGIN;

CREATE TABLE IF NOT EXISTS controllership_finance.document_requirement_operation (
    operation_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id     UUID         NOT NULL
        REFERENCES controllership_finance.checklist_template (template_id)
        ON DELETE RESTRICT,
    item_key        VARCHAR(32)  NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    request_hash    CHAR(64)     NOT NULL,
    actor_subject   UUID         NOT NULL,
    result          JSONB        NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Escopo canônico da chave: (template_id, idempotency_key) — mesmo
-- padrão de document_version (V004): chave repetida com payload
-- divergente é conflito, com payload idêntico é replay.
CREATE UNIQUE INDEX IF NOT EXISTS doc_req_op_template_key_uidx
    ON controllership_finance.document_requirement_operation
    (template_id, idempotency_key);

COMMIT;
