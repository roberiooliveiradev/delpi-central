BEGIN;

CREATE TABLE travel_expenses.pix_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL UNIQUE REFERENCES travel_expenses.reports (id) ON DELETE CASCADE,
    stored_name TEXT NOT NULL,
    original_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX travel_expenses_pix_report_idx
    ON travel_expenses.pix_attachments (report_id);

COMMENT ON TABLE travel_expenses.pix_attachments IS 'QR/captura PIX para ressarcimento — um arquivo por prestação.';

COMMIT;
