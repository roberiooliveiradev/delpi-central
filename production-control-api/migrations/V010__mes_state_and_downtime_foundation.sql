BEGIN;

-- Fundação MES: estado operacional do CT + paradas + catálogo de motivos.
-- Não altera production_runs e não executa backfill: as tabelas de eventos
-- nascem vazias; a captura começa quando o runtime for integrado (Etapa 02).

CREATE TABLE IF NOT EXISTS production_control.downtime_reason_catalog (
    code VARCHAR(40) PRIMARY KEY,
    label VARCHAR(120) NOT NULL,
    category VARCHAR(40) NOT NULL,
    -- NULL = "classificação MES/OEE ainda não governada".
    default_planned BOOLEAN,
    default_counts_as_availability_loss BOOLEAN,
    requires_note BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pc_downtime_reasons_active
    ON production_control.downtime_reason_catalog (active, sort_order);

CREATE TABLE IF NOT EXISTS production_control.work_center_state_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch VARCHAR(2) NOT NULL CHECK (branch IN ('01', '02')),
    work_center VARCHAR(40) NOT NULL,
    run_id UUID REFERENCES production_control.production_runs (id) ON DELETE RESTRICT,
    state VARCHAR(20) NOT NULL CHECK (
        state IN ('idle', 'setup', 'producing', 'stopped', 'planned_stop')
    ),
    source VARCHAR(40) NOT NULL DEFAULT 'system',
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_pc_state_events_time_range
        CHECK (ended_at IS NULL OR ended_at >= started_at)
);

-- Invariante central: no máximo UM estado aberto por filial + CT.
CREATE UNIQUE INDEX IF NOT EXISTS uq_pc_state_events_one_open_per_work_center
    ON production_control.work_center_state_events (branch, work_center)
    WHERE ended_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_pc_state_events_work_center_timeline
    ON production_control.work_center_state_events (branch, work_center, started_at);

CREATE INDEX IF NOT EXISTS idx_pc_state_events_run
    ON production_control.work_center_state_events (run_id);

CREATE INDEX IF NOT EXISTS idx_pc_state_events_state
    ON production_control.work_center_state_events (state);

CREATE TABLE IF NOT EXISTS production_control.downtime_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch VARCHAR(2) NOT NULL CHECK (branch IN ('01', '02')),
    work_center VARCHAR(40) NOT NULL,
    run_id UUID REFERENCES production_control.production_runs (id) ON DELETE RESTRICT,
    state_event_id UUID REFERENCES production_control.work_center_state_events (id) ON DELETE RESTRICT,
    production_order VARCHAR(40),
    operation_code VARCHAR(20),
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    reason_code VARCHAR(40)
        REFERENCES production_control.downtime_reason_catalog (code) ON DELETE RESTRICT,
    -- Snapshots da classificação aplicada no momento; NULL enquanto não
    -- classificada ou quando o motivo não traz defaults governados.
    planned BOOLEAN,
    counts_as_availability_loss BOOLEAN,
    source VARCHAR(40) NOT NULL DEFAULT 'system',
    confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    confirmed_at TIMESTAMPTZ,
    confirmed_by_type VARCHAR(40),
    confirmed_by_ref VARCHAR(120),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_pc_downtime_events_time_range
        CHECK (ended_at IS NULL OR ended_at >= started_at),
    -- Parada pode nascer sem motivo (Pause antes da classificação), mas nunca
    -- pode estar confirmada sem motivo nem carregar confirmação órfã.
    CONSTRAINT ck_pc_downtime_events_confirmed_requires_reason
        CHECK (NOT confirmed OR reason_code IS NOT NULL),
    CONSTRAINT ck_pc_downtime_events_confirmation_coherence
        CHECK (
            (confirmed AND confirmed_at IS NOT NULL)
            OR (NOT confirmed AND confirmed_at IS NULL)
        )
);

-- Invariante central: no máximo UMA parada aberta por filial + CT.
CREATE UNIQUE INDEX IF NOT EXISTS uq_pc_downtime_events_one_open_per_work_center
    ON production_control.downtime_events (branch, work_center)
    WHERE ended_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_pc_downtime_events_work_center_timeline
    ON production_control.downtime_events (branch, work_center, started_at);

CREATE INDEX IF NOT EXISTS idx_pc_downtime_events_run
    ON production_control.downtime_events (run_id);

CREATE INDEX IF NOT EXISTS idx_pc_downtime_events_state_event
    ON production_control.downtime_events (state_event_id);

-- Catálogo inicial: códigos estáveis, sem classificação OEE inventada.
INSERT INTO production_control.downtime_reason_catalog (
    code, label, category, requires_note, sort_order
) VALUES
    ('machine_mechanical', 'Falha mecânica',           'machine',     FALSE, 10),
    ('machine_electrical', 'Falha elétrica',           'machine',     FALSE, 20),
    ('tool',               'Ferramenta',               'tooling',     FALSE, 30),
    ('raw_material',       'Falta de material',        'material',    FALSE, 40),
    ('quality',            'Qualidade',                'quality',     FALSE, 50),
    ('setup',              'Setup / preparação',       'setup',       FALSE, 60),
    ('maintenance',        'Manutenção',               'maintenance', FALSE, 70),
    ('no_operator',        'Falta de operador',        'people',      FALSE, 80),
    ('logistics',          'Logística / abastecimento', 'logistics',  FALSE, 90),
    ('break',              'Intervalo',                'planned',     FALSE, 100),
    ('cleaning',           'Limpeza',                  'planned',     FALSE, 110),
    ('other',              'Outro',                    'other',       TRUE,  990)
ON CONFLICT (code) DO NOTHING;

COMMENT ON TABLE production_control.downtime_reason_catalog IS
    'Catálogo MES de motivos de parada; code é a identidade estável.';
COMMENT ON TABLE production_control.work_center_state_events IS
    'Timeline MES do estado operacional do CT (fatos; independente de telemetria).';
COMMENT ON TABLE production_control.downtime_events IS
    'Paradas MES com classificação posterior; um evento aberto por CT.';

COMMIT;
