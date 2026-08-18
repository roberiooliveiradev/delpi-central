-- E9.S2 — mural global único (wall sem group_id).

CREATE UNIQUE INDEX IF NOT EXISTS uq_commercial_interaction_rooms_wall_global
    ON commercial.interaction_rooms (kind)
    WHERE kind = 'wall' AND group_id IS NULL AND deleted_at IS NULL;

COMMENT ON INDEX commercial.uq_commercial_interaction_rooms_wall_global IS
    'Garante um único mural global (kind=wall sem group_id).';
