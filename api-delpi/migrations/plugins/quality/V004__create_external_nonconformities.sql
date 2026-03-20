CREATE TABLE IF NOT EXISTS quality.external_nonconformities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL,
    company_unit VARCHAR(100) NOT NULL,
    supplier_id UUID NOT NULL,
    supplier_name_snapshot VARCHAR(255) NOT NULL,
    customer_name VARCHAR(255),
    origin_type VARCHAR(50) NOT NULL,
    source_channel VARCHAR(50),
    material_code VARCHAR(100),
    material_description VARCHAR(255),
    material_specification TEXT,
    lot_number VARCHAR(100),
    purchase_order VARCHAR(100),
    invoice_number VARCHAR(100),
    document_reference VARCHAR(100),
    occurrence_date DATE NOT NULL,
    detection_date DATE NOT NULL,
    defective_quantity NUMERIC(18,4) NOT NULL DEFAULT 0,
    inspected_quantity NUMERIC(18,4),
    uom VARCHAR(20),
    severity VARCHAR(30) NOT NULL,
    priority VARCHAR(30) NOT NULL,
    occurrence_type VARCHAR(50),
    defect_category VARCHAR(100),
    recurrence_flag BOOLEAN NOT NULL DEFAULT FALSE,
    containment_required BOOLEAN NOT NULL DEFAULT FALSE,
    title VARCHAR(255) NOT NULL,
    problem_description TEXT NOT NULL,
    business_impact TEXT,
    customer_impact TEXT,
    production_impact TEXT,
    cost_estimate NUMERIC(18,2),
    current_status VARCHAR(50) NOT NULL DEFAULT 'draft',
    supplier_status VARCHAR(50) NOT NULL DEFAULT 'not-requested',
    responsible_user_id VARCHAR(100),
    opened_by_user_id VARCHAR(100) NOT NULL,
    due_date DATE,
    closed_at TIMESTAMPTZ,
    cancellation_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_external_nonconformities_code UNIQUE (code),
    CONSTRAINT fk_external_nonconformities_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES quality.external_nc_suppliers (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT ck_external_nonconformities_defective_quantity
        CHECK (defective_quantity >= 0),
    CONSTRAINT ck_external_nonconformities_inspected_quantity
        CHECK (inspected_quantity IS NULL OR inspected_quantity >= 0),
    CONSTRAINT ck_external_nonconformities_cost_estimate
        CHECK (cost_estimate IS NULL OR cost_estimate >= 0),

    CONSTRAINT ck_external_nonconformities_current_status
        CHECK (
            current_status IN (
                'draft',
                'open',
                'under-triage',
                'containment-defined',
                'under-investigation',
                'action-plan-approved',
                'in-progress',
                'pending-effectiveness-check',
                'closed',
                'cancelled',
                'reopened'
            )
        ),

    CONSTRAINT ck_external_nonconformities_supplier_status
        CHECK (
            supplier_status IN (
                'not-requested',
                'awaiting-supplier',
                'supplier-responded',
                'supplier-action-pending',
                'supplier-validated',
                'supplier-overdue'
            )
        ),

    CONSTRAINT ck_external_nonconformities_closed_at
        CHECK (
            (current_status = 'closed' AND closed_at IS NOT NULL)
            OR
            (current_status <> 'closed')
        )
);