-- Histórico de alterações das NCs LMP (append-only).
-- Registra ator (id, e-mail, nome) e diff dos campos.

CREATE TABLE IF NOT EXISTS engineering.lmp_nonconformity_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nonconformity_id UUID NOT NULL,
    event_type VARCHAR(40) NOT NULL,
    changes JSONB NOT NULL DEFAULT '{}'::jsonb,
    actor_user_id VARCHAR(100) NOT NULL,
    actor_email VARCHAR(255),
    actor_name VARCHAR(300),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_lmp_nc_history_nc
        FOREIGN KEY (nonconformity_id)
        REFERENCES engineering.lmp_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_lmp_nc_history_event_type CHECK (
        event_type IN ('created', 'updated')
    )
);

CREATE INDEX IF NOT EXISTS ix_lmp_nc_history_nc_created
    ON engineering.lmp_nonconformity_history (nonconformity_id, created_at DESC);

CREATE OR REPLACE FUNCTION engineering.prevent_lmp_nc_history_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'lmp_nonconformity_history is append-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_lmp_nc_history_no_mutation
    ON engineering.lmp_nonconformity_history;

CREATE TRIGGER trg_lmp_nc_history_no_mutation
    BEFORE UPDATE OR DELETE ON engineering.lmp_nonconformity_history
    FOR EACH ROW
    EXECUTE PROCEDURE engineering.prevent_lmp_nc_history_mutation();

COMMENT ON TABLE engineering.lmp_nonconformity_history IS
    'Histórico imutável de criação/alteração de NCs LMP (ator + diffs).';
COMMENT ON COLUMN engineering.lmp_nonconformity_history.actor_user_id IS
    'ID do usuário autenticado que gerou o evento.';
COMMENT ON COLUMN engineering.lmp_nonconformity_history.actor_email IS
    'E-mail do usuário no momento do evento.';
COMMENT ON COLUMN engineering.lmp_nonconformity_history.actor_name IS
    'Nome do usuário no momento do evento.';
COMMENT ON COLUMN engineering.lmp_nonconformity_history.changes IS
    'JSONB com campos alterados: { "fields": [ { "field", "label", "old", "new" } ] }.';
