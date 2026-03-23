CREATE INDEX IF NOT EXISTS idx_internal_nonconformities_current_status
    ON quality.internal_nonconformities (current_status);

CREATE INDEX IF NOT EXISTS idx_internal_nonconformities_detection_date
    ON quality.internal_nonconformities (detection_date);

CREATE INDEX IF NOT EXISTS idx_internal_nonconformities_due_date
    ON quality.internal_nonconformities (due_date);

CREATE INDEX IF NOT EXISTS idx_internal_nonconformities_item_code
    ON quality.internal_nonconformities (item_code);

CREATE INDEX IF NOT EXISTS idx_internal_nonconformities_lot_number
    ON quality.internal_nonconformities (lot_number);

CREATE INDEX IF NOT EXISTS idx_internal_nonconformities_production_order
    ON quality.internal_nonconformities (production_order);

CREATE INDEX IF NOT EXISTS idx_internal_nonconformities_sector
    ON quality.internal_nonconformities (sector);

CREATE INDEX IF NOT EXISTS idx_internal_nonconformities_responsible_user_id
    ON quality.internal_nonconformities (responsible_user_id);

CREATE INDEX IF NOT EXISTS idx_internal_nc_root_causes_nonconformity_id
    ON quality.internal_nc_root_causes (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_internal_nc_actions_nonconformity_id
    ON quality.internal_nc_actions (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_internal_nc_actions_root_cause_id
    ON quality.internal_nc_actions (root_cause_id);

CREATE INDEX IF NOT EXISTS idx_internal_nc_actions_status
    ON quality.internal_nc_actions (status);

CREATE INDEX IF NOT EXISTS idx_internal_nc_actions_due_date
    ON quality.internal_nc_actions (due_date);

CREATE INDEX IF NOT EXISTS idx_internal_nc_effectiveness_checks_nonconformity_id
    ON quality.internal_nc_effectiveness_checks (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_internal_nc_effectiveness_checks_action_id
    ON quality.internal_nc_effectiveness_checks (action_id);

CREATE INDEX IF NOT EXISTS idx_internal_nc_team_members_nonconformity_id
    ON quality.internal_nc_team_members (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_internal_nc_team_members_user_id
    ON quality.internal_nc_team_members (user_id);

CREATE INDEX IF NOT EXISTS idx_internal_nc_comments_nonconformity_id
    ON quality.internal_nc_comments (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_internal_nc_audit_events_nonconformity_id
    ON quality.internal_nc_audit_events (nonconformity_id);

CREATE INDEX IF NOT EXISTS idx_internal_nc_audit_events_event_type
    ON quality.internal_nc_audit_events (event_type);

CREATE INDEX IF NOT EXISTS idx_internal_nc_audit_events_created_at
    ON quality.internal_nc_audit_events (created_at);