CREATE INDEX IF NOT EXISTS idx_external_nonconformities_supplier_id
    ON quality.external_nonconformities (supplier_id);

CREATE INDEX IF NOT EXISTS idx_external_nonconformities_current_status
    ON quality.external_nonconformities (current_status);

CREATE INDEX IF NOT EXISTS idx_external_nonconformities_supplier_status
    ON quality.external_nonconformities (supplier_status);

CREATE INDEX IF NOT EXISTS idx_external_nonconformities_due_date
    ON quality.external_nonconformities (due_date);

CREATE INDEX IF NOT EXISTS idx_external_nonconformities_occurrence_date
    ON quality.external_nonconformities (occurrence_date);

CREATE INDEX IF NOT EXISTS idx_external_nonconformities_detection_date
    ON quality.external_nonconformities (detection_date);

CREATE INDEX IF NOT EXISTS idx_external_nonconformities_responsible_user_id
    ON quality.external_nonconformities (responsible_user_id);

CREATE INDEX IF NOT EXISTS idx_external_nonconformities_material_code
    ON quality.external_nonconformities (material_code);

CREATE INDEX IF NOT EXISTS idx_external_nonconformities_lot_number
    ON quality.external_nonconformities (lot_number);

CREATE INDEX IF NOT EXISTS idx_external_nonconformities_purchase_order
    ON quality.external_nonconformities (purchase_order);

CREATE INDEX IF NOT EXISTS idx_external_nonconformities_invoice_number
    ON quality.external_nonconformities (invoice_number);

CREATE INDEX IF NOT EXISTS idx_external_nc_root_causes_nonconformity_id
    ON quality.external_nc_root_causes (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_root_causes_is_root_cause
    ON quality.external_nc_root_causes (is_root_cause);

CREATE INDEX IF NOT EXISTS idx_external_nc_actions_nonconformity_id
    ON quality.external_nc_actions (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_actions_root_cause_id
    ON quality.external_nc_actions (root_cause_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_actions_status
    ON quality.external_nc_actions (status);

CREATE INDEX IF NOT EXISTS idx_external_nc_actions_due_date
    ON quality.external_nc_actions (due_date);

CREATE INDEX IF NOT EXISTS idx_external_nc_actions_effectiveness_due_date
    ON quality.external_nc_actions (effectiveness_due_date);

CREATE INDEX IF NOT EXISTS idx_external_nc_effectiveness_checks_nonconformity_id
    ON quality.external_nc_effectiveness_checks (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_effectiveness_checks_action_id
    ON quality.external_nc_effectiveness_checks (action_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_attachments_nonconformity_id
    ON quality.external_nc_attachments (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_attachments_action_id
    ON quality.external_nc_attachments (action_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_attachments_effectiveness_check_id
    ON quality.external_nc_attachments (effectiveness_check_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_comments_nonconformity_id
    ON quality.external_nc_comments (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_team_members_nonconformity_id
    ON quality.external_nc_team_members (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_team_members_user_id
    ON quality.external_nc_team_members (user_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_audit_events_nonconformity_id
    ON quality.external_nc_audit_events (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_external_nc_audit_events_event_type
    ON quality.external_nc_audit_events (event_type);

CREATE INDEX IF NOT EXISTS idx_external_nc_audit_events_created_at
    ON quality.external_nc_audit_events (created_at);

CREATE INDEX IF NOT EXISTS idx_external_nc_suppliers_active
    ON quality.external_nc_suppliers (active);

CREATE INDEX IF NOT EXISTS idx_external_nc_suppliers_legal_name
    ON quality.external_nc_suppliers (legal_name);

CREATE INDEX IF NOT EXISTS idx_external_nc_suppliers_trade_name
    ON quality.external_nc_suppliers (trade_name);