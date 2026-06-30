-- Permite registrar exclusão (soft delete) de planos e ações removidas no histórico.

ALTER TABLE quality.quality_action_history
    DROP CONSTRAINT IF EXISTS ck_quality_action_history_event_type;

ALTER TABLE quality.quality_action_history
    ADD CONSTRAINT ck_quality_action_history_event_type CHECK (
        event_type IN (
            'plan_created',
            'plan_updated',
            'plan_deleted',
            'status_changed',
            'action_created',
            'action_updated',
            'action_completed',
            'action_deleted',
            'ishikawa_updated',
            'five_whys_updated',
            'effectiveness_reviewed',
            'effectiveness_submitted',
            'effectiveness_approval_rejected',
            'plan_closed',
            'plan_reopened'
        )
    );
