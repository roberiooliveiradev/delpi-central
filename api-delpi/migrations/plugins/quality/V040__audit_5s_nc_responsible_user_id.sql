-- UUID do usuário Minha Delpi (core-api.users.id) designado como responsável da NC.
-- responsible_name permanece como rótulo de exibição; NCs legadas ficam só com nome.

ALTER TABLE quality.audit_5s_nonconformities
    ADD COLUMN IF NOT EXISTS responsible_user_id VARCHAR(100);

CREATE INDEX IF NOT EXISTS ix_audit_5s_nc_responsible_user_id
    ON quality.audit_5s_nonconformities (responsible_user_id)
    WHERE responsible_user_id IS NOT NULL;
