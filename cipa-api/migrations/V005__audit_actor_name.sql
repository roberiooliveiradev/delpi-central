BEGIN;

-- Snapshot imutável do ator no instante da ação (id já existia em actor_user_id).
ALTER TABLE cipa.meeting_minute_audit_logs
    ADD COLUMN IF NOT EXISTS actor_name VARCHAR(200);

ALTER TABLE cipa.meeting_minute_audit_logs
    ADD COLUMN IF NOT EXISTS actor_email VARCHAR(320);

COMMIT;
