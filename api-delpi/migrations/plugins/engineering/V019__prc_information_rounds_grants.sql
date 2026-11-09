-- PRC-REF-019 — grants eng_prc sobre rodadas/perguntas/respostas.
-- Soft-update em rounds/questions/answers (CAS); sem DELETE físico.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'eng_prc') THEN
        GRANT SELECT, INSERT, UPDATE
            ON engineering.product_registration_info_rounds TO eng_prc;
        GRANT SELECT, INSERT, UPDATE
            ON engineering.product_registration_info_questions TO eng_prc;
        GRANT SELECT, INSERT, UPDATE
            ON engineering.product_registration_info_answers TO eng_prc;

        REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_info_rounds FROM eng_prc;
        REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_info_questions FROM eng_prc;
        REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_info_answers FROM eng_prc;
    END IF;
END $$;

COMMENT ON TABLE engineering.product_registration_info_rounds IS
    'PRC-REF-019: rodadas de informações; eng_prc SELECT/INSERT/UPDATE.';
