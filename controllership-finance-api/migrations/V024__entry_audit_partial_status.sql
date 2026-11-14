-- V024 — execução parcial quando o XML de uma nota não pôde ser lido.
-- Não reescreve a V023. Rollback de código não apaga a constraint nova.

BEGIN;

ALTER TABLE controllership_finance.entry_audit_analysis
    DROP CONSTRAINT IF EXISTS entry_audit_analysis_status_check;

ALTER TABLE controllership_finance.entry_audit_analysis
    ADD CONSTRAINT entry_audit_analysis_status_check
    CHECK (status IN ('queued', 'running', 'done', 'failed', 'partial'));

ALTER TABLE controllership_finance.entry_audit_run
    DROP CONSTRAINT IF EXISTS entry_audit_run_status_check;

ALTER TABLE controllership_finance.entry_audit_run
    ADD CONSTRAINT entry_audit_run_status_check
    CHECK (status IN ('queued', 'running', 'done', 'failed', 'partial'));

COMMIT;
