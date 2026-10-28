-- V018 — DRE-ACCESS-019: entrega documental a destinatários externos
-- (doc 91 Opção B, Plano 113 §29, doc 112 §54; decisões D-DRE-ACCESS-01,
-- D-DRE-RELEASE-01, D-DRE-COLLAB-01 do gate CF-PROC0072-DRE-ACCESS-018).
--
-- Decisões de contrato (owner: controllership-finance-api):
--   * `role='RECIPIENT'` em closing_review_assignment: vínculo de
--     consulta do destinatário externo ao pacote (package_id + area =
--     recipient_area). É o 4º papel — não concede review, não entra em
--     _visible_areas do P5 interno nem em elegibilidade de decisão.
--     A atribuição é por pacote (competência+área), mesmo lifecycle de
--     REVIEWER (ativo/desativado, assigned_by, auditoria).
--   * `audience='SHARED'` em document_message: mensagem visível ao
--     destinatário com vínculo de liberação ao documento. INTERNAL
--     permanece fechado à Controladoria; o CHECK é aditivo — nenhuma
--     linha existente muda de semântica.
--   * `document_adjustment_request`: solicitação de esclarecimento/
--     revisão aberta pelo destinatário sobre documento liberado.
--     OPEN → ANSWERED → CONFIRMED: a resposta da Controladoria NÃO
--     encerra a solicitação — somente a confirmação do requerente
--     conclui (decisão de produto: responder ≠ aprovar/encerrar).
--     version_no é CONTEXTUAL (carimbo da versão corrente no envio,
--     mesmo critério de document_message).
--   * Idempotência no mesmo padrão U1/U5/U9: UNIQUE(document_id,
--     idempotency_key) + request_hash — replay deduplica, divergente
--     é conflito.
--   * append-only na conversa; estados do request transitam por
--     UPDATE único na linha com trilha de auditoria por evento.
--
-- Compatibilidade: alterações aditivas (CHECK alargado, role novo,
-- tabela nova) — nenhum dado existente muda.
-- Rollback seguro: DROP TABLE document_adjustment_request (se vazia) +
-- restaurar CHECKs anteriores via migration nova — migrations são
-- imutáveis; o rollback é outra migration, nunca edição deste arquivo.

BEGIN;

-- 1) Recipient role: alarga o catálogo de papéis e a forma composta.
ALTER TABLE controllership_finance.closing_review_assignment
    DROP CONSTRAINT closing_review_assignment_role_check;

ALTER TABLE controllership_finance.closing_review_assignment
    ADD CONSTRAINT closing_review_assignment_role_check
    CHECK (role IN ('REVIEWER', 'COORDINATOR', 'RECIPIENT'));

ALTER TABLE controllership_finance.closing_review_assignment
    DROP CONSTRAINT closing_review_assignment_check;

ALTER TABLE controllership_finance.closing_review_assignment
    ADD CONSTRAINT closing_review_assignment_check
    CHECK (
        (role IN ('REVIEWER', 'RECIPIENT') AND package_id IS NOT NULL
         AND area IS NOT NULL)
        OR (role = 'COORDINATOR' AND package_id IS NULL
            AND area IS NULL)
    );

-- 2) Audiência compartilhada da conversa documental.
ALTER TABLE controllership_finance.document_message
    DROP CONSTRAINT document_message_audience_check;

ALTER TABLE controllership_finance.document_message
    ADD CONSTRAINT document_message_audience_check
    CHECK (audience IN ('INTERNAL', 'SHARED'));

-- 3) Solicitação de ajuste/esclarecimento do destinatário (D-DRE-COLLAB-01).
CREATE TABLE IF NOT EXISTS controllership_finance.document_adjustment_request (
    request_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id      UUID         NOT NULL
        REFERENCES controllership_finance.closing_document (document_id)
        ON DELETE RESTRICT,
    competence_id    UUID         NOT NULL
        REFERENCES controllership_finance.monthly_competence (competence_id)
        ON DELETE RESTRICT,
    version_no       INT          CHECK (version_no >= 1),
    state            VARCHAR(16)  NOT NULL DEFAULT 'OPEN'
        CHECK (state IN ('OPEN', 'ANSWERED', 'CONFIRMED')),
    body             TEXT         NOT NULL
        CHECK (char_length(btrim(body)) BETWEEN 1 AND 4000),
    requester_subject UUID        NOT NULL,
    requester_name   VARCHAR(255),
    idempotency_key  VARCHAR(128) NOT NULL,
    request_hash     CHAR(64)     NOT NULL,
    answer_body      TEXT,
    answered_by      UUID,
    answered_name    VARCHAR(255),
    answered_at      TIMESTAMPTZ,
    confirmed_by     UUID,
    confirmed_at     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (document_id, idempotency_key)
);

-- Fila de trabalho da Controladoria: requests abertos por competência.
CREATE INDEX IF NOT EXISTS document_adjustment_request_open_idx
    ON controllership_finance.document_adjustment_request
        (competence_id, state) WHERE state = 'OPEN';

-- Consulta do destinatário por documento.
CREATE INDEX IF NOT EXISTS document_adjustment_request_document_idx
    ON controllership_finance.document_adjustment_request
        (document_id, created_at);

COMMIT;
