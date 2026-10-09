-- V055 — Soft delete de salas de interação do Transformômetro.
--
-- 1) tm_interaction_rooms.deleted_at — sala excluída permanece
--    persistida (mensagens/anexos/reações históricas intactas), mas
--    sai das consultas de salas ativas.
-- 2) A unicidade por processo passa a valer apenas para sala ATIVA:
--    a constraint UNIQUE(processo_id) impediria reabrir a sala após
--    soft delete; substituída por índice único parcial.
BEGIN;

ALTER TABLE transformometro.tm_interaction_rooms
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

ALTER TABLE transformometro.tm_interaction_rooms
    DROP CONSTRAINT IF EXISTS uq_tm_interaction_rooms_processo;

CREATE UNIQUE INDEX IF NOT EXISTS uq_tm_interaction_rooms_processo_active
    ON transformometro.tm_interaction_rooms (processo_id)
    WHERE deleted_at IS NULL;

COMMIT;
