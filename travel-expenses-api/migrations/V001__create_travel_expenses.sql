BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS travel_expenses;

COMMENT ON SCHEMA travel_expenses IS 'Despesas de viagem — prestações, cupons e pacote.';

CREATE TABLE travel_expenses.categories (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO travel_expenses.categories (id, label, sort_order) VALUES
    ('lodging', 'Hospedagem', 10),
    ('meals', 'Alimentação', 20),
    ('fuel', 'Combustível', 30),
    ('ground_transport', 'Deslocamento', 40),
    ('air_transport', 'Aéreo', 50),
    ('toll', 'Pedágio', 60),
    ('parking', 'Estacionamento', 70),
    ('communication', 'Comunicação', 80),
    ('other', 'Outros', 90);

CREATE TABLE travel_expenses.report_sequences (
    unit_code CHAR(2) NOT NULL,
    year INT NOT NULL,
    last_n INT NOT NULL DEFAULT 0,
    PRIMARY KEY (unit_code, year)
);

CREATE TABLE travel_expenses.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    number TEXT NOT NULL,
    unit_code CHAR(2) NOT NULL CHECK (unit_code IN ('01', '02')),
    owner_user_id TEXT NOT NULL,
    created_by_name TEXT,
    created_by_email TEXT,
    destination TEXT NOT NULL DEFAULT '',
    purpose TEXT NOT NULL DEFAULT '',
    period_start DATE,
    period_end DATE,
    cost_center_code TEXT,
    cost_center_label TEXT,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'submitted', 'returned', 'approved', 'in_finance', 'closed')),
    total_amount_brl NUMERIC(14, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (unit_code, number)
);

CREATE INDEX travel_expenses_reports_owner_idx
    ON travel_expenses.reports (owner_user_id, updated_at DESC);
CREATE INDEX travel_expenses_reports_unit_status_idx
    ON travel_expenses.reports (unit_code, status, updated_at DESC);

CREATE TABLE travel_expenses.expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES travel_expenses.reports (id) ON DELETE CASCADE,
    expense_date DATE NOT NULL,
    category_id TEXT NOT NULL REFERENCES travel_expenses.categories (id),
    merchant TEXT NOT NULL DEFAULT '',
    amount_brl NUMERIC(14, 2) NOT NULL CHECK (amount_brl >= 0),
    notes TEXT NOT NULL DEFAULT '',
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX travel_expenses_expenses_report_idx
    ON travel_expenses.expenses (report_id, expense_date, sort_order);

CREATE TABLE travel_expenses.receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_id UUID NOT NULL REFERENCES travel_expenses.expenses (id) ON DELETE CASCADE,
    stored_name TEXT NOT NULL,
    original_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX travel_expenses_receipts_expense_idx
    ON travel_expenses.receipts (expense_id, created_at);

CREATE TABLE travel_expenses.audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES travel_expenses.reports (id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT,
    actor_user_id TEXT,
    actor_name TEXT,
    actor_email TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX travel_expenses_audit_report_idx
    ON travel_expenses.audit_events (report_id, created_at DESC);

COMMIT;
