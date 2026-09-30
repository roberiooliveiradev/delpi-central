BEGIN;

-- V013 — Snapshots de Performance congelados no Play do Production Run.
--
-- Depois que o run inicia, os parâmetros que interpretam aquele run ficam
-- estáveis: alteração futura em SHY/SG2 (TOTVS) não pode mudar a leitura
-- de um run já iniciado. Runs legados permanecem com NULL (sem backfill).

ALTER TABLE production_control.production_runs
    ADD COLUMN IF NOT EXISTS ideal_cycle_seconds_snapshot NUMERIC(18, 6);

ALTER TABLE production_control.production_runs
    ADD COLUMN IF NOT EXISTS setup_seconds_snapshot NUMERIC(18, 6);

ALTER TABLE production_control.production_runs
    ADD COLUMN IF NOT EXISTS standard_time_source VARCHAR(40);

ALTER TABLE production_control.production_runs
    ADD COLUMN IF NOT EXISTS standard_time_data_quality_snapshot VARCHAR(50);

ALTER TABLE production_control.production_runs
    ADD COLUMN IF NOT EXISTS workstation_type_snapshot VARCHAR(40);

ALTER TABLE production_control.production_runs
    ADD COLUMN IF NOT EXISTS pieces_per_pulse_snapshot NUMERIC(18, 6);

ALTER TABLE production_control.production_runs
    DROP CONSTRAINT IF EXISTS ck_pc_production_runs_ideal_cycle_positive;

ALTER TABLE production_control.production_runs
    ADD CONSTRAINT ck_pc_production_runs_ideal_cycle_positive
    CHECK (ideal_cycle_seconds_snapshot IS NULL OR ideal_cycle_seconds_snapshot > 0);

ALTER TABLE production_control.production_runs
    DROP CONSTRAINT IF EXISTS ck_pc_production_runs_setup_seconds_nonneg;

ALTER TABLE production_control.production_runs
    ADD CONSTRAINT ck_pc_production_runs_setup_seconds_nonneg
    CHECK (setup_seconds_snapshot IS NULL OR setup_seconds_snapshot >= 0);

ALTER TABLE production_control.production_runs
    DROP CONSTRAINT IF EXISTS ck_pc_production_runs_pieces_per_pulse_positive;

ALTER TABLE production_control.production_runs
    ADD CONSTRAINT ck_pc_production_runs_pieces_per_pulse_positive
    CHECK (pieces_per_pulse_snapshot IS NULL OR pieces_per_pulse_snapshot > 0);

COMMENT ON COLUMN production_control.production_runs.ideal_cycle_seconds_snapshot IS
    'Ciclo padrão congelado no Play, em segundos por peça física (api-delpi, já normalizado pelo piecesFactor da unidade); NULL quando indisponível.';

COMMENT ON COLUMN production_control.production_runs.setup_seconds_snapshot IS
    'Setup congelado no Play, em segundos (COALESCE HY_SETUP, G2_SETUP na api-delpi); separado do ciclo unitário.';

COMMENT ON COLUMN production_control.production_runs.standard_time_source IS
    'Fonte do tempo padrão congelada: shy_tempad, shy_tempom_quant, sg2_tempad ou unavailable.';

COMMENT ON COLUMN production_control.production_runs.standard_time_data_quality_snapshot IS
    'Qualidade do snapshot: complete, standard_time_unavailable, piece_conversion_unavailable ou upstream_unavailable (falha local ao consultar a api-delpi).';

COMMENT ON COLUMN production_control.production_runs.workstation_type_snapshot IS
    'Tipo de posto congelado no Play: manual_workstation quando H8_FERRAM=MOD; NULL para os demais (sem classificação confiável).';

COMMENT ON COLUMN production_control.production_runs.pieces_per_pulse_snapshot IS
    'Peças físicas por incremento do counter Pulse congelado no Play; hoje sempre 1 (pulso 1:1). Não confundir com pieces_conversion_factor (unidade ERP→peça).';

COMMIT;
