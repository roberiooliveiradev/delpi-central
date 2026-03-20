CREATE TABLE IF NOT EXISTS quality.internal_nonconformities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL,
    source_type VARCHAR(30) NOT NULL,
    source_inspection_id UUID,
    production_order VARCHAR(100),
    item_code VARCHAR(100) NOT NULL,
    item_description VARCHAR(255) NOT NULL,
    lot_number VARCHAR(100),
    sector VARCHAR(100) NOT NULL,
    operation_code VARCHAR(100),
    operation_description VARCHAR(255),
    defect_category VARCHAR(100) NOT NULL,
    defect_description TEXT NOT NULL,
    detected_by_user_id VARCHAR(100) NOT NULL,
    detection_date DATE NOT NULL,
    defective_quantity NUMERIC(18,4) NOT NULL DEFAULT 0,
    inspected_quantity NUMERIC(18,4),
    severity VARCHAR(30) NOT NULL,
    priority VARCHAR(30) NOT NULL,
    current_status VARCHAR(50) NOT NULL DEFAULT 'draft',
    containment_action_summary TEXT,
    disposition_type VARCHAR(50),
    immediate_cause_notes TEXT,
    root_cause_summary TEXT,
    responsible_user_id VARCHAR(100),
    due_date DATE,
    closed_at TIMESTAMPTZ,
    cancellation_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_internal_nonconformities_code UNIQUE (code),

    CONSTRAINT ck_internal_nonconformities_source_type
        CHECK (source_type IN ('manual', 'inspection')),

    CONSTRAINT ck_internal_nonconformities_defective_quantity
        CHECK (defective_quantity >= 0),

    CONSTRAINT ck_internal_nonconformities_inspected_quantity
        CHECK (inspected_quantity IS NULL OR inspected_quantity >= 0),

    CONSTRAINT ck_internal_nonconformities_current_status
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

    CONSTRAINT ck_internal_nonconformities_disposition_type
        CHECK (
            disposition_type IS NULL
            OR disposition_type IN (
                'retrabalho',
                'sucata',
                'segregacao',
                'liberacao-condicional',
                'reinspecao',
                'devolucao-interna'
            )
        ),

    CONSTRAINT ck_internal_nonconformities_closed_at
        CHECK (
            (current_status = 'closed' AND closed_at IS NOT NULL)
            OR
            (current_status <> 'closed')
        )
);