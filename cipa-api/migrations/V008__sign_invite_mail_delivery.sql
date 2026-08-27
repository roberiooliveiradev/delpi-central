-- Status de envio e entrega de e-mail por convite de assinatura (CIPA).

BEGIN;

ALTER TABLE cipa.meeting_minute_sign_invites
    ADD COLUMN IF NOT EXISTS mail_template_key VARCHAR(32),
    ADD COLUMN IF NOT EXISTS mail_recipient VARCHAR(320),
    ADD COLUMN IF NOT EXISTS mail_send_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS mail_delivery_status VARCHAR(32) NOT NULL DEFAULT 'not_applicable',
    ADD COLUMN IF NOT EXISTS mail_attempts INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS mail_last_error TEXT,
    ADD COLUMN IF NOT EXISTS mail_sent_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS mail_delivered_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS mail_trace_id VARCHAR(128);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_cipa_sign_invites_mail_send_status'
          AND conrelid = 'cipa.meeting_minute_sign_invites'::regclass
    ) THEN
        ALTER TABLE cipa.meeting_minute_sign_invites
            ADD CONSTRAINT ck_cipa_sign_invites_mail_send_status
            CHECK (mail_send_status IN (
                'pending',
                'skipped_no_email',
                'skipped_mail_disabled',
                'skipped_graph_unconfigured',
                'failed',
                'accepted'
            ));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_cipa_sign_invites_mail_delivery_status'
          AND conrelid = 'cipa.meeting_minute_sign_invites'::regclass
    ) THEN
        ALTER TABLE cipa.meeting_minute_sign_invites
            ADD CONSTRAINT ck_cipa_sign_invites_mail_delivery_status
            CHECK (mail_delivery_status IN (
                'not_applicable',
                'trace_pending',
                'delivered',
                'bounced',
                'unknown'
            ));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_cipa_sign_invites_mail_trace_pending
    ON cipa.meeting_minute_sign_invites (mail_sent_at DESC)
    WHERE mail_send_status = 'accepted'
      AND mail_delivery_status = 'trace_pending';

COMMENT ON COLUMN cipa.meeting_minute_sign_invites.mail_send_status IS
    'Resultado síncrono do sendMail Graph (accepted = HTTP 202).';
COMMENT ON COLUMN cipa.meeting_minute_sign_invites.mail_delivery_status IS
    'Entrega confirmada via Message Trace (trace_pending → delivered/bounced/unknown).';

COMMIT;
