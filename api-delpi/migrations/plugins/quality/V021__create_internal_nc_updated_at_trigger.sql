DROP TRIGGER IF EXISTS trg_internal_nonconformities_set_updated_at
    ON quality.internal_nonconformities;
CREATE TRIGGER trg_internal_nonconformities_set_updated_at
BEFORE UPDATE ON quality.internal_nonconformities
FOR EACH ROW
EXECUTE FUNCTION quality.set_updated_at();

DROP TRIGGER IF EXISTS trg_internal_nc_actions_set_updated_at
    ON quality.internal_nc_actions;
CREATE TRIGGER trg_internal_nc_actions_set_updated_at
BEFORE UPDATE ON quality.internal_nc_actions
FOR EACH ROW
EXECUTE FUNCTION quality.set_updated_at();