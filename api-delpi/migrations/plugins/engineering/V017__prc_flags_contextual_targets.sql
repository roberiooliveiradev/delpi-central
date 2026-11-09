-- D16-REF-01 — alvos contextuais (target_attribute + target_key) e
-- unicidade parcial de bandeira OPEN por solicitação+alvo.
-- Aditivo: preserva IDs, histórico, soft-delete, GENERAL legado e grants.
-- Não converte GENERAL → FIELD; não escreve SB1/SA5.

ALTER TABLE engineering.product_registration_flags
    ADD COLUMN IF NOT EXISTS target_attribute VARCHAR(32),
    ADD COLUMN IF NOT EXISTS target_key       VARCHAR(240);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_prc_flags_target_attribute'
    ) THEN
        ALTER TABLE engineering.product_registration_flags
            ADD CONSTRAINT ck_prc_flags_target_attribute
            CHECK (
                target_attribute IS NULL
                OR target_attribute IN ('partNumber', 'catalogNumber')
            );
    END IF;
END $$;

-- Backfill determinístico sem reatribuir GENERAL a um campo.
UPDATE engineering.product_registration_flags
SET target_key = CASE
    WHEN subject = 'FIELD'
         AND target_path IS NOT NULL
         AND btrim(target_path) <> ''
        THEN 'FIELD:' || btrim(target_path)
    WHEN subject = 'SUPPLIER_LINK'
         AND supplier_key IS NOT NULL
         AND coalesce(btrim(supplier_key->>'supplierCode'), '') <> ''
         AND coalesce(btrim(supplier_key->>'store'), '') <> ''
         AND target_attribute IS NOT NULL
        THEN 'SUPPLIER:'
             || btrim(supplier_key->>'supplierCode')
             || '|'
             || btrim(supplier_key->>'store')
             || '|'
             || target_attribute
    WHEN subject = 'SUPPLIER_LINK'
         AND supplier_key IS NOT NULL
         AND coalesce(btrim(supplier_key->>'supplierCode'), '') <> ''
         AND coalesce(btrim(supplier_key->>'store'), '') <> ''
        THEN 'SUPPLIER_LEGACY:'
             || btrim(supplier_key->>'supplierCode')
             || '|'
             || btrim(supplier_key->>'store')
             || ':'
             || id::text
    WHEN subject = 'GENERAL'
        THEN 'GENERAL:' || id::text
    ELSE 'LEGACY:' || id::text
END
WHERE target_key IS NULL;

ALTER TABLE engineering.product_registration_flags
    ALTER COLUMN target_key SET NOT NULL;

-- Inventário de conflitos OPEN (não silenciar). Se houver duplicata
-- contextual pré-existente, o índice único abaixo falhará de forma
-- explícita — operador deve reconciliar antes de reaplicar.
CREATE UNIQUE INDEX IF NOT EXISTS uq_prc_flags_open_target
    ON engineering.product_registration_flags (request_id, target_key)
    WHERE status = 'OPEN' AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_prc_flags_target_path
    ON engineering.product_registration_flags (target_path, status, created_at DESC)
    WHERE deleted_at IS NULL AND target_path IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_prc_flags_target_attribute
    ON engineering.product_registration_flags (
        target_attribute, status, created_at DESC
    )
    WHERE deleted_at IS NULL AND target_attribute IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_prc_flags_status_created
    ON engineering.product_registration_flags (status, created_at DESC, id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_prc_flags_target_key
    ON engineering.product_registration_flags (request_id, target_key)
    WHERE deleted_at IS NULL;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'eng_prc') THEN
        GRANT SELECT, INSERT, UPDATE
            ON engineering.product_registration_flags TO eng_prc;
        REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_flags FROM eng_prc;
    END IF;
END $$;

COMMENT ON COLUMN engineering.product_registration_flags.target_attribute IS
    'D16-REF-01: partNumber|catalogNumber para SUPPLIER_LINK; NULL em FIELD/GENERAL.';
COMMENT ON COLUMN engineering.product_registration_flags.target_key IS
    'D16-REF-01: chave normalizada de unicidade OPEN (request_id, target_key).';
