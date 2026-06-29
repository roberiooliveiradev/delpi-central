-- Linha do tempo PAC — nome e e-mail de quem alterou (além do id)

ALTER TABLE quality.quality_action_history
    ADD COLUMN IF NOT EXISTS created_by_name VARCHAR(200),
    ADD COLUMN IF NOT EXISTS created_by_email VARCHAR(255);

ALTER TABLE quality.quality_audit_log
    ADD COLUMN IF NOT EXISTS actor_name VARCHAR(200),
    ADD COLUMN IF NOT EXISTS actor_email VARCHAR(255);

ALTER TABLE quality.quality_problem_evidences
    ADD COLUMN IF NOT EXISTS uploaded_by_name VARCHAR(200),
    ADD COLUMN IF NOT EXISTS uploaded_by_email VARCHAR(255);

COMMENT ON COLUMN quality.quality_action_history.created_by_name IS
    'Nome exibido do autor do evento na linha do tempo.';
COMMENT ON COLUMN quality.quality_action_history.created_by_email IS
    'E-mail do autor do evento na linha do tempo.';
COMMENT ON COLUMN quality.quality_audit_log.actor_name IS
    'Nome exibido do ator na trilha de auditoria.';
COMMENT ON COLUMN quality.quality_audit_log.actor_email IS
    'E-mail do ator na trilha de auditoria.';
COMMENT ON COLUMN quality.quality_problem_evidences.uploaded_by_name IS
    'Nome exibido de quem anexou a evidência.';
COMMENT ON COLUMN quality.quality_problem_evidences.uploaded_by_email IS
    'E-mail de quem anexou a evidência.';
