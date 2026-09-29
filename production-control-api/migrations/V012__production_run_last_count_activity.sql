-- V012 — Baseline de atividade de contagem para detecção automática de parada.
--
-- `last_count_activity_at` = instante do último incremento real de peças
-- (ou do Play, como baseline). Persistido para sobreviver a restart de
-- API/container. NULL em runs legados: o poller inicializa o baseline no
-- primeiro snapshot Pulse válido — nunca gera parada retroativa.

ALTER TABLE production_control.production_runs
    ADD COLUMN IF NOT EXISTS last_count_activity_at TIMESTAMPTZ NULL;
