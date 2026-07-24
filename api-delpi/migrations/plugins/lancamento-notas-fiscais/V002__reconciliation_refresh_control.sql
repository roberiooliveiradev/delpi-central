-- Controle de intervalo mínimo da conciliação sob demanda (Etapa 4B).
-- Singleton compartilhado entre instâncias da API (postgres-plugins).

CREATE TABLE IF NOT EXISTS lancamento_notas_fiscais.reconciliation_refresh_control (
    singleton SMALLINT PRIMARY KEY DEFAULT 1,
    last_started_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_lnf_refresh_control_singleton CHECK (singleton = 1)
);

INSERT INTO lancamento_notas_fiscais.reconciliation_refresh_control (singleton)
VALUES (1)
ON CONFLICT (singleton) DO NOTHING;
