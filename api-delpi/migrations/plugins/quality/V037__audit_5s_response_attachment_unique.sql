-- Uma foto por critério (resposta) na avaliação 5S.
CREATE UNIQUE INDEX IF NOT EXISTS uq_audit_5s_response_attachments_response_id
    ON quality.audit_5s_response_attachments (response_id);

CREATE INDEX IF NOT EXISTS idx_audit_5s_response_attachments_response_id
    ON quality.audit_5s_response_attachments (response_id);
