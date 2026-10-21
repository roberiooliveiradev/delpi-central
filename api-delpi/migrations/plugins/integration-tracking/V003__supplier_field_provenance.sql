-- Supplier write provenance — field-level origin/mode bound to operations.
-- Owner: api-delpi (postgres-plugins, schema integration_tracking).
--
-- Rows are immutable facts of intent recorded atomically with the CREATED
-- operation. Operational state stays in integration_operations (the
-- authority); this table never mirrors status and never stores field
-- values, secrets or external payloads — only source/mode metadata.

CREATE TABLE IF NOT EXISTS integration_tracking.supplier_field_provenance (
    provenance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id UUID NOT NULL,
    supplier_code VARCHAR(6),
    supplier_store VARCHAR(2),
    environment_key VARCHAR(120),
    field_key VARCHAR(60) NOT NULL,
    source_type VARCHAR(30) NOT NULL,
    change_mode VARCHAR(60),
    source_id VARCHAR(120),
    source_reference VARCHAR(300),
    source_retrieved_at TIMESTAMPTZ,
    reason_code VARCHAR(120),
    review_id VARCHAR(120),
    decision_id VARCHAR(120),
    initiating_client_id VARCHAR(120),
    actor_subject VARCHAR(120),
    provenance_schema_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_supplier_field_provenance_operation
        FOREIGN KEY (operation_id)
        REFERENCES integration_tracking.integration_operations (operation_id)
        ON DELETE RESTRICT,
    CONSTRAINT supplier_field_provenance_source_type_chk CHECK (
        source_type IN (
            'MANUAL_USER_INPUT',
            'GOVERNMENT_API',
            'THIRD_PARTY_API',
            'INTERNAL_SYSTEM',
            'IMPORT',
            'AUTOMATION_RULE',
            'UNKNOWN_LEGACY'
        )
    ),
    CONSTRAINT supplier_field_provenance_change_mode_chk CHECK (
        change_mode IS NULL
        OR change_mode IN (
            'MANUAL_DIRECT',
            'EXTERNAL_SUGGESTION_USER_APPROVED',
            'BULK_SUGGESTION_USER_APPROVED',
            'AUTOMATED_BY_APPROVED_POLICY',
            'SYSTEM_SYNC',
            'IMPORT_JOB'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_supplier_field_provenance_op
    ON integration_tracking.supplier_field_provenance (operation_id);

CREATE INDEX IF NOT EXISTS idx_supplier_field_provenance_supplier
    ON integration_tracking.supplier_field_provenance
    (supplier_code, supplier_store, field_key);

CREATE INDEX IF NOT EXISTS idx_supplier_field_provenance_client
    ON integration_tracking.supplier_field_provenance (initiating_client_id);
