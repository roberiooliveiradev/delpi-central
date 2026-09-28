BEGIN;

ALTER TABLE production_control.production_runs
    ADD COLUMN IF NOT EXISTS target_pieces_snapshot BIGINT;

ALTER TABLE production_control.production_runs
    DROP CONSTRAINT IF EXISTS ck_pc_production_runs_target_pieces_positive;

ALTER TABLE production_control.production_runs
    ADD CONSTRAINT ck_pc_production_runs_target_pieces_positive
    CHECK (target_pieces_snapshot IS NULL OR target_pieces_snapshot > 0);

COMMENT ON COLUMN production_control.production_runs.target_pieces_snapshot IS
    'Meta congelada do run em peças inteiras, normalizada no Play; NULL para runs legados ou unidade sem conversão.';

COMMIT;
