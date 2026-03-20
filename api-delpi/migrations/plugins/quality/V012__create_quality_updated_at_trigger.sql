CREATE OR REPLACE FUNCTION quality.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_document_sequences_set_updated_at
    ON quality.document_sequences;
CREATE TRIGGER trg_document_sequences_set_updated_at
BEFORE UPDATE ON quality.document_sequences
FOR EACH ROW
EXECUTE FUNCTION quality.set_updated_at();

DROP TRIGGER IF EXISTS trg_external_nc_suppliers_set_updated_at
    ON quality.external_nc_suppliers;
CREATE TRIGGER trg_external_nc_suppliers_set_updated_at
BEFORE UPDATE ON quality.external_nc_suppliers
FOR EACH ROW
EXECUTE FUNCTION quality.set_updated_at();

DROP TRIGGER IF EXISTS trg_external_nonconformities_set_updated_at
    ON quality.external_nonconformities;
CREATE TRIGGER trg_external_nonconformities_set_updated_at
BEFORE UPDATE ON quality.external_nonconformities
FOR EACH ROW
EXECUTE FUNCTION quality.set_updated_at();

DROP TRIGGER IF EXISTS trg_external_nc_actions_set_updated_at
    ON quality.external_nc_actions;
CREATE TRIGGER trg_external_nc_actions_set_updated_at
BEFORE UPDATE ON quality.external_nc_actions
FOR EACH ROW
EXECUTE FUNCTION quality.set_updated_at();