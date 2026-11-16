BEGIN;

-- Chamado #1597: modalidade dentro de Deslocamento, sem categoria nova.
ALTER TABLE travel_expenses.expenses
    ADD COLUMN IF NOT EXISTS transport_mode TEXT
        CHECK (transport_mode IS NULL OR transport_mode IN ('own_vehicle', 'ride_hailing', 'public_transport')),
    ADD COLUMN IF NOT EXISTS distance_km NUMERIC(12, 2)
        CHECK (distance_km IS NULL OR distance_km > 0),
    ADD COLUMN IF NOT EXISTS rate_brl_per_km NUMERIC(10, 2)
        CHECK (rate_brl_per_km IS NULL OR rate_brl_per_km > 0);

-- Tarifas por vigencia: alterar apenas inserindo uma NOVA data de vigencia.
-- Despesas antigas guardam o valor aplicado no lancamento.
CREATE TABLE IF NOT EXISTS travel_expenses.mileage_rates (
    valid_from DATE PRIMARY KEY,
    rate_brl_per_km NUMERIC(10, 2) NOT NULL CHECK (rate_brl_per_km > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO travel_expenses.mileage_rates (valid_from, rate_brl_per_km)
VALUES (DATE '2026-01-01', 1.20)
ON CONFLICT (valid_from) DO NOTHING;

-- Reserva duravel evita dois envios simultaneos do mesmo relatorio.
-- Estado 'sending' incerto nao e reprocessado automaticamente.
CREATE TABLE IF NOT EXISTS travel_expenses.finance_dispatches (
    report_id UUID PRIMARY KEY REFERENCES travel_expenses.reports (id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('sending', 'sent', 'failed')),
    recipient_email TEXT NOT NULL,
    cc_email TEXT NOT NULL,
    attempt_count INT NOT NULL DEFAULT 1 CHECK (attempt_count > 0),
    last_error TEXT,
    sent_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMIT;
