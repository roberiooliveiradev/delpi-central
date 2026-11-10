-- PRC-REF-023 — grants mínimos do principal dedicado eng_prc.
-- Sem DELETE/TRUNCATE: retenção auditável (estado DELETED lógico).

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'eng_prc') THEN
        GRANT SELECT, INSERT, UPDATE
            ON engineering.product_registration_attachments TO eng_prc;
        REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_attachments FROM eng_prc;
    END IF;
END $$;
