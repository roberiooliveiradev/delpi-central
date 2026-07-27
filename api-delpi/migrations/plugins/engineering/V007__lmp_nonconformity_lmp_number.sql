-- Número da LMP (campo legado, opcional) nas NCs.
-- Mantém sale_number como OV; lmp_number cobre cadastros antigos.

ALTER TABLE engineering.lmp_nonconformities
    ADD COLUMN IF NOT EXISTS lmp_number VARCHAR(40);

CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_lmp_number
    ON engineering.lmp_nonconformities (lmp_number)
    WHERE lmp_number IS NOT NULL;

COMMENT ON COLUMN engineering.lmp_nonconformities.lmp_number IS
    'Número da LMP (legado / opcional). Distinto da OV (sale_number).';
COMMENT ON COLUMN engineering.lmp_nonconformities.sale_number IS
    'Número da OV (Protheus). Distinto do número legado da LMP (lmp_number).';
