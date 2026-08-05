-- Planejamento Orçamentário — itens de investimento CAPEX (Fase 2B.1)
-- Schema: planejamento_orcamentario
-- category_id = catálogo capex_categories (não é conta contábil do ERP).
-- required_date = Data Rcbto / data em que o bem precisa estar disponível.
-- priority = 1..4 (planilha original); origin = national|imported (Carta).
-- status nesta fase: draft | archived. Soft-archive (sem exclusão física).

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.capex_investments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id UUID NOT NULL REFERENCES planejamento_orcamentario.budget_exercises(id),
    unit_id VARCHAR(20) NOT NULL REFERENCES planejamento_orcamentario.org_units(code),
    area_id VARCHAR(40) REFERENCES planejamento_orcamentario.org_areas(code),
    cost_center_id VARCHAR(40) NOT NULL REFERENCES planejamento_orcamentario.org_cost_centers(code),
    category_id UUID REFERENCES planejamento_orcamentario.capex_categories(id),
    -- Conta contábil ERP (separada da categoria de negócio); nullable até fonte confiável.
    accounting_account_code VARCHAR(40),
    description TEXT,
    justification TEXT,
    probable_supplier_name VARCHAR(200),
    probable_supplier_code VARCHAR(40),
    estimated_amount NUMERIC(18, 2),
    currency VARCHAR(3) NOT NULL DEFAULT 'BRL',
    required_date DATE,
    priority VARCHAR(10),
    origin VARCHAR(20),
    classification VARCHAR(10),
    -- Turno da planilha (1/2/3); nome canônico de domínio alinhado à spec.
    shift VARCHAR(10),
    application VARCHAR(100),
    observations TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    version INTEGER NOT NULL DEFAULT 1,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(100),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_by VARCHAR(100),
    archived_at TIMESTAMPTZ,

    CONSTRAINT ck_po_capex_inv_status CHECK (status IN ('draft', 'archived')),
    CONSTRAINT ck_po_capex_inv_currency CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT ck_po_capex_inv_priority CHECK (
        priority IS NULL OR priority IN ('1', '2', '3', '4')
    ),
    CONSTRAINT ck_po_capex_inv_origin CHECK (
        origin IS NULL OR origin IN ('national', 'imported')
    ),
    CONSTRAINT ck_po_capex_inv_classification CHECK (
        classification IS NULL OR classification IN ('1', '2', '3', '4', '5', '6')
    ),
    CONSTRAINT ck_po_capex_inv_shift CHECK (
        shift IS NULL OR shift IN ('1', '2', '3')
    ),
    CONSTRAINT ck_po_capex_inv_amount CHECK (
        estimated_amount IS NULL OR estimated_amount > 0
    ),
    CONSTRAINT ck_po_capex_inv_version CHECK (version >= 1)
);

CREATE INDEX IF NOT EXISTS ix_po_capex_inv_exercise
    ON planejamento_orcamentario.capex_investments (exercise_id);

CREATE INDEX IF NOT EXISTS ix_po_capex_inv_cost_center
    ON planejamento_orcamentario.capex_investments (cost_center_id);

CREATE INDEX IF NOT EXISTS ix_po_capex_inv_category
    ON planejamento_orcamentario.capex_investments (category_id)
    WHERE category_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_po_capex_inv_status
    ON planejamento_orcamentario.capex_investments (status);

CREATE INDEX IF NOT EXISTS ix_po_capex_inv_priority
    ON planejamento_orcamentario.capex_investments (priority)
    WHERE priority IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_po_capex_inv_origin
    ON planejamento_orcamentario.capex_investments (origin)
    WHERE origin IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_po_capex_inv_created_by
    ON planejamento_orcamentario.capex_investments (created_by);

CREATE INDEX IF NOT EXISTS ix_po_capex_inv_exercise_cc_status
    ON planejamento_orcamentario.capex_investments (exercise_id, cost_center_id, status);

CREATE INDEX IF NOT EXISTS ix_po_capex_inv_updated
    ON planejamento_orcamentario.capex_investments (updated_at DESC);
