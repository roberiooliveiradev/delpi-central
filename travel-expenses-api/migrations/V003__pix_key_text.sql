BEGIN;

ALTER TABLE travel_expenses.reports
    ADD COLUMN IF NOT EXISTS pix_key_type TEXT,
    ADD COLUMN IF NOT EXISTS pix_key_value TEXT;

DROP TABLE IF EXISTS travel_expenses.pix_attachments;

COMMENT ON COLUMN travel_expenses.reports.pix_key_type IS
    'Tipo da chave PIX para ressarcimento: cpf, cnpj, email, phone, random';
COMMENT ON COLUMN travel_expenses.reports.pix_key_value IS
    'Chave PIX digitada para ressarcimento';

COMMIT;
