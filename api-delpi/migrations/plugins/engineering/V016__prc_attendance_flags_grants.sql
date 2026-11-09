-- D16 — grants mínimos de eng_prc sobre product_registration_flags.
-- V015 criou a tabela; grants ficam versionados à parte porque o
-- principal eng_prc é provisionado fora do SQL de schema (eng_prc_grants.sql).
-- Soft-delete usa UPDATE (deleted_at); sem DELETE físico operacional.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'eng_prc') THEN
        GRANT SELECT, INSERT, UPDATE
            ON engineering.product_registration_flags TO eng_prc;
        REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_flags FROM eng_prc;
    END IF;
END $$;

COMMENT ON TABLE engineering.product_registration_flags IS
    'D16: bandeiras operacionais PRC; soft-delete; eng_prc SELECT/INSERT/UPDATE.';
