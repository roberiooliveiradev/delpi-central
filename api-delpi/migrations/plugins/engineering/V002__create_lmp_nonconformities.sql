-- Não conformidades LMP (substitui planilha no dashboard-lmps)

CREATE TABLE IF NOT EXISTS engineering.lmp_nonconformities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registered_at TIMESTAMPTZ NOT NULL,
    sale_number VARCHAR(20),
    branch_code VARCHAR(2),
    material_code VARCHAR(60),
    supplier_name VARCHAR(200),
    purchase_order VARCHAR(40),
    invoice_number VARCHAR(40),
    qty_received NUMERIC(18, 4),
    qty_accepted NUMERIC(18, 4),
    qty_rejected NUMERIC(18, 4),
    status VARCHAR(40) NOT NULL DEFAULT 'open',
    defect_description TEXT,
    corrective_actions TEXT,
    technical_opinion TEXT,
    created_by VARCHAR(120),
    updated_by VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_lmp_nonconformities_status CHECK (
        status IN ('open', 'in_progress', 'done')
    )
);

CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_registered_at
    ON engineering.lmp_nonconformities (registered_at DESC);

CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_status
    ON engineering.lmp_nonconformities (status);

CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_sale_number
    ON engineering.lmp_nonconformities (sale_number)
    WHERE sale_number IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_material_code
    ON engineering.lmp_nonconformities (material_code)
    WHERE material_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_branch_code
    ON engineering.lmp_nonconformities (branch_code)
    WHERE branch_code IS NOT NULL;
