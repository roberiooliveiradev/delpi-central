-- Convites de assinatura (magic link) + signatário externo (e-mail sem user Delpi).
-- Não editar V042; esta migration é o único ponto de alteração de schema.

BEGIN;

-- Signatários: user_id opcional; e-mail obrigatório quando sem user.
ALTER TABLE transformometro.tm_meeting_minute_signers
    ALTER COLUMN user_id DROP NOT NULL;

ALTER TABLE transformometro.tm_meeting_minute_signers
    ADD COLUMN IF NOT EXISTS invite_email VARCHAR(320);

ALTER TABLE transformometro.tm_meeting_minute_signers
    DROP CONSTRAINT IF EXISTS tm_meeting_minute_signers_version_id_user_id_key;

CREATE UNIQUE INDEX IF NOT EXISTS uq_tm_signers_version_user
    ON transformometro.tm_meeting_minute_signers (version_id, user_id)
    WHERE user_id IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_tm_signers_user_or_email'
          AND conrelid = 'transformometro.tm_meeting_minute_signers'::regclass
    ) THEN
        ALTER TABLE transformometro.tm_meeting_minute_signers
            ADD CONSTRAINT ck_tm_signers_user_or_email
            CHECK (user_id IS NOT NULL OR invite_email IS NOT NULL);
    END IF;
END $$;

-- Assinaturas: user_id pode ser nulo (externo via magic link).
ALTER TABLE transformometro.tm_meeting_minute_signatures
    ALTER COLUMN user_id DROP NOT NULL;

ALTER TABLE transformometro.tm_meeting_minute_signatures
    DROP CONSTRAINT IF EXISTS tm_meeting_minute_signatures_version_id_user_id_key;

CREATE UNIQUE INDEX IF NOT EXISTS uq_tm_signatures_version_user
    ON transformometro.tm_meeting_minute_signatures (version_id, user_id)
    WHERE user_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS transformometro.tm_meeting_minute_sign_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signer_id UUID NOT NULL
        REFERENCES transformometro.tm_meeting_minute_signers(id) ON DELETE CASCADE,
    minute_id UUID NOT NULL
        REFERENCES transformometro.tm_meeting_minutes(id) ON DELETE CASCADE,
    unit_code CHAR(2) NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tm_sign_invites_token_hash UNIQUE (token_hash)
);

CREATE INDEX IF NOT EXISTS idx_tm_sign_invites_signer_open
    ON transformometro.tm_meeting_minute_sign_invites (signer_id)
    WHERE consumed_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_tm_sign_invites_minute
    ON transformometro.tm_meeting_minute_sign_invites (minute_id, created_at DESC);

COMMENT ON TABLE transformometro.tm_meeting_minute_sign_invites IS
    'Tokens opacos (só hash) para assinatura pública de atas Transforma+.';

COMMIT;
