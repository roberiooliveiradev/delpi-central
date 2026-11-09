-- V021 — CF-UX-054: a trilha de auditoria deixa de impedir a exclusão
-- de uma competência sem dependências operacionais.
--
-- `closing_audit_event` é append-only. A FK ON DELETE RESTRICT fazia
-- a auditoria de abertura bloquear qualquer DELETE da competência.
-- ON DELETE SET NULL preserva a linha histórica (entity_id, event_type,
-- ator, detail e created_at). O detail da exclusão guarda period e
-- competence_id. Nenhum log é apagado e nenhuma FK operacional passa
-- a CASCADE.

BEGIN;

ALTER TABLE controllership_finance.closing_audit_event
    DROP CONSTRAINT closing_audit_event_competence_id_fkey;

ALTER TABLE controllership_finance.closing_audit_event
    ADD CONSTRAINT closing_audit_event_competence_id_fkey
    FOREIGN KEY (competence_id)
    REFERENCES controllership_finance.monthly_competence (competence_id)
    ON DELETE SET NULL;

COMMENT ON CONSTRAINT closing_audit_event_competence_id_fkey
    ON controllership_finance.closing_audit_event IS
    'CF-UX-054: auditoria histórica não bloqueia a exclusão da competência. SET NULL preserva a linha; entity_id e detail mantêm a referência.';

COMMIT;
