-- PRC-TRACK — grants mínimos de eng_prc sobre as flags de produto.
-- Estados encerrados são terminais (CR-07): UPDATE fecha ciclo; sem
-- DELETE físico operacional.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'eng_prc') THEN
        GRANT SELECT, INSERT, UPDATE
            ON engineering.product_registration_record_flags TO eng_prc;
        REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_record_flags FROM eng_prc;
        GRANT SELECT, INSERT
            ON engineering.product_registration_record_flag_events TO eng_prc;
        REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_record_flag_events FROM eng_prc;
    END IF;
END $$;

COMMENT ON TABLE engineering.product_registration_record_flags IS
    'PRC-TRACK: bandeiras por produto/alvo; projeção temporal por revisão; eng_prc SELECT/INSERT/UPDATE.';

COMMENT ON TABLE engineering.product_registration_record_flag_events IS
    'PRC-TRACK: eventos auditáveis de bandeira por revisão de contexto; eng_prc SELECT/INSERT.';
