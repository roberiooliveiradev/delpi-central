-- Kaizens operacionais (cadastro PostgreSQL — substitui planilha no fluxo do app)

CREATE TABLE IF NOT EXISTS quality.kaizens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submodule_id UUID NOT NULL,
    branch_code VARCHAR(10) NOT NULL,
    title VARCHAR(500) NOT NULL,
    accountable VARCHAR(200),
    sector VARCHAR(200),
    investment NUMERIC(14, 2),
    savings_type VARCHAR(30) NOT NULL DEFAULT 'tempo',
    seconds_per_occurrence NUMERIC(14, 4),
    occurrences_per_day NUMERIC(14, 4),
    hourly_cost NUMERIC(14, 4),
    quantity_saved_per_day NUMERIC(14, 4),
    unit_material_cost NUMERIC(14, 4),
    fixed_daily_savings NUMERIC(14, 2),
    daily_savings NUMERIC(14, 2),
    annual_savings NUMERIC(14, 2),
    status VARCHAR(30) NOT NULL DEFAULT 'em_andamento',
    date_implemented DATE,
    date_discontinued DATE,
    notes TEXT,
    created_by_user_id VARCHAR(100) NOT NULL,
    updated_by_user_id VARCHAR(100),
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_quality_kaizens_submodule
        FOREIGN KEY (submodule_id)
        REFERENCES quality.submodules (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT ck_quality_kaizens_savings_type CHECK (
        savings_type IN ('tempo', 'material', 'financeiro', 'qualitativo', 'misto')
    ),

    CONSTRAINT ck_quality_kaizens_status CHECK (
        status IN ('em_andamento', 'implantado', 'descontinuado', 'cancelado')
    )
);

CREATE INDEX IF NOT EXISTS ix_quality_kaizens_branch_status
    ON quality.kaizens (branch_code, status)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_quality_kaizens_date_implemented
    ON quality.kaizens (date_implemented)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_quality_kaizens_submodule
    ON quality.kaizens (submodule_id)
    WHERE deleted_at IS NULL;
