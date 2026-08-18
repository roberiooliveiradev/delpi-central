BEGIN;

ALTER TABLE strategic_indicators.settings_audit
    DROP CONSTRAINT IF EXISTS ck_si_settings_audit_event_type;

ALTER TABLE strategic_indicators.settings_audit
    ADD CONSTRAINT ck_si_settings_audit_event_type CHECK (
        event_type IN (
            'settings.updated',
            'indicator_goal.created',
            'indicator_goal.updated',
            'indicator_goal.activated',
            'indicator_goal.deactivated',
            'config.exported',
            'config.imported'
        )
    );

COMMIT;
