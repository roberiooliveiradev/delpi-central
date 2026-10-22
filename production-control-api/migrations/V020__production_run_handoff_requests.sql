BEGIN;

-- Troca guiada de OP (handoff): idempotência durável da confirmação.
-- Uma linha por requestId confirmado — persistida na MESMA transação que
-- encerra o run anterior e cria o novo; replay devolve a resposta gravada.

CREATE TABLE IF NOT EXISTS production_control.production_run_handoff_requests (
    request_id UUID PRIMARY KEY,
    branch VARCHAR(2) NOT NULL CHECK (branch IN ('01', '02')),
    work_center VARCHAR(40) NOT NULL,
    previous_run_id UUID NOT NULL,
    new_run_id UUID,
    request_hash VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (status IN ('completed')),
    response JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pc_run_handoff_requests_previous_run
    ON production_control.production_run_handoff_requests (previous_run_id);

COMMENT ON TABLE production_control.production_run_handoff_requests IS
    'Idempotência durável da troca guiada de OP — requestId → resultado confirmado.';

-- O segmento do run encerrado pela troca fecha com end_reason='handoff'.
ALTER TABLE production_control.production_run_segments
    DROP CONSTRAINT production_run_segments_end_reason_check;
ALTER TABLE production_control.production_run_segments
    ADD CONSTRAINT production_run_segments_end_reason_check CHECK (
        end_reason IS NULL
        OR end_reason IN ('pause', 'stop', 'epoch_change', 'device_swap', 'abort', 'handoff')
    );

COMMIT;
