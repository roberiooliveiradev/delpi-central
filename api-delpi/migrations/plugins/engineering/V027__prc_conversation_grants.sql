-- PRC-CONVERSATION — grants mínimos do principal dedicado eng_prc.
-- Sem DELETE/TRUNCATE: remoção é lógica (state='DELETED'), retenção
-- auditável — mesmo padrão de V023 (anexos do caso).

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'eng_prc') THEN
        GRANT SELECT, INSERT, UPDATE
            ON engineering.product_registration_comments TO eng_prc;
        REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_comments FROM eng_prc;

        GRANT SELECT, INSERT, UPDATE
            ON engineering.product_registration_comment_attachments TO eng_prc;
        REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_comment_attachments FROM eng_prc;
    END IF;
END $$;
