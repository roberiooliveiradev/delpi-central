-- V016 — U9 conversas documentais do fechamento (GO PO doc-113 §21;
-- DR doc-112 §43): mensagem livre persistida, iniciada pela
-- Controladoria sem exigir solicitação prévia da DRE.
--
-- Decisões de contrato (owner: controllership-finance-api):
--   * a conversa pertence ao aggregate `closing_document` — a mensagem
--     carrega `document_id` E `competence_id` (integridade denormalizada
--     no banco, mesmo critério de `closing_audit_event`); nome de arquivo
--     nunca é chave de vínculo.
--   * `version_no` é CONTEXTUAL — carimbo da versão corrente no momento
--     do envio; a conversa continua do documento, não de uma versão
--     específica. NULL só em cenários futuros fora do documento.
--   * `audience` é fechada: 'INTERNAL' = somente Controladoria autorizada
--     (`access` + escopo). Acesso da DRE/Contabilidade a documentos não
--     liberados é decisão de gate transversal futuro — este slice NÃO
--     cria audiência compartilhada nem inventa visibilidade.
--   * append-only: sem UPDATE/DELETE por contrato de aplicação — o
--     histórico da conversa nunca é reescrito.
--   * `author_name` é snapshot do claim `name` autenticado (pode ser
--     NULL quando o claim não existe — a UI mostra identificação neutra
--     e nunca o UUID). `author_subject` é a identidade canônica.
--   * Idempotência D-U9=A, mesmo padrão de U1/U5 (supplies-api):
--     UNIQUE(document_id, idempotency_key) + request_hash do corpo —
--     replay idêntico deduplica, divergente é conflito.
--
-- Compatibilidade: tabela nova — nenhum dado existente muda.
-- Rollback seguro: DROP TABLE document_message (somente se vazia; a
-- migration não contém caminho destrutivo automático).

BEGIN;

CREATE TABLE IF NOT EXISTS controllership_finance.document_message (
    message_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID         NOT NULL
        REFERENCES controllership_finance.closing_document (document_id)
        ON DELETE RESTRICT,
    competence_id   UUID         NOT NULL
        REFERENCES controllership_finance.monthly_competence (competence_id)
        ON DELETE RESTRICT,
    version_no      INT          CHECK (version_no >= 1),
    audience        VARCHAR(24)  NOT NULL DEFAULT 'INTERNAL'
        CHECK (audience IN ('INTERNAL')),
    body            TEXT         NOT NULL
        CHECK (char_length(btrim(body)) BETWEEN 1 AND 4000),
    author_subject  UUID         NOT NULL,
    author_name     VARCHAR(255),
    idempotency_key VARCHAR(128) NOT NULL,
    request_hash    CHAR(64)     NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (document_id, idempotency_key)
);

-- Leitura da conversa: cronológica por documento (U9 list).
CREATE INDEX IF NOT EXISTS document_message_document_idx
    ON controllership_finance.document_message (document_id, created_at);

-- Varredura por competência (relatórios/investigação futura).
CREATE INDEX IF NOT EXISTS document_message_competence_idx
    ON controllership_finance.document_message (competence_id, created_at);

COMMIT;
