-- Lançamento de Notas Fiscais — schema inicial (Etapa 2A)
-- Schema: lancamento_notas_fiscais (slug: lancamento-notas-fiscais)
-- Downgrade no projeto: scripts/run_plugins_migrations.py reset --plugin lancamento-notas-fiscais

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS lancamento_notas_fiscais.invoice_posting_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    branch_code VARCHAR(2) NOT NULL,
    document_number VARCHAR(9) NOT NULL,
    document_match_key VARCHAR(9) NOT NULL,
    series VARCHAR(3) NOT NULL DEFAULT '',

    supplier_code VARCHAR(6) NOT NULL,
    supplier_store VARCHAR(2) NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    supplier_short_name VARCHAR(50),

    issue_date DATE NOT NULL,
    amount NUMERIC(18, 2) NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    observation TEXT,

    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    block_reason VARCHAR(40),
    block_description TEXT,

    created_by_user_id VARCHAR(100) NOT NULL,
    created_by_name VARCHAR(200) NOT NULL,
    assignee_user_id VARCHAR(100),
    assignee_name VARCHAR(200),

    cancelled_at TIMESTAMPTZ,
    cancelled_by_user_id VARCHAR(100),
    cancelled_by_name VARCHAR(200),
    cancel_justification TEXT,

    completion_source VARCHAR(20),
    sf1_recno INTEGER,
    erp_entry_date DATE,
    reconciled_at TIMESTAMPTZ,

    divergence_alert BOOLEAN NOT NULL DEFAULT FALSE,
    divergence_detected_at TIMESTAMPTZ,
    divergence_detail TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_lnf_requests_branch
        CHECK (branch_code IN ('01', '02')),

    CONSTRAINT ck_lnf_requests_document_number
        CHECK (document_number ~ '^[0-9]{8,9}$'),

    CONSTRAINT ck_lnf_requests_document_match_key
        CHECK (document_match_key ~ '^[0-9]{9}$'),

    CONSTRAINT ck_lnf_requests_document_match_consistency
        CHECK (document_match_key = lpad(document_number, 9, '0')),

    CONSTRAINT ck_lnf_requests_series
        CHECK (
            char_length(series) <= 3
            AND series = upper(btrim(series))
        ),

    CONSTRAINT ck_lnf_requests_amount
        CHECK (amount >= 0),

    CONSTRAINT ck_lnf_requests_status
        CHECK (status IN (
            'pending',
            'in_progress',
            'blocked',
            'posted',
            'cancelled'
        )),

    CONSTRAINT ck_lnf_requests_block_reason
        CHECK (
            block_reason IS NULL
            OR block_reason IN (
                'purchase_order',
                'supplier_registration',
                'information_correction',
                'other'
            )
        ),

    CONSTRAINT ck_lnf_requests_blocked_fields
        CHECK (
            (
                status = 'blocked'
                AND block_reason IS NOT NULL
                AND block_description IS NOT NULL
                AND btrim(block_description) <> ''
            )
            OR (
                status <> 'blocked'
                AND block_reason IS NULL
                AND block_description IS NULL
            )
        ),

    CONSTRAINT ck_lnf_requests_cancelled_fields
        CHECK (
            (
                status = 'cancelled'
                AND cancel_justification IS NOT NULL
                AND btrim(cancel_justification) <> ''
                AND cancelled_at IS NOT NULL
                AND cancelled_by_user_id IS NOT NULL
                AND btrim(cancelled_by_user_id) <> ''
            )
            OR (
                status <> 'cancelled'
                AND cancel_justification IS NULL
                AND cancelled_at IS NULL
                AND cancelled_by_user_id IS NULL
                AND cancelled_by_name IS NULL
            )
        ),

    CONSTRAINT ck_lnf_requests_completion_source
        CHECK (
            completion_source IS NULL
            OR completion_source IN ('auto', 'manual')
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_lnf_requests_active_fiscal_key
    ON lancamento_notas_fiscais.invoice_posting_requests (
        branch_code,
        supplier_code,
        supplier_store,
        document_match_key,
        series
    )
    WHERE status <> 'cancelled';

CREATE INDEX IF NOT EXISTS ix_lnf_requests_status_received_at
    ON lancamento_notas_fiscais.invoice_posting_requests (status, received_at);

CREATE INDEX IF NOT EXISTS ix_lnf_requests_branch_status_received_at
    ON lancamento_notas_fiscais.invoice_posting_requests (branch_code, status, received_at);

CREATE INDEX IF NOT EXISTS ix_lnf_requests_supplier
    ON lancamento_notas_fiscais.invoice_posting_requests (supplier_code, supplier_store);

CREATE INDEX IF NOT EXISTS ix_lnf_requests_document_number
    ON lancamento_notas_fiscais.invoice_posting_requests (document_number);

CREATE INDEX IF NOT EXISTS ix_lnf_requests_issue_date
    ON lancamento_notas_fiscais.invoice_posting_requests (issue_date);

CREATE INDEX IF NOT EXISTS ix_lnf_requests_assignee
    ON lancamento_notas_fiscais.invoice_posting_requests (assignee_user_id)
    WHERE assignee_user_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS lancamento_notas_fiscais.invoice_posting_history (
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

    CONSTRAINT fk_lnf_history_request
        FOREIGN KEY (request_id)
        REFERENCES lancamento_notas_fiscais.invoice_posting_requests (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_lnf_history_actor_origin
        CHECK (actor_origin IN ('user', 'system')),

    CONSTRAINT ck_lnf_history_event_type
        CHECK (char_length(btrim(event_type)) > 0)
);

CREATE INDEX IF NOT EXISTS ix_lnf_history_request_created_at
    ON lancamento_notas_fiscais.invoice_posting_history (request_id, created_at);

CREATE TABLE IF NOT EXISTS lancamento_notas_fiscais.invoice_posting_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    author_user_id VARCHAR(100) NOT NULL,
    author_name VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_lnf_comments_request
        FOREIGN KEY (request_id)
        REFERENCES lancamento_notas_fiscais.invoice_posting_requests (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_lnf_comments_body_not_blank
        CHECK (char_length(btrim(body)) > 0)
);

CREATE INDEX IF NOT EXISTS ix_lnf_comments_request_created_at
    ON lancamento_notas_fiscais.invoice_posting_comments (request_id, created_at);
