-- Corrige exclusão de NC: ON DELETE CASCADE do histórico conflitava com
-- o trigger append-only (BEFORE DELETE RAISE). DELETE no histórico só é
-- permitido com GUC de sessão app.allow_lmp_nc_history_delete=true
-- (definido pelo repositório ao excluir a NC pai). UPDATE continua bloqueado.

CREATE OR REPLACE FUNCTION engineering.prevent_lmp_nc_history_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE'
       AND lower(coalesce(current_setting('app.allow_lmp_nc_history_delete', true), ''))
           = 'true' THEN
        RETURN OLD;
    END IF;

    RAISE EXCEPTION 'lmp_nonconformity_history is append-only';
END;
$$;

COMMENT ON FUNCTION engineering.prevent_lmp_nc_history_mutation() IS
    'Bloqueia UPDATE e DELETE no histórico; DELETE liberado só com app.allow_lmp_nc_history_delete=true (exclusão da NC pai).';
