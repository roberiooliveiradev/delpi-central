BEGIN;

-- MES shadow: sessão de bancada + runs de contagem (golpes Pulse → peças).

CREATE TABLE IF NOT EXISTS production_control.operator_bench_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch VARCHAR(2) NOT NULL CHECK (branch IN ('01', '02')),
    work_center VARCHAR(40) NOT NULL,
    operator_code VARCHAR(40) NOT NULL,
    operator_name VARCHAR(120),
    session_token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pc_bench_sessions_token_hash
    ON production_control.operator_bench_sessions (session_token_hash)
    WHERE ended_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_pc_bench_sessions_work_center
    ON production_control.operator_bench_sessions (branch, work_center)
    WHERE ended_at IS NULL;

CREATE TABLE IF NOT EXISTS production_control.production_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch VARCHAR(2) NOT NULL CHECK (branch IN ('01', '02')),
    work_center VARCHAR(40) NOT NULL,
    production_order VARCHAR(40) NOT NULL,
    operation_code VARCHAR(20) NOT NULL,
    device_id UUID NOT NULL,
    operator_code VARCHAR(40) NOT NULL,
    operator_name VARCHAR(120),
    bench_session_id UUID REFERENCES production_control.operator_bench_sessions (id),
    status VARCHAR(20) NOT NULL CHECK (
        status IN ('running', 'paused', 'completed', 'aborted')
    ),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    pieces_total BIGINT NOT NULL DEFAULT 0 CHECK (pieces_total >= 0),
    planned_qty_snapshot NUMERIC(18, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pc_production_runs_one_active_per_work_center
    ON production_control.production_runs (branch, work_center)
    WHERE status IN ('running', 'paused');

CREATE INDEX IF NOT EXISTS idx_pc_production_runs_status
    ON production_control.production_runs (status)
    WHERE status IN ('running', 'paused');

CREATE INDEX IF NOT EXISTS idx_pc_production_runs_device
    ON production_control.production_runs (device_id)
    WHERE status IN ('running', 'paused');

CREATE TABLE IF NOT EXISTS production_control.production_run_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES production_control.production_runs (id) ON DELETE CASCADE,
    device_id UUID NOT NULL,
    anchor_counter BIGINT NOT NULL,
    anchor_epoch BIGINT NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    pieces BIGINT NOT NULL DEFAULT 0 CHECK (pieces >= 0),
    end_reason VARCHAR(40) CHECK (
        end_reason IS NULL
        OR end_reason IN ('pause', 'stop', 'epoch_change', 'device_swap', 'abort')
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pc_run_segments_one_open
    ON production_control.production_run_segments (run_id)
    WHERE ended_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_pc_run_segments_run_id
    ON production_control.production_run_segments (run_id);

COMMENT ON TABLE production_control.production_runs IS
    'MES shadow — run de contagem no cockpit; não grava SH6010/HZA.';
COMMENT ON TABLE production_control.production_run_segments IS
    'Segmentos de âncora absoluta (counter + epoch) do device Pulse.';

COMMIT;
