-- Id UUID da linha de status para a trilha closing_audit_event,
-- cujo entity_id é UUID. A stable_key continua a chave de negócio
-- e vai no payload do evento. A V023 não é reescrita.

ALTER TABLE controllership_finance.entry_audit_status
    ADD COLUMN IF NOT EXISTS id UUID NOT NULL DEFAULT gen_random_uuid();

CREATE UNIQUE INDEX IF NOT EXISTS entry_audit_status_id_uidx
    ON controllership_finance.entry_audit_status (id);
