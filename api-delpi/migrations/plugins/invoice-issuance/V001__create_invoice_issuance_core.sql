-- Invoice issuance requests — schema inicial
-- Schema: invoice_issuance (slug: invoice-issuance)
-- Aplicar somente com `up`. Nunca `reset` em produção.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS invoice_issuance.invoice_issuance_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    branch_code VARCHAR(2) NOT NULL,
    party_type VARCHAR(20) NOT NULL,
    party_code VARCHAR(6) NOT NULL,
    party_store VARCHAR(2) NOT NULL,
    party_name VARCHAR(200) NOT NULL,
    tax_id VARCHAR(20),

    invoice_type VARCHAR(30) NOT NULL,
    invoice_type_other VARCHAR(200),

    freight_mode VARCHAR(10) NOT NULL,
    carrier_name VARCHAR(200),
    weight_kg NUMERIC(18, 3) NOT NULL,
    volume_count INTEGER NOT NULL,

    purchase_order_number VARCHAR(60),
    observation TEXT,

    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    return_reason TEXT,
    checklist JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_by_user_id VARCHAR(100) NOT NULL,
    created_by_name VARCHAR(200) NOT NULL,
    assignee_user_id VARCHAR(100),
    assignee_name VARCHAR(200),

    cancelled_at TIMESTAMPTZ,
    cancelled_by_user_id VARCHAR(100),
    cancelled_by_name VARCHAR(200),
    cancel_justification TEXT,
    issued_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_ii_requests_branch
        CHECK (branch_code IN ('01', '02')),

    CONSTRAINT ck_ii_requests_party_type
        CHECK (party_type IN ('customer', 'supplier')),

    CONSTRAINT ck_ii_requests_invoice_type
        CHECK (invoice_type IN (
            'sale',
            'return',
            'sample',
            'repair_shipment',
            'other'
        )),

    CONSTRAINT ck_ii_requests_invoice_type_other
        CHECK (
            (invoice_type = 'other' AND invoice_type_other IS NOT NULL AND btrim(invoice_type_other) <> '')
            OR (invoice_type <> 'other' AND invoice_type_other IS NULL)
        ),

    CONSTRAINT ck_ii_requests_freight_mode
        CHECK (freight_mode IN ('cif', 'fob')),

    CONSTRAINT ck_ii_requests_weight
        CHECK (weight_kg > 0),

    CONSTRAINT ck_ii_requests_volumes
        CHECK (volume_count > 0),

    CONSTRAINT ck_ii_requests_status
        CHECK (status IN (
            'pending',
            'in_progress',
            'issued',
            'returned',
            'cancelled'
        )),

    CONSTRAINT ck_ii_requests_cancelled_fields
        CHECK (
            (
                status = 'cancelled'
                AND cancel_justification IS NOT NULL
                AND btrim(cancel_justification) <> ''
                AND cancelled_at IS NOT NULL
            )
            OR (
                status <> 'cancelled'
                AND cancel_justification IS NULL
                AND cancelled_at IS NULL
                AND cancelled_by_user_id IS NULL
                AND cancelled_by_name IS NULL
            )
        )
);

CREATE INDEX IF NOT EXISTS ix_ii_requests_branch_status_created
    ON invoice_issuance.invoice_issuance_requests (branch_code, status, created_at);

CREATE INDEX IF NOT EXISTS ix_ii_requests_created_by
    ON invoice_issuance.invoice_issuance_requests (created_by_user_id);

CREATE TABLE IF NOT EXISTS invoice_issuance.invoice_issuance_request_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    line_number INTEGER NOT NULL,
    product_code VARCHAR(30) NOT NULL,
    product_description VARCHAR(200) NOT NULL,
    quantity NUMERIC(18, 4) NOT NULL,
    unit_price NUMERIC(18, 4) NOT NULL,
    stock_write_off BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_ii_items_request
        FOREIGN KEY (request_id)
        REFERENCES invoice_issuance.invoice_issuance_requests (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_ii_items_quantity
        CHECK (quantity > 0),

    CONSTRAINT ck_ii_items_unit_price
        CHECK (unit_price >= 0),

    CONSTRAINT uq_ii_items_line
        UNIQUE (request_id, line_number)
);

CREATE INDEX IF NOT EXISTS ix_ii_items_request
    ON invoice_issuance.invoice_issuance_request_items (request_id);

CREATE TABLE IF NOT EXISTS invoice_issuance.invoice_issuance_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    stored_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_by_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_ii_attachments_request
        FOREIGN KEY (request_id)
        REFERENCES invoice_issuance.invoice_issuance_requests (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_ii_attachments_size
        CHECK (size_bytes > 0)
);

CREATE INDEX IF NOT EXISTS ix_ii_attachments_request
    ON invoice_issuance.invoice_issuance_attachments (request_id);

CREATE TABLE IF NOT EXISTS invoice_issuance.invoice_issuance_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    actor_origin VARCHAR(10) NOT NULL,
    actor_user_id VARCHAR(100),
    actor_name VARCHAR(200),
    from_status VARCHAR(20),
    to_status VARCHAR(20),
    changes JSONB NOT NULL DEFAULT '{}'::jsonb,
    justification TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_ii_history_request
        FOREIGN KEY (request_id)
        REFERENCES invoice_issuance.invoice_issuance_requests (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_ii_history_actor_origin
        CHECK (actor_origin IN ('user', 'system'))
);

CREATE INDEX IF NOT EXISTS ix_ii_history_request_created
    ON invoice_issuance.invoice_issuance_history (request_id, created_at);
