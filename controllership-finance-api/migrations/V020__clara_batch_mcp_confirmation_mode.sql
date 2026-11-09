-- CF-UX-053 — allow conversational MCP confirmation mode on batches.
-- Forward-only: extend consent_mode CHECK; do not rewrite V012.
-- Runtime still defaults to Portal V014 until Security ack arms the
-- conversational channel (CLARA_CONVERSATIONAL_SECURITY_ACK).

ALTER TABLE controllership_finance.clara_batch
    DROP CONSTRAINT IF EXISTS clara_batch_consent_mode_check;

ALTER TABLE controllership_finance.clara_batch
    ADD CONSTRAINT clara_batch_consent_mode_check
    CHECK (consent_mode IN (
        'NONE',
        'CONSOLIDATED',
        'HOST_ATTESTED',
        'MCP_CONFIRMATION'
    ));
