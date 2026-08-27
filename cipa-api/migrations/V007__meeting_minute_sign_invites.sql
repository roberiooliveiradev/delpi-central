-- Convites de assinatura (magic link) para atas CIPA.

BEGIN;

CREATE TABLE IF NOT EXISTS cipa.meeting_minute_sign_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signer_id UUID NOT NULL
        REFERENCES cipa.meeting_minute_signers(id) ON DELETE CASCADE,
    minute_id UUID NOT NULL
        REFERENCES cipa.meeting_minutes(id) ON DELETE CASCADE,
    unit_code CHAR(2) NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cipa_sign_invites_token_hash UNIQUE (token_hash)
);

CREATE INDEX IF NOT EXISTS idx_cipa_sign_invites_signer_open
    ON cipa.meeting_minute_sign_invites (signer_id)
    WHERE consumed_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_cipa_sign_invites_minute
    ON cipa.meeting_minute_sign_invites (minute_id, created_at DESC);

COMMENT ON TABLE cipa.meeting_minute_sign_invites IS
    'Tokens opacos (só hash) para assinatura pública de atas CIPA.';

COMMIT;
